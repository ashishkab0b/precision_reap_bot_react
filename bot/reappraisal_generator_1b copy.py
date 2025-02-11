# bot/reappraisal_generator.py

import json
import asyncio
import aiohttp
import os
from typing import List, Tuple, Dict
from db.crud import create_analysis_data, create_llm_query
from db.db_session import get_session
import random 
import re
from bot.logger_setup import setup_logger

logger = setup_logger()


prompt_template_value = """
You are an empathetic friend who is offering a cognitive reappraisal to your friend.
Both you and your friend really value {value_name}.
{value_description}
In the cognitive reappraisal that you provide to your friend, be sure that the reappraisal appeals to your shared value of {value_name}.

Thinking about the situation described in the messages, what are the kinds of things that someone who values {value_name} might care about or focus on?

Respond with a 2 sentence cognitive reappraisal that addresses the kinds of things that someone who values {value_name} would care about and will help your friend feel better about the situation they're facing.
Do NOT explicitly mention that you're trying to make a reappraisal that relates to the value of {value_name}.
Do NOT invent any information that you haven't been told.
"""

judge_template = """
You are an empathetic friend who is picking between several cognitive reappraisals for your friend's emotional issue.
Read about the issue and then choose two cognitive reappraisals that you think would be most effective for your friend from the following reappraisals. 
Please be aware that your friend is someone who holds the following values very dearly:

{value_list_str}

You can identify the two most effective cognitive reappraisals by considering deeply what exactly is at the heart of their emotional issue and then thinking about what would be most alleviating for them to hear. The most effective reappraisals should speak to the concerns that are most central to the issue. Moreover, it helps if the reappraisal directly appeals to their values as listed above. However, first and foremost, the reappraisals you pick should make sense and be relevant to the issue. If a reappraisal doesn't make sense or is inappropriate for the situation, don't pick it.
If a reappraisal makes a claim that isn't supported by the information you've been given, don't pick it.
Respond with a JSON-formatted list with exactly two elements, each of which is the number of a reappraisal in the list below. The list sits under a key called "integers". It should be parseable JSON. 

{reappraisal_list_str}
"""


