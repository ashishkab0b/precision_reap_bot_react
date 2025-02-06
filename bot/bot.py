# bot/bot.py

from fastapi import FastAPI, Request
import yaml
from pathlib import Path
from db.crud import (
    get_conversation_messages, 
    create_conversation,
    create_message,
    get_conversation_by_id,
    update_conversation
    )
from fastapi.exceptions import HTTPException
from db.db_session import get_session
from db.models import RoleEnum, ResponseTypeEnum, ConvoStateEnum
from bot.bot_flow import run_state_logic, Chatbot
from bot.logger_setup import setup_logger
from bot.config import CurrentConfig
import uuid

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
    logger.debug(f"Entered bot /new_chat endpoint")
    data = await request.json()
    pid = data.get('pid')

    # Generate a new conversation code
    convo_code = str(uuid.uuid4())
    
    with get_session() as session:
        try:
            convo = create_conversation(session=session,
                                        pid=pid,
                                        convo_code=convo_code)
            session.flush()
        except Exception as e:
            logger.error(f"Error creating conversation")
            logger.exception(e)
            raise 
        first_msg = {
            "convoId": convo.id,
            "role": RoleEnum.ASSISTANT,
            "responseType": ResponseTypeEnum.TEXT,
            "content": bot_msgs['start']['content'],
            "options": None,
        }
        try:
            msg = create_message(session=session, 
                                 convo_id=convo.id,
                                 role=first_msg['role'],
                                 state=ConvoStateEnum.START,
                                 response_type=first_msg['responseType'],
                                 content=first_msg['content'],
                                 options=first_msg['options'])
            
            # Update the conversation state
            convo.state = ConvoStateEnum.ISSUE_INTERVIEW
            session.flush()
            first_msg['msgId'] = msg.id
        except Exception as e:
            logger.error(f"Error creating first message")
            logger.exception(e)
            raise
            
        resp = {
            "convoId": convo.id,
            "convoCode": convo.convo_code,
            "convoState": convo.state,
            "messages": [first_msg]
        }
        return resp
            
    
@app.post("/send_message")
async def send_message(request: Request):
    data = await request.json()

    convo_id = data.get('convoId')
    content = data.get('content') or ""
    response_type = data.get('responseType')
    options = data.get('options')
    
    user_msg = {
        "role": RoleEnum.USER,
        "content": content,
        "responseType": response_type,
        "options": options
    }

    # 1) Let the BotFlow do its thing
    result = await run_state_logic(
        convo_id=convo_id,
        user_msg=user_msg
    )

    # 2) Format the return 
    resp = {
        "convoId": convo_id,
        "role": RoleEnum.ASSISTANT,
        "responseType": result.get("responseType"), 
        "content": result.get("content", ""),
        "options": result.get("options", {}),
        "convoState": result.get("convoState")
    }

    return resp

    