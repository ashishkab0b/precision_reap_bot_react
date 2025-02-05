# flask_app/blueprints/chat.py

from flask import Blueprint, request, jsonify, current_app
from db.crud import (
    get_conversation_messages, 
    get_conversation_by_pid_code
    )
from db.db_session import get_session
from db.models import RoleEnum, ResponseTypeEnum, ConvoStateEnum
import requests
import uuid

chat_bp = Blueprint('chat', __name__)

# ---- Sending messages ---- #

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
def send_message_route():
    current_app.logger.debug(f'Entered /send_message endpoint')
    data = request.get_json()
    current_app.logger.debug(f'/send_message received data: {data}')

    # Extract data from request
    convo_id = data.get('convoId')
    content = data.get('content')
    response_type = data.get('responseType')
    options = data.get('options')
    
    # Send message to bot and get response
    try:
        bot_response = send_message_to_bot({
            'convoId': convo_id,
            'content': content,
            'responseType': response_type,
            'options': options
        })
        current_app.logger.debug(f"/send_message returning: {bot_response}")
        return jsonify(bot_response), 201
    except Exception as e:
        current_app.logger.error(f'Error in /send_message')
        current_app.logger.exception(e)
        return jsonify({'error': 'Internal server error'}), 500
    
# ---- Starting conversations ---- #

@chat_bp.route('/new_chat', methods=['POST'])
def new_chat_route():
    """
    Start a new conversation with the bot and return 201 on success.
    """
    current_app.logger.debug(f'Entered flask /new_chat endpoint')
    data = request.get_json()
    current_app.logger.debug(f'/new_chat received data: {data}')
    pid = data.get('pid')
    if not pid:
        return jsonify({'error': 'Missing pid'}), 400
    
    # Send the initial request to the bot
    url = current_app.config['BOT_SERVICE_URL'] + '/new_chat'
    payload = {
        'pid': pid
    }
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        current_app.logger.debug(f'fast api /new_chat returned: {resp.json()}')
        output = {
            'convoId': data['convoId'],
            'code': data['convoCode'],
            'state': data['convoState'],
            'messages': data['messages']
        }
        return jsonify(output), 201
    except Exception as e:
        current_app.logger.error(f'Error in /new_chat')
        current_app.logger.exception(e)
        return jsonify({'error': 'Internal server error'}), 500  

# ---- Getting existing conversation ---- #
@chat_bp.route('/get_conversation', methods=['GET'])
def get_conversation_route():
    """
    Get messages for a conversation.
    """
    current_app.logger.debug(f'Entered /get_conversation endpoint')
    
    # Extract data from request (pid and code query params)
    pid = request.args.get('pid')
    code = request.args.get('code')
    current_app.logger.debug(f'/get_conversation received pid: {pid}, code: {code}')
    
    # Check for missing data
    if not pid:
        current_app.logger.error(f'Missing pid in /get_conversation')
        return jsonify({'error': 'Missing pid'}), 400
    
    if not code:
        current_app.logger.info(f'No code found for pid: {pid}')
        return jsonify({'exists': False}), 200
    
    # Get conversation object
    with get_session() as session:
        convo = get_conversation_by_pid_code(session=session, pid=pid, convo_code=code)
        if not convo:
            current_app.logger.warning(f'No conversation found for pid: {pid} and code: {code}')
            return jsonify({'exists': False}), 200
        messages = get_conversation_messages(session=session, convo_id=convo.id)
        messages_out = []
        for msg in messages:
            messages_out.append({
                'msgId': msg.id,
                'convoId': msg.convo_id,
                'content': msg.content,
                'role': msg.role,
                'responseType': msg.response_type,
                'options': msg.options
            })
        return jsonify({
            'exists': True,
            'convoId': convo.id,
            'convoState': convo.state,
            'messages': messages_out,
        }), 200
    
