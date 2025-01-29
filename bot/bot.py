# bot/bot.py

from fastapi import FastAPI, Request
import yaml
from pathlib import Path
from db.crud import (
    get_user_conversations, 
    get_conversation_messages, 
    create_conversation,
    create_message,
    get_conversation_by_id,
    update_conversation
    )
import openai
import asyncio
from fastapi.exceptions import HTTPException
# from db.db_session_async import get_async_session
from db.db_session import get_session
from db.models import RoleEnum, ResponseTypeEnum, ConvoStateEnum
from bot.bot_flow import run_state_logic, Chatbot
from bot.logger_setup import setup_logger
from bot.config import CurrentConfig

'''
uvicorn bot.bot:app --host 0.0.0.0 --port 8001 --reload
'''
# Set up the logger
logger = setup_logger()

# Get the directory of the current script
current_dir = Path(__file__).parent

# Load the prompts and bot messages
prompts_file = current_dir / 'prompts.yml'
with open(prompts_file, "r") as ymlfile:
    prompts = yaml.safe_load(ymlfile)
    
bot_msgs_file = current_dir / 'bot_msgs.yml'
with open(bot_msgs_file, "r") as ymlfile:
    bot_msgs = yaml.safe_load(ymlfile)

# Initialize the FastAPI app
app = FastAPI()

@app.post("/new_chat")
async def new_chat(request: Request):
    data = await request.json()
    
    with get_session() as session:
        try:
            convo = create_conversation(session=session, user_id=data['user_id'])
            session.flush()
            resp = {
                "convo_id": convo.id,
                "role": RoleEnum.ASSISTANT,
                "response_type": ResponseTypeEnum.TEXT,
                "content": bot_msgs['start']['content'],
                "options": None,
            }
            msg = create_message(session=session, 
                                 user_id=data['user_id'], 
                                 conversation_id=convo.id,
                                 role=resp['role'],
                                 state=ConvoStateEnum.START,
                                 response_type=resp['response_type'],
                                 content=resp['content'],
                                 options=resp['options'])
            
            # Update the conversation state
            convo.state = ConvoStateEnum.ISSUE_INTERVIEW
            session.commit()
            resp['msg_id'] = msg.id
            return resp
        except Exception as e:
            logger.error(f"Error in /new_chat")
            logger.exception(e)
            session.rollback()
            return {"error": "Internal server error"}
    
@app.post("/send_message")
async def send_message(request: Request):
    data = await request.json()

    user_id = data.get('user_id')
    convo_id = data.get('conversation_id')
    content = data.get('content') or ""
    response_type = data.get('response_type')
    options = data.get('options')
    
    user_msg = {
        "role": RoleEnum.USER,
        "content": content,
        "response_type": response_type,
        "options": options
    }

    # 1) Let the BotFlow do its thing
    result = run_state_logic(
        conversation_id=convo_id,
        user_id=user_id,
        user_msg=user_msg
    )

    # 2) Format the return 
    resp = {
        "convo_id": convo_id,
        "role": RoleEnum.ASSISTANT,
        "response_type": result.get("response_type"), 
        "content": result.get("content", ""),
        "options": result.get("options", {}),
        "convo_state": result.get("convo_state")
    }

    return resp

    