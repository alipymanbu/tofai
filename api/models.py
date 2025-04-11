"""
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union, Literal
from datetime import datetime
from services.ai.framework_model import FrameworkResult
from enum import Enum

# ============ Session Models ============

class SessionStatus(int, Enum):
    """Enum for job status."""
    UNDEFINED = 0
    STARTED = 1
    EXPIRED = 2

class Session(BaseModel):
    """Model for a user session."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    status: SessionStatus = SessionStatus.UNDEFINED
    result: Optional[FrameworkResult] = None
    framework_id: str = "brand_awareness_video"
    current_step_id: str

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

class UserResponse(BaseModel):
    """Response model for select options."""
    job_id: str
    framework_id: str
    created_at: datetime

# ============ Jobs Models ============

class JobStatus(int, Enum):
    """Enum for job status."""
    UNDEFINED = 0
    PENDING = 1
    PROCESSING = 2
    COMPLETED = 3
    FAILED = 4
    CANCELED = 5

class Job(BaseModel):
    """Model for a background job."""
    id: str
    session_id: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    status: str = JobStatus.UNDEFINED
    progress: int = Field(default=0, ge=0, le=100)
    tasks_completed: Optional[List[str]] = None
    error: Optional[str] = None
    completed_at: Optional[datetime] = None