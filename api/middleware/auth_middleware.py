from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Callable, Awaitable
import logging
from starlette.types import ASGIApp, Scope, Receive, Send

from services.auth.cognito_service import CognitoService
from api.models import User

logger = logging.getLogger(__name__)
cognito_service = CognitoService()

class AuthMiddleware:
    """Middleware for checking authentication across all API endpoints."""
    
    def __init__(
        self,
        app: ASGIApp,
        exempt_paths: list[str] = None,
    ):
        self.app = app
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
        self, scope: Scope, receive: Receive, send: Send
    ):
        if scope["type"] != "http":
            # If it's not HTTP, just forward the request
            await self.app(scope, receive, send)
            return

        # For HTTP requests, apply the middleware logic
        path = scope.get("path", "")
        method = scope.get("method", "")
        
        # Skip authentication for OPTIONS requests (needed for CORS preflight)
        if method == "OPTIONS":
            await self.app(scope, receive, send)
            return
            
        # Skip authentication for exempt paths
        if any(path.startswith(exempt_path) for exempt_path in self.exempt_paths):
            await self.app(scope, receive, send)
            return
        
        # Check for authentication token in cookies
        headers = dict(scope.get("headers", []))
        cookie_header = headers.get(b"cookie", b"").decode()
        cookies = {}
        for cookie in cookie_header.split(";"):
            if "=" in cookie:
                name, value = cookie.strip().split("=", 1)
                cookies[name] = value
        
        id_token = cookies.get("id_token")
        if not id_token:
            # No token found, return 401
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"}
            )
            await response(scope, receive, send)
            return
        
        # Verify the token
        claims = cognito_service.verify_token(id_token)
        if not claims:
            # Invalid token, return 401
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authentication token"}
            )
            await response(scope, receive, send)
            return
        
        # Add user to request state by modifying scope
        user = User.from_cognito_claims(claims)
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["user"] = user
        scope["state"]["claims"] = claims
        
        # Continue processing the request
        await self.app(scope, receive, send)