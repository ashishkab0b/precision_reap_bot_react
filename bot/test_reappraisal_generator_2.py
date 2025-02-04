import asyncio
import os
from reappraisal_generator_2 import ReappraisalGenerator
import json

async def main():
    # Example conversation history
    messages = [
        {
            "role": "assistant",
            "content": "I understand that you're feeling financial regret. Before we dive deeper, is there any broader context you think we should know? This could include things about yourself, other people involved, or any relevant history or circumstances you haven't mentioned yet."
        },
        {
            "role": "user",
            "content": "I made some impulsive purchases last year, and now I'm struggling to keep up with my bills. I didn't really think about how things would add up over time."
        },
        {
            "role": "assistant",
            "content": "That makes sense. It sounds like these purchases felt manageable in the moment, but over time, they created financial strain. How has this issue affected other areas of your life beyond just your financial situation?"
        },
        {
            "role": "user",
            "content": "It’s been stressful. I’ve had to cut back on socializing because I can’t afford to go out, and I feel guilty whenever I spend money on anything."
        },
        {
            "role": "assistant",
            "content": "I can see how that would be difficult—feeling isolated and weighed down by guilt. If you imagine an ideal world, how would this situation be different for you?"
        },
        {
            "role": "user",
            "content": "In an ideal world, I would have been more disciplined with my spending and had enough savings to cover unexpected expenses. I wouldn’t feel this constant stress."
        },
        {
            "role": "assistant",
            "content": "That makes sense. Let’s take a moment to focus on what you’re feeling right now. Can you list the emotions you’re experiencing about this situation? You can name multiple emotions, and they don’t all have to be negative."
        },
        {
            "role": "user",
            "content": "I feel regret, anxiety, and shame."
        },
        {
            "role": "assistant",
            "content": "You mentioned feeling regret. From what you've shared, it seems like this comes from looking back at your spending choices and wishing you had done things differently. If you think about it more specifically, is there anything else that makes you feel this regret?"
        },
        {
            "role": "user",
            "content": "I think I regret not listening to my own instincts. I had moments where I hesitated before buying things, but I ignored those feelings and justified the purchases anyway."
        },
        {
            "role": "assistant",
            "content": "That makes sense—it sounds like part of the regret is not just about the purchases themselves but about not trusting yourself in those moments. You also mentioned anxiety. If you’re comfortable, could you elaborate on what specifically is making you feel anxious?"
        }
    ]
    
    # Check for API key in environment
    api_token = os.getenv("OPENAI_API_KEY")
    if not api_token:
        raise ValueError("The OPENAI_API_KEY environment variable is not set.")
    
    with open('/Users/ashish/files/research/projects/vbr/precision_reap_bot_react_study/bot/val_list_model.json', 'r') as f:
        all_vals = json.load(f)
        
    # Instantiate ReappraisalGenerator with the full list of possible values
    reap_gen = ReappraisalGenerator(all_vals=all_vals)

    
    # Generate all reappraisals concurrently
    values_reaps, general_reap = await reap_gen.generate_all_reappraisals(messages)
    
    print("==== Value reaps ====")
    print(json.dumps(values_reaps, indent=2))
    print("\n==== General Reappraisal ====")
    print(general_reap)

if __name__ == "__main__":
    asyncio.run(main())