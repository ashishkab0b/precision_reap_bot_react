# bot_flow.py

import yaml
import json
import logging
from typing import Optional, List, Dict, Tuple
from pathlib import Path
import random

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
from bot.label_conversation import label_convo

logger = setup_logger()

# Load prompts and bot_msgs
bot_dir = Path(__file__).parent
with open(bot_dir / "bot_msgs.yml", "r") as f:
    bot_msgs = yaml.safe_load(f)

with open(bot_dir / "prompts.yml", "r") as f:
    prompts = yaml.safe_load(f)

# Need to link the llm query table id and messaage ids

class Chatbot:
    """
    A small utility to query OpenAI with a 'system' prompt + conversation history.
    """
    @staticmethod
    def query_gpt(system_prompt: str,
                  messages: List[Dict[str, str]],
                  user_id: Optional[int] = None,
                  message_id: Optional[int] = None,
                  max_tries: int = 3) -> str:
        """
        Query GPT with the system prompt + any additional messages.
        Returns the text or an empty string if it fails.
        """
        model = CurrentConfig.openai_chat_model
        temperature = CurrentConfig.openai_temperature

        # Construct the final message array
        full_messages = [{"role": "developer", "content": system_prompt}] + messages
        logger.debug(f"Calling OpenAI with {len(messages)} messages and system prompt: {system_prompt}")
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
                    llm_query = create_llm_query(
                        session=session,
                        user_id=user_id,
                        message_id=message_id,
                        completion=completion_dict,
                        tokens_prompt=tokens_prompt,
                        tokens_completion=tokens_completion,
                        llm_model=model
                    )
                    output["llm_query_id"] = llm_query.id
                    session.commit()
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
    def __init__(self, conversation_id: int, user_id: int):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.user_msg = None          # The current message object (if any)
        self.bot_msg = None           # The bot's message object(s), if applicable
        
        logger.debug(f"Initializing {self.__class__.__name__} with convo_id={conversation_id}, user_id={user_id}")

    def process_input(self, user_msg):
        """
        Save user input to DB (if needed) and store locally.
        """
        self.user_msg = user_msg
        self.user_msg["content"] = str(self.user_msg["content"]).strip()
        # if self.user_msg["content"]:
        #     # Save user message in DB
        #     with self._get_session() as session:
        #         create_message(
        #             session=session,
        #             user_id=self.user_id,
        #             conversation_id=self.conversation_id,
        #             content=self.user_msg["content"],
        #             role=RoleEnum.USER,
        #             state=self._current_state(),
        #             response_type=self.user_msg["response_type"],
        #             options=self.user_msg["options"]
        #         )
        #         session.commit()
        return self.user_msg
    
    def next_state(self) -> Tuple[str, Dict]:
        """
        By default, does nothing. 
        Child classes will override to say: (next_state_name, {...data...}).
        """
        return self._current_state(), {}
    
    def generate_output(self, **kwargs) -> Optional[str]:
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
            "response_type": ResponseTypeEnum.TEXT,
            "convo_state": ConvoStateEnum.ISSUE_INTERVIEW,
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
        
        if len(convo_msgs) == 2:
            # Label the conversation
            label_convo(self.conversation_id)

        system_prompt = prompts["issue_interview"]
        gpt_query_output = Chatbot.query_gpt(system_prompt, convo_msgs)  # {"content": "...", "token_prompt": 123, "token_completion": 456}
        gpt_response = gpt_query_output["content"]
        finished = "::finished::" in gpt_response
        gpt_clean = gpt_response.replace("::finished::", "")
        
        # Save the bot response to DB
        bot_msg = {
            "content": gpt_clean,
            "response_type": ResponseTypeEnum.TEXT,
            "options": {}
        }

        if finished:
            # Move to next state
            with self._get_session() as session:
                # this is redundant with create_message() updating state
                update_conversation(
                    session=session, 
                    conversation=get_conversation_by_id(session, self.conversation_id),
                    state=ConvoStateEnum.RATE_ISSUE)
                session.commit()
            return (ConvoStateEnum.RATE_ISSUE, {})
        else:
            # Stay in ISSUE_INTERVIEW
            return (ConvoStateEnum.ISSUE_INTERVIEW, {"bot_msg": bot_msg})
    
    def generate_output(self, **kwargs) -> Optional[str]:
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
            msgs = get_conversation_messages(session, self.conversation_id)
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
                    user_id=self.user_id, 
                    conversation_id=self.conversation_id, 
                    field=user_msg["options"].get("question_id"),
                    content=user_msg["content"]
                )
                session.commit()
            except Exception as e:
                logger.error(f"Error saving rating, user_id={self.user_id}, convo_id={self.conversation_id}")
                logger.exception(e)
                session.rollback()

    def next_state(self) -> Tuple[str, Dict]:
        """

        """
        with self._get_session() as session:
            data = get_conversation_analysis_data(session, self.conversation_id)
            missing_fields = self._missing_fields(data)

        if not missing_fields:
            # All rating questions are answered
            with self._get_session() as session:
                # Update the conversation state
                update_conversation(
                    session=session, 
                    conversation=get_conversation_by_id(session, self.conversation_id),
                    state=ConvoStateEnum.GENERATE_REAP)
                session.commit()
            return (ConvoStateEnum.GENERATE_REAP, {})  # proceed
        else:
            # Still have questions left
            next_q = missing_fields[0]  # pick the first unanswered
            return (ConvoStateEnum.RATE_ISSUE, {"question_id": next_q})

    def generate_output(self, **kwargs) -> Optional[str]:
        """
        If 'question_id' in kwargs, we retrieve the question text from bot_msgs.yml
        and return it with response_type='slider'.
        """
        question_id = kwargs.get("question_id")
        if not question_id:
            logger.debug("No question_id in kwargs.")
            with self._get_session() as session:
                data = get_conversation_analysis_data(session, self.conversation_id)
                missing_fields = self._missing_fields(data)
            if missing_fields:
                question_id = missing_fields[0]
            else:
                return None
        bot_msg = bot_msgs[question_id].copy()
        bot_msg['options']['question_id'] = question_id
        # logger.debug(f"BotRateIssue.generate_output: {bot_msg}")
        return bot_msg

    def _missing_fields(self, data: List[AnalysisData]) -> List[str]:
        """
        Returns a list of rating fields still None for RATE_ISSUE.
        """
        req_fields = ["rate_issue_neg", "rate_issue_pos"]
        have_fields = [d.field for d in data]
        missing = [f for f in req_fields if f not in have_fields]
        return missing
        
    


