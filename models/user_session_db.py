from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from api.models import User

class UserSessionDBModel(BaseModel):
    """DB Model for associating users with sessions."""
    user: User
    session_ids: List[str] = []
    created_at: datetime
    updated_at: Optional[datetime] = None