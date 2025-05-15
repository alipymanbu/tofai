from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, List
from uuid import uuid4
from datetime import datetime, timezone

from services.storage.database import DataAccess
from api.models import Feedback, User, CreateorUpdateFeedbackRequest
from models.feedback_db import FeedbackDBModel
import logging
from api.dependency.data import get_data_access
from api.dependency.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

def generate_feedback_id(session_id: str, step_id: str, context_id: str) -> str:
    """Generate a unique feedback ID."""
    return f"{session_id}_{step_id}_{context_id}_{uuid4()}"

@router.post("/feedback", response_model=Feedback, status_code=status.HTTP_201_CREATED)
async def create_or_update_feedback(
    request: CreateorUpdateFeedbackRequest,
    user: User = Depends(get_current_user),
    db: DataAccess = Depends(get_data_access)
):
    """Create a new session and associate it with the authenticated user."""
    feedback_db_model = FeedbackDBModel(
        feedback=Feedback(
            id=request.id or generate_feedback_id(request.session_id, request.step_id, request.context_id),
            session_id=request.session_id,
            feedback_type=request.feedback_type,
            feedback_qual=request.feedback_qual,
            step_id=request.step_id,
            context_id=request.context_id,
            created_at=datetime.now(timezone.utc)
        )
    )
    try:
        # Insert session with user association
        if not request.id:
          await db.insert_feedback(feedback_db_model=feedback_db_model)
        else:
          await db.update_feedback(feedback_db_model=feedback_db_model)
        return feedback_db_model.feedback
    except Exception as e:
        logger.error(f"Error creating session with exception: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating or updating feedback.")

@router.get("/feedback/{feedback_id}", response_model=Feedback)
async def get_session(
    feedback_id: str, 
    user: User = Depends(get_current_user),
    db: DataAccess = Depends(get_data_access)
):
    """Get feedback."""
    try:
        feedback_db_model = await db.get_feedback(feedback_id=feedback_id)
        if not feedback_db_model:
            raise HTTPException(status_code=404, detail="Feedback not found")
        return feedback_db_model.feedback
    except Exception as e:
        logger.error(f"Error getting feedback with exception: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting feedback.")

@router.delete("/feedback/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback(
    feedback_id: str, 
    user: User = Depends(get_current_user),
    db: DataAccess = Depends(get_data_access)
):
    """Delete a feedback."""
    try:
        await db.delete_feedback(feedback_id)
    except ValueError as e:
        logger.error(f"Error deleting feedback with exception: {e}")
        raise HTTPException(status_code=404, detail=f"Error deleting feedback")
    return None
