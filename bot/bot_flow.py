# bot/bot_flow.py

import yaml
import json
import logging
from typing import Optional, List, Dict, Tuple
from pathlib import Path
import random
import asyncio

import openai
from db.crud import (
    create_message,
    get_conversation_by_id,
    update_conversation,
    create_analysis_data,
    get_conversation_analysis_data,
    create_llm_query,
)

from db.db_session import get_session
from db.models import ConvoStateEnum, RoleEnum, ResponseTypeEnum, AnalysisData
from db.crud import get_conversation_messages
from bot.config import CurrentConfig
from bot.logger_setup import setup_logger
from bot.reappraisal_generator_1b import ReappraisalGenerator

logger = setup_logger()

# Load prompts and bot_msgs
bot_dir = Path(__file__).parent
with open(bot_dir / "bot_msgs.yml", "r") as f:
    bot_msgs = yaml.safe_load(f)

with open(bot_dir / "prompts.yml", "r") as f:
    prompts = yaml.safe_load(f)
    
with open(bot_dir / "val_list.json", "r") as f:
    val_list = json.load(f)

# Need to link the llm query table id and messaage ids

class Chatbot:
    """
    A small utility to query OpenAI with a 'system' prompt + conversation history.
    """
    @staticmethod
    def query_gpt(system_prompt: str,
                  messages: List[Dict[str, str]],
                  convo_id: Optional[int],
                  message_id: Optional[int] = None,
                  max_tries: int = 3) -> str:
        """
        Query GPT with the system prompt + any additional messages.
        Returns the text or an empty string if it fails.
        """
        model = CurrentConfig.openai_chat_model
        temperature = CurrentConfig.openai_temperature

        # Construct the final message array
        # if model contains "4o" then role is system, else developer
        # role = "system" if "4o" in model else "developer"
        role = "developer"
        full_messages = [{"role": role, "content": system_prompt}] + messages 
        logger.debug(f"Calling OpenAI with {len(messages)} messages and system prompt: {system_prompt}")
        # logger.debug(f"Calling OpenAI with system prompt: {system_prompt}")
        # logger.debug(f"Messages: {messages}")
        for attempt in range(max_tries):
            try:
                # Query GPT
                completion = openai.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    messages=full_messages,
                )
                logger.debug(f"OpenAI response: {completion.choices[0].message.content}")
                gpt_output = completion.choices[0].message.content
                tokens_prompt = completion.usage.prompt_tokens
                tokens_completion = completion.usage.completion_tokens
                
                output = {
                    "content": gpt_output,
                    "tokens_prompt": tokens_prompt,
                    "tokens_completion": tokens_completion
                    }
                
                # Save the query to the DB
                completion_dict = completion.to_dict()
                with get_session() as session:
                    try:
                        llm_query = create_llm_query(
                            session=session,
                            convo_id=convo_id,
                            message_id=message_id,
                            completion=completion_dict,
                            tokens_prompt=tokens_prompt,
                            tokens_completion=tokens_completion,
                            llm_model=model
                        )
                        output["llm_query_id"] = llm_query.id
                    except Exception as ex:
                        logger.error("Error saving LLM query.")
                        logger.exception(ex)
                        raise
                return output
            except Exception as e:
                logger.error(f"Error calling OpenAI (attempt {attempt+1})")
                logger.exception(e)
        
        logger.error("Max retries reached for query_gpt. Returning empty string.")
        return {"content": "", "tokens_prompt": 0, "tokens_completion": 0}


