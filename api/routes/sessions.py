from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, List
from uuid import uuid4
from datetime import datetime, timezone

from services.storage.database import DataAccess
from api.models import Session, SessionStatus, User
from models.session_db import SessionDBModel
import logging
from api.dependencies import get_data_access
from api.dependency.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/sessions", response_model=Session, status_code=status.HTTP_201_CREATED)
async def create_session(
    user: User = Depends(get_current_user),
    db: DataAccess = Depends(get_data_access)
):
    """Create a new session and associate it with the authenticated user."""
    session_db_model = SessionDBModel(
        session=Session(
            id=str(uuid4()),
            created_at=datetime.now(timezone.utc),
            status=SessionStatus.STARTED,
            current_step_id="initial_input"
        )
    )
    try:
        # Insert session with user association
        await db.insert_session(
            session_db_model=session_db_model,
            user=user
        )
        return session_db_model.session
    except Exception as e:
        logger.error(f"Error creating session with exception: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating session.")

@router.get("/sessions/{session_id}", response_model=Session)
async def get_session(
    session_id: str, 
    user: User = Depends(get_current_user),
    db: DataAccess = Depends(get_data_access)
):
    """Get session details."""
    try:
        session_db_model = await db.get_session(session_id)
        if not session_db_model:
            raise HTTPException(status_code=404, detail="Session not found")
        return session_db_model.session
    except Exception as e:
        logger.error(f"Error getting session with exception: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting session.")

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str, 
    user: User = Depends(get_current_user),
    db: DataAccess = Depends(get_data_access)
):
    """Delete a session."""
    try:
        await db.delete_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return None

@router.get("/sessions/user/me", response_model=List[Session])
async def get_my_sessions(
    user: User = Depends(get_current_user),
    db: DataAccess = Depends(get_data_access)
):
    """Get all sessions for the current user."""
    try:
        session_models = await db.get_sessions_for_user(user.id)
        return [sm.session for sm in session_models]
    except Exception as e:
        logger.error(f"Error getting user sessions with exception: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting sessions.")