"""
Admin-only routes that require specific roles.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List

from api.dependency.auth import get_current_user, has_role
from services.storage.database import DataAccess
from api.dependency.data import get_data_access
from api.models import User

router = APIRouter()

@router.get("/users", response_model=List[User])
async def get_all_users(
    user: User = Depends(has_role("admin")),
    db: DataAccess = Depends(get_data_access)
):
    """
    Get all users in the system.
    Requires admin role.
    """
    # This is a placeholder implementation
    # In a real application, you would query the database for all users
    return [user]

@router.get("/debug/current-user")
async def get_debug_current_user(
    user: User = Depends(get_current_user)
):
    """
    Debug endpoint to see the current user's Cognito claims.
    """
    return user