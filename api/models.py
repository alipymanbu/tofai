"""
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union, Literal
from datetime import datetime
from services.ai.framework_model import FrameworkResult
from enum import Enum

# ============ User Models ============

class User(BaseModel):
    """Model for a user in the system."""
    id: str
    username: str
    email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_cognito_claims(cls, claims: Dict[str, Any]) -> "User":
        """Create a User instance from Cognito claims."""
        return cls(
            id=claims.get("sub"),
            username=claims.get("cognito:username") or claims.get("username") or claims.get("email"),
            email=claims.get("email"),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

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

# ============ Feedback Models ============

class FeedbackType(str, Enum):
    """Enum for feedback types."""
    POSITIVE = "positive"
    NEGATIVE = "negative"

class Feedback(BaseModel):
    """Model for feedback on a generated option."""
    id: str
    session_id: str
    step_id: str
    context_id: str
    created_at: datetime
    feedback_type: FeedbackType
    feedback_qual: Optional[str] = None
    framework_id: str = "brand_awareness_video"
    step_version: Optional[int] = None
    
class CreateorUpdateFeedbackRequest(BaseModel):
    """Request model for /api/feedback."""
    id: Optional[str] = None # If present, existing feedback will be updated.
    session_id: str
    step_id: str
    context_id: str
    feedback_type: FeedbackType
    feedback_qual: Optional[str] = None
    framework_id: str = "brand_awareness_video"

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
    created_at: datetime
    next_api: str | None = None
    wait_for_user_action: bool | None = None

class InitInputRequest(BaseModel):
    """Request with values for initial user input."""
    framework_id: str
    brand_link: str

class SelectRequest(BaseModel):
    """Request with values for user selection."""
    framework_id: str
    step_id: str
    option_index: int = Field(default=0, ge=0)
    result_index: int = Field(default=0, ge=0)
    lineage_id: str

class UserResponse(BaseModel):
    """Response model for select options."""
    job_id: str
    framework_id: str
    created_at: datetime
    next_api: str | None = None
    wait_for_user_action: bool | None = None

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