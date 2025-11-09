"""Portfolio model"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid


class Portfolio(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str
    risk_tolerance: str  # 'low', 'medium', 'high'
    roi_expectations: float
    retirement_age: Optional[int] = None
    investment_horizon: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    allocations: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
