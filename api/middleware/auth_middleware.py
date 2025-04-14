from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Callable, Awaitable
import logging

from services.auth.cognito_service import CognitoService
from api.models import User

logger = logging.getLogger(__name__)
cognito_service = CognitoService()

class AuthMiddleware:
    """Middleware for checking authentication across all API endpoints."""
    
    def __init__(
        self,
        exempt_paths: list[str] = None,
    ):
        self.exempt_paths = exempt_paths or [
            "/api/health",
            "/api/auth/login",
            "/api/auth/logout",
            "/api/auth/callback",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
    
    async def __call__(
        self, request: Request, call_next: Callable[[Request], Awaitable]
    ):
        # Skip authentication for exempt paths
        path = request.url.path
        if any(path.startswith(exempt_path) for exempt_path in self.exempt_paths):
            return await call_next(request)
        
        # Check for authentication token
        id_token = request.cookies.get("id_token")
        if not id_token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"}
            )
        
        # Verify the token
        claims = cognito_service.verify_token(id_token)
        if not claims:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authentication token"}
            )
        
        # Create a User model and add to request state
        user = User.from_cognito_claims(claims)
        request.state.user = user
        # Keep the original claims for role checking
        request.state.claims = claims
        
        # Continue processing the request
        return await call_next(request)