class BotGenerateReappraisal(BotStep):
    def _current_state(self):
        return ConvoStateEnum.GENERATE_REAP

    def next_state(self) -> Tuple[str, Dict]:
        """
        
        """
        with self._get_session() as session:
            # Update the conversation state
            update_conversation(
                session=session, 
                conversation=get_conversation_by_id(session, self.conversation_id),
                state=ConvoStateEnum.RATE_REAP_1)
            session.commit()
        return (ConvoStateEnum.RATE_REAP_1, {})

    def generate_output(self, **kwargs) -> Optional[str]:
        
        gpt_query_output = Chatbot.query_gpt(
            system_prompt=prompts["general_reappraise"],
            messages=self._gather_relevant_messages()
        )
        reappraisal = gpt_query_output["content"]
        bot_msg = {
            "content": reappraisal,
            "response_type": ResponseTypeEnum.CONTINUE,
            "options": {}
        }
        
        # save to db
        # with self._get_session() as session:
        #     msg = create_message(
        #         session=session,
        #         user_id=self.user_id,
        #         conversation_id=self.conversation_id,
        #         content=reappraisal,
        #         role=RoleEnum.ASSISTANT,
        #         state=self._current_state(),
        #         response_type=ResponseTypeEnum.TEXT
        #     )
        #     session.commit()
        #     msg_id = msg.id
        #     bot_msg["msg_id"] = msg_id
        
        return bot_msg

    def _gather_relevant_messages(self):
        """
        Similar to the gather messages approach in the other steps.
        """
        relevant_states = [
            ConvoStateEnum.ISSUE_INTERVIEW,
        ]
        with self._get_session() as session:
            msgs = get_conversation_messages(session, self.conversation_id)
            # Convert to OpenAI's format: [{"role": "user", "content": "..."}]
            result = []
            for m in msgs:
                # We'll only feed user/assistant messages to GPT
                if m.role == RoleEnum.USER or m.role == RoleEnum.ASSISTANT:
                    if m.state in relevant_states:
                        result.append({"role": m.role.value, "content": m.content})
        return result


