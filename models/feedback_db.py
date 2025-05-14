from pydantic import BaseModel
from api.models import Feedback

class FeedbackDBModel(BaseModel):
    """DB Model for a user session."""
    feedback: Feedback