class BotStep:
    """
    Base class for a step (or 'state') in the conversation flow.
    Subclasses implement:
      - process_input
      - next_state
      - generate_output
    """
    def __init__(self, convo_id: int):
        self.convo_id = convo_id
        self.user_msg = None          # The current message object (if any)
        self.bot_msg = None           # The bot's message object(s), if applicable
        
        logger.debug(f"Initializing {self.__class__.__name__} with convo_id={convo_id}")

    def process_input(self, user_msg):
        """
        Strip whitespace and store locally.
        """
        self.user_msg = user_msg
        self.user_msg["content"] = str(self.user_msg["content"]).strip()
        return self.user_msg
    
    def next_state(self) -> Tuple[str, Dict]:
        """
        By default, does nothing. 
        Child classes will override to say: (next_state_name, {...data...}).
        """
        return self._current_state(), {}
    
    async def generate_output(self, **kwargs) -> Optional[str]:
        """
        Generate text from GPT or a static response. Typically returns a string or None.
        Child classes override to produce content.
        """
        return None

    def _current_state(self) -> ConvoStateEnum:
        """
        Return the ConvoStateEnum that this BotStep represents.
        Subclasses can just do `return ConvoStateEnum.ISSUE_INTERVIEW`, etc.
        """
        raise NotImplementedError("Subclass must return the correct ConvoStateEnum.")
    
    def _get_session(self):
        """
        Overwrite or import your own `get_session()` from db_session 
        for DB transactions.
        """
        return get_session()


# ------------------------------------------------------------------------------
# Subclasses
# ------------------------------------------------------------------------------

class BotStart(BotStep):
    def _current_state(self):
        return ConvoStateEnum.START

    def next_state(self) -> Tuple[str, Dict]:
        """
        Move from START -> ISSUE_INTERVIEW automatically
        and provide a starter message from the bot_msgs.yml
        """
        bot_msg = {
            "content": bot_msgs["start"]["content"],
            "responseType": ResponseTypeEnum.TEXT,
            "convoState": ConvoStateEnum.ISSUE_INTERVIEW,
            "options": {"question_id": "start"}
        }
        return (ConvoStateEnum.ISSUE_INTERVIEW, {
            "bot_msg": bot_msg
        })


class BotIssueInterview(BotStep):
    

    def _current_state(self):
        return ConvoStateEnum.ISSUE_INTERVIEW

    def next_state(self) -> Tuple[str, Dict]:
        """
        1. We build a GPT prompt from the conversation.
        2. If it has '::finished::', we move on to RATE_ISSUE,
           otherwise we stay in ISSUE_INTERVIEW.
        """
        # 1) Gather conversation messages relevant to the "issue_interview" state
        convo_msgs = self._gather_relevant_messages()
        
        system_prompt = prompts["issue_interview"]
        gpt_query_output = Chatbot.query_gpt(system_prompt, convo_msgs, convo_id=self.convo_id)  # {"content": "...", "token_prompt": 123, "token_completion": 456}
        gpt_response = gpt_query_output["content"]
        finished = "::finished::" in gpt_response
        gpt_clean = gpt_response.replace("::finished::", "")
        
        bot_msg = {
            "content": gpt_clean,
            "responseType": ResponseTypeEnum.TEXT,
            "options": {}
        }

        if finished:
            # Move to next state
            with self._get_session() as session:
                # this is redundant with create_message() updating state
                try:
                    update_conversation(
                        session=session, 
                        conversation=get_conversation_by_id(session, self.convo_id),
                        state=ConvoStateEnum.RATE_ISSUE)
                except Exception as e:
                    logger.error(f"Error updating conversation state, convo_id={self.convo_id}")
                    logger.exception(e)
                    raise
            return (ConvoStateEnum.RATE_ISSUE, {})
        else:
            # Stay in ISSUE_INTERVIEW
            return (ConvoStateEnum.ISSUE_INTERVIEW, {"bot_msg": bot_msg})
    
    async def generate_output(self, **kwargs) -> Optional[str]:
        """
        We simply return the bot response we passed from .next_state().
        """
        logger.debug(f"BotIssueInterview.generate_output: {kwargs}")
        if "bot_msg" in kwargs:
            return kwargs["bot_msg"]
        
        logger.error("No bot_msg in kwargs.")
        return None

    def _gather_relevant_messages(self):
        """
        Retrieve conversation messages where state=ISSUE_INTERVIEW or role=USER, etc.
        Or just get everything from the conversation if you want the entire history.
        This is an example pattern:
        """
        with self._get_session() as session:
            msgs = get_conversation_messages(session, self.convo_id)
            # Convert to OpenAI's format: [{"role": "user", "content": "..."}]
            result = []
            for m in msgs:
                # We'll only feed user/assistant messages to GPT
                if m.role == RoleEnum.USER or m.role == RoleEnum.ASSISTANT:
                    result.append({"role": m.role.value, "content": m.content})
        return result


