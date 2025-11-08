from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import finnhub
import httpx
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Finnhub setup
finnhub_client = finnhub.Client(api_key=os.environ.get('FINNHUB_API_KEY', ''))

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    age: Optional[int] = None
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
    
    # Liquidity & Goals
    liquidity_requirements: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    # Each item: {"goal": "house", "when": "2025", "amount": 50000}
    
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
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_conversation_at: Optional[datetime] = None

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
    session_token = None
    # Get from cookie or header
    # (handled by get_current_user)
    
    # Delete all sessions for user
    await db.user_sessions.delete_many({"user_id": user.id})
    
    # Clear cookie
    response.delete_cookie("session_token", path="/")
    
    return {"success": True}

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

# Helper function for context extraction
async def extract_and_update_context(user_id: str, user_message: str, ai_response: str):
    """Extract context from conversation and update user context"""
    
    extraction_prompt = f"""Based on the following conversation, extract any relevant financial information about the user.
Return ONLY a JSON object with the extracted information. Use null for any information not mentioned.

User message: {user_message}
AI response: {ai_response}

Extract the following if mentioned:
{{
  "portfolio_type": "personal or institutional (null if not mentioned)",
  "age": number or null,
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
  "liquidity_requirements": [{{"goal": "string", "when": "string", "amount": number}}] or null,
  "sector_preferences": {{"stocks": {{"allowed": true, "sectors": ["tech", "healthcare"]}}, "crypto": {{"allowed": false}}}} or null,
  "institution_name": "string or null",
  "institution_sector": "string or null",
  "annual_revenue": number or null,
  "annual_profit": number or null,
  "retirement_plans": "string or null",
  "making_for": "self or someone_else (null if not mentioned)",
  "existing_investments": {{"description": "string"}} or null
}}

Return ONLY valid JSON, no other text."""

    try:
        # Use LLM to extract structured data
        chat = LlmChat(
            api_key=os.environ.get('OPENAI_API_KEY'),
            session_id=f"context_extraction_{user_id}_{uuid.uuid4()}",
            system_message="You are a data extraction assistant. Extract financial information from conversations and return it as valid JSON."
        ).with_model("openai", "gpt-5")
        
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

