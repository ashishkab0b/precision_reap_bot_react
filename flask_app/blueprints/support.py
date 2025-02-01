# flask_app/blueprints/support.py

from flask import Blueprint, request, jsonify, current_app

import requests
import mailtrap as mt
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
import requests

support_bp = Blueprint('support', __name__)

@support_bp.route('/support', methods=['POST'])
@login_required
def submit_feedback():
    current_app.logger.debug("Entered submit_feedback route.")
    data = request.get_json()
    email = data.get('email')
    query_type = data.get('type') 
    message = data.get('message')
    is_urgent = data.get('urgent', False)
    recaptcha_token = data.get('recaptcha')

    # Validate recaptcha token
    if not recaptcha_token:
        return jsonify({'error': 'reCAPTCHA token is required.'}), 400

    try:
        # Verify reCAPTCHA with Google's API
        recaptcha_response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': current_app.config['RECAPTCHA_SECRET_KEY'],  # Your reCAPTCHA secret key
                'response': recaptcha_token
            }
        )
        recaptcha_result = recaptcha_response.json()

        if not recaptcha_result.get('success') or recaptcha_result.get('score', 0) < 0.5:
            current_app.logger.warning(f"reCAPTCHA failed: {recaptcha_result}")
            return jsonify({'error': 'reCAPTCHA verification failed. Please try again.'}), 400
    except Exception as e:
        current_app.logger.error("Error verifying reCAPTCHA.")
        current_app.logger.exception(e)
        return jsonify({'error': 'An error occurred during reCAPTCHA verification.'}), 500

    if not message or not query_type:
        return jsonify({'error': 'Query type and message are required.'}), 400

    user = current_user

    if not email:
        return jsonify({'error': 'Email is required.'}), 400

    messages_list = [{
        'sender': email,
        'message': message,
    }]
    
    # Send email to the support team
    try:
        subject = f"Reappraise.it: New '{query_type}' query from {email}"
        body = f"From: {email}"
        body += f"\n\n"
        body += f"Query Type: {query_type}"
        body += f"\n\n"
        body += f"Is urgent: {is_urgent}"
        body += f"\n\n"
        body += f"Message: {message}"
        if is_urgent:
            subject = f"URGENT: {subject}"

        mail = mt.Mail(
            sender=mt.Address(email="support@emapingbot.com", name="Support request"),
            to=[mt.Address(email=current_app.config['MAIL_SUPPORT_RECIPIENT'])],
            subject=subject,
            text=body,
            category=query_type,
        )

        client = mt.MailtrapClient(token=current_app.config['MAILTRAP_API_TOKEN'])
        response = client.send(mail)
        current_app.logger.debug(f"Mailtrap response: {response}")
    except Exception as e:
        current_app.logger.error(f'Error sending email for user {user_id} - {email}.')
        current_app.logger.exception(e)
        # return jsonify({'error': 'An error occurred while sending the email.'}), 500
    else:
        current_app.logger.info(f"Email sent for user {user_id} - {email}.")
        # return jsonify({'success': 'Email sent successfully.'}), 200

    # Save the feedback to the database
    try:
        support_query = create_support_query(
            session=db.session,
            user_id=user_id,
            email=email,
            messages=messages_list,
            query_type=query_type,
            is_urgent=is_urgent
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error saving feedback for user {user_id} - {email}.')
        current_app.logger.exception(e)
        return jsonify({'error': 'An error occurred while saving feedback.'}), 500
    else:
        current_app.logger.info(f"Saved support request from user_id={user_id} - {email}.")
        return jsonify({'message': 'Feedback submitted successfully.'}), 201