class BotRateIssue(BotStep):
    """
    We have 2 questions in the 'rate_issue' category:
      1) rate_issue_neg
      2) rate_issue_pos

    We'll require that both are filled before moving on.
    """

    question_order = ["rate_issue_neg", "rate_issue_pos"]

    def _current_state(self):
        return ConvoStateEnum.RATE_ISSUE
    
    def process_input(self, user_msg):
        super().process_input(user_msg)
        logger.debug(f"BotRateIssue.process_input: {user_msg}")
        
        # Save the issue rating to the DB
        with self._get_session() as session:
            try:
                data = create_analysis_data(
                    session=session, 
                    convo_id=self.convo_id, 
                    field=user_msg["options"].get("question_id"),
                    content=user_msg["content"]
                )
            except Exception as e:
                logger.error(f"Error saving rating, convo_id={self.convo_id}")
                logger.exception(e)
                raise

    def next_state(self) -> Tuple[str, Dict]:
        """

        """
        with self._get_session() as session:
            data = get_conversation_analysis_data(session, self.convo_id)
            missing_fields = self._missing_fields(data)

        if not missing_fields:
            # All rating questions are answered
            with self._get_session() as session:
                try:
                    # Update the conversation state
                    update_conversation(
                        session=session, 
                        conversation=get_conversation_by_id(session, self.convo_id),
                        state=ConvoStateEnum.RATE_VALUES)
                except Exception as e:
                    logger.error(f"Error updating conversation state, convo_id={self.convo_id}")
                    logger.exception(e)
                    raise
            return (ConvoStateEnum.RATE_VALUES, {})  # proceed
        else:
            # Still have questions left
            next_q = missing_fields[0]  # pick the first unanswered
            return (ConvoStateEnum.RATE_ISSUE, {"question_id": next_q})

    async def generate_output(self, **kwargs) -> Optional[str]:
        """
        If 'question_id' in kwargs, we retrieve the question text from bot_msgs.yml
        and return it with response_type='slider'.
        """
        question_id = kwargs.get("question_id")
        if not question_id:
            logger.debug("No question_id in kwargs.")
            with self._get_session() as session:
                data = get_conversation_analysis_data(session, self.convo_id)
                missing_fields = self._missing_fields(data)
            if missing_fields:
                question_id = missing_fields[0]
            else:
                return None
        bot_msg = bot_msgs[question_id].copy()
        bot_msg['options']['question_id'] = question_id
        logger.debug(f"BotRateIssue.generate_output: {bot_msg}")
        return bot_msg

    def _missing_fields(self, data: List[AnalysisData]) -> List[str]:
        """
        Returns a list of rating fields still None for RATE_ISSUE.
        """
        req_fields = ["rate_issue_neg", "rate_issue_pos"]
        have_fields = [d.field for d in data]
        missing = [f for f in req_fields if f not in have_fields]
        return missing
    
        
