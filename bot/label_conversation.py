
from db.crud import (
    get_user_conversations, 
    get_conversation_messages, 
    create_conversation,
    create_message,
    get_conversation_by_id,
    update_conversation
    )


from db.db_session import get_session
from bot.logger_setup import setup_logger
import yaml
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from db.models import RoleEnum, ResponseTypeEnum, ConvoStateEnum

# Set up the logger
logger = setup_logger()

# Get the directory of the current script
current_dir = Path(__file__).parent

# Load the prompts and bot messages
prompts_file = current_dir / 'prompts.yml'
with open(prompts_file, "r") as ymlfile:
    prompts = yaml.safe_load(ymlfile)

def label_convo(convo_id: int) -> Dict:
    """
    Generate a label for a conversation based on the conversation messages and update the conversation with the label.

    Args:
        convo_id (int): ID of the conversation to label

    Returns:
        Dict: Response dictionary with success or error message
    """
    from bot.bot_flow import Chatbot  # Importing here to avoid circular imports
    
    with get_session() as session:
        try:
            msgs = get_conversation_messages(session=session, conversation_id=convo_id)
            issue_msgs = [{"role": msg.role.lower(), "content": msg.content} for msg in msgs if msg.state == ConvoStateEnum.ISSUE_INTERVIEW]
            gpt_query_output = Chatbot.query_gpt(system_prompt=prompts['label_issue'], 
                                                 messages=issue_msgs)
            label_text = gpt_query_output["content"]
        except Exception as e:
            logger.error(f"Error labeling conversation")
            logger.exception(e)
            session.rollback()
            return {"success": False, "error": "Internal server error"}
        
        try:
            with get_session() as session:
                convo = get_conversation_by_id(session=session, 
                                               conversation_id=convo_id)
                convo = update_conversation(session=session,
                                            conversation=convo,
                                            oneline_summary=label_text)
                session.commit()
                logger.info(f"Updated conversation={convo_id} with label: {label_text}")
                return {"success": True}
        except Exception as e:
            logger.error(f"Error labeling conversation")
            logger.exception(e)
            session.rollback()
            return {"success": False, "error": "Internal server error"}
        
    return {"success": True, "label": label_text}