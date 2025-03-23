from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid
import pytz

class BaseDBModel(BaseModel):
    """Base model for all database models."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    updated_at: Optional[datetime] = None