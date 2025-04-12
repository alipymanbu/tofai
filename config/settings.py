import os
from pydantic_settings import BaseSettings
from config.secrets import MONGO_DB_CREDS, AWS_CREDS, REDIS_CREDS

class Settings(BaseSettings):
    # Server
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database
    MONGODB_URI: str = os.getenv("MONGODB_URI", f"mongodb+srv://{MONGO_DB_CREDS["user"]}:{MONGO_DB_CREDS["password"]}@tofai-cluster0.kpxoiil.mongodb.net/?appName=tofai-cluster0&tlsAllowInvalidCertificates=true")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "tofai")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis-14879.c285.us-west-2-2.ec2.redns.redis-cloud.com")
    REDIS_PORT: str = os.getenv("REDIS_PORT", "14879")
    REDIS_USER: str = os.getenv("REDIS_USER", REDIS_CREDS["user"])
    REDIS_SECRET: str = os.getenv("REDIS_SECRET", REDIS_CREDS["password"])
    
    # AI Services
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Storage
    S3_BUCKET: str = os.getenv("S3_BUCKET", "tofai-media")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", AWS_CREDS["key"])
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", AWS_CREDS["secret"])
    AWS_REGION: str = os.getenv("AWS_REGION", "us-west-2")
    
    # Celery settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development_secret_key")
    
    class Config:
        env_file = ".env"

settings = Settings()