import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    openai_api_key = os.environ['OPENAI_API_KEY']
    # openai_chat_model = "gpt-4o"
    # openai_chat_model = "o3-mini"
    # openai_chat_model = "gpt-4o-mini"
    # openai_temperature = 1
    pass



class DevelopmentConfig(BaseConfig):
    pass
    


class ProductionConfig(BaseConfig):
    pass
    


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig
}

current_env = os.getenv("FLASK_ENV", "development")
CurrentConfig = config_map.get(current_env, DevelopmentConfig)