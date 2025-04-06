"""
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# ============ Session Models ============

class SessionUpdateRequest(BaseModel):
    """Model for session update request."""
    status: Optional[str] = None
    current_step: Optional[str] = None

# ============ Framework Models ============

class GenerateOptionsRequest(BaseModel):
    """Request model for generating options."""
    framework_id: str = "brand_awareness_video"
    step_id: str

class GenerateOptionsResponse(BaseModel):
    """Response model for generate options."""
    job_id: str
    framework_id: str
    step_id: str
    options: List[Union[str, Dict[str, str]]]
    created_at: datetime

class InitInputRequest(BaseModel):
    """Request with values for initial user input."""
    framework_id: str
    brand_link: str

# ============ Jobs Models ============

class JobStatusResponse(BaseModel):
    """Model for job status response."""
    message: str
    job_id: str
    status: str
    progress: Optional[int] = None

class JobResponse(BaseModel):
    """API response for job details."""
    id: str
    session_id: str
    type: str
    status: str
    progress: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
                "session_id": "b2c3d4e5-f6g7-h8i9-j0k1-l2m3n4o5p6q7",
                "type": "script",
                "status": "completed",
                "progress": 100,
                "created_at": "2025-03-21T12:30:00.000Z",
                "completed_at": "2025-03-21T12:31:00.000Z",
                "result": {
                    "script": {
                        "scenes": [
                            {
                                "sceneNumber": 1,
                                "narration": "Introducing our new product",
                                "visualDescription": "Product on a pedestal",
                                "duration": 5
                            }
                        ]
                    }
                }
            }
        }

# ============ Video Models ============

class VideoResponse(BaseModel):
    """Model for video response."""
    video_url: str
    thumbnail_url: str
    duration: int
    format: str
    resolution: str