class BotRateValues(BotStep):
    
    def _current_state(self):
        return ConvoStateEnum.RATE_VALUES
    
    def process_input(self, user_msg):
        super().process_input(user_msg)
        logger.debug(f"BotRateValues.process_input: {user_msg}")
        
        if user_msg["content"] == "":
            return
        
        # Save the value rating to the DB
        with self._get_session() as session:
            try:
                data = create_analysis_data(
                    session=session, 
                    convo_id=self.convo_id, 
                    field=user_msg["options"].get("question_id"),
                    content=user_msg["content"]
                )
            except Exception as e:
                logger.error(f"Error saving rating, convo_id={self.convo_id}")
                logger.exception(e)
                raise
                    
    def next_state(self) -> Tuple[str, Dict]:
        with self._get_session() as session:
            data = get_conversation_analysis_data(session, self.convo_id)
            missing_fields = self._missing_fields(data)
        if not missing_fields:
            # All rating questions are answered
            with self._get_session() as session:
                try:
                    update_conversation(
                        session=session, 
                        conversation=get_conversation_by_id(session, self.convo_id),
                        state=ConvoStateEnum.RANK_REAPS)
                except Exception as e:
                    logger.error(f"Error updating conversation state, convo_id={self.convo_id}")
                    logger.exception(e)
                    raise
            return (ConvoStateEnum.RANK_REAPS, {"init": True})
        else:
            # Still have questions left
            next_q = missing_fields[0]
            return (ConvoStateEnum.RATE_VALUES, {"question_id": next_q})
    
    async def generate_output(self, **kwargs):
        question_id = kwargs.get("question_id")
        if not question_id:
            bot_msg = bot_msgs["intro_rate_vals"].copy()
            return bot_msg
        else:
            val_name = question_id.split("_")[-1]
            val_label = [v["label"] for v in val_list if v["name"] == val_name][0]
            val_description = [v["short_description"] for v in val_list if v["name"] == val_name][0]
            bot_msg = bot_msgs["rate_val"].copy()
            bot_msg['content'] = bot_msg['content'].format(
                val_label=val_label,
                val_description=val_description)
            bot_msg['options']['question_id'] = question_id
            return bot_msg
            
    
    def _missing_fields(self, data: AnalysisData) -> List[str]:
        
        all_vals = [v["name"] for v in val_list]
        req_fields = [f"rate_val_{v}" for v in all_vals]
        have_fields = [d.field for d in data]
        missing = [f for f in req_fields if f not in have_fields]
        shuffled_missing = random.sample(missing, len(missing))
        return shuffled_missing
    

