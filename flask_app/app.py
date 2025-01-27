
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException
from flask_app.logger_setup import setup_logger
from werkzeug.middleware.proxy_fix import ProxyFix

# Import extensions
from flask_app.extensions import init_extensions, login_manager, db
from flask_app.config import CurrentConfig

def create_app(config=CurrentConfig):
    # Load environment variables
    load_dotenv()

    # Create and configure the Flask app
    app = Flask(__name__)
    app.config.from_object(config)
    # app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Initialize logger
    logger = setup_logger()
    app.logger = logger

    # Initialize Flask extensions
    init_extensions(app)
    

    # Register Blueprints
    from flask_app.blueprints.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from flask_app.blueprints.chat import chat_bp
    app.register_blueprint(chat_bp, url_prefix='/chat')
    from flask_app.blueprints.user import user_bp
    app.register_blueprint(user_bp, url_prefix='/user')
    
    # User loader
    from db.db_session import get_session
    from db.crud import get_user_by_id
    @login_manager.user_loader
    def load_user(user_id):
        with get_session() as session:
            return get_user_by_id(session, user_id)
        
    # Health Check
    @app.route('/health', methods=['GET'])
    def health():
        return {'status': 'healthy'}, 200
    
    # Log all requests
    # @app.before_request
    # def log_request():
    #     logger.info(f"{request.method} {request.url}")
        

    # Error Handlers
    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({'error': 'Unauthorized access'}), 401
    
    @app.errorhandler(404)
    def not_found_error(e):
        logger.warning(f"404 Not Found: {request.method} {request.url}")
        return {'error': 'Resource not found'}, 404

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        logger.error(f"HTTPException: {e.description} ({e.code}) at {request.method} {request.url}")
        return {'error': e.description}, e.code

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.exception(f"Unhandled Exception at {request.method} {request.url}")
        return {'error': 'Internal server error'}, 500
    
    # Create all tables
    with app.app_context():
        db.create_all()

    return app