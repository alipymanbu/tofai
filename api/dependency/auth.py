from fastapi import Depends, HTTPException, Request, status
from typing import Dict, Any, Optional
import logging

from services.auth.cognito_service import CognitoService
from api.models import User

logger = logging.getLogger(__name__)
cognito_service = CognitoService()

async def get_current_user(request: Request) -> User:
    """
    Get the current authenticated user from the request.
    First tries to get user from request state (set by middleware),
    then falls back to verifying the token manually.
    """
    # If middleware has already verified the token
    if hasattr(request.state, "user") and request.state.user:
        return request.state.user
    
    # Fallback: Verify the token manually
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
    
    return User.from_cognito_claims(claims)

async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """
    Verify the user is active.
    This is a placeholder for additional checks you might want to add.
    """
    return user

def has_role(required_role: str):
    """
    Dependency function to check if a user has a specific role.
    
    Args:
        required_role: The role required to access the endpoint
        
    Returns:
        A dependency function that verifies the user has the required role
    """
    async def role_checker(
        user: User = Depends(get_current_user),
        request: Request = None
    ) -> User:
        # Since we're now using a User model, we need to get the roles from the request
        # This assumes that roles are stored in the token claims and accessible via request.state
        user_roles = []
        
        # Get claims from request state if available
        if request and hasattr(request.state, "user"):
            claims = request.state.user
            
            # Check cognito:groups
            if "cognito:groups" in claims:
                if isinstance(claims["cognito:groups"], list):
                    user_roles.extend(claims["cognito:groups"])
                else:
                    user_roles.append(claims["cognito:groups"])
                    
            # Check custom:role if it exists
            if "custom:role" in claims:
                user_roles.append(claims["custom:role"])
            
            # Check standard "roles" claim if it exists
            if "roles" in claims:
                if isinstance(claims["roles"], list):
                    user_roles.extend(claims["roles"])
                else:
                    user_roles.append(claims["roles"])
        
        # TODO: In a more complete implementation, you'd also store roles in the User model
        # For now, we'll just check if the required_role is "admin" and the user is admin
        # This is a placeholder for your actual role check logic
        if required_role != "admin" or user.username != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required to access this resource"
            )
        
        return user
    
    return role_checker