import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Server
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "tofai")
    
    # Redis
    REDIS_URI: str = os.getenv("REDIS_URI", "redis://localhost:6379/0")
    
    # AI Services
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # AI Model Selection
    STRATEGY_MODEL: str = os.getenv("STRATEGY_MODEL", "claude")
    SCRIPT_MODEL: str = os.getenv("SCRIPT_MODEL", "claude")
    VISUALS_MODEL: str = os.getenv("VISUALS_MODEL", "stable-diffusion")
    AUDIO_MODEL: str = os.getenv("AUDIO_MODEL", "eleven-labs")
    VIDEO_MODEL: str = os.getenv("VIDEO_MODEL", "internal-renderer")
    
    # Storage
    S3_BUCKET: str = os.getenv("S3_BUCKET", "tofai-media")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    
    # Celery settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development_secret_key")
    
    class Config:
        env_file = ".env"

settings = Settings()