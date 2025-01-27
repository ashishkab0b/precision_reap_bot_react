from flask import Flask, request, session, jsonify
from transitions import Machine
from transitions import State

states = [
    "start", 
    "issue_interview", 
    "rate_issue", 
    "generate_reap", 
    "rate_reap_1", 
    "refine_reap", 
    "rate_reap_2", 
    "complete"
    ]

transitions = [
    {"trigger": "to_issue_interview", "source": "start", "dest": "issue_interview"},
    {"trigger": "to_rate_issue", "source": "issue_interview", "dest": "rate_issue"},
    {"trigger": "to_generate_reap", "source": "rate_issue", "dest": "generate_reap"},
    {"trigger": "to_rate_reap_1", "source": "generate_reap", "dest": "rate_reap_1"},
    {"trigger": "to_refine_reap", "source": "rate_reap_1", "dest": "refine_reap"},
    {"trigger": "to_rate_reap_2", "source": "refine_reap", "dest": "rate_reap_2"},
    {"trigger": "to_complete", "source": "rate_reap_2", "dest": "complete"}
]

class BotStateMachine:
    def __init__(self):
        self.name = "BotStateMachine"
        
        self.machine = Machine(
            model=self,
            states=states,
            transitions=transitions,
            initial="start"
        )

# example use:
# bot = BotStateMachine()
# bot.to_issue_interview()
# print(bot.state)
# bot.to_rate_issue()
# print(bot.state)