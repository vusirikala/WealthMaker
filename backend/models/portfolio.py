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


class UserPortfolio(BaseModel):
    """Enhanced portfolio model for multi-portfolio management"""
    model_config = ConfigDict(extra="ignore")
    portfolio_id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str
    name: str  # Portfolio name (e.g., "Retirement Fund", "Growth Portfolio")
    goal: Optional[str] = None  # Portfolio goal/purpose
    type: str = "manual"  # 'manual' or 'ai'
    
    # Portfolio characteristics
    risk_tolerance: str = "medium"  # 'low', 'medium', 'high'
    roi_expectations: float = 10.0
    investment_horizon: Optional[str] = None
    
    # Allocations (target percentages)
    allocations: List[Dict[str, Any]] = Field(default_factory=list)
    # Each allocation: {ticker, allocation_percentage, sector, asset_type}
    
    # Holdings (actual investments)
    holdings: List[Dict[str, Any]] = Field(default_factory=list)
    # Each holding: {ticker, shares, purchase_price, current_price, cost_basis, current_value}
    
    # Investment tracking
    total_invested: float = 0.0  # Total amount invested
    current_value: float = 0.0  # Current portfolio value
    total_return: float = 0.0  # Total return ($ amount)
    total_return_percentage: float = 0.0  # Total return (%)
    
    # Metadata
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_invested_at: Optional[datetime] = None


class CreatePortfolioRequest(BaseModel):
    """Request model for creating a new portfolio"""
    name: str
    goal: Optional[str] = None
    type: str = "manual"  # 'manual' or 'ai'
    risk_tolerance: str = "medium"
    roi_expectations: float = 10.0
    allocations: List[Dict[str, Any]] = Field(default_factory=list)


class InvestmentRequest(BaseModel):
    """Request model for investing in a portfolio"""
    amount: float  # Amount to invest in dollars


class UpdateAllocationRequest(BaseModel):
    """Request model for updating portfolio allocations"""
    allocations: List[Dict[str, Any]]  # Array of {ticker, allocation_percentage}
