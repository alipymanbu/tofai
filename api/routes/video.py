from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from uuid import uuid4
from datetime import datetime

from services.storage.database import get_db

router = APIRouter()

class VideoResponse(BaseModel):
    """Model for video response."""
    video_url: str
    thumbnail_url: str
    duration: int
    format: str
    resolution: str

class JobStatusResponse(BaseModel):
    """Model for job status response."""
    message: str
    job_id: str
    status: str
    progress: Optional[int] = None

@router.post("/sessions/{session_id}/video", response_model=JobStatusResponse)
async def generate_video(
    session_id: str,
    parameters: Optional[Dict[str, Any]] = None,
    background_tasks: BackgroundTasks = None,
    db = Depends(get_db)
):
    """Generate final video by combining visuals and audio."""
    # Check if session exists and has visuals and audio
    session = await db.sessions.find_one({"id": session_id})
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.get("visuals"):
        raise HTTPException(status_code=400, detail="Visuals must be completed first")
    
    if not session.get("audio"):
        raise HTTPException(status_code=400, detail="Audio must be completed first")
    
    # Create a new job for video generation
    job_id = str(uuid4())
    job = {
        "id": job_id,
        "session_id": session_id,
        "type": "video",
        "status": "pending",
        "progress": 0,
        "created_at": datetime.utcnow(),
        "parameters": parameters or {}
    }
    
    await db.jobs.insert_one(job)
    
    # In a real implementation, start video generation in the background
    # For now, we'll just return a job ID
    
    return {
        "message": "Video generation started",
        "job_id": job_id,
        "status": "pending",
        "progress": 0
    }

@router.get("/sessions/{session_id}/video", response_model=Union[VideoResponse, JobStatusResponse])
async def get_video(session_id: str, db = Depends(get_db)):
    """Get generated video or job status if generation is in progress."""
    session = await db.sessions.find_one({"id": session_id})
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.get("video"):
        # Check if there's a job in progress
        job = await db.jobs.find_one({
            "session_id": session_id,
            "type": "video",
            "status": {"$in": ["pending", "processing"]}
        })
        
        if job:
            return {
                "message": "Video generation in progress",
                "job_id": job["id"],
                "status": job["status"],
                "progress": job.get("progress", 0)
            }
        else:
            raise HTTPException(status_code=404, detail="Video not found")
    
    # Format and return video
    video_data = session["video"]
    
    return {
        "video_url": video_data.get("videoUrl", video_data.get("video_url")),
        "thumbnail_url": video_data.get("thumbnailUrl", video_data.get("thumbnail_url")),
        "duration": video_data.get("duration", 0),
        "format": video_data.get("format", "mp4"),
        "resolution": video_data.get("resolution", "720p")
    }