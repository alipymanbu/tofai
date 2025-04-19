from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from typing import Optional, Dict, Any
import logging

from services.auth.cognito_service import CognitoService
from config.auth_settings import auth_settings
from config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)
is_development = settings.ENVIRONMENT == "development"
cognito_service = CognitoService()

@router.get("/login")
async def login(request: Request, state: Optional[str] = None):
    """Redirect to Cognito login page."""
    login_url = cognito_service.get_login_url(state=state)
    return RedirectResponse(login_url)

@router.get("/logout")
async def logout():
    """Redirect to Cognito logout."""
    logout_url = cognito_service.get_logout_url()
    return RedirectResponse(logout_url)

@router.get("/callback")
async def callback(request: Request, response: Response, code: str, state: Optional[str] = None):
    """Handle the callback from Cognito after login."""
    try:
        tokens = cognito_service.exchange_code_for_tokens(code)
        if not tokens:
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
        id_token = tokens.get("id_token")
        claims = cognito_service.verify_token(id_token)
        if not claims:
            raise HTTPException(status_code=401, detail="Invalid token")
        access_token = tokens.get("access_token")
        redirect_url = state or "http://localhost:3000/"
        redirect_response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
        redirect_response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="none" if is_development else "lax", # Adjust as needed
            max_age=3600,
            path="/",
        )
        redirect_response.set_cookie(
            key="id_token",
            value=id_token,
            httponly=True,
            secure=True,
            samesite="none" if is_development else "lax", # Adjust as needed
            max_age=3600,
            path="/",
        )
        if "refresh_token" in tokens:
            redirect_response.set_cookie(
                key="refresh_token",
                value=tokens["refresh_token"],
                httponly=True,
                secure=True,
                samesite="none" if is_development else "lax", # Adjust as needed
                max_age=30 * 24 * 3600,
                path="/",
            )
        redirect_response.headers["Refresh"] = f"0;url={redirect_url}"
        return redirect_response

    except Exception as e:
        logger.exception(f"Error in Cognito callback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")

@router.get("/user")
async def get_current_user(request: Request):
    """Get the current user from the ID token."""
    id_token = request.cookies.get("id_token")
    if not id_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    claims = cognito_service.verify_token(id_token)
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return claims