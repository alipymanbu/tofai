from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum

from models.base import BaseDBModel

class JobStatus(str, Enum):
    """Enum for job status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"

class JobType(str, Enum):
    """Enum for job type."""
    STRATEGY = "strategy"
    SCRIPT = "script"
    IMAGE = "image"
    SPEECH = "speech"
    MUSIC = "music"
    VIDEO = "video"

class Job(BaseDBModel):
    """Model for a background job."""
    session_id: str
    type: str
    status: str = JobStatus.PENDING
    progress: int = Field(default=0, ge=0, le=100)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    completed_at: Optional[datetime] = None
    
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