class BotRateReap1(BotStep):

    def _current_state(self):
        return ConvoStateEnum.RATE_REAP_1
    
    def process_input(self, user_msg):
        """_summary_

        Args:
            user_msg (_type_): _description_
        """
        super().process_input(user_msg)
        logger.debug(f"BotRateReap1.process_input: {user_msg}")
        
        # Save the reappraisal rating to the DB
        with self._get_session() as session:
            try:
                data = create_analysis_data(
                    session=session, 
                    user_id=self.user_id, 
                    conversation_id=self.conversation_id, 
                    field=user_msg["options"].get("question_id"),
                    content=user_msg["content"]
                )
                session.commit()
            except Exception as e:
                logger.error(f"Error saving rating, user_id={self.user_id}, convo_id={self.conversation_id}")
                logger.exception(e)
                session.rollback()

    def next_state(self) -> Tuple[str, Dict]:
        """
        
        """
        with self._get_session() as session:
            data = get_conversation_analysis_data(session, self.conversation_id)
            missing_fields = self._missing_fields(data)

        if not missing_fields:
            # All rating questions are answered
            with self._get_session() as session:
                # Update the conversation state
                update_conversation(
                    session=session, 
                    conversation=get_conversation_by_id(session, self.conversation_id),
                    state=ConvoStateEnum.REFINE_REAP)
                session.commit()
            return (ConvoStateEnum.REFINE_REAP, {"init": True})
        else:
            # Still have questions left
            next_q = missing_fields[0]
            return (ConvoStateEnum.RATE_REAP_1, {"question_id": next_q})
        
        
        

    def generate_output(self, **kwargs) -> Optional[str]:
        """
        If 'question_id' in kwargs, we retrieve the question text from bot_msgs.yml
        and return it with response_type='slider'.
        """
        question_id = kwargs.get("question_id")
        if not question_id:
            logger.debug("No question_id in kwargs.")
            with self._get_session() as session:
                data = get_conversation_analysis_data(session, self.conversation_id)
                missing_fields = self._missing_fields(data)
            if missing_fields:
                question_id = missing_fields[0]
            else:
                return None
        
        bot_msg = bot_msgs[question_id].copy()
        bot_msg['options']['question_id'] = question_id
        # logger.debug(f"BotRateIssue.generate_output: {bot_msg}")
        return bot_msg
    


    def _missing_fields(self, data: AnalysisData) -> List[str]:
        
        # get all fields in bot_msgs that start with rate_reap_1
        req_fields = [k for k in bot_msgs.keys() if k.startswith("rate_reap_1")]
        have_fields = [d.field for d in data]
        missing = [f for f in req_fields if f not in have_fields]
        return missing

