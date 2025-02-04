# bot/reappraisal_generator.py

import json
import asyncio
import aiohttp
import os
from typing import List, Tuple
import yaml


    
prompt_general = """
Read the conversation about an issue the user is facing. 
Respond with a 2 sentence cognitive reappraisal that will help them feel better.
Do NOT invent any information that you haven't been told. 
Do not provide validation for the user's feelings. 
Do not provide advice or solutions.
Just offer them a different perspective that will help them feel better.
"""
    
prompt_possible_values = '''
Read the conversation about an issue the user is facing. 
Look at the list of values below and respond with several cognitive reappraisals that appeal to whichever values will allow you to make the most relevant and most effective cognitive reappraisals.
A reappraisal appeals to a value if someone who really values that value would feel better after hearing the reappraisal because it speaks to what they care deeply about.
Each reappraisal should be 2 sentences.
Do NOT explicitly mention that you're trying to make a reappraisal that appeals to a particular value.
Do NOT invent any information that you haven't been told.
Respond with a JSON formatted list where each element contains a value name (as designated by the "name" field in the list below) and the cognitive reappraisal that appeals to that value.
Do not provide validation for the user's feelings. 
Do not provide advice or solutions.
Just offer them a different perspective that will help them feel better.

<output-format>
[
    {{"name": "value1", "reappraisal": "reappraisal1"}},
    {{"name": "value2", "reappraisal": "reappraisal2"}},
    ...
]
</output-format>

<values>
{vals}
</values>

<conversation>
{conversation}
</conversation>
'''


json_schema = {
  "name": "value_reappraisal_list",
  "schema": {
    "type": "object",
    "properties": {
      "reappraisals": {
        "type": "array",
        "description": "A list of reappraisals and the value associated with them.",
        "items": {
          "type": "object",
          "properties": {
            "name": {
              "type": "string",
              "description": "The name of the value associated with the reappraisal."
            },
            "reappraisal": {
              "type": "string",
              "description": "The reappraisal content."
            }
          },
          "required": [
            "name",
            "reappraisal"
          ],
          "additionalProperties": False
        }
      }
    },
    "required": [
      "reappraisals"
    ],
    "additionalProperties": False
  },
  "strict": True
}


class ReappraisalGenerator:
    def __init__(self, all_vals: List[dict]):
        self.api_token = os.getenv("OPENAI_API_KEY")
        self.all_vals = all_vals
        self.reap_model = "o1"
        
    
    async def _generate_general_reap(
        self,
        session: aiohttp.ClientSession,
        msg_history: List[dict]
    ) -> str:
        """Request a general cognitive reappraisal asynchronously."""
        prompt = prompt_general
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
            reap = data["choices"][0]["message"]["content"].strip()
            return reap
    
    async def _generate_value_reaps(
        self,
        session: aiohttp.ClientSession,
        msg_history: List[dict],
        val_list: List[dict]
    ) -> List[dict]:
        """Request cognitive reappraisals for a list of values asynchronously."""
        prompt = prompt_possible_values.format(
            vals=json.dumps(val_list),
            conversation=json.dumps(msg_history)
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        payload = {
            "model": self.reap_model,
            "messages": msg_history + [{"role": "developer", "content": prompt}],
            "reasoning_effort": "medium",
        }
        url = "https://api.openai.com/v1/chat/completions"
        async with session.post(url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
            reaps = data["choices"][0]["message"]["content"].strip()
            return json.loads(reaps)
    
    
    async def generate_all_reappraisals(
        self,
        msg_history: List[dict]
    ) -> Tuple[str, str, str]:
        """

        """
        async with aiohttp.ClientSession() as session:
            general_task = asyncio.create_task(
                self._generate_general_reap(session, msg_history)
            )
            value_task = asyncio.create_task(
                self._generate_value_reaps(session, msg_history, self.all_vals)
            )

            # Run them concurrently
            value_reaps, general_reap = await asyncio.gather(value_task, general_task)

            return value_reaps, general_reap