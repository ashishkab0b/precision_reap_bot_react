from flask import Blueprint, request, jsonify, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import generate_csrf
from db.models import db, User
from db.db_session import get_session
from db.crud import get_user_by_email, create_user
from flask_app.blueprints.reddit import reddit_bp


auth_bp = Blueprint('auth', __name__)
auth_bp.register_blueprint(reddit_bp)


@auth_bp.route('/csrf-token', methods=['GET'])
def get_csrf_token():
    token = generate_csrf()
    return jsonify({'csrf_token': token})

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Check if email and password are provided
    if not email or not password:
        return jsonify({'error': 'Missing email or password'}), 400
    
    # Hash the password
    hashed_password = generate_password_hash(password)

    with get_session() as session:
        
        # Check if user already exists
        if get_user_by_email(session, email):
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        create_user(session, email, hashed_password)
        
        # Commit the transaction
        session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    with get_session() as session:
        user = get_user_by_email(session, email)

    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return jsonify({'message': 'Login successful'}), 200

    return jsonify({'error': 'Invalid email or password'}), 401

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/current_user', methods=['GET'])
@login_required
def get_current_user():
    return jsonify({'email': current_user.email}), 200

@auth_bp.route('/check_email', methods=['POST'])
def check_email():
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    with get_session() as session:
        user = get_user_by_email(session, email)

    # Return whether the user exists
    return jsonify({'exists': bool(user)})