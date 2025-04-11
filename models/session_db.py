from pydantic import BaseModel
from api.models import Session

class SessionDBModel(BaseModel):
    """DB Model for a user session."""
    session: Session