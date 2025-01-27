# flask_app/blueprints/chat.py

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from db.crud import (
    get_user_conversations, 
    get_conversation_messages, 
    get_conversation_by_id,
    create_conversation,
    create_message,
    soft_delete_conversation
    )
from db.db_session import get_session
from db.models import RoleEnum, ResponseTypeEnum, ConvoStateEnum
import requests
import asyncio
import aiohttp

chat_bp = Blueprint('chat', __name__)
def send_message_to_bot(data):
    url = current_app.config['BOT_SERVICE_URL'] + '/send_message'
    current_app.logger.debug(f"Sending message to bot at {url} with data: {data}")
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        current_app.logger.error(f'Error sending message to bot')
        current_app.logger.exception(e)
        return {'error': 'Bot service error'}

@chat_bp.route('/send_message', methods=['POST'])
@login_required
def send_message_route():
    current_app.logger.debug(f'Entered /send_message endpoint with user: {current_user.email}')
    data = request.get_json()
    current_app.logger.debug(f'/send_message received data: {data}')

    # Extract data from request
    convo_id = data.get('conversation_id')
    content = data.get('content')
    response_type = data.get('response_type')
    response_type_enum = ResponseTypeEnum[response_type.upper()]
    options = data.get('options')
    

    # Send message to bot and get response
    try:
        bot_response = send_message_to_bot({
            'user_id': current_user.id,
            'conversation_id': convo_id,
            'content': content,
            'response_type': response_type,
            'options': options
        })
        current_app.logger.debug(f"/send_message returning: {bot_response}")
        return jsonify(bot_response), 201
    except Exception as e:
        current_app.logger.error(f'Error in /send_message')
        current_app.logger.exception(e)
        return jsonify({'error': 'Internal server error'}), 500
    
    
 

@chat_bp.route('/new_chat', methods=['POST'])
@login_required
def new_chat_route():
    current_app.logger.debug(f'Entered /new_chat endpoint with user: {current_user.email}')
    url = current_app.config['BOT_SERVICE_URL'] + '/new_chat'
    # TODO: DO I NEED TO PASS ANY AUTHENTICATION HERE?
    payload = {
        'user_id': current_user.id,
    }
    try:
        resp = requests.post(url, json=payload)
        return jsonify(resp.json()), 200
    except Exception as e:
        current_app.logger.error(f'Error in /new_chat')
        current_app.logger.exception(e)
        return jsonify({'error': 'Internal server error'}), 500   
    
@chat_bp.route('/delete_conversation/<conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation_route(conversation_id):
    """
    Deletes a conversation by id
    
    Args:
        conversation_id (int): The id of the conversation to delete
        
    Returns:
        dict: A message indicating success or failure
    """
    current_app.logger.debug(f'Entered /delete_conversation endpoint with user: {current_user.email} and conversation_id: {conversation_id}')
    with get_session() as session:
        try:
            convo = get_conversation_by_id(session=session, conversation_id=conversation_id)
            if not convo:
                return jsonify({'error': 'Conversation not found'}), 404
            soft_delete_conversation(session=session, conversation=convo)
            session.commit()
            current_app.logger.debug(f"Conversation {conversation_id} deleted")
            return jsonify({'message': 'Conversation deleted successfully'}), 200
        except Exception as e:
            current_app.logger.error(f'Error in /delete_conversation')
            current_app.logger.exception(e)
            session.rollback()
            return jsonify({'error': 'Internal server error'}), 500
    
    
@chat_bp.route('/get_messages', methods=['GET'])
@login_required
def get_messages_route():
    current_app.logger.debug(f'Entered /get_messages endpoint with user: {current_user.email}')
    convo_id = request.args.get('conversation_id', type=int)

    with get_session() as session:
        try:
            msgs = get_conversation_messages(session=session, conversation_id=convo_id)
            msgs_out = []
            for msg in msgs:
                msgs_out.append({
                    'msg_id': msg.id,
                    'convo_id': msg.conversation_id,
                    'content': msg.content,
                    'role': msg.role,
                    'response_type': msg.response_type,
                    'options': msg.options,
                    'bot_version': msg.bot_version,
                })
            return jsonify(msgs_out), 200
        except Exception as e:
            current_app.logger.error(f'Error in /get_messages')
            current_app.logger.exception(e)
            session.rollback()
            return jsonify({'error': 'Internal server error'}), 500
        
        
@chat_bp.route('/get_conversation', methods=['GET'])
@login_required
def get_conversation_route():
    current_app.logger.debug(f'Entered /get_conversation endpoint with user: {current_user.email}')
    convo_id = request.args.get('conversation_id', type=int)
    with get_session() as session:
        try:
            convo = get_conversation_by_id(session=session, conversation_id=convo_id)
            current_app.logger.debug(f'/get_conversation returning: {convo}')
            return jsonify({
                'convo_id': convo.id,
                'user_id': convo.user_id,
                'state': convo.state,
                'oneline_summary': convo.oneline_summary,
                'ephemeral': convo.ephemeral,
                'last_active_at': convo.last_active_at,
            }), 200
        except Exception as e:
            current_app.logger.error(f'Error in /get_conversation')
            current_app.logger.exception(e)
            session.rollback()
            return jsonify({'error': 'Internal server error'}), 500


@chat_bp.route('/get_conversations', methods=['GET'])
@login_required
def get_conversations_route():
    current_app.logger.debug(f'Entered /get_conversations endpoint with user: {current_user.email}')
    with get_session() as session:
        try:
            convos = get_user_conversations(session=session, user_id=current_user.id)
            convo_out = []
            for convo in convos:
                
                # Skip ephemeral conversations
                if convo.ephemeral is True:
                    continue
                
                # Make a label if it doesn't exist
                if convo.oneline_summary is None:
                    msgs = get_conversation_messages(session=session, conversation_id=convo.id)
                    user_msgs = [msg for msg in msgs if msg.role == RoleEnum.USER]
                    label = user_msgs[0].content[:20] if user_msgs else 'No messages'
                else:
                    label = convo.oneline_summary
                
                convo_out.append({
                    'id': convo.id,
                    'label': label,
                })
            return jsonify(convo_out), 200
        except Exception as e:
            current_app.logger.error(f'Error in /get_conversations')
            current_app.logger.exception(e)
            session.rollback()
            return jsonify({'error': 'Internal server error'}), 500

# @chat_bp.route('/label_issue', methods=['POST'])
# @login_required
# def label_issue_route():
#     current_app.logger.debug(f'Entered /label_issue endpoint with user: {current_user.email}')
#     data = request.get_json()
#     convo_id = data.get('convo_id')
#     url = current_app.config['BOT_SERVICE_URL'] + '/label_issue'
#     payload = {
#         'convo_id': convo_id,
#     }
#     try:
#         resp = requests.post(url, json=payload)
#         resp_json = resp.json()
#         current_app.logger.debug(f"Received response from bot service: {resp_json}")
#     except Exception as e:
#         current_app.logger.error(f'Error in /label_issue')
#         current_app.logger.exception(e)
#         return jsonify({'error': 'Internal server error'}), 500
        
            
        