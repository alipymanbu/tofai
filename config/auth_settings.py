from pydantic_settings import BaseSettings
from config.secrets import AUTH_CREDS

class AuthSettings(BaseSettings):
    COGNITO_REGION: str = AUTH_CREDS["region"]  # Change to your region
    COGNITO_USER_POOL_ID: str = AUTH_CREDS["user_pool_id"]  # Fill from AWS Console
    COGNITO_APP_CLIENT_ID: str = AUTH_CREDS["client_id"]  # Fill from AWS Console
    COGNITO_APP_CLIENT_SECRET: str = AUTH_CREDS["client_secret"] # Fill from AWS Console
    COGNITO_DOMAIN: str = AUTH_CREDS["domain"]  # Fill from AWS Console
    COGNITO_REDIRECT_URL: str = AUTH_CREDS["redirect_url"]  # Fill from AWS Console
    COGNITO_LOGOUT_URL: str = AUTH_CREDS["logout_url"]  # Fill from AWS Console
    COGNITO_SCOPE: str = AUTH_CREDS["scope"]  # Fill from AWS Console
    
    # JWT configs
    COGNITO_ALGORITHMS: list = ["RS256"]
    COGNITO_JWKS_URI: str = AUTH_CREDS["token_signing_url"]  # Will be populated during initialization
    
    def __init__(self, **data):
        super().__init__(**data)
        self.COGNITO_JWKS_URI = f"https://cognito-idp.{self.COGNITO_REGION}.amazonaws.com/{self.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    
    class Config:
        env_file = ".env"

auth_settings = AuthSettings()