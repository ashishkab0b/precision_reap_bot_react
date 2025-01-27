from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from db.crud import (
    get_user_by_id,
    update_user
)
from db.db_session import get_session

user_bp = Blueprint('user', __name__)

@user_bp.route('/update_user', methods=['POST'])
@login_required
def update_user_route():
    """
    Updates partial user info. Accepts JSON body with any of the allowed fields:
      { "age": ..., "gender": ..., "research_consent": ... }
    """
    data = request.json
    current_app.logger.debug(f'Entered /update_user endpoint with user: {current_user.email}')
    current_app.logger.debug(f'/update_user received data: {data}')
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    allowed_fields = ['age', 'gender', 'research_consent']
    
    consent_map = {"yes": True, "no": False}

    with get_session() as session:
        try:
            user = get_user_by_id(session, current_user.id)
            if not user:
                return jsonify({'error': 'User not found'}), 404

            update_data = {k: v for k, v in data.items() if k in allowed_fields}
            if 'research_consent' in update_data:
                update_data['research_consent'] = consent_map.get(update_data['research_consent'].lower())
                
            update_user(session, user, **update_data)
            session.commit()
        except Exception as e:
            current_app.logger.error(f'Error in /update_user')
            current_app.logger.exception(e)
            return jsonify({'error': 'Internal server error'}), 500

    return jsonify({'message': 'User updated successfully'}), 200

@user_bp.route('/get_user_data', methods=['GET'])
@login_required
def get_user_data():
    """
    Returns the current user's public fields, e.g.:
      {
        'id': ...
        'email': ...
        'age': ...
        'gender': ...
        'research_consent': ...
      }
    """
    current_app.logger.debug(f'Entered /get_user_data endpoint with user: {current_user.email}')
    with get_session() as session:
        user = get_user_by_id(session, current_user.id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user_data = {
            'id': user.id,
            'email': user.email,
            'age': user.age,
            'gender': user.gender,
            'research_consent': user.research_consent
        }

    return jsonify(user_data), 200