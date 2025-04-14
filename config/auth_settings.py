from pydantic_settings import BaseSettings

class AuthSettings(BaseSettings):
    COGNITO_REGION: str = "us-east-1"  # Change to your region
    COGNITO_USER_POOL_ID: str = ""  # Fill from AWS Console
    COGNITO_APP_CLIENT_ID: str = ""  # Fill from AWS Console
    COGNITO_APP_CLIENT_SECRET: str = ""  # Fill from AWS Console
    COGNITO_DOMAIN: str = ""  # Fill from AWS Console
    COGNITO_REDIRECT_URL: str = "http://localhost:8000/api/auth/callback"
    COGNITO_LOGOUT_URL: str = "http://localhost:8000"
    
    # JWT configs
    COGNITO_ALGORITHMS: list = ["RS256"]
    COGNITO_JWKS_URI: str = ""  # Will be populated during initialization
    
    def __init__(self, **data):
        super().__init__(**data)
        self.COGNITO_JWKS_URI = f"https://cognito-idp.{self.COGNITO_REGION}.amazonaws.com/{self.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    
    class Config:
        env_file = ".env"

auth_settings = AuthSettings()