@api_router.post("/chat/send", response_model=ChatResponse)
async def send_message(chat_request: ChatRequest, user: User = Depends(require_auth)):
    user_message = chat_request.message
    
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
    
    if user_context['portfolio_type'] == 'personal':
        if user_context.get('age'):
            context_info += f"\n- Age: {user_context['age']}"
        if user_context.get('retirement_age'):
            context_info += f"\n- Retirement Age: {user_context['retirement_age']}"
        if user_context.get('retirement_plans'):
            context_info += f"\n- Retirement Plans: {user_context['retirement_plans']}"
    elif user_context['portfolio_type'] == 'institutional':
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
        context_info += "\n- Liquidity Requirements:"
        for req in user_context['liquidity_requirements']:
            context_info += f"\n  * {req.get('goal', 'Goal')}: {req.get('when', 'TBD')} (${req.get('amount', 0):,.0f})"
    
    if user_context.get('sector_preferences'):
        context_info += "\n- Sector Preferences:"
        for sector, prefs in user_context['sector_preferences'].items():
            if prefs.get('allowed'):
                sectors = prefs.get('sectors', [])
                context_info += f"\n  * {sector.capitalize()}: {', '.join(sectors) if sectors else 'All'}"
    
    if user_context.get('existing_investments'):
        context_info += f"\n- Existing Investments: {user_context['existing_investments']}"
    
    # Get current portfolio
    portfolio_doc = await db.portfolios.find_one({"user_id": user.id})
    if portfolio_doc:
        context_info += f"\n\nCurrent Portfolio:\n- Risk Tolerance: {portfolio_doc.get('risk_tolerance', 'Not set')}\n- ROI Expectations: {portfolio_doc.get('roi_expectations', 'Not set')}%\n- Allocations: {len(portfolio_doc.get('allocations', []))} assets"
    
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
    
    # Create system message
    system_message = f"""You are an expert financial advisor helping users build and manage their investment portfolio.{context_info}

{portfolio_type_guidance}

Your role:
1. Understand user's investment preferences and continuously build their context/memory
2. Extract and remember key information about their financial situation, goals, and preferences
3. Recommend portfolio allocations across different asset classes (stocks, bonds, crypto, indexes)
4. Suggest specific tickers and allocation percentages
5. Explain your recommendations in clear, simple terms
6. ONLY suggest portfolio updates when you have specific recommendations

KEY INFORMATION TO GATHER (if not already known):
- Portfolio type (personal vs institutional)
- Age and retirement plans (for personal) or company details (for institutional)
- Net worth and income
- Investment amount (monthly/annual) and mode (SIP vs ad-hoc)
- Liquidity needs and future financial goals
- Risk tolerance (detailed understanding, not just a number)
- ROI expectations
- Investment style and activity preference
- Existing investments
- Sector preferences and restrictions
- Investment strategy preferences
- Diversification preference

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
   - User explicitly requests a portfolio (new or updated)
   - User provides clear investment preferences (risk, ROI goals, etc.)
   - You have specific tickers and allocations to recommend

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
        # Initialize LLM chat
        chat = LlmChat(
            api_key=os.environ.get('OPENAI_API_KEY'),
            session_id=f"portfolio_chat_{user.id}",
            system_message=system_message
        ).with_model("openai", "gpt-5")
        
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
    
    # Extract and update user context from conversation
    try:
        await extract_and_update_context(user.id, user_message, ai_response)
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
async def get_portfolio(user: User = Depends(require_auth)):
    portfolio = await db.portfolios.find_one({"user_id": user.id}, {"_id": 0})
    
    if not portfolio:
        # Create default portfolio
        portfolio_doc = {
            "_id": str(uuid.uuid4()),
            "user_id": user.id,
            "risk_tolerance": "medium",
            "roi_expectations": 10.0,
            "preferences": {},
            "allocations": get_default_allocations("medium"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.portfolios.insert_one(portfolio_doc)
        portfolio = await db.portfolios.find_one({"user_id": user.id}, {"_id": 0})
    
    # Convert dates
    if isinstance(portfolio.get('created_at'), str):
        portfolio['created_at'] = datetime.fromisoformat(portfolio['created_at'])
    if isinstance(portfolio.get('updated_at'), str):
        portfolio['updated_at'] = datetime.fromisoformat(portfolio['updated_at'])
    
    return portfolio

# News routes
@api_router.get("/news")
async def get_portfolio_news(user: User = Depends(require_auth)):
    portfolio = await db.portfolios.find_one({"user_id": user.id})
    
    if not portfolio or not portfolio.get('allocations'):
        return []
    
    # Get unique tickers
    tickers = list(set([alloc['ticker'] for alloc in portfolio['allocations'] if alloc['asset_type'] == 'Stocks']))
    
    all_news = []
    try:
        for ticker in tickers[:5]:  # Limit to 5 stocks to avoid rate limits
            try:
                news = finnhub_client.company_news(ticker, _from="2025-01-01", to="2025-12-31")
                for item in news[:3]:  # Top 3 news per stock
                    all_news.append({
                        "ticker": ticker,
                        "headline": item.get('headline', ''),
                        "summary": item.get('summary', ''),
                        "url": item.get('url', ''),
                        "image": item.get('image', ''),
                        "source": item.get('source', ''),
                        "datetime": datetime.fromtimestamp(item.get('datetime', 0), tz=timezone.utc) if item.get('datetime') else None
                    })
            except Exception as e:
                logger.error(f"Error fetching news for {ticker}: {e}")
                continue
    except Exception as e:
        logger.error(f"Finnhub error: {e}")
    
    # Sort by datetime
    all_news.sort(key=lambda x: x['datetime'] if x['datetime'] else datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    
    return all_news[:20]  # Return top 20 news items

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()