class BotRefineReap(BotStep):
    
    def __init__(self, conversation_id, user_id):
        super().__init__(conversation_id, user_id)
        self.convo_msgs = None
    
    def _current_state(self):
        return ConvoStateEnum.REFINE_REAP
    
    def _make_bot_msg(self) -> Dict:
        sys_prompt = prompts["refine_reappraisal"]
        self.convo_msgs = self._gather_relevant_messages()
        gpt_query_output = Chatbot.query_gpt(sys_prompt, self.convo_msgs)
        bot_text = gpt_query_output["content"]
        bot_msg = {
            "content": bot_text,
            "response_type": ResponseTypeEnum.TEXT,
            "options": {},
        }
        return bot_msg
    

    def next_state(self) -> Tuple[str, Dict]:
        """_summary_

        Returns:
            Tuple[str, Dict]: _description_
        """
        
        bot_msg = self._make_bot_msg()
        if "::finished::" in bot_msg["content"]:
            with self._get_session() as session:
                update_conversation(
                    session=session, 
                    conversation=get_conversation_by_id(session, self.conversation_id),
                    state=ConvoStateEnum.RATE_REAP_2)
                session.commit()
            return (ConvoStateEnum.RATE_REAP_2, {})
        else:
            return (ConvoStateEnum.REFINE_REAP, {"bot_msg": bot_msg})

    def generate_output(self, **kwargs) -> Optional[str]:
        """_summary_

        Returns:
            Optional[str]: _description_
        """
        if "init" in kwargs and kwargs["init"]:
            bot_msg = self._make_bot_msg()
            # attach initial reappraisal to the message
            initial_reap = [m["content"] for m in self.convo_msgs if m["state"] == ConvoStateEnum.GENERATE_REAP and m["role"] == RoleEnum.ASSISTANT][0]
            bot_msg["content"] = f"Reappraisal: <i>{initial_reap}</i><br/><br/>{bot_msg['content']}"
            return bot_msg
        
        if "bot_msg" in kwargs:
            return kwargs["bot_msg"]
        
    def _gather_relevant_messages(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        relevant_states = [
            ConvoStateEnum.ISSUE_INTERVIEW,
            ConvoStateEnum.GENERATE_REAP,
            ConvoStateEnum.REFINE_REAP,
        ]
        with self._get_session() as session:
            msgs = get_conversation_messages(session, self.conversation_id)
            # Convert to OpenAI's format: [{"role": "user", "content": "..."}]
            result = []
            for m in msgs:
                # We'll only feed user/assistant messages to GPT
                if m.role == RoleEnum.USER or m.role == RoleEnum.ASSISTANT:
                    if m.state in relevant_states:
                        result.append({"role": m.role.value, "content": m.content, "state": m.state})
        return result
    
    def _gather_reap_ratings(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        reap_1_fields = [
            "rate_reap_1_success",
            "rate_reap_1_care",
            "rate_reap_1_believe",
            "rate_reap_1_neg",
            "rate_reap_1_pos"
            ]
        
        with self._get_session() as session:
            data = get_conversation_analysis_data(session, self.conversation_id)
            return data
        
    


class BotRateReap2(BotStep):
    question_order = [
        "rate_reap_2_success",
        "rate_reap_2_care",
        "rate_reap_2_believe",
        "rate_reap_2_neg",
        "rate_reap_2_pos"
    ]

    def _current_state(self):
        return ConvoStateEnum.RATE_REAP_2
    
    def process_input(self, user_msg):
        """_summary_

        Args:
            user_msg (_type_): _description_
        """
        super().process_input(user_msg)
        logger.debug(f"BotRateReap2.process_input: {user_msg}")
        
        # Save the reappraisal rating to the DB
        with self._get_session() as session:
            try:
                data = create_analysis_data(
                    session=session, 
                    user_id=self.user_id, 
                    conversation_id=self.conversation_id, 
                    field=user_msg["options"].get("question_id"),
                    content=user_msg["content"]
                )
                session.commit()
            except Exception as e:
                logger.error(f"Error saving rating, user_id={self.user_id}, convo_id={self.conversation_id}")
                logger.exception(e)
                session.rollback()

    def next_state(self) -> Tuple[str, Dict]:
        with self._get_session() as session:
            data = get_conversation_analysis_data(session, self.conversation_id)
            missing_fields = self._missing_fields(data)

        if not missing_fields:
            # All rating questions are answered
            with self._get_session() as session:
                # Update the conversation state
                update_conversation(
                    session=session, 
                    conversation=get_conversation_by_id(session, self.conversation_id),
                    state=ConvoStateEnum.COMPLETE)
                session.commit()
            return (ConvoStateEnum.COMPLETE, {})
        else:
            # Still have questions left
            next_q = missing_fields[0]
            return (ConvoStateEnum.RATE_REAP_2, {"question_id": next_q})

    def generate_output(self, **kwargs) -> Optional[str]:
        question_id = kwargs.get("question_id")
        if not question_id:
            logger.debug("No question_id in kwargs.")
            with self._get_session() as session:
                data = get_conversation_analysis_data(session, self.conversation_id)
                missing_fields = self._missing_fields(data)
            if missing_fields:
                question_id = missing_fields[0]
            else:
                return None
        
        bot_msg = bot_msgs[question_id].copy()
        bot_msg['options']['question_id'] = question_id
        return bot_msg
    
    def _missing_fields(self, data: AnalysisData) -> List[str]:
        
        req_fields = [k for k in bot_msgs.keys() if k.startswith("rate_reap_2")]
        have_fields = [d.field for d in data]
        missing = [f for f in req_fields if f not in have_fields]
        return missing
    


class BotComplete(BotStep):
    def _current_state(self):
        return ConvoStateEnum.COMPLETE

    def next_state(self) -> Tuple[str, Dict]:
        # No further state
        return (ConvoStateEnum.COMPLETE, {})

    def generate_output(self, **kwargs) -> Optional[str]:
        bot_msg = bot_msgs["complete"].copy()
        return bot_msg
    
        


# ------------------------------------------------------------------------------
# Example: State Machine Router
# ------------------------------------------------------------------------------
def run_state_logic(conversation_id: int, user_id: int, user_msg: Dict):
    with BotStep(0,0)._get_session() as session:
        convo = get_conversation_by_id(session, conversation_id)
        if not convo:
            return {"error": "Conversation not found."}
        current_state = convo.state

    # 2) Map ConvoStateEnum -> BotStep
    state_map = {
        ConvoStateEnum.START: BotStart,
        ConvoStateEnum.ISSUE_INTERVIEW: BotIssueInterview,
        ConvoStateEnum.RATE_ISSUE: BotRateIssue,
        ConvoStateEnum.GENERATE_REAP: BotGenerateReappraisal,
        ConvoStateEnum.RATE_REAP_1: BotRateReap1,
        ConvoStateEnum.REFINE_REAP: BotRefineReap,
        ConvoStateEnum.RATE_REAP_2: BotRateReap2,
        ConvoStateEnum.COMPLETE: BotComplete
    }

    StepClass = state_map.get(current_state, BotComplete)
    step_obj = StepClass(conversation_id, user_id)

    # 3) process user input
    if user_msg:
        step_obj.process_input(user_msg)
    # save to db
    with step_obj._get_session() as session:
        msg = create_message(
            session=session,
            user_id=user_id,
            conversation_id=conversation_id,
            content=step_obj.user_msg["content"],
            role=RoleEnum.USER,
            state=current_state,
            response_type=step_obj.user_msg["response_type"],
            options=user_msg["options"]
        )
        session.commit()
        # step_obj.user_msg["msg_id"] = msg.id

    # 4) move to next state
    new_state, data = step_obj.next_state()
    if current_state != new_state:
        logger.debug(f"Moving from {current_state} to {new_state}")
        StepClass = state_map.get(new_state, BotComplete)
        step_obj = StepClass(conversation_id, user_id)
        

    # 5) generate_output
    bot_msg = step_obj.generate_output(**data) or {}
    bot_msg["convo_state"] = new_state
    
    # save to db
    with step_obj._get_session() as session:
        msg = create_message(
            session=session,
            user_id=user_id,
            conversation_id=conversation_id,
            content=bot_msg["content"],
            role=RoleEnum.ASSISTANT,
            state=new_state,
            response_type=bot_msg["response_type"],
            options=bot_msg["options"]
        )
        session.commit()
        bot_msg["msg_id"] = msg.id

    # 6) update conversation
    with step_obj._get_session() as session:
        convo = get_conversation_by_id(session, conversation_id)
        if convo:
            update_conversation(session, convo, state=new_state)
            session.commit()
            
    return bot_msg