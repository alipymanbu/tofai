from pydantic_settings import BaseSettings
import os

class AuthSettings(BaseSettings):
    model_config = {
        "extra": "ignore", # Ignore extra fields in the environment
        "env_file": ".tofai-secrets.env", # Load environment variables from .tofai.env
    }  
    COGNITO_REGION: str = os.getenv("COGNITO_REGION", "")
    COGNITO_USER_POOL_ID: str = os.getenv("COGNITO_USER_POOL_ID", "")
    COGNITO_APP_CLIENT_ID: str = os.getenv("COGNITO_CLIENT_ID", "")
    COGNITO_APP_CLIENT_SECRET: str = os.getenv("COGNITO_CLIENT_SECRET", "")
    COGNITO_DOMAIN: str = os.getenv("COGNITO_DOMAIN", "")
    COGNITO_REDIRECT_URL: str = os.getenv("COGNITO_REDIRECT_URL", "")
    COGNITO_LOGOUT_URL: str = os.getenv("COGNITO_LOGOUT_URL", "")
    COGNITO_SCOPE: str = os.getenv("COGNITO_SCOPE", "")
    
    # JWT configs
    COGNITO_ALGORITHMS: list = ["RS256"]
    COGNITO_JWKS_URI: str = os.getenv("COGNITO_TOKEN_SIGNING_URL", "")
    
    def __init__(self, **data):
        super().__init__(**data)
        print("COGNITO_REGION", self.COGNITO_REGION)
        print("COGNITO_USER_POOL_ID", self.COGNITO_USER_POOL_ID)
        # self.COGNITO_JWKS_URI = f"https://cognito-idp.{self.COGNITO_REGION}.amazonaws.com/{self.COGNITO_USER_POOL_ID}/.well-known/jwks.json"

auth_settings = AuthSettings()