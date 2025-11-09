"""
WealthMaker Backend - Modular FastAPI Application
Main application file that imports and registers all route modules
"""
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import finnhub
import httpx
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'wealthmaker')]

# Finnhub setup
finnhub_client = finnhub.Client(api_key=os.environ.get('FINNHUB_API_KEY', ''))

# Create the main app and API router
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(alias="_id")
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    role: str  # 'user' or 'assistant'
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    # Each portfolio item structure:
    # {
    #   "portfolio_id": "unique_id",
    #   "portfolio_name": "Retirement Fund",
    #   "goal_id": "linked_goal_id",  # Links to liquidity_requirements
    #   "goal_name": "Retirement",  # For quick reference
    #   "total_value": 150000,  # Current total value
    #   "cost_basis": 120000,  # Original investment amount
    #   "unrealized_gain_loss": 30000,  # Current gain/loss
    #   "unrealized_gain_loss_percentage": 25.0,  # % gain/loss
    #   "account_type": "401k|IRA|Roth_IRA|brokerage|crypto_wallet|savings|other",
    #   "account_provider": "Vanguard, Fidelity, Coinbase, etc.",
    #   "is_tax_advantaged": true,  # Tax-advantaged account?
    #   "holdings": [
    #     {
    #       "asset_id": "unique_asset_id",
    #       "asset_name": "Apple Inc.",
    #       "ticker": "AAPL",
    #       "asset_type": "stock|bond|crypto|etf|mutual_fund|index_fund|reit|commodity|cash",
    #       "sector": "Technology",
    #       "quantity": 100,
    #       "purchase_price": 150.00,
    #       "current_price": 180.00,
    #       "total_value": 18000,
    #       "cost_basis": 15000,
    #       "unrealized_gain_loss": 3000,
    #       "unrealized_gain_loss_percentage": 20.0,
    #       "allocation_percentage": 12.0,  # % of total portfolio
    #       "purchase_date": "2023-01-15",
    #       "notes": "Long-term hold"
    #     }
    #   ],
    #   "allocation_summary": {
    #     "stocks": 60.0,
    #     "bonds": 30.0,
    #     "cash": 10.0
    #   },
    #   "sector_allocation": {
    #     "technology": 25.0,
    #     "healthcare": 15.0,
    #     "finance": 20.0
    #   },
    #   "performance_metrics": {
    #     "ytd_return": 8.5,
    #     "one_year_return": 12.3,
    #     "three_year_return": 15.7,
    #     "inception_return": 25.0
    #   },
    #   "last_rebalanced": "2024-01-01",
    #   "last_updated": "2024-01-15",
    #   "notes": "Conservative allocation for near-term goal"
    # }
    
    # Liquidity & Goals - Comprehensive goal tracking
    liquidity_requirements: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    # Each item structure:
    # {
    #   "goal_id": "unique_id",
    #   "goal_name": "Buy a house",
    #   "goal_type": "house_purchase",  # house_purchase, vacation, wedding, education, retirement, business, emergency_fund, vehicle, healthcare, other
    #   "description": "3 bedroom house in suburbs",
    #   "target_amount": 250000,  # Total cost
    #   "amount_saved": 50000,  # Amount already saved
    #   "amount_needed": 200000,  # Remaining amount needed
    #   "target_date": "2026-12-31",  # When they need the money
    #   "timeline_years": 3,  # Years until target date
    #   "priority": "high",  # high, medium, low
    #   "is_flexible": false,  # Can this timeline be adjusted?
    #   "monthly_allocation": 5000,  # How much they plan to save monthly
    #   "funding_strategy": "sip",  # sip, lump_sum, mixed
    #   "risk_appetite_for_goal": "moderate",  # Risk tolerance specific to this goal
    #   "notes": "First home purchase, need for down payment",
    #   "progress_percentage": 20,  # (amount_saved / target_amount) * 100
    #   "created_at": "2024-01-01",
    #   "updated_at": "2024-01-15"
    # }
    
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
    # ['value_investing', 'growth_investing', 'income_investing', 'index_funds', 
    #  'buy_and_hold', 'dollar_cost_averaging', 'momentum_investing', etc.]
    
    # Sector Preferences
    sector_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # {"stocks": {"allowed": true, "sectors": ["tech", "healthcare"]},
    #  "crypto": {"allowed": false}, 
    #  "bonds": {"allowed": true}, etc.}
    
    # Onboarding Status
    onboarding_completed: Optional[bool] = False  # Track if user completed initial onboarding
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_conversation_at: Optional[datetime] = None
    first_chat_initiated: Optional[bool] = False  # Track if chat has been auto-initiated

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

