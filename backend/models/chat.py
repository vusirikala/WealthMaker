"""Chat-related models"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import uuid


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    role: str  # 'user' or 'assistant'
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatRequest(BaseModel):
    message: str


class PortfolioSuggestion(BaseModel):
    risk_tolerance: str
    roi_expectations: float
    allocations: List[Dict[str, Any]]
    reasoning: str


class ChatResponse(BaseModel):
    message: str
    portfolio_updated: bool = False
    portfolio_suggestion: Optional[PortfolioSuggestion] = None
    suggestion_id: Optional[str] = None


class AcceptPortfolioRequest(BaseModel):
    suggestion_id: str
    portfolio_data: Dict[str, Any]


class SessionDataResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: str
    session_token: str
