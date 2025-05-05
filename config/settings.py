import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = {
        "extra": "ignore", # Ignore extra fields in the environment
        "env_file": ".tofai-secrets.env", # Load environment variables from .tofai.env
    }  
    # Server
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "tofai")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "")
    REDIS_PORT: str = os.getenv("REDIS_PORT", "")
    REDIS_USER: str = os.getenv("REDIS_USER", "")
    REDIS_SECRET: str = os.getenv("REDIS_SECRET", "")
    
    # AI Services
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_PROJECT_NUMBER: int = int(os.getenv("GEMINI_API_PROJECT_NUMBER", 0))
    GEMINI_API_SECRET: str = os.getenv("GEMINI_API_SECRET", "")
    ELEVEN_TTS_SECRET: str = os.getenv("ELEVEN_TTS_SECRET", "")

    # APIs
    GOOGLE_SEARCH_API_KEY: str = os.getenv("GOOGLE_SEARCH_API_KEY", "")
    GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID", "")
    
    # Storage
    S3_REGION: str = os.getenv("S3_REGION", "us-east-2")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    
    # Celery settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development_secret_key")

settings = Settings()