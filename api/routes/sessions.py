
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import uuid4
from datetime import datetime
import pytz

from models.session import SessionResponse
from services.storage.database import get_db

router = APIRouter()

@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(db = Depends(get_db)):
    """Create a new session."""
    session = {
        "id": str(uuid4()),
        "created_at": datetime.now(pytz.UTC),
        "status": "started",
        "current_step": "brand-framework"
    }
    
    await db.sessions.insert_one(session)
    
    return session

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db = Depends(get_db)):
    """Get session details."""
    session = await db.sessions.find_one({"id": session_id})
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session

class SessionUpdateRequest(BaseModel):
    """Model for session update request."""
    status: Optional[str] = None
    current_step: Optional[str] = None

@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    update_data: SessionUpdateRequest,
    db = Depends(get_db)
):
    """Update session status or current step."""
    # Prepare update data
    update_fields = {}
    if update_data.status:
        update_fields["status"] = update_data.status
    if update_data.current_step:
        update_fields["current_step"] = update_data.current_step
    
    update_fields["updated_at"] = datetime.now(pytz.UTC)
    
    # Update the session
    result = await db.sessions.update_one(
        {"id": session_id},
        {"$set": update_fields}
    )
    
    # Handle both MongoDB result object and boolean result from in-memory DB
    if hasattr(result, 'matched_count'):
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
    elif not result:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get updated session
    session = await db.sessions.find_one({"id": session_id})
    return session

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, db = Depends(get_db)):
    """Delete a session."""
    result = await db.sessions.delete_one({"id": session_id})
    
    # Handle both MongoDB result object and boolean result from in-memory DB
    if hasattr(result, 'deleted_count'):
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
    elif not result:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Also delete related jobs
    await db.jobs.delete_many({"session_id": session_id})
    
    return None