class BotRankReaps(BotStep):
    """
    A step where we generate three reappraisals (for top values,
    bottom values, and a general reappraisal) and prompt the user
    to rank them by helpfulness.
    """

    def process_input(self, user_msg):
        """
        Handle the user's ranking input for the three reappraisals.
        We store the ranking in analysis_data so we can refer back
        to it later.
        """
        super().process_input(user_msg)
        logger.debug(f"BotRankReaps.process_input: {user_msg}")
        if user_msg["content"] == "":
            return
        ranking = user_msg.get("content", [])
        with self._get_session() as session:
            try:
                create_analysis_data(
                    session=session,
                    convo_id=self.convo_id,
                    field="reap_ranks",
                    content=json.dumps(ranking)
                )
            except Exception as e:
                logger.error(f"Error saving ranking, convo_id={self.convo_id}")
                logger.exception(e)
                raise
                    

    def next_state(self) -> Tuple[str, Dict]:
        """
        Decide which state to move to after the user has submitted
        their ranking. Adjust as needed for your flow.
        """
        with self._get_session() as session:
            data = get_conversation_analysis_data(session, self.convo_id)
            logger.debug(f"Fields completed: {[d.field for d in data]}")
            if not any([d.field == "reap_ranks" for d in data]):
                return (ConvoStateEnum.RANK_REAPS, {})
            
        return (ConvoStateEnum.RATE_REAPS, {})

    async def generate_output(self, **kwargs) -> Optional[str]:
        """
        Asynchronously generate three reappraisals (top values,
        bottom values, general). Then create a single message
        with responseType=RANKING, prompting the user to rank them.
        """
        if "init" in kwargs and kwargs["init"]:
            bot_msg = {
                "content": bot_msgs["intro_rank_reaps"]["content"],
                "responseType": ResponseTypeEnum.CONTINUE,
                "options": {}
            }
            return bot_msg

        with self._get_session() as session:
            try:
                analysis_data = get_conversation_analysis_data(session, self.convo_id)
            except Exception as e:
                logger.error(f"Error fetching analysis data, convo_id={self.convo_id}")
                logger.exception(e)
                raise
            # 1) Fetch the user's top/bottom values from analysis_data (adjust fields as needed).
            val_data = [x for x in analysis_data if x.field.startswith("rate_val_")]
            # get the top 4 and bottom 4 values by the field "content"
            top_vals = sorted(val_data, key=lambda x: x.content, reverse=True)[:4]
            bottom_vals = sorted(val_data, key=lambda x: x.content)[:4]
            top_val_names = [x.field.split("_")[-1] for x in top_vals]
            bottom_val_names = [x.field.split("_")[-1] for x in bottom_vals]
            logger.debug(f"Top values: {top_val_names}")
            logger.debug(f"Bottom values: {bottom_val_names}")
                

            # 2) Prepare message history for the reappraisal generator
            #    (just an example of user vs assistant messages).
            try:
                convo_msgs = get_conversation_messages(session, self.convo_id)
            except Exception as e:
                logger.error(f"Error fetching conversation messages, convo_id={self.convo_id}")
                logger.exception(e)
                raise
            
            msg_history = []
            for m in convo_msgs:
                if m.state != ConvoStateEnum.ISSUE_INTERVIEW:
                    continue
                if m.role == RoleEnum.USER:
                    msg_history.append({"role": "user", "content": m.content})
                elif m.role == RoleEnum.ASSISTANT:
                    msg_history.append({"role": "assistant", "content": m.content})

            # 3) Create and configure our ReappraisalGenerator.
            #    If you have a list of all possible values, load them as `all_vals` here.
            
            reap_gen = ReappraisalGenerator(all_vals=val_list, convo_id=self.convo_id)
            reap_gen.set_top_n_vals([v.lower() for v in top_val_names])
            reap_gen.set_bottom_n_vals([v.lower() for v in bottom_val_names])

            # 4) Generate the reappraisals asynchronously
            
            reap_dict = await reap_gen.generate_all_reappraisals(msg_history)  # {"reap_top": {...}, "reap_bottom": {...}, "reap_general": {...}}
            # put in random order and record everything
            # reap_keys = ["reap_top", "reap_bottom", "reap_general"]
            reap_keys = ["reap_top1", "reap_top2", "reap_bottom1", "reap_bottom2"]
            n_reaps = len(reap_keys)
            idx_shuffled = random.sample(range(n_reaps), n_reaps)
            reap_texts_shuffled = [reap_dict[reap_keys[idx]]['reap_text'] for idx in idx_shuffled]
                
            try:
                create_analysis_data(
                    session=session, convo_id=self.convo_id,
                    field='reap_top1_idx', content=str(idx_shuffled[0]))
                create_analysis_data(
                    session=session, convo_id=self.convo_id,
                    field='reap_top2_idx', content=str(idx_shuffled[1]))
                create_analysis_data(
                    session=session, convo_id=self.convo_id,
                    field='reap_bottom1_idx', content=str(idx_shuffled[2]))
                create_analysis_data(
                    session=session, convo_id=self.convo_id,
                    field='reap_bottom2_idx', content=str(idx_shuffled[3]))
                
                create_analysis_data(
                    session=session, convo_id=self.convo_id,
                    field='reap_top1_text', content=reap_dict['reap_top1']['reap_text'])
                create_analysis_data(
                    session=session, convo_id=self.convo_id,
                    field='reap_top2_text', content=reap_dict['reap_top2']['reap_text'])
                create_analysis_data(
                    session=session, convo_id=self.convo_id,
                    field='reap_bottom1_text', content=reap_dict['reap_bottom1']['reap_text'])
                create_analysis_data(
                    session=session, convo_id=self.convo_id,
                    field='reap_bottom2_text', content=reap_dict['reap_bottom2']['reap_text'])
                
                create_analysis_data(
                    session=session, convo_id=self.convo_id,
                    field='reap_top1_value', content=reap_dict['reap_top1']['reap_type'])
                create_analysis_data(
                    session=session, convo_id=self.convo_id,
                    field='reap_top2_value', content=reap_dict['reap_top2']['reap_type'])
                create_analysis_data(
                    session=session, convo_id=self.convo_id,
                    field='reap_bottom1_value', content=reap_dict['reap_bottom1']['reap_type'])
                create_analysis_data(
                    session=session, convo_id=self.convo_id,
                    field='reap_bottom2_value', content=reap_dict['reap_bottom2']['reap_type'])
            except Exception as e:
                logger.error(f"Error saving reappraisals, convo_id={self.convo_id}")
                logger.exception(e)
                raise
                
            logger.debug(f"Reappraisals: {reap_dict}")

            bot_msg = {
                "content": bot_msgs["rank_reaps"]["content"],
                "responseType": ResponseTypeEnum.RANKING,
                "options": {"items": reap_texts_shuffled}
            }
            return bot_msg