# Auth dependency
async def get_current_user(request: Request) -> Optional[User]:
    # Check session_token from cookie first
    session_token = request.cookies.get("session_token")
    
    # Fallback to Authorization header
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.replace("Bearer ", "")
    
    if not session_token:
        return None
    
    # Find session in database
    session = await db.user_sessions.find_one({"session_token": session_token})
    if not session:
        return None
    
    # Check if session expired
    expires_at = session["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    
    # Get user
    user_doc = await db.users.find_one({"_id": session["user_id"]})
    if not user_doc:
        return None
    
    return User(**user_doc)

async def require_auth(user: Optional[User] = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# Auth routes
@api_router.get("/auth/me")
async def get_me(user: User = Depends(require_auth)):
    return user

@api_router.post("/auth/session")
async def process_session(request: Request, response: Response):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        logger.error("No session ID in request")
        raise HTTPException(status_code=400, detail="Session ID required")
    
    logger.info(f"Processing session ID: {session_id[:10]}...")
    
    # Call Emergent auth service
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            resp.raise_for_status()
            session_data = resp.json()
            logger.info(f"Successfully got session data for user: {session_data.get('email')}")
        except Exception as e:
            logger.error(f"Failed to get session data: {e}")
            raise HTTPException(status_code=400, detail="Invalid session")
    
    # Check if user exists
    existing_user = await db.users.find_one({"_id": session_data["id"]})
    if not existing_user:
        # Create new user
        user_doc = {
            "_id": session_data["id"],
            "email": session_data["email"],
            "name": session_data["name"],
            "picture": session_data.get("picture"),
            "created_at": datetime.now(timezone.utc)
        }
        await db.users.insert_one(user_doc)
        logger.info(f"Created new user: {session_data['email']}")
    else:
        logger.info(f"User already exists: {session_data['email']}")
    
    # Create session
    session_token = session_data["session_token"]
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session_doc = {
        "user_id": session_data["id"],
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    }
    await db.user_sessions.insert_one(session_doc)
    logger.info(f"Created session for user: {session_data['email']}")
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )
    logger.info(f"Set cookie for user: {session_data['email']}")
    
    return {"success": True, "user": session_data}

@api_router.post("/auth/logout")
async def logout(response: Response, user: User = Depends(require_auth)):
    # Delete all sessions for user
    await db.user_sessions.delete_many({"user_id": user.id})
    
    # Clear cookie
    response.delete_cookie("session_token", path="/")
    
    return {"success": True}

@api_router.delete("/auth/account")
async def delete_account(response: Response, user: User = Depends(require_auth)):
    """
    Delete user account and all associated data
    WARNING: This action is irreversible
    """
    try:
        # Delete all user data from all collections
        await db.user_sessions.delete_many({"user_id": user.id})
        await db.user_context.delete_many({"user_id": user.id})
        await db.portfolios.delete_many({"user_id": user.id})
        await db.chat_messages.delete_many({"user_id": user.id})
        await db.portfolio_suggestions.delete_many({"user_id": user.id})
        
        # Clear cookie
        response.delete_cookie("session_token", path="/")
        
        logger.info(f"Account deleted for user: {user.email}")
        
        return {"success": True, "message": "Account deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete account")

# User Context routes
@api_router.get("/context")
async def get_user_context(user: User = Depends(require_auth)):
    context = await db.user_context.find_one({"user_id": user.id})
    if not context:
        # Create default context
        default_context = {
            "_id": str(uuid.uuid4()),
            "user_id": user.id,
            "portfolio_type": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.user_context.insert_one(default_context)
        return default_context
    return context

@api_router.put("/context")
async def update_user_context(context_update: Dict[str, Any], user: User = Depends(require_auth)):
    context = await db.user_context.find_one({"user_id": user.id})
    
    if not context:
        # Create new context
        context_update["_id"] = str(uuid.uuid4())
        context_update["user_id"] = user.id
        context_update["created_at"] = datetime.now(timezone.utc)
        context_update["updated_at"] = datetime.now(timezone.utc)
        await db.user_context.insert_one(context_update)
        return context_update
    else:
        # Update existing context
        context_update["updated_at"] = datetime.now(timezone.utc)
        await db.user_context.update_one(
            {"user_id": user.id},
            {"$set": context_update}
        )
        updated_context = await db.user_context.find_one({"user_id": user.id})
        return updated_context

# Goals Management routes
@api_router.get("/goals")
async def get_user_goals(user: User = Depends(require_auth)):
    """Get all financial goals for the user"""
    context = await db.user_context.find_one({"user_id": user.id})
    if not context or not context.get('liquidity_requirements'):
        return {"goals": []}
    return {"goals": context.get('liquidity_requirements', [])}

@api_router.post("/goals")
async def add_goal(goal_data: Dict[str, Any], user: User = Depends(require_auth)):
    """Add a new financial goal"""
    # Generate goal_id if not provided
    if 'goal_id' not in goal_data:
        goal_data['goal_id'] = str(uuid.uuid4())
    
    # Calculate derived fields
    if 'target_amount' in goal_data and 'amount_saved' in goal_data:
        goal_data['amount_needed'] = goal_data['target_amount'] - goal_data['amount_saved']
        goal_data['progress_percentage'] = round((goal_data['amount_saved'] / goal_data['target_amount']) * 100, 2)
    
    # Add timestamps
    goal_data['created_at'] = datetime.now(timezone.utc).isoformat()
    goal_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Update context with new goal
    context = await db.user_context.find_one({"user_id": user.id})
    
    if not context:
        # Create new context with goal
        new_context = {
            "_id": str(uuid.uuid4()),
            "user_id": user.id,
            "liquidity_requirements": [goal_data],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.user_context.insert_one(new_context)
        return {"success": True, "goal": goal_data}
    else:
        # Add to existing goals
        liquidity_requirements = context.get('liquidity_requirements', [])
        liquidity_requirements.append(goal_data)
        
        await db.user_context.update_one(
            {"user_id": user.id},
            {"$set": {
                "liquidity_requirements": liquidity_requirements,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        return {"success": True, "goal": goal_data}

@api_router.put("/goals/{goal_id}")
async def update_goal(goal_id: str, goal_update: Dict[str, Any], user: User = Depends(require_auth)):
    """Update an existing financial goal"""
    context = await db.user_context.find_one({"user_id": user.id})
    
    if not context or not context.get('liquidity_requirements'):
        raise HTTPException(status_code=404, detail="No goals found")
    
    liquidity_requirements = context.get('liquidity_requirements', [])
    goal_found = False
    
    for i, goal in enumerate(liquidity_requirements):
        if goal.get('goal_id') == goal_id:
            # Update the goal
            liquidity_requirements[i].update(goal_update)
            
            # Recalculate derived fields
            if 'target_amount' in liquidity_requirements[i] and 'amount_saved' in liquidity_requirements[i]:
                liquidity_requirements[i]['amount_needed'] = liquidity_requirements[i]['target_amount'] - liquidity_requirements[i]['amount_saved']
                liquidity_requirements[i]['progress_percentage'] = round((liquidity_requirements[i]['amount_saved'] / liquidity_requirements[i]['target_amount']) * 100, 2)
            
            liquidity_requirements[i]['updated_at'] = datetime.now(timezone.utc).isoformat()
            goal_found = True
            break
    
    if not goal_found:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    await db.user_context.update_one(
        {"user_id": user.id},
        {"$set": {
            "liquidity_requirements": liquidity_requirements,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return {"success": True, "goal": liquidity_requirements[i]}

@api_router.delete("/goals/{goal_id}")
async def delete_goal(goal_id: str, user: User = Depends(require_auth)):
    """Delete a financial goal"""
    context = await db.user_context.find_one({"user_id": user.id})
    
    if not context or not context.get('liquidity_requirements'):
        raise HTTPException(status_code=404, detail="No goals found")
    
    liquidity_requirements = context.get('liquidity_requirements', [])
    original_length = len(liquidity_requirements)
    liquidity_requirements = [g for g in liquidity_requirements if g.get('goal_id') != goal_id]
    
    if len(liquidity_requirements) == original_length:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    await db.user_context.update_one(
        {"user_id": user.id},
        {"$set": {
            "liquidity_requirements": liquidity_requirements,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return {"success": True, "message": "Goal deleted"}

# Existing Portfolio Management routes
@api_router.get("/portfolios/existing")
async def get_existing_portfolios(user: User = Depends(require_auth)):
    """Get all existing portfolios for the user"""
    context = await db.user_context.find_one({"user_id": user.id})
    if not context or not context.get('existing_portfolios'):
        return {"portfolios": []}
    return {"portfolios": context.get('existing_portfolios', [])}

@api_router.post("/portfolios/existing")
async def add_existing_portfolio(portfolio_data: Dict[str, Any], user: User = Depends(require_auth)):
    """Add a new existing portfolio"""
    # Generate portfolio_id if not provided
    if 'portfolio_id' not in portfolio_data:
        portfolio_data['portfolio_id'] = str(uuid.uuid4())
    
    # Calculate total value from holdings if provided
    if 'holdings' in portfolio_data and portfolio_data['holdings']:
        total_value = sum(holding.get('total_value', 0) for holding in portfolio_data['holdings'])
        cost_basis = sum(holding.get('cost_basis', 0) for holding in portfolio_data['holdings'])
        portfolio_data['total_value'] = total_value
        portfolio_data['cost_basis'] = cost_basis
        portfolio_data['unrealized_gain_loss'] = total_value - cost_basis
        if cost_basis > 0:
            portfolio_data['unrealized_gain_loss_percentage'] = round(((total_value - cost_basis) / cost_basis) * 100, 2)
        
        # Calculate allocation percentages for each holding
        for holding in portfolio_data['holdings']:
            if total_value > 0:
                holding['allocation_percentage'] = round((holding.get('total_value', 0) / total_value) * 100, 2)
        
        # Calculate allocation summary by asset type
        allocation_summary = {}
        for holding in portfolio_data['holdings']:
            asset_type = holding.get('asset_type', 'other')
            allocation_pct = holding.get('allocation_percentage', 0)
            allocation_summary[asset_type] = allocation_summary.get(asset_type, 0) + allocation_pct
        portfolio_data['allocation_summary'] = allocation_summary
        
        # Calculate sector allocation
        sector_allocation = {}
        for holding in portfolio_data['holdings']:
            sector = holding.get('sector', 'other')
            allocation_pct = holding.get('allocation_percentage', 0)
            sector_allocation[sector] = sector_allocation.get(sector, 0) + allocation_pct
        portfolio_data['sector_allocation'] = sector_allocation
    
    # Add timestamps
    portfolio_data['last_updated'] = datetime.now(timezone.utc).isoformat()
    
    # Update context with new portfolio
    context = await db.user_context.find_one({"user_id": user.id})
    
    if not context:
        # Create new context with portfolio
        new_context = {
            "_id": str(uuid.uuid4()),
            "user_id": user.id,
            "existing_portfolios": [portfolio_data],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.user_context.insert_one(new_context)
        return {"success": True, "portfolio": portfolio_data}
    else:
        # Add to existing portfolios
        existing_portfolios = context.get('existing_portfolios', [])
        existing_portfolios.append(portfolio_data)
        
        await db.user_context.update_one(
            {"user_id": user.id},
            {"$set": {
                "existing_portfolios": existing_portfolios,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        return {"success": True, "portfolio": portfolio_data}

@api_router.put("/portfolios/existing/{portfolio_id}")
async def update_existing_portfolio(portfolio_id: str, portfolio_update: Dict[str, Any], user: User = Depends(require_auth)):
    """Update an existing portfolio"""
    context = await db.user_context.find_one({"user_id": user.id})
    
    if not context or not context.get('existing_portfolios'):
        raise HTTPException(status_code=404, detail="No portfolios found")
    
    existing_portfolios = context.get('existing_portfolios', [])
    portfolio_found = False
    
    for i, portfolio in enumerate(existing_portfolios):
        if portfolio.get('portfolio_id') == portfolio_id:
            # Update the portfolio
            existing_portfolios[i].update(portfolio_update)
            
            # Recalculate if holdings changed
            if 'holdings' in existing_portfolios[i] and existing_portfolios[i]['holdings']:
                total_value = sum(holding.get('total_value', 0) for holding in existing_portfolios[i]['holdings'])
                cost_basis = sum(holding.get('cost_basis', 0) for holding in existing_portfolios[i]['holdings'])
                existing_portfolios[i]['total_value'] = total_value
                existing_portfolios[i]['cost_basis'] = cost_basis
                existing_portfolios[i]['unrealized_gain_loss'] = total_value - cost_basis
                if cost_basis > 0:
                    existing_portfolios[i]['unrealized_gain_loss_percentage'] = round(((total_value - cost_basis) / cost_basis) * 100, 2)
                
                # Recalculate allocation percentages
                for holding in existing_portfolios[i]['holdings']:
                    if total_value > 0:
                        holding['allocation_percentage'] = round((holding.get('total_value', 0) / total_value) * 100, 2)
                
                # Recalculate allocation summary
                allocation_summary = {}
                for holding in existing_portfolios[i]['holdings']:
                    asset_type = holding.get('asset_type', 'other')
                    allocation_pct = holding.get('allocation_percentage', 0)
                    allocation_summary[asset_type] = allocation_summary.get(asset_type, 0) + allocation_pct
                existing_portfolios[i]['allocation_summary'] = allocation_summary
                
                # Recalculate sector allocation
                sector_allocation = {}
                for holding in existing_portfolios[i]['holdings']:
                    sector = holding.get('sector', 'other')
                    allocation_pct = holding.get('allocation_percentage', 0)
                    sector_allocation[sector] = sector_allocation.get(sector, 0) + allocation_pct
                existing_portfolios[i]['sector_allocation'] = sector_allocation
            
            existing_portfolios[i]['last_updated'] = datetime.now(timezone.utc).isoformat()
            portfolio_found = True
            break
    
    if not portfolio_found:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    await db.user_context.update_one(
        {"user_id": user.id},
        {"$set": {
            "existing_portfolios": existing_portfolios,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return {"success": True, "portfolio": existing_portfolios[i]}

@api_router.delete("/portfolios/existing/{portfolio_id}")
async def delete_existing_portfolio(portfolio_id: str, user: User = Depends(require_auth)):
    """Delete an existing portfolio"""
    context = await db.user_context.find_one({"user_id": user.id})
    
    if not context or not context.get('existing_portfolios'):
        raise HTTPException(status_code=404, detail="No portfolios found")
    
    existing_portfolios = context.get('existing_portfolios', [])
    original_length = len(existing_portfolios)
    existing_portfolios = [p for p in existing_portfolios if p.get('portfolio_id') != portfolio_id]
    
    if len(existing_portfolios) == original_length:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    await db.user_context.update_one(
        {"user_id": user.id},
        {"$set": {
            "existing_portfolios": existing_portfolios,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return {"success": True, "message": "Portfolio deleted"}

@api_router.get("/portfolios/existing/{portfolio_id}")
async def get_portfolio_by_id(portfolio_id: str, user: User = Depends(require_auth)):
    """Get a specific portfolio by ID"""
    context = await db.user_context.find_one({"user_id": user.id})
    
    if not context or not context.get('existing_portfolios'):
        raise HTTPException(status_code=404, detail="No portfolios found")
    
    for portfolio in context.get('existing_portfolios', []):
        if portfolio.get('portfolio_id') == portfolio_id:
            return {"portfolio": portfolio}
    
    raise HTTPException(status_code=404, detail="Portfolio not found")

# Helper function for context extraction
async def extract_and_update_context(user_id: str, user_message: str, ai_response: str):
    """Extract context from conversation and update user context"""
    
    extraction_prompt = f"""Based on the following conversation, extract any relevant financial information about the user.
Return ONLY a JSON object with the extracted information. Use null for any information not mentioned.

IMPORTANT: 
- Extract NEW information or UPDATES to existing information
- If user says "change", "update", "actually", "correct", they are modifying previous information
- Numbers can be written as "$50,000", "50k", "50000" - extract the numeric value
- Percentages can be "10%", "ten percent" - extract the numeric value

User message: {user_message}
AI response: {ai_response}

Extract the following if mentioned:
{{
  "portfolio_type": "personal or institutional (null if not mentioned)",
  "date_of_birth": "YYYY-MM-DD format or null",
  "retirement_age": number or null,
  "net_worth": number or null,
  "annual_income": number or null,
  "monthly_investment": number or null,
  "annual_investment": number or null,
  "investment_mode": "sip, adhoc, or both (null if not mentioned)",
  "risk_tolerance": "conservative, moderate, aggressive, or very_aggressive (null if not mentioned)",
  "risk_details": "string description of risk tolerance (null if not mentioned)",
  "roi_expectations": number or null,
  "investment_style": "active, passive, or hybrid (null if not mentioned)",
  "activity_level": "string description (null if not mentioned)",
  "diversification_preference": "highly_diversified, moderately_diversified, or concentrated (null if not mentioned)",
  "investment_strategy": ["array", "of", "strategies"] or null,
  "liquidity_requirements": [
    {{
      "goal_id": "unique_string_id",
      "goal_name": "string (e.g., 'Buy a house')",
      "goal_type": "house_purchase|vacation|wedding|education|retirement|business|emergency_fund|vehicle|healthcare|other",
      "description": "detailed description",
      "target_amount": number (total cost),
      "amount_saved": number (already saved),
      "amount_needed": number (remaining needed),
      "target_date": "YYYY-MM-DD",
      "timeline_years": number,
      "priority": "high|medium|low",
      "is_flexible": boolean,
      "monthly_allocation": number,
      "funding_strategy": "sip|lump_sum|mixed",
      "risk_appetite_for_goal": "conservative|moderate|aggressive",
      "notes": "any additional notes",
      "progress_percentage": number (0-100)
    }}
  ] or null,
  "sector_preferences": {{"stocks": {{"allowed": true, "sectors": ["tech", "healthcare"]}}, "crypto": {{"allowed": false}}}} or null,
  "institution_name": "string or null",
  "institution_sector": "string or null",
  "annual_revenue": number or null,
  "annual_profit": number or null,
  "retirement_plans": "string or null",
  "making_for": "self or someone_else (null if not mentioned)",
  "existing_investments": {{"description": "string"}} or null,
  "existing_portfolios": [
    {{
      "portfolio_id": "unique_id",
      "portfolio_name": "string (e.g., 'Retirement 401k')",
      "goal_name": "string (linked goal)",
      "total_value": number,
      "cost_basis": number,
      "account_type": "401k|IRA|Roth_IRA|brokerage|crypto_wallet|savings|other",
      "account_provider": "string (e.g., 'Vanguard')",
      "holdings": [
        {{
          "ticker": "string",
          "asset_name": "string",
          "asset_type": "stock|bond|crypto|etf|mutual_fund|index_fund|reit|commodity|cash",
          "quantity": number,
          "current_price": number,
          "total_value": number
        }}
      ]
    }}
  ] or null
}}

Return ONLY valid JSON, no other text."""

    try:
        # Use LLM to extract structured data
        chat = LlmChat(
            api_key=os.environ.get('OPENAI_API_KEY'),
            session_id=f"context_extraction_{user_id}_{uuid.uuid4()}",
            system_message="You are a data extraction assistant. Extract financial information from conversations and return it as valid JSON."
        ).with_model("openai", "gpt-4o")
        
        extraction_response = await chat.send_message(UserMessage(text=extraction_prompt))
        
        # Parse the JSON response
        import json
        import re
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', extraction_response, re.DOTALL)
        if json_match:
            extracted_data = json.loads(json_match.group())
            
            # Remove null values and empty arrays
            update_data = {k: v for k, v in extracted_data.items() if v is not None and v != [] and v != {}}
            
            if update_data:
                # Update user context
                update_data["updated_at"] = datetime.now(timezone.utc)
                update_data["last_conversation_at"] = datetime.now(timezone.utc)
                
                await db.user_context.update_one(
                    {"user_id": user_id},
                    {"$set": update_data},
                    upsert=True
                )
                logger.info(f"Updated context for user {user_id}: {list(update_data.keys())}")
    
    except Exception as e:
        logger.error(f"Error in context extraction: {e}")

# Helper function to analyze context completeness
def analyze_context_completeness(user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze what information is missing from user context"""
    
    missing_fields = []
    optional_missing = []
    portfolio_type = user_context.get('portfolio_type')
    
    # Essential fields for everyone
    if not portfolio_type:
        missing_fields.append({
            "field": "portfolio_type",
            "importance": "critical",
            "question": "Are you creating this portfolio for yourself personally, or for an institution/organization?"
        })
    
    # Personal portfolio requirements
    if portfolio_type == 'personal':
        if not user_context.get('date_of_birth'):
            missing_fields.append({
                "field": "date_of_birth",
                "importance": "high",
                "question": "What is your date of birth? This helps me understand your investment timeline."
            })
        
        if not user_context.get('annual_income'):
            missing_fields.append({
                "field": "annual_income",
                "importance": "high",
                "question": "What is your approximate annual income?"
            })
        
        if not user_context.get('net_worth'):
            optional_missing.append({
                "field": "net_worth",
                "importance": "medium",
                "question": "What is your approximate net worth (total assets minus debts)?"
            })
        
        if not user_context.get('retirement_age'):
            optional_missing.append({
                "field": "retirement_age",
                "importance": "medium",
                "question": "At what age are you planning to retire?"
            })
    
    # Institutional portfolio requirements
    elif portfolio_type == 'institutional':
        if not user_context.get('institution_name'):
            missing_fields.append({
                "field": "institution_name",
                "importance": "high",
                "question": "What is the name of your institution/organization?"
            })
        
        if not user_context.get('annual_revenue'):
            optional_missing.append({
                "field": "annual_revenue",
                "importance": "medium",
                "question": "What is your organization's approximate annual revenue?"
            })
    
    # Investment amount - critical for everyone
    if not user_context.get('monthly_investment') and not user_context.get('annual_investment'):
        missing_fields.append({
            "field": "investment_amount",
            "importance": "critical",
            "question": "How much are you planning to invest? (monthly or annually)"
        })
    
    # Investment mode
    if not user_context.get('investment_mode'):
        missing_fields.append({
            "field": "investment_mode",
            "importance": "high",
            "question": "Do you prefer to invest regularly every month (SIP), make lump sum investments, or both?"
        })
    
    # Risk tolerance - essential
    if not user_context.get('risk_tolerance'):
        missing_fields.append({
            "field": "risk_tolerance",
            "importance": "critical",
            "question": "How would you describe your risk tolerance? Are you conservative (prefer safety), moderate (balanced), or aggressive (willing to take risks for higher returns)?"
        })
    
    # ROI expectations
    if not user_context.get('roi_expectations'):
        missing_fields.append({
            "field": "roi_expectations",
            "importance": "high",
            "question": "What annual return are you targeting? (e.g., 8%, 12%, 15%)"
        })
    
    # Financial goals
    if not user_context.get('liquidity_requirements') or len(user_context.get('liquidity_requirements', [])) == 0:
        missing_fields.append({
            "field": "financial_goals",
            "importance": "critical",
            "question": "What are your main financial goals? (e.g., retirement, buying a house, children's education, emergency fund)"
        })
    
    # Investment strategy
    if not user_context.get('investment_strategy') or len(user_context.get('investment_strategy', [])) == 0:
        optional_missing.append({
            "field": "investment_strategy",
            "importance": "medium",
            "question": "Do you have any preferred investment strategies? (e.g., value investing, growth investing, index funds, dividend investing)"
        })
    
    # Sector preferences
    if not user_context.get('sector_preferences'):
        optional_missing.append({
            "field": "sector_preferences",
            "importance": "medium",
            "question": "Are there any sectors or asset classes you want to avoid or prefer? (e.g., tech stocks, crypto, real estate)"
        })
    
    # Existing portfolios
    if not user_context.get('existing_portfolios') or len(user_context.get('existing_portfolios', [])) == 0:
        optional_missing.append({
            "field": "existing_portfolios",
            "importance": "medium",
            "question": "Do you have any existing investment accounts or portfolios? (e.g., 401k, IRA, brokerage accounts)"
        })
    
    # Calculate completeness score
    total_critical = len([f for f in missing_fields if f['importance'] == 'critical'])
    total_high = len([f for f in missing_fields if f['importance'] == 'high'])
    
    # Ready for portfolio if no critical fields missing and at most 2 high priority missing
    is_ready_for_portfolio = total_critical == 0 and total_high <= 2
    
    completeness_percentage = 100
    if missing_fields or optional_missing:
        total_fields = len(missing_fields) + len(optional_missing)
        missing_count = len(missing_fields) + (len(optional_missing) * 0.5)  # Optional fields count as half
        completeness_percentage = max(0, int(100 - (missing_count / total_fields * 100)))
    
    return {
        "is_ready_for_portfolio": is_ready_for_portfolio,
        "completeness_percentage": completeness_percentage,
        "missing_critical": [f for f in missing_fields if f['importance'] == 'critical'],
        "missing_high": [f for f in missing_fields if f['importance'] == 'high'],
        "missing_medium": optional_missing,
        "next_question": missing_fields[0] if missing_fields else (optional_missing[0] if optional_missing else None)
    }

# Helper function to generate contextual greeting/question
async def generate_smart_question(user_id: str, user_context: Dict[str, Any], chat_history: List[Dict]) -> str:
    """Generate intelligent questions based on missing context"""
    
    analysis = analyze_context_completeness(user_context)
    
    # If this is first message (no chat history), start with greeting
    if len(chat_history) == 0:
        # Check if user has basic info from onboarding form
        has_basic_info = user_context.get('portfolio_type') and user_context.get('risk_tolerance')
        
        if has_basic_info:
            # User completed onboarding form
            return f"""Welcome to WealthMaker! I'm your AI financial advisor.

I see you've provided some initial information - great start! You're {user_context.get('age', 'N/A')} years old, looking for a {user_context.get('risk_tolerance', 'moderate')} risk portfolio with a target return of {user_context.get('roi_expectations', 'N/A')}%.

Let me ask a few more questions to create the perfect portfolio for you. {analysis['next_question']['question'] if analysis['next_question'] else "How can I help you with your investment goals today?"}"""
        else:
            # User skipped or hasn't done onboarding
            return """Welcome to WealthMaker! I'm your AI financial advisor, and I'm here to help you build a personalized investment portfolio.

To create the best portfolio for you, I'll need to understand your financial situation and goals. Let's start with a few questions.

First, are you creating this portfolio for yourself personally, or for an institution/organization?"""
    
    # If ready for portfolio, signal that we can proceed
    if analysis['is_ready_for_portfolio']:
        return None  # Signal that we have enough info
    
    # Generate question based on what's missing
    next_q = analysis['next_question']
    if next_q:
        # Add context about why we're asking
        prefix = ""
        if analysis['completeness_percentage'] < 30:
            prefix = "Great! "
        elif analysis['completeness_percentage'] < 60:
            prefix = "Thanks for that information. "
        else:
            prefix = "We're almost there! "
        
        return f"{prefix}{next_q['question']}"
    
    return None

# Chat routes
@api_router.get("/chat/messages")
async def get_chat_messages(user: User = Depends(require_auth)):
    messages = await db.chat_messages.find(
        {"user_id": user.id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    
    for msg in messages:
        if isinstance(msg['timestamp'], str):
            msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
    
    return messages

@api_router.get("/chat/init")
async def initialize_chat(user: User = Depends(require_auth)):
    """Initialize chat with a greeting message for first-time users"""
    
    # Get user context to check if chat has been initiated
    user_context = await db.user_context.find_one({"user_id": user.id})
    
    # If no context or first_chat_initiated is False/None, generate initial message
    if not user_context or not user_context.get('first_chat_initiated', False):
        # Check if there are already messages (user might have started chatting before we added this feature)
        existing_messages = await db.chat_messages.count_documents({"user_id": user.id})
        
        if existing_messages > 0:
            # User has already chatted, don't auto-initiate
            if user_context:
                await db.user_context.update_one(
                    {"user_id": user.id},
                    {"$set": {"first_chat_initiated": True, "updated_at": datetime.now(timezone.utc)}}
                )
            return {"message": None}
        
        # Generate personalized initial message - simple and conversational
        initial_message = f"""Hi {user.name}! 👋 Welcome to WealthMaker!

I'm your AI financial advisor, and I'm excited to help you build a personalized investment portfolio.

**What's your main financial goal right now?** 💼"""

        # Save the initial message to chat history
        ai_msg_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user.id,
            "role": "assistant",
            "message": initial_message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.chat_messages.insert_one(ai_msg_doc)
        
        # Mark chat as initiated in user context
        if user_context:
            await db.user_context.update_one(
                {"user_id": user.id},
                {"$set": {"first_chat_initiated": True, "updated_at": datetime.now(timezone.utc)}}
            )
        else:
            # Create user context if it doesn't exist
            new_context = {
                "_id": str(uuid.uuid4()),
                "user_id": user.id,
                "first_chat_initiated": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            await db.user_context.insert_one(new_context)
        
        return {
            "message": initial_message,
            "timestamp": ai_msg_doc["timestamp"]
        }
    
    # Chat already initiated
    return {"message": None}

# DISABLED: Using modular routes/chat.py instead
# @api_router.post("/chat/send", response_model=ChatResponse)
@api_router.post("/chat/send-disabled", response_model=ChatResponse)
async def send_message_old(chat_request: ChatRequest, user: User = Depends(require_auth)):
    user_message = chat_request.message
    
    # Get chat history FIRST to check if this is first message
    chat_history = await db.chat_messages.find(
        {"user_id": user.id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(100)
    
    # Save user message
    user_msg_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "role": "user",
        "message": user_message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.chat_messages.insert_one(user_msg_doc)
    
    # Get user context
    user_context = await db.user_context.find_one({"user_id": user.id})
    if not user_context:
        # Create default context
        user_context = {
            "_id": str(uuid.uuid4()),
            "user_id": user.id,
            "portfolio_type": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.user_context.insert_one(user_context)
    
    # Build context string
    context_info = "\n\n=== USER CONTEXT & MEMORY ==="
    
    if user_context.get('portfolio_type'):
        context_info += f"\n- Portfolio Type: {user_context['portfolio_type']}"
    
    if user_context.get('portfolio_type') == 'personal':
        if user_context.get('date_of_birth'):
            # Calculate age from date of birth
            from dateutil.relativedelta import relativedelta
            dob_str = user_context['date_of_birth']
            # Handle both string dates (YYYY-MM-DD) and datetime objects
            if isinstance(dob_str, str):
                # Parse string date and ensure it's timezone-aware
                if 'T' in dob_str or 'Z' in dob_str or '+' in dob_str:
                    dob = datetime.fromisoformat(dob_str.replace('Z', '+00:00'))
                else:
                    # Simple date string like "1990-01-01"
                    dob = datetime.strptime(dob_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            else:
                dob = dob_str
            
            # Ensure both datetimes are timezone-aware for comparison
            if dob.tzinfo is None:
                dob = dob.replace(tzinfo=timezone.utc)
            
            age = relativedelta(datetime.now(timezone.utc), dob).years
            context_info += f"\n- Age: {age} (DOB: {str(dob)[:10]})"
        if user_context.get('retirement_age'):
            context_info += f"\n- Retirement Age: {user_context['retirement_age']}"
        if user_context.get('retirement_plans'):
            context_info += f"\n- Retirement Plans: {user_context['retirement_plans']}"
    elif user_context.get('portfolio_type') == 'institutional':
        if user_context.get('institution_name'):
            context_info += f"\n- Institution: {user_context['institution_name']}"
        if user_context.get('institution_sector'):
            context_info += f"\n- Sector: {user_context['institution_sector']}"
        if user_context.get('annual_revenue'):
            context_info += f"\n- Annual Revenue: ${user_context['annual_revenue']:,.2f}"
    
    if user_context.get('net_worth'):
        context_info += f"\n- Net Worth: ${user_context['net_worth']:,.2f}"
    if user_context.get('annual_income'):
        context_info += f"\n- Annual Income: ${user_context['annual_income']:,.2f}"
    if user_context.get('monthly_investment'):
        context_info += f"\n- Monthly Investment: ${user_context['monthly_investment']:,.2f}"
    if user_context.get('investment_mode'):
        context_info += f"\n- Investment Mode: {user_context['investment_mode']}"
    
    if user_context.get('risk_tolerance'):
        context_info += f"\n- Risk Tolerance: {user_context['risk_tolerance']}"
        if user_context.get('risk_details'):
            context_info += f" ({user_context['risk_details']})"
    if user_context.get('roi_expectations'):
        context_info += f"\n- ROI Expectations: {user_context['roi_expectations']}%"
    
    if user_context.get('investment_style'):
        context_info += f"\n- Investment Style: {user_context['investment_style']}"
    if user_context.get('activity_level'):
        context_info += f"\n- Activity Level: {user_context['activity_level']}"
    if user_context.get('diversification_preference'):
        context_info += f"\n- Diversification: {user_context['diversification_preference']}"
    
    if user_context.get('investment_strategy'):
        context_info += f"\n- Investment Strategy: {', '.join(user_context['investment_strategy'])}"
    
    if user_context.get('liquidity_requirements'):
        context_info += "\n\n- FINANCIAL GOALS & LIQUIDITY NEEDS:"
        for req in user_context['liquidity_requirements']:
            goal_name = req.get('goal_name', req.get('goal', 'Goal'))
            target_amount = req.get('target_amount', req.get('amount', 0)) or 0
            amount_saved = req.get('amount_saved', 0) or 0
            amount_needed = req.get('amount_needed', target_amount - amount_saved) or 0
            target_date = req.get('target_date', req.get('when', 'TBD'))
            priority = req.get('priority', 'medium')
            progress = req.get('progress_percentage', 0) or 0
            
            context_info += f"\n  * {goal_name} ({priority} priority)"
            context_info += f"\n    - Target: ${target_amount:,.0f} by {target_date}"
            context_info += f"\n    - Saved: ${amount_saved:,.0f} ({progress:.1f}%)"
            context_info += f"\n    - Still Needed: ${amount_needed:,.0f}"
            
            if req.get('monthly_allocation'):
                context_info += f"\n    - Monthly Allocation: ${req['monthly_allocation']:,.0f}"
            if req.get('description'):
                context_info += f"\n    - Details: {req['description']}"
    
    if user_context.get('sector_preferences'):
        context_info += "\n- Sector Preferences:"
        for sector, prefs in user_context['sector_preferences'].items():
            if prefs.get('allowed'):
                sectors = prefs.get('sectors', [])
                context_info += f"\n  * {sector.capitalize()}: {', '.join(sectors) if sectors else 'All'}"
    
    if user_context.get('existing_investments'):
        context_info += f"\n- Existing Investments: {user_context['existing_investments']}"
    
    # Display existing portfolios
    if user_context.get('existing_portfolios'):
        context_info += "\n\n- EXISTING PORTFOLIOS:"
        for portfolio in user_context['existing_portfolios']:
            portfolio_name = portfolio.get('portfolio_name', 'Portfolio')
            goal_name = portfolio.get('goal_name', 'General')
            total_value = portfolio.get('total_value', 0)
            cost_basis = portfolio.get('cost_basis', 0)
            gain_loss = portfolio.get('unrealized_gain_loss', 0)
            gain_loss_pct = portfolio.get('unrealized_gain_loss_percentage', 0)
            account_type = portfolio.get('account_type', 'N/A')
            
            context_info += f"\n  * {portfolio_name} (for {goal_name})"
            context_info += f"\n    - Account Type: {account_type}"
            context_info += f"\n    - Current Value: ${total_value:,.2f}"
            context_info += f"\n    - Cost Basis: ${cost_basis:,.2f}"
            context_info += f"\n    - Gain/Loss: ${gain_loss:,.2f} ({gain_loss_pct:.2f}%)"
            
            if portfolio.get('allocation_summary'):
                context_info += "\n    - Allocation: "
                alloc_str = ", ".join([f"{k}: {v:.1f}%" for k, v in portfolio['allocation_summary'].items()])
                context_info += alloc_str
            
            if portfolio.get('holdings'):
                context_info += f"\n    - Holdings: {len(portfolio['holdings'])} assets"
                # Show top 3 holdings
                top_holdings = sorted(portfolio['holdings'], key=lambda x: x.get('total_value', 0), reverse=True)[:3]
                for holding in top_holdings:
                    ticker = holding.get('ticker', 'N/A')
                    value = holding.get('total_value', 0)
                    alloc_pct = holding.get('allocation_percentage', 0)
                    context_info += f"\n      - {ticker}: ${value:,.2f} ({alloc_pct:.1f}%)"
    
    # Analyze context completeness
    context_analysis = analyze_context_completeness(user_context)
    
    context_info += "\n\n=== INFORMATION GATHERING STATUS ==="
    context_info += f"\n- Profile Completeness: {context_analysis['completeness_percentage']}%"
    context_info += f"\n- Ready for Portfolio Creation: {'YES' if context_analysis['is_ready_for_portfolio'] else 'NO - More information needed'}"
    
    if context_analysis['missing_critical']:
        context_info += f"\n- CRITICAL Missing Info: {len(context_analysis['missing_critical'])} fields"
    if context_analysis['missing_high']:
        context_info += f"\n- HIGH Priority Missing: {len(context_analysis['missing_high'])} fields"
    if context_analysis['missing_medium']:
        context_info += f"\n- OPTIONAL Missing: {len(context_analysis['missing_medium'])} fields"
    
    # Get current portfolio
    portfolio_doc = await db.portfolios.find_one({"user_id": user.id})
    if portfolio_doc:
        context_info += f"\n\nCurrent Portfolio:\n- Risk Tolerance: {portfolio_doc.get('risk_tolerance', 'Not set')}\n- ROI Expectations: {portfolio_doc.get('roi_expectations', 'Not set')}%\n- Allocations: {len(portfolio_doc.get('allocations', []))} assets"
    
    # Check if we should ask a smart question
    smart_question = await generate_smart_question(user.id, user_context, chat_history)
    
    # Determine if personal or institutional guidance needed
    portfolio_type_guidance = ""
    if user_context.get('portfolio_type') == 'personal':
        portfolio_type_guidance = """
PERSONAL PORTFOLIO GUIDANCE:
- Ask about personal financial goals (retirement, buying a home, children's education, etc.)
- Consider age, retirement plans, and life events
- Focus on long-term wealth building and tax efficiency
- Ask about family situation and dependents
"""
    elif user_context.get('portfolio_type') == 'institutional':
        portfolio_type_guidance = """
INSTITUTIONAL PORTFOLIO GUIDANCE:
- Ask about institutional goals (capital preservation, growth, income generation)
- Consider regulatory requirements and compliance
- Focus on portfolio size, liquidity needs, and risk management
- Ask about investment committee requirements and reporting needs
"""
    else:
        portfolio_type_guidance = """
INITIAL ASSESSMENT:
- First, determine if this is a personal or institutional portfolio
- Ask: "Are you creating this portfolio for yourself personally, or for an institution/organization?"
- Based on their answer, tailor subsequent questions accordingly
"""
    
    # Determine conversation mode based on context completeness
    conversation_mode = ""
    if not context_analysis['is_ready_for_portfolio']:
        conversation_mode = """
=== CURRENT MODE: INFORMATION GATHERING ===

You are in INFORMATION GATHERING mode. Your primary task is to collect essential information before making any portfolio recommendations.

RULES FOR THIS MODE:
1. DO NOT suggest any portfolio allocations yet - you don't have enough information
2. Ask ONE focused question at a time to gather missing information
3. Be conversational and friendly, not robotic
4. Acknowledge user's answers before asking the next question
5. Explain briefly WHY you need each piece of information
6. Adapt your questions based on their previous answers
7. If user asks about portfolios, explain you need more information first

YOUR NEXT QUESTION SHOULD BE ABOUT: {context_analysis['next_question']['field'] if context_analysis['next_question'] else 'general financial situation'}
"""
    else:
        conversation_mode = """
=== CURRENT MODE: ADVISORY MODE ===

You have sufficient information! You can now:
1. Provide specific portfolio recommendations
2. Answer questions about investment strategies
3. Suggest portfolio adjustments
4. Offer detailed financial advice

You may still ask clarifying questions, but you have enough to create an initial portfolio.
"""
    
    # Create system message
    system_message = f"""You are an expert financial advisor helping users build and manage their investment portfolio.{context_info}

{conversation_mode}

{portfolio_type_guidance}

Your role:
1. Understand user's investment preferences and continuously build their context/memory
2. Extract and remember key information about their financial situation, goals, and preferences
3. Ask smart, contextual questions based on what information is missing
4. ONLY recommend portfolios when you have sufficient information (Ready for Portfolio Creation: YES)
5. Explain your recommendations in clear, simple terms

KEY INFORMATION TO GATHER (if not already known):
- Portfolio type (personal vs institutional)
- Age and retirement plans (for personal) or company details (for institutional)
- Net worth and income
- Investment amount (monthly/annual) and mode (SIP vs ad-hoc)
- Risk tolerance (detailed understanding, not just a number)

CRITICAL: DETAILED FINANCIAL GOALS - Ask about EACH goal:
For every financial goal, gather these specific details:
1. Goal Name: What exactly is the goal? (e.g., "Buy a 3-bedroom house in suburbs")
2. Goal Type: house_purchase, vacation, wedding, children_education, retirement, start_business, emergency_fund, vehicle_purchase, healthcare, other
3. Total Cost: How much money does this goal require in total?
4. Amount Already Saved: How much have they already saved for this goal?
5. Target Date: When do they need this money? (specific date or timeframe)
6. Priority Level: Is this high, medium, or low priority?
7. Flexibility: Can the timeline be adjusted if needed?
8. Monthly Savings: How much can they allocate monthly toward this goal?
9. Funding Strategy: Will they save monthly (SIP), invest a lump sum, or both?
10. Risk Appetite for Goal: How much risk are they willing to take for THIS specific goal?
11. Additional Details: Any other important information about this goal

IMPORTANT: Different goals may have different risk tolerances. A goal 30 years away (retirement) can handle more risk than a goal 2 years away (house down payment).

Examples of questions to ask:
- "I see you want to buy a house. How much do you estimate it will cost?"
- "When are you planning to make this purchase?"
- "Have you already started saving for this? If so, how much have you saved?"
- "How much can you set aside monthly toward this goal?"
- "Is this timeline flexible, or is it a fixed date?"
- "Would you be comfortable with moderate market risk for this goal, or do you need this money to be very safe?"

CRITICAL: EXISTING PORTFOLIOS - Ask about EACH existing portfolio:
For every existing investment account or portfolio, gather:
1. Portfolio Name: What do they call this account? (e.g., "My 401k", "Robinhood Account")
2. Linked Goal: Which goal is this portfolio for? (retirement, emergency fund, etc.)
3. Account Type: 401k, IRA, Roth IRA, brokerage account, crypto wallet, savings account, etc.
4. Account Provider: Where is it held? (Vanguard, Fidelity, Robinhood, Coinbase, etc.)
5. Total Current Value: What's the total value right now?
6. Original Investment: How much did they originally put in (cost basis)?
7. Holdings: What specific assets do they own?
   - For each holding: ticker/name, asset type, quantity, current price, total value
8. Performance: How has it performed? (gains/losses)
9. Last Update: When did they last check or update this information?

Examples of questions to ask:
- "Do you have any existing investment accounts or portfolios?"
- "What type of account is this? (401k, IRA, regular brokerage, etc.)"
- "What's the current total value of this portfolio?"
- "Which goal is this portfolio intended for?"
- "What are the main holdings in this portfolio? (stocks, bonds, funds, etc.)"
- "Can you tell me about your largest positions? (ticker symbols and approximate values)"
- "Has this portfolio been performing well? What are your gains or losses?"

IMPORTANT: Understanding existing portfolios helps avoid:
- Duplicating investments
- Creating imbalanced overall allocations
- Missing opportunities to optimize existing holdings
- Ignoring tax implications of existing accounts

When recommending portfolios: 

Your role:
1. Understand user's investment preferences (risk tolerance, ROI expectations, retirement goals, investment horizon)
2. Recommend portfolio allocations across different asset classes (stocks, bonds, crypto, indexes)
3. Suggest specific tickers and allocation percentages
4. Explain your recommendations in clear, simple terms
5. ONLY suggest portfolio updates when you have specific recommendations

When recommending portfolios:
- For LOW risk: 60-70% bonds, 20-30% blue-chip stocks, 5-10% index funds
- For MEDIUM risk: 40% stocks, 30% bonds, 20% index funds, 10% alternative investments
- For HIGH risk: 50-60% growth stocks, 20% crypto, 10-15% emerging markets, 10% bonds

IMPORTANT INSTRUCTIONS:
1. ONLY create a portfolio suggestion when:
   - Profile Completeness is at least 70% AND Ready for Portfolio Creation is YES
   - User explicitly requests a portfolio (new or updated)
   - You have enough information about their goals, risk tolerance, and investment amount
   - You have specific tickers and allocations to recommend
   
   If Ready for Portfolio Creation is NO, DO NOT suggest portfolios. Instead, gather the missing information first.

2. When you DO have a portfolio recommendation, end your response with this EXACT format:
   
   [PORTFOLIO_SUGGESTION]
   {{
     "risk_tolerance": "medium",
     "roi_expectations": 10.0,
     "allocations": [
       {{"asset_type": "Stocks", "ticker": "AAPL", "allocation": 20, "sector": "Technology"}},
       {{"asset_type": "Bonds", "ticker": "AGG", "allocation": 30, "sector": "Fixed Income"}}
     ],
     "reasoning": "Brief explanation of why this portfolio suits the user"
   }}
   [/PORTFOLIO_SUGGESTION]

   Then ask: "Would you like me to update your portfolio with these recommendations?"

3. For general questions, portfolio discussions, or clarifications, respond normally WITHOUT the portfolio suggestion marker and WITHOUT asking about updates.

Always provide specific ticker symbols (e.g., AAPL, MSFT, BTC-USD, SPY) and allocation percentages when making recommendations.

Respond in a friendly, professional tone. Keep responses concise but informative."""
    
    try:
        # Special handling for first message or if smart question needed
        if smart_question and len(chat_history) == 0:
            # First interaction - use smart greeting
            ai_response = smart_question
        elif smart_question and not context_analysis['is_ready_for_portfolio'] and len(user_message.lower().split()) < 5:
            # Short user response and still gathering info - guide with smart question
            # But first, let AI process the user's answer
            chat = LlmChat(
                api_key=os.environ.get('OPENAI_API_KEY'),
                session_id=f"portfolio_chat_{user.id}",
                system_message=system_message
            ).with_model("openai", "gpt-4o")
            
            llm_message = UserMessage(text=user_message)
            ai_response = await chat.send_message(llm_message)
        else:
            # Normal conversation flow
            chat = LlmChat(
                api_key=os.environ.get('OPENAI_API_KEY'),
                session_id=f"portfolio_chat_{user.id}",
                system_message=system_message
            ).with_model("openai", "gpt-4o")
            
            # Send message
            llm_message = UserMessage(text=user_message)
            ai_response = await chat.send_message(llm_message)
        
    except Exception as e:
        logger.error(f"LLM error: {e}")
        ai_response = "I apologize, but I'm having trouble processing your request right now. Please try again."
    
    # Check if response contains a portfolio suggestion
    portfolio_suggestion = None
    suggestion_id = None
    clean_response = ai_response
    
    if "[PORTFOLIO_SUGGESTION]" in ai_response and "[/PORTFOLIO_SUGGESTION]" in ai_response:
        try:
            # Extract the JSON between markers
            start = ai_response.index("[PORTFOLIO_SUGGESTION]") + len("[PORTFOLIO_SUGGESTION]")
            end = ai_response.index("[/PORTFOLIO_SUGGESTION]")
            json_str = ai_response[start:end].strip()
            
            # Parse the portfolio data
            import json
            portfolio_data = json.loads(json_str)
            
            # Generate a suggestion ID
            suggestion_id = str(uuid.uuid4())
            
            # Store suggestion temporarily
            await db.portfolio_suggestions.insert_one({
                "_id": suggestion_id,
                "user_id": user.id,
                "portfolio_data": portfolio_data,
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=24)
            })
            
            portfolio_suggestion = portfolio_data
            
            # Remove the marker from the response
            clean_response = ai_response[:ai_response.index("[PORTFOLIO_SUGGESTION]")].strip()
            
            logger.info(f"Portfolio suggestion created with ID: {suggestion_id}")
            
        except Exception as e:
            logger.error(f"Error parsing portfolio suggestion: {e}")
    
    # Detect if user wants to update existing context
    update_keywords = ['change', 'update', 'modify', 'correct', 'actually', 'instead']
    is_context_update = any(keyword in user_message.lower() for keyword in update_keywords)
    
    # Extract and update user context from conversation
    try:
        await extract_and_update_context(user.id, user_message, ai_response)
        
        # If this was a context update, acknowledge it
        if is_context_update:
            logger.info(f"Context update detected for user {user.id}")
    except Exception as e:
        logger.error(f"Error extracting context: {e}")
    
    # Save AI response (clean version)
    ai_msg_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "role": "assistant",
        "message": clean_response,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "suggestion_id": suggestion_id
    }
    await db.chat_messages.insert_one(ai_msg_doc)
    
    return ChatResponse(
        message=clean_response, 
        portfolio_updated=False,
        portfolio_suggestion=portfolio_suggestion,
        suggestion_id=suggestion_id
    )

async def update_portfolio_from_conversation(user_id: str, user_message: str, ai_response: str):
    """Update portfolio based on conversation - simplified version"""
    portfolio = await db.portfolios.find_one({"user_id": user_id})
    
    lower_msg = user_message.lower()
    
    # Extract risk tolerance
    risk = None
    if 'low risk' in lower_msg or 'conservative' in lower_msg or 'safe' in lower_msg:
        risk = 'low'
    elif 'high risk' in lower_msg or 'aggressive' in lower_msg:
        risk = 'high'
    elif 'medium risk' in lower_msg or 'moderate' in lower_msg or 'balanced' in lower_msg:
        risk = 'medium'
    
    # Extract ROI expectations
    roi = None
    if '5%' in lower_msg or 'five percent' in lower_msg:
        roi = 5.0
    elif '10%' in lower_msg or 'ten percent' in lower_msg:
        roi = 10.0
    elif '15%' in lower_msg or 'fifteen percent' in lower_msg:
        roi = 15.0
    elif '20%' in lower_msg or 'twenty percent' in lower_msg:
        roi = 20.0
    
    if portfolio:
        # Update existing
        update_data = {"updated_at": datetime.now(timezone.utc)}
        if risk:
            update_data["risk_tolerance"] = risk
        if roi:
            update_data["roi_expectations"] = roi
        
        await db.portfolios.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
    else:
        # Create new
        portfolio_doc = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "risk_tolerance": risk or 'medium',
            "roi_expectations": roi or 10.0,
            "preferences": {},
            "allocations": get_default_allocations(risk or 'medium'),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.portfolios.insert_one(portfolio_doc)

def get_default_allocations(risk_tolerance: str) -> List[Dict[str, Any]]:
    """Generate default portfolio allocations based on risk tolerance"""
    if risk_tolerance == 'low':
        return [
            {"asset_type": "Bonds", "ticker": "AGG", "allocation": 60, "sector": "Fixed Income"},
            {"asset_type": "Stocks", "ticker": "AAPL", "allocation": 15, "sector": "Technology"},
            {"asset_type": "Stocks", "ticker": "JNJ", "allocation": 15, "sector": "Healthcare"},
            {"asset_type": "Index", "ticker": "SPY", "allocation": 10, "sector": "Diversified"}
        ]
    elif risk_tolerance == 'high':
        return [
            {"asset_type": "Stocks", "ticker": "TSLA", "allocation": 25, "sector": "Technology"},
            {"asset_type": "Stocks", "ticker": "NVDA", "allocation": 25, "sector": "Technology"},
            {"asset_type": "Crypto", "ticker": "BTC-USD", "allocation": 20, "sector": "Cryptocurrency"},
            {"asset_type": "Stocks", "ticker": "PLTR", "allocation": 15, "sector": "Technology"},
            {"asset_type": "Bonds", "ticker": "AGG", "allocation": 10, "sector": "Fixed Income"},
            {"asset_type": "Index", "ticker": "QQQ", "allocation": 5, "sector": "Technology"}
        ]
    else:  # medium
        return [
            {"asset_type": "Stocks", "ticker": "AAPL", "allocation": 20, "sector": "Technology"},
            {"asset_type": "Stocks", "ticker": "MSFT", "allocation": 15, "sector": "Technology"},
            {"asset_type": "Bonds", "ticker": "AGG", "allocation": 30, "sector": "Fixed Income"},
            {"asset_type": "Index", "ticker": "SPY", "allocation": 20, "sector": "Diversified"},
            {"asset_type": "Stocks", "ticker": "V", "allocation": 10, "sector": "Financial"},
            {"asset_type": "Index", "ticker": "VTI", "allocation": 5, "sector": "Diversified"}
        ]

# Portfolio routes
@api_router.post("/portfolio/accept")
async def accept_portfolio(request: AcceptPortfolioRequest, user: User = Depends(require_auth)):
    """Accept a portfolio suggestion and update the user's portfolio"""
    try:
        # Get the suggestion
        suggestion = await db.portfolio_suggestions.find_one({"_id": request.suggestion_id, "user_id": user.id})
        
        if not suggestion:
            raise HTTPException(status_code=404, detail="Portfolio suggestion not found or expired")
        
        portfolio_data = request.portfolio_data
        
        # Check if user has an existing portfolio
        existing_portfolio = await db.portfolios.find_one({"user_id": user.id})
        
        portfolio_doc = {
            "user_id": user.id,
            "risk_tolerance": portfolio_data.get("risk_tolerance", "medium"),
            "roi_expectations": portfolio_data.get("roi_expectations", 10.0),
            "preferences": portfolio_data.get("preferences", {}),
            "allocations": portfolio_data.get("allocations", []),
            "updated_at": datetime.now(timezone.utc)
        }
        
        if existing_portfolio:
            # Update existing portfolio
            await db.portfolios.update_one(
                {"user_id": user.id},
                {"$set": portfolio_doc}
            )
            logger.info(f"Updated portfolio for user {user.id}")
        else:
            # Create new portfolio
            portfolio_doc["_id"] = str(uuid.uuid4())
            portfolio_doc["created_at"] = datetime.now(timezone.utc)
            await db.portfolios.insert_one(portfolio_doc)
            logger.info(f"Created new portfolio for user {user.id}")
        
        # Delete the suggestion after acceptance
        await db.portfolio_suggestions.delete_one({"_id": request.suggestion_id})
        
        return {"success": True, "message": "Portfolio updated successfully"}
        
    except Exception as e:
        logger.error(f"Error accepting portfolio: {e}")
        raise HTTPException(status_code=500, detail="Failed to update portfolio")

@api_router.get("/portfolio")
async def get_portfolio_legacy(user: User = Depends(require_auth)):
    """Get user's AI-generated portfolio (legacy endpoint for frontend compatibility)"""
    portfolio = await db.portfolios.find_one({"user_id": user.id})
    if not portfolio:
        return {"portfolio": None, "message": "No portfolio found"}
    
    # Convert ObjectId to string for JSON serialization
    if '_id' in portfolio:
        portfolio['_id'] = str(portfolio['_id'])
    
    return portfolio

# Import and include all route modules
from routes import auth, context, goals, portfolios, chat, news, data, admin, portfolio_management

# Register all routers
api_router.include_router(auth.router)
api_router.include_router(context.router)
api_router.include_router(goals.router)
api_router.include_router(portfolios.router)
api_router.include_router(portfolio_management.router)  # New multi-portfolio management
api_router.include_router(chat.router)
api_router.include_router(news.router)
api_router.include_router(data.router)
api_router.include_router(admin.router)

# Include the API router in the main app
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "WealthMaker API", "version": "1.0.0", "status": "active"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connections on shutdown"""
    from utils.database import client
    client.close()
    logger.info("Database connection closed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
