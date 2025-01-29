import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    

    SECRET_KEY = os.environ['SECRET_KEY']
    WTF_CSRF_ENABLED = True
    
    NEW_USER_OTP_EXPIRY_MIN = 60
    
    MAIL_SERVER = 'live.smtp.mailtrap.io'
    MAIL_PORT = 587
    MAIL_USERNAME = os.environ['MAIL_USERNAME']
    MAIL_PASSWORD = os.environ['MAIL_PASSWORD']
    MAILTRAP_API_TOKEN = os.environ['MAILTRAP_API_TOKEN']
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_SUPPORT_RECIPIENT = os.environ['MAIL_SUPPORT_RECIPIENT']
    
    SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']
    SQLALCHEMY_ENGINE_OPTIONS = {'connect_args': {'options': '-csearch_path=public'}}

    RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', None)
    
    SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']
    
    REDDIT_CLIENT_ID = os.environ['REDDIT_CLIENT_ID']
    REDDIT_CLIENT_SECRET = os.environ['REDDIT_CLIENT_SECRET']
    REDDIT_USER_AGENT = "reappraiseit app by u/reappraiseit"
    REDDIT_SCOPES = ["identity", "history", "mysubreddits", "read"]
    


class DevelopmentConfig(BaseConfig):
    
    DEBUG = True
    BASE_URL = "http://localhost:3000"
    BOT_SERVICE_URL = "http://localhost:8001"
    
    
    REDDIT_REDIRECT_URI = "http://localhost:8080/auth/reddit/auth_callback"
        
    SESSION_COOKIE_SAMESITE="Lax"  # "None" if HTTPS
    SESSION_COOKIE_SECURE=False    # True if HTTPS

class ProductionConfig(BaseConfig):
    
    DEBUG = False
    BASE_URL = "https://reappraise.it"
    BOT_SERVICE_URL = "http://bot:8001"
        
    SESSION_COOKIE_SAMESITE=None  # "None" if HTTPS
    SESSION_COOKIE_SECURE=True    # True if HTTPS

config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig
}

current_env = os.getenv("FLASK_ENV", "development")
CurrentConfig = config_map.get(current_env, DevelopmentConfig)