class BotRateReaps(BotStep):
    
    def _current_state(self):
        return ConvoStateEnum.RATE_REAPS
    
    def process_input(self, user_msg):
        super().process_input(user_msg)
        logger.debug(f"BotRateReaps.process_input: {user_msg}")
        if user_msg["content"] == "":
            if "rate_reap_step" in user_msg["options"].get("question_id", ""):
                user_msg = {"content": "step", "options": user_msg["options"]}
            else:
                return
            
        # Save the reappraisal rating to the DB
        with self._get_session() as session:
            try:
                data = create_analysis_data(
                    session=session, 
                    convo_id=self.convo_id, 
                    field=user_msg["options"].get("question_id"),
                    content=user_msg["content"]
                )
            except Exception as e:
                logger.error(f"Error saving rating, convo_id={self.convo_id}")
                logger.exception(e)
                raise
    
    def next_state(self):
        """
        Move to the next state after the user has rated the reappraisals.
        """
        with self._get_session() as session:
            try:
                data = get_conversation_analysis_data(session, self.convo_id)
            except Exception as e:
                logger.error(f"Error fetching analysis data, convo_id={self.convo_id}")
                logger.exception(e)
                raise
            
            missing_fields = self._missing_fields(data)
            if not missing_fields:
                # All rating questions are answered
                try:
                    # Update the conversation state
                    update_conversation(
                        session=session, 
                        conversation=get_conversation_by_id(session, self.convo_id),
                        state=ConvoStateEnum.COMPLETE)
                except Exception as e:
                    logger.error(f"Error updating conversation state, convo_id={self.convo_id}")
                    logger.exception(e)
                    raise
                return (ConvoStateEnum.COMPLETE, {})  # proceed
            else:
                # Still have questions left
                next_q = missing_fields[0]  # e.g. rate_reap_top
                next_q_type = next_q.split("_")[-1]  # e.g. top, bottom, general
                next_q_text_id = f"reap_{next_q_type}_text"
                reap_text = [d.content for d in data if d.field == next_q_text_id][0]
                passalong = {
                    "question_id": next_q,
                    "reap_text": reap_text
                    }
                return (ConvoStateEnum.RATE_REAPS, passalong)
    
    async def generate_output(self, **kwargs):
        
        question_id = kwargs.get("question_id")  # e.g. rate_reap_success_top
        reap_text = kwargs.get("reap_text")
        if not question_id:
            bot_msg = bot_msgs["intro_rate_reaps"].copy()
            return bot_msg
        else:
            reap_type = question_id.split("_")[-1]  # e.g. top, bottom, general
            q_type = question_id.split("_")[-2]  # e.g. success, care, neg, pos
            bot_msg_key = f"rate_reap_{q_type}"  # e.g. rate_reap_success
            bot_msg = bot_msgs[bot_msg_key].copy()
            bot_msg['content'] = bot_msg['content'].format(reap_text=reap_text)
            bot_msg['options']['question_id'] = question_id
            return bot_msg
    
    def _missing_fields(self, data: List[AnalysisData]) -> List[str]:
        """
        Returns a list of rating fields still None for RATE_REAP.
        """
        req_field_stems = ["rate_reap_step", "rate_reap_neg", "rate_reap_pos", "rate_reap_success", "rate_reap_care", "rate_reap_insight"]
        reap_types = ["top1", "bottom1", "top2", "bottom2"]
        random.seed(self.convo_id)
        random.shuffle(reap_types)
        req_fields = [f"{stem}_{reap_type}" for reap_type in reap_types for stem in req_field_stems] 
        
        have_fields = [d.field for d in data]
        missing = [f for f in req_fields if f not in have_fields]
        return missing
    
    
    # def _(self, data: List[AnalysisData]) -> List[str]:
    #     """
        
    #     """
    #     missing_fields = self._missing_fields(data)
        
        