class ReappraisalGenerator:
    def __init__(self, all_vals: List[dict], convo_id: int):
        self.api_token = os.getenv("OPENAI_API_KEY")
        self.all_vals = all_vals
        self.reap_model = "o1"
        self.judge_model = "o3-mini"
        self.convo_id = convo_id
        
        # Will be set by the user of the class
        self.selected_vals_top: List[dict] = []
        self.selected_vals_bottom: List[dict] = []
    
    def set_top_n_vals(self, vals: List[str]):
        """Set the selected values for 'top' reappraisals."""
        self.selected_vals_top = [v for v in self.all_vals if v.get("name", "").lower() in [v.lower() for v in vals]]
        
    def set_bottom_n_vals(self, vals: List[str]):
        """Set the selected values for 'bottom' reappraisals."""
        self.selected_vals_bottom = [v for v in self.all_vals if v.get("name", "").lower() in [v.lower() for v in vals]]
    
    async def _generate_value_reap(
        self,
        sess: aiohttp.ClientSession,
        value_name: str,
        value_description: str,
        msg_history: List[dict]
    ) -> dict:
        """Request a cognitive reappraisal for the specified value asynchronously."""
        prompt = prompt_template_value.format(
            value_name=value_name, 
            value_description=value_description
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        if self.reap_model in ["gpt-4o", "gpt-4o-mini"]:
            role = "system"
            params = {
                "temperature": 1.0
            }
        elif self.reap_model in ["o1", "o3-mini"]:
            role = "developer"
            params = {
                "reasoning_effort": "medium"
            }
        else:
            role = "developer"
        full_messages = msg_history + [{"role": role, "content": prompt}]
        payload = {
            "model": self.reap_model,
            "messages": full_messages,
        }
        payload.update(params)
        # logger.debug(f'value reap prompt: {prompt}')
        url = "https://api.openai.com/v1/chat/completions"
        async with sess.post(url, headers=headers, json=payload) as resp:
            resp.raise_for_status()  # Raise exception for HTTP errors.
            data = await resp.json()
            reap_text = data["choices"][0]["message"]["content"].strip()
            
            output = {
                "reap_type": value_name,
                "reap_text": reap_text
            }
            
            with get_session() as session:
                try:
                    create_analysis_data(
                        session=session,
                        convo_id=self.convo_id,
                        field=f"reap_{value_name}_text",
                        content=reap_text
                    )
                    create_llm_query(
                        session=session,
                        convo_id=self.convo_id,
                        completion=json.dumps(data),
                        tokens_prompt=data["usage"]["prompt_tokens"],
                        tokens_completion=data["usage"]["completion_tokens"],
                        llm_model=self.reap_model,
                        prompt_messages=full_messages
                    )
                except Exception as e:
                    logger.error(f"Error in saving generated reappraisals")
                    logger.exception(e)
                    raise
                
            return output
    
    def _make_reappraisal_list_str(self, reappraisal_list: List[dict]) -> str:
        """Format the list of cognitive reappraisals into a numbered string."""
        return "\n".join(f"{i+1}. {r['reap_text']}" for i, r in enumerate(reappraisal_list))
    
    def _make_value_list_str_for_judge(self, value_list: List[dict]) -> str:
        """Format the list of values into a string for the judge model."""
        val_list_str = ""
        for val in value_list:
            val_list_str += f" - {val['name']} - {val['description']}\n"
        return val_list_str
    
    async def _select_reappraisal(
        self,
        sess: aiohttp.ClientSession,
        reappraisal_list: List[str],
        relevant_vals: List[dict],
        msg_history: List[dict]
    ) -> str:
        """
        Request the judge model to pick the best reappraisal asynchronously.
        Returns the index of the chosen reappraisal from that list
        """
        reappraisal_list_str = self._make_reappraisal_list_str(reappraisal_list)
        value_list_str = self._make_value_list_str_for_judge(relevant_vals)
        prompt = judge_template.format(reappraisal_list_str=reappraisal_list_str,
                                       value_list_str=value_list_str)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        # if self.judge_model in ["gpt-4o", "gpt-4o-mini"]:
        #     role = "system"
        # elif self.judge_model in ["o1", "o3-mini"]:
        #     role = "developer"
        # else:
        #     role = "developer"
        role = "developer"
        full_messages = msg_history + [{"role": role, "content": prompt}],
        payload = {
            "model": self.judge_model,
            "messages": full_messages,
            "reasoning_effort": "medium",
            "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "integer_list",
                "schema": {
                    "type": "object",
                    "properties": {
                    "integers": {
                        "type": "array",
                        "description": "A list containing exactly two integers.",
                        "items": {
                        "type": "number"
                        }
                    }
                    },
                    "required": [
                    "integers"
                    ],
                    "additionalProperties": False
                },
                "strict": True
            }
            }
        }
        url = "https://api.openai.com/v1/chat/completions"
        logger.debug(f'payload: {payload}')
        async with sess.post(url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
            
            with get_session() as session:
                try:
                    create_llm_query(
                        session=session,
                        convo_id=self.convo_id,
                        completion=json.dumps(data),
                        tokens_prompt=data["usage"]["prompt_tokens"],
                        tokens_completion=data["usage"]["completion_tokens"],
                        llm_model=self.judge_model,
                        prompt_messages=full_messages
                    )
                except Exception as e:
                    logger.error(f"Error in _select_reappraisal")
                    logger.exception(e)
                    raise
                    
                
            
            judge_response = data["choices"][0]["message"]["content"]
            judge_response_list = json.loads(judge_response)["integers"]
            selected_indices = [int(i) - 1 for i in judge_response_list]
            assert len(selected_indices) == 2, "Judge model should return exactly 2 indices"
            return selected_indices

    async def _generate_and_select_value_reappraisals_for(
        self,
        sess: aiohttp.ClientSession,
        values: List[dict],
        msg_history: List[dict]
    ) -> dict:
        """
        Helper: Generate a cognitive reappraisal for each of the given values concurrently,
        then pick the best one with the judge model.
        """

        tasks = []
        for val in values:
            tasks.append(
                self._generate_value_reap(
                    sess, 
                    val.get("name", ""), 
                    val.get("description", ""), 
                    msg_history
                )
            )
        reappraisal_list = await asyncio.gather(*tasks) # dicts containing 'reap_type' and 'reap_text'
        selected_reappraisal_idx = await self._select_reappraisal(
            sess=sess, 
            reappraisal_list=reappraisal_list, 
            relevant_vals=values,
            msg_history=msg_history, 
            )
        # reap = reappraisal_list[selected_reappraisal_idx]  # dicts containing 'reap_type' and 'reap_text'
        reaps = [reap for i, reap in enumerate(reappraisal_list) if i in selected_reappraisal_idx]
            
        return reaps
    
    async def generate_all_reappraisals(
        self,
        msg_history: List[dict]
    ) -> Tuple[str, str, str]:
        """
        Run three tasks concurrently:
         1) Generate & select best reappraisal from selected_vals_top
         2) Generate & select best reappraisal from selected_vals_bottom
         3) Generate a general reappraisal
         
        Returns a tuple of (best_top_reappraisal, best_bottom_reappraisal, general_reappraisal).
        """
        async with aiohttp.ClientSession() as sess:
            # Create tasks for each of the three bullet points
            top_task = asyncio.create_task(
                self._generate_and_select_value_reappraisals_for(
                    sess=sess, values=self.selected_vals_top, msg_history=msg_history
                )
            )
            bottom_task = asyncio.create_task(
                self._generate_and_select_value_reappraisals_for(
                    sess=sess, values=self.selected_vals_bottom, msg_history=msg_history
                )
            )

            # Run them concurrently
            reaps_top, reaps_bottom = await asyncio.gather(
                top_task, bottom_task
            )
            
            # each of the outputs are dicts containing 'reap_type' and 'reap_text'
            output = {
                "reap_top1": reaps_top[0],
                "reap_top2": reaps_top[1],
                "reap_bottom1": reaps_bottom[0],
                "reap_bottom2": reaps_bottom[1]
            }
            return output