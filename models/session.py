from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from app.models.base import BaseDBModel

class BrandFrameworkQuestion(BaseModel):
    """Model for a brand framework question."""
    id: str
    title: str
    description: str
    type: Literal["text", "select", "multi-select"]
    order: int
    is_required: bool = True

class BrandFrameworkOption(BaseModel):
    """Model for a brand framework question option."""
    id: str
    value: str
    description: str
    examples: List[str] = Field(default_factory=list)

class BrandFrameworkQuestionWithOptions(BrandFrameworkQuestion):
    """Model for a brand framework question with AI-generated options."""
    options: List[BrandFrameworkOption] = Field(default_factory=list)
    previous_answers: Dict[str, str] = Field(default_factory=dict)

class BrandFrameworkAnswer(BaseModel):
    """Model for a brand framework question answer."""
    question_id: str
    question: str
    answer: str
    selected_option_id: Optional[str] = None

class BrandFramework(BaseModel):
    """Model for a complete brand framework."""
    brand_name: str
    industry: str
    brand_personality: str
    target_audience: str
    content_goal: str
    brand_voice: str
    brand_values: List[str]
    differentiator: str
    completed_questions: List[BrandFrameworkAnswer] = Field(default_factory=list)

class Strategy(BaseModel):
    """Model for a content strategy."""
    content_theme: str
    key_messages: List[str]
    recommended_length: str
    call_to_action: str

class Session(BaseDBModel):
    """Model for a user session."""
    checkpoint: Literal["started", "strategy", "script", "image", "speech", "music", "video", "completed"] = "started"
    current_step: Literal["brand-framework", "strategy", "script", "visuals", "audio", "video"] = "brand-framework"
    brand_framework: Optional[Dict[str, Any]] = None
    strategy: Optional[Dict[str, Any]] = None
    script: Optional[Dict[str, Any]] = None
    visuals: Optional[Dict[str, Any]] = None
    audio: Optional[Dict[str, Any]] = None
    video: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
                "created_at": "2025-03-21T12:30:00.000Z",
                "updated_at": "2025-03-21T12:45:00.000Z",
                "status": "strategy",
                "current_step": "script",
                "brand_framework": {
                    "brand_name": "Acme Corp",
                    "industry": "Technology",
                    "brand_personality": "Innovative",
                    "target_audience": "Small business owners",
                    "content_goal": "Brand awareness",
                    "brand_voice": "Professional yet approachable",
                    "brand_values": ["Innovation", "Reliability", "Customer-focus"],
                    "differentiator": "AI-powered solutions"
                },
                "strategy": {
                    "content_theme": "Simplifying Business With AI",
                    "key_messages": [
                        "AI can save small businesses time and money",
                        "Our solutions are easy to implement",
                        "Join thousands of satisfied customers"
                    ],
                    "recommended_length": "30-45 seconds",
                    "call_to_action": "Book a free demo today"
                }
            }
        }

class SessionResponse(BaseModel):
    """API response for session details."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: str
    current_step: str
    brand_analysis: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
                "created_at": "2025-03-21T12:30:00.000Z",
                "updated_at": "2025-03-21T12:45:00.000Z",
                "status": "strategy",
                "current_step": "script",
                "brand_analysis": {
                    "analysis_data": {
                        "brand_name": "Acme Corp",
                        "industry": "Technology",
                        "brand_personality": "Innovative",
                        "target_audience": "Small business owners",
                        "brand_values": ["Innovation", "Quality", "Customer-focus"]
                    }
                }
            }
        }