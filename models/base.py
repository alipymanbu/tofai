from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class BaseDBModel(BaseModel):
    """Base model for all database models."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now(datetime.timezone.utc))
    updated_at: Optional[datetime] = None