"""UserContext model for storing user profile and preferences"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import uuid


class UserContext(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str
    
    # Basic Type
    portfolio_type: Optional[str] = None  # 'personal' or 'institutional'
    making_for: Optional[str] = None  # 'self' or 'someone_else'
    
    # Personal Information (for personal portfolios)
    date_of_birth: Optional[str] = None  # YYYY-MM-DD format
    retirement_age: Optional[int] = None
    retirement_plans: Optional[str] = None
    
    # Institution Information (for institutional portfolios)
    institution_name: Optional[str] = None
    institution_sector: Optional[str] = None
    annual_revenue: Optional[float] = None
    annual_profit: Optional[float] = None
    
    # Financial Information
    net_worth: Optional[float] = None
    annual_income: Optional[float] = None
    monthly_investment: Optional[float] = None
    annual_investment: Optional[float] = None
    investment_mode: Optional[str] = None  # 'sip', 'adhoc', 'both'
    existing_investments: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Existing Portfolio - Goal-based portfolio tracking
    existing_portfolios: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    # Each portfolio item structure documented in original server.py comments
    
    # Liquidity & Goals - Comprehensive goal tracking
    liquidity_requirements: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    # Each item structure documented in original server.py comments
    
    # Risk & Returns
    risk_tolerance: Optional[str] = None  # 'conservative', 'moderate', 'aggressive', 'very_aggressive'
    risk_details: Optional[str] = None  # Detailed risk description
    roi_expectations: Optional[float] = None
    
    # Investment Preferences
    investment_style: Optional[str] = None  # 'active', 'passive', 'hybrid'
    activity_level: Optional[str] = None  # How often they want to rebalance
    diversification_preference: Optional[str] = None  # 'highly_diversified', 'moderately_diversified', 'concentrated'
    
    # Investment Strategy
    investment_strategy: Optional[List[str]] = Field(default_factory=list)
    
    # Sector Preferences
    sector_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_conversation_at: Optional[datetime] = None
