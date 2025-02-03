import asyncio
import os
from reappraisal_generator import ReappraisalGenerator

async def main():
    messages = [
        {"role": "assistant", "content": "I’m here to listen. Can you describe what’s been on your mind lately?"},
        {"role": "user", "content": "I just feel really overwhelmed with work. No matter how much I do, it never feels like enough."},
        {"role": "assistant", "content": "That sounds really exhausting. When did you start feeling this way?"},
        {"role": "user", "content": "I guess it's been building up for months, but it got worse in the past few weeks."},
    ]
    
    api_token = os.getenv("OPENAI_API_KEY")
    if not api_token:
        raise ValueError("The OPENAI_API_KEY environment variable is not set.")
    
    reap_gen = ReappraisalGenerator(api_token=api_token)
    reappraisal_list, selected_reappraisal = await reap_gen.generate_reappraisal(msg_history=messages)
    
    print("Generated Cognitive Reappraisals:")
    for idx, rep in enumerate(reappraisal_list, start=1):
        print(f"{idx}. {rep}\n")
    
    print("Judge's Selected Reappraisal:")
    print(selected_reappraisal)

if __name__ == "__main__":
    asyncio.run(main())