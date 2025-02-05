# bot/reappraisal_generator.py

import json
import asyncio
import aiohttp
import os
from typing import List, Tuple, Dict
from db.crud import create_analysis_data
from db.db_session import get_session
import random 

prompt_template_general = """
You are an empathetic friend who is offering a cognitive reappraisal to your friend.
Respond with a 2-3 sentence cognitive reappraisal that will help them feel better about the situation they're facing.
Do NOT invent any information that you haven't been told. 
"""

prompt_template_value = """
You are an empathetic friend who is offering a cognitive reappraisal to your friend.
Both you and your friend really value {value_name}.
{value_description}
In the cognitive reappraisal that you provide to your friend, be sure that the reappraisal appeals to your shared value of {value_name}.

Thinking about the situation described in the messages, what are the kinds of things that someone who values {value_name} might care about or focus on?

Respond with a 2-3 sentence cognitive reappraisal that addresses the kinds of things that someone who values {value_name} would care about and will help your friend feel better about the situation they're facing.
Do NOT explicitly mention that you're trying to make a reappraisal that relates to the value of {value_name}.
Do NOT invent any information that you haven't been told.
"""

judge_template = """
You are an empathetic friend who is picking between several cognitive reappraisals for your friend's emotional issue.
Read about the issue and then choose the cognitive reappraisal that you think would be most effective for your friend from the following reappraisals. 
You can identify the most effective cognitive reappraisal by considering deeply what exactly is at the heart of their emotional issue and then thinking about what would be most alleviating for them to hear. In other words, the reappraisal should speak to the concerns that are most central to the issue.
Moreover, the reappraisal you pick should make sense. If a reappraisal doesn't make sense or is inappropriate for the situation, don't pick it.
Respond with only the number of the reappraisal and nothing else.
{reappraisal_list_str}
"""


class ReappraisalGenerator:
    def __init__(self, all_vals: List[dict], convo_id: int):
        self.api_token = os.getenv("OPENAI_API_KEY")
        self.all_vals = all_vals
        self.reap_model = "o1"
        # self.reap_model = "gpt-4o"
        self.judge_model = "o3-mini"
        self.convo_id = convo_id
        
        # Will be set by the user of the class
        self.selected_vals_top: List[dict] = []
        self.selected_vals_bottom: List[dict] = []
    
    def set_top_n_vals(self, vals: List[str]):
        """Set the selected values for 'top' reappraisals."""
        self.selected_vals_top = [v for v in self.all_vals if v.get("name", "").lower() in vals]
        
    def set_bottom_n_vals(self, vals: List[str]):
        """Set the selected values for 'bottom' reappraisals."""
        self.selected_vals_bottom = [v for v in self.all_vals if v.get("name", "").lower() in vals]
    
    async def _generate_general_reap(
        self,
        session: aiohttp.ClientSession,
        msg_history: List[dict]
    ) -> str:
        """Request a general cognitive reappraisal asynchronously."""
        prompt = prompt_template_general
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        payload = {
            "model": self.reap_model,
            "messages": msg_history + [{"role": "developer", "content": prompt}],
            "temperature": 1.0,
        }
        url = "https://api.openai.com/v1/chat/completions"
        async with session.post(url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
            reap_text = data["choices"][0]["message"]["content"].strip()
            output = {
                "reap_type": "general",
                "reap_text": reap_text
            }
            return output
    
    async def _generate_value_reap(
        self,
        session: aiohttp.ClientSession,
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
        payload = {
            "model": self.reap_model,
            "messages": msg_history + [{"role": "developer", "content": prompt}],
            "temperature": 1.0,
        }
        url = "https://api.openai.com/v1/chat/completions"
        async with session.post(url, headers=headers, json=payload) as resp:
            resp.raise_for_status()  # Raise exception for HTTP errors.
            data = await resp.json()
            reap_text = data["choices"][0]["message"]["content"].strip()
            
            output = {
                "reap_type": value_name,
                "reap_text": reap_text
            }
            
            with get_session() as session:
                create_analysis_data(
                    session=session,
                    convo_id=self.convo_id,
                    field=f"reap_{value_name}_text",
                    content=reap_text
                )
                session.commit()
                
            return output
    
    def _make_reappraisal_list_str(self, reappraisal_list: List[dict]) -> str:
        """Format the list of cognitive reappraisals into a numbered string."""
        return "\n".join(f"{i+1}. {r['reap_text']}" for i, r in enumerate(reappraisal_list))
    
    async def _select_reappraisal(
        self,
        session: aiohttp.ClientSession,
        reappraisal_list: List[str],
        msg_history: List[dict]
    ) -> str:
        """
        Request the judge model to pick the best reappraisal asynchronously.
        Returns the index of the chosen reappraisal from that list
        """
        reappraisal_list_str = self._make_reappraisal_list_str(reappraisal_list)
        prompt = judge_template.format(reappraisal_list_str=reappraisal_list_str)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        payload = {
            "model": self.judge_model,
            "messages": msg_history + [{"role": "developer", "content": prompt}],
            "reasoning_effort": "medium",
        }
        url = "https://api.openai.com/v1/chat/completions"
        async with session.post(url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
            judge_response = data["choices"][0]["message"]["content"].strip()
            
            try:
                selected_index = int(judge_response) - 1
                if selected_index < 0 or selected_index >= len(reappraisal_list):
                    raise ValueError
            except ValueError:
                raise ValueError(f"Invalid judge response: {judge_response}")
            # Return the actual reappraisal corresponding to the judge's choice.
            return selected_index
            # return reappraisal_list[selected_index]

    async def _generate_and_select_value_reappraisals_for(
        self,
        session: aiohttp.ClientSession,
        values: List[dict],
        msg_history: List[dict]
    ) -> dict:
        """
        Helper: Generate a cognitive reappraisal for each of the given values concurrently,
        then pick the best one with the judge model.
        """
        if not values:
            # If no values provided, return an empty string or some placeholder
            return ""

        tasks = []
        for val in values:
            tasks.append(
                self._generate_value_reap(
                    session, 
                    val.get("name", ""), 
                    val.get("description", ""), 
                    msg_history
                )
            )
        reappraisal_list = await asyncio.gather(*tasks) # dicts containing 'reap_type' and 'reap_text'
        selected_reappraisal_idx = await self._select_reappraisal(session, reappraisal_list, msg_history)
        reap = reappraisal_list[selected_reappraisal_idx]  # dict containing 'reap_type' and 'reap_text'
            
        return reap
    
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
        async with aiohttp.ClientSession() as session:
            # Create tasks for each of the three bullet points
            top_task = asyncio.create_task(
                self._generate_and_select_value_reappraisals_for(
                    session, self.selected_vals_top, msg_history
                )
            )
            bottom_task = asyncio.create_task(
                self._generate_and_select_value_reappraisals_for(
                    session, self.selected_vals_bottom, msg_history
                )
            )
            general_task = asyncio.create_task(
                self._generate_general_reap(session, msg_history)
            )

            # Run them concurrently
            reap_top, reap_bottom, reap_general = await asyncio.gather(
                top_task, bottom_task, general_task
            )
            
            # each of the outputs are dicts containing 'reap_type' and 'reap_text'
            output = {
                "reap_top": reap_top,
                "reap_bottom": reap_bottom,
                "reap_general": reap_general
            }
            return output