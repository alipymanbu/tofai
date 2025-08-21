from pydantic import Field
from pydantic_settings import BaseSettings
import os

class AuthSettings(BaseSettings):
    model_config = {
        "extra": "ignore", # Ignore extra fields in the environment
        "env_file": ".tofai-secrets.env", # Load environment variables from .tofai.env
    }  
    COGNITO_REGION: str = Field(os.getenv("COGNITO_REGION", ""))
    COGNITO_USER_POOL_ID: str = Field(os.getenv("COGNITO_USER_POOL_ID", ""))
    COGNITO_APP_CLIENT_ID: str = Field(os.getenv("COGNITO_CLIENT_ID", ""), alias="COGNITO_CLIENT_ID")
    COGNITO_APP_CLIENT_SECRET: str = Field(os.getenv("COGNITO_CLIENT_SECRET", ""), alias="COGNITO_CLIENT_SECRET")
    COGNITO_DOMAIN: str = Field(os.getenv("COGNITO_DOMAIN", ""))
    COGNITO_REDIRECT_URL: str = Field(os.getenv("COGNITO_REDIRECT_URL", ""))
    COGNITO_LOGOUT_URL: str = Field(os.getenv("COGNITO_LOGOUT_URL", ""))
    COGNITO_SCOPE: str = Field(os.getenv("COGNITO_SCOPE", ""))
    
    # JWT configs
    COGNITO_ALGORITHMS: list = ["RS256"]
    COGNITO_JWKS_URI: str = Field(os.getenv("COGNITO_TOKEN_SIGNING_URL", ""), alias="COGNITO_TOKEN_SIGNING_URL")
    
    def __init__(self, **data):
        super().__init__(**data)

auth_settings = AuthSettings()