class BotComplete(BotStep):
    def _current_state(self):
        return ConvoStateEnum.COMPLETE

    def next_state(self) -> Tuple[str, Dict]:
        # No further state
        return (ConvoStateEnum.COMPLETE, {})

    async def generate_output(self, **kwargs) -> Optional[str]:
        bot_msg = bot_msgs["complete"].copy()
        return bot_msg
        


# ------------------------------------------------------------------------------
#  State Machine Router
# ------------------------------------------------------------------------------
async def run_state_logic(convo_id: int, user_msg: Dict):
    with BotStep(0)._get_session() as session:
        try:
            convo = get_conversation_by_id(session, convo_id)
        except Exception as e:
            logger.error(f"Error fetching conversation, convo_id={convo_id}")
            logger.exception(e)
            raise
        if not convo:
            return {"error": "Conversation not found."}
        current_state = convo.state

        # 2) Map ConvoStateEnum -> BotStep
        state_map = {
            ConvoStateEnum.START: BotStart,
            ConvoStateEnum.ISSUE_INTERVIEW: BotIssueInterview,
            ConvoStateEnum.RATE_ISSUE: BotRateIssue,
            ConvoStateEnum.RATE_VALUES: BotRateValues,
            ConvoStateEnum.RANK_REAPS: BotRankReaps,
            ConvoStateEnum.RATE_REAPS: BotRateReaps,
            ConvoStateEnum.COMPLETE: BotComplete
        }

        StepClass = state_map.get(current_state, BotComplete)
        step_obj = StepClass(convo_id)

        # 3) process user input
        if user_msg:
            step_obj.process_input(user_msg)
        # save input message to db

        try:
            msg = create_message(
                session=session,
                convo_id=convo_id,
                content=step_obj.user_msg["content"],
                role=RoleEnum.USER,
                state=current_state,
                response_type=step_obj.user_msg["responseType"],
                options=user_msg["options"]
            )
        # step_obj.user_msg["msgId"] = msg.id
        except Exception as e:
            logger.error(f"Error saving user message, convo_id={convo_id}")
            logger.exception(e)
            raise

        # 4) move to next state
        new_state, data = step_obj.next_state()
        if current_state != new_state:
            logger.debug(f"Moving from {current_state} to {new_state}")
            StepClass = state_map.get(new_state, BotComplete)
            step_obj = StepClass(convo_id)
            

        # 5) generate_output
        bot_msg = await step_obj.generate_output(**data) or {}
        bot_msg["convoState"] = new_state
    
    # save output message to db
        try: 
            msg = create_message(
                session=session,
                convo_id=convo_id,
                content=bot_msg["content"],
                role=RoleEnum.ASSISTANT,
                state=new_state,
                response_type=bot_msg["responseType"],
                options=bot_msg["options"]
            )
            session.flush()
            bot_msg["msgId"] = msg.id
        except Exception as e:
            logger.error(f"Error saving bot message, convo_id={convo_id}")
            logger.exception(e)
            raise

    # 6) update conversation
        try:
            convo = get_conversation_by_id(session, convo_id)
            if convo:
                update_conversation(session, convo, state=new_state)
        except Exception as e:
            logger.error(f"Error updating conversation, convo_id={convo_id}")
            logger.exception(e)
            raise
            
    return bot_msg