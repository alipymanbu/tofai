from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal, List
from datetime import datetime
from enum import Enum

from api.models import Job

class JobDBModel(BaseModel):
    """DB Model for a background job."""
    job: Job