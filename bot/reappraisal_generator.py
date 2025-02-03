import json
import asyncio
import aiohttp
import os
from typing import List, Tuple

# Templates defined outside the class
prompt_template = """
You are an empathetic friend who is offering a cognitive reappraisal to your friend.
Both you and your friend really value {value_name}.
{value_description}
In the cognitive reappraisal that you provide to your friend, be sure that the reappraisal appeals to your shared value of {value_name}.
Respond with a 2-3 sentence cognitive reappraisal that appeals to your shared value of {value_name} and will help them feel better about the situation they're facing.
Do NOT explicitly mention that you're trying to make a reappraisal that appeals to the value of {value_name}.
Do NOT invent any information that you haven't been told.
"""

judge_template = """
You are an empathetic friend who is picking between several cognitive reappraisals for your friend's emotional issue.
Read about the issue and then choose the cognitive reappraisal that you think would be most effective for your friend from the following reappraisals. 
You can identify the most effective cognitive reappraisal by considering deeply what exactly is at the heart of their emotional issue and then thinking about what would be most alleviating for them to hear.
Respond with only the number of the reappraisal and nothing else.
{reappraisal_list_str}
"""

class ReappraisalGenerator:
    def __init__(self, api_token: str, json_file: str = "/Users/ashish/files/research/projects/precision_reap_bot_react/bot/other_vals copy 4.json"):
        self.api_token = api_token
        self.reap_model = "gpt-4o"
        self.judge_model = "o3-mini"
        
        # Load values from the JSON file.
        try:
            with open(json_file, "r") as f:
                self.all_vals = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file '{json_file}' not found.")
        
        # Pre-filter values to only include the desired ones.
        desired_names = ["autonomy", "spirituality", "safety"]
        self.selected_vals = [v for v in self.all_vals if v.get("name", "").lower() in desired_names]
    
    async def _generate_value_reap(
        self,
        session: aiohttp.ClientSession,
        value_name: str,
        value_description: str,
        msg_history: List[dict]
    ) -> str:
        """Request a cognitive reappraisal for the specified value asynchronously."""
        prompt = prompt_template.format(
            value_name=value_name, 
            value_description=value_description
        )
        print(prompt)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        payload = {
            "model": self.reap_model,
            "messages": msg_history + [{"role": "user", "content": prompt}],
            "temperature": 1.0,
        }
        url = "https://api.openai.com/v1/chat/completions"
        async with session.post(url, headers=headers, json=payload) as resp:
            resp.raise_for_status()  # Raise exception for HTTP errors.
            data = await resp.json()
            reap = data["choices"][0]["message"]["content"].strip()
            return reap
    
    def _make_reappraisal_list_str(self, reappraisal_list: List[str]) -> str:
        """Format the list of cognitive reappraisals into a numbered string."""
        return "\n".join(f"{i+1}. {rep}" for i, rep in enumerate(reappraisal_list))
    
    async def _generate_judge_reap(
        self,
        session: aiohttp.ClientSession,
        reappraisal_list: List[str],
        msg_history: List[dict]
    ) -> str:
        """
        Request the judge model to pick the best reappraisal asynchronously.
        Returns the actual reappraisal text chosen by the judge.
        """
        reappraisal_list_str = self._make_reappraisal_list_str(reappraisal_list)
        prompt = judge_template.format(reappraisal_list_str=reappraisal_list_str)
        print(f'judge prompt: {prompt}')
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        payload = {
            "model": self.judge_model,
            "messages": msg_history + [{"role": "user", "content": prompt}],
            "reasoning_effort": "medium",
        }
        url = "https://api.openai.com/v1/chat/completions"
        async with session.post(url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
            judge_response = data["choices"][0]["message"]["content"].strip()
            print('judge response: ', judge_response)
            try:
                selected_index = int(judge_response) - 1
                if selected_index < 0 or selected_index >= len(reappraisal_list):
                    raise ValueError
            except ValueError:
                raise ValueError(f"Invalid judge response: {judge_response}")
            # Return the actual reappraisal corresponding to the judge's choice.
            return reappraisal_list[selected_index]
    
    async def generate_reappraisal(self, msg_history: List[dict]) -> Tuple[List[str], str]:
        """
        Generate a cognitive reappraisal for each selected value concurrently.
        Then, let the judge model select the best reappraisal.
        
        Returns:
            Tuple[List[str], str]: A tuple containing the list of generated reappraisals and the judge's selected reappraisal.
        """
        async with aiohttp.ClientSession() as session:
            # Launch asynchronous tasks for each pre-selected value.
            tasks = [
                self._generate_value_reap(
                    session,
                    val.get("name", ""),
                    val.get("description", ""),
                    msg_history
                )
                for val in self.selected_vals
            ]
            reappraisal_list = await asyncio.gather(*tasks)
            selected_reappraisal = await self._generate_judge_reap(session, reappraisal_list, msg_history)
            return reappraisal_list, selected_reappraisal