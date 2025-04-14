import boto3
import requests
import json
import base64
import time
import hmac
import hashlib
from jose import jwk, jwt
from jose.utils import base64url_decode
from typing import Dict, Any, Optional
import logging

from config.auth_settings import auth_settings

logger = logging.getLogger(__name__)

class CognitoService:
    """Service for handling AWS Cognito authentication."""
    
    def __init__(self):
        """Initialize the Cognito service."""
        self.region = auth_settings.COGNITO_REGION
        self.user_pool_id = auth_settings.COGNITO_USER_POOL_ID
        self.client_id = auth_settings.COGNITO_APP_CLIENT_ID
        self.client_secret = auth_settings.COGNITO_APP_CLIENT_SECRET
        self.domain = auth_settings.COGNITO_DOMAIN
        self.redirect_uri = auth_settings.COGNITO_REDIRECT_URL
        self.logout_uri = auth_settings.COGNITO_LOGOUT_URL
        
        # Initialize boto3 client
        self.client = boto3.client('cognito-idp', region_name=self.region)
        
        # Get the JSON Web Key Set for token validation
        self.jwks = self._get_jwks()
        
    def _get_jwks(self) -> Dict:
        """Fetch the JSON Web Key Set from Cognito."""
        try:
            keys_url = auth_settings.COGNITO_JWKS_URI
            response = requests.get(keys_url)
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error fetching JWKS: {str(e)}")
            return {"keys": []}
    
    def get_login_url(self, state: str = None) -> str:
        """Generate the URL for Cognito hosted UI login."""
        base_url = f"https://{self.domain}.auth.{self.region}.amazoncognito.com/login"
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "openid email profile",
            "redirect_uri": self.redirect_uri
        }
        
        if state:
            params["state"] = state
            
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    def get_logout_url(self) -> str:
        """Generate the URL for Cognito hosted UI logout."""
        base_url = f"https://{self.domain}.auth.{self.region}.amazoncognito.com/logout"
        params = {
            "client_id": self.client_id,
            "logout_uri": self.logout_uri
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        try:
            token_endpoint = f"https://{self.domain}.auth.{self.region}.amazoncognito.com/oauth2/token"
            
            # Create the authorization string with client ID and secret
            auth_string = f"{self.client_id}:{self.client_secret}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {encoded_auth}"
            }
            
            data = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "code": code,
                "redirect_uri": self.redirect_uri
            }
            
            response = requests.post(token_endpoint, headers=headers, data=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error exchanging code for tokens: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception exchanging code for tokens: {str(e)}")
            return None
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify the JWT token from Cognito."""
        try:
            # Get token header data
            headers = jwt.get_unverified_headers(token)
            kid = headers['kid']
            
            # Find the key that was used to sign the token
            key = None
            for k in self.jwks['keys']:
                if k['kid'] == kid:
                    key = k
                    break
            
            if not key:
                logger.error("Key not found in JWKS")
                return None
            
            # Verify the signature
            public_key = jwk.construct(key)
            message, encoded_signature = token.rsplit('.', 1)
            decoded_signature = base64url_decode(encoded_signature.encode())
            
            # Verify the token
            if not public_key.verify(message.encode(), decoded_signature):
                logger.error("Signature verification failed")
                return None
            
            # Verify the claims
            claims = jwt.get_unverified_claims(token)
            
            # Verify token is not expired
            if time.time() > claims['exp']:
                logger.error("Token is expired")
                return None
                
            # Verify audience (client ID)
            if claims['client_id'] != self.client_id and claims.get('aud') != self.client_id:
                logger.error("Token audience mismatch")
                return None
                
            # Verify issuer
            expected_issuer = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"
            if claims['iss'] != expected_issuer:
                logger.error("Token issuer mismatch")
                return None
            
            return claims
            
        except Exception as e:
            logger.error(f"Exception verifying token: {str(e)}")
            return None
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information using the access token."""
        try:
            userinfo_endpoint = f"https://{self.domain}.auth.{self.region}.amazoncognito.com/oauth2/userInfo"
            
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            response = requests.get(userinfo_endpoint, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error getting user info: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception getting user info: {str(e)}")
            return None
    
    def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh the access token using the refresh token."""
        try:
            token_endpoint = f"https://{self.domain}.auth.{self.region}.amazoncognito.com/oauth2/token"
            
            # Create the authorization string with client ID and secret
            auth_string = f"{self.client_id}:{self.client_secret}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {encoded_auth}"
            }
            
            data = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "refresh_token": refresh_token
            }
            
            response = requests.post(token_endpoint, headers=headers, data=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error refreshing tokens: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception refreshing tokens: {str(e)}")
            return None