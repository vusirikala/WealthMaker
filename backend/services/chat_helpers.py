"""Helper functions for chat service"""
from datetime import datetime, timezone
from typing import Dict, Any, List
import logging
import uuid
import json
import re
import os
from emergentintegrations.llm.chat import LlmChat, UserMessage
from utils.database import db

logger = logging.getLogger(__name__)


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
  "liquidity_requirements": [goals array] or null,
  "sector_preferences": {{}} or null,
  "institution_name": "string or null",
  "institution_sector": "string or null",
  "annual_revenue": number or null,
  "annual_profit": number or null,
  "retirement_plans": "string or null",
  "making_for": "self or someone_else (null if not mentioned)",
  "existing_investments": {{}} or null,
  "existing_portfolios": [portfolios array] or null
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

I see you've provided some initial information - great start! You're looking for a {user_context.get('risk_tolerance', 'moderate')} risk portfolio with a target return of {user_context.get('roi_expectations', 'N/A')}%.

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


def get_default_allocations(risk_tolerance: str) -> List[Dict[str, Any]]:
    """Generate default portfolio allocations based on risk tolerance"""
    if risk_tolerance == 'low':
        return [
            {"asset_type": "bond", "ticker": "AGG", "allocation_percentage": 60, "sector": "Fixed Income"},
            {"asset_type": "stock", "ticker": "AAPL", "allocation_percentage": 15, "sector": "Technology"},
            {"asset_type": "stock", "ticker": "JNJ", "allocation_percentage": 15, "sector": "Healthcare"},
            {"asset_type": "etf", "ticker": "SPY", "allocation_percentage": 10, "sector": "Diversified"}
        ]
    elif risk_tolerance == 'high':
        return [
            {"asset_type": "stock", "ticker": "TSLA", "allocation_percentage": 25, "sector": "Technology"},
            {"asset_type": "stock", "ticker": "NVDA", "allocation_percentage": 25, "sector": "Technology"},
            {"asset_type": "crypto", "ticker": "BTC-USD", "allocation_percentage": 20, "sector": "Cryptocurrency"},
            {"asset_type": "stock", "ticker": "PLTR", "allocation_percentage": 15, "sector": "Technology"},
            {"asset_type": "bond", "ticker": "AGG", "allocation_percentage": 10, "sector": "Fixed Income"},
            {"asset_type": "etf", "ticker": "QQQ", "allocation_percentage": 5, "sector": "Technology"}
        ]
    else:  # medium
        return [
            {"asset_type": "stock", "ticker": "AAPL", "allocation_percentage": 20, "sector": "Technology"},
            {"asset_type": "stock", "ticker": "MSFT", "allocation_percentage": 15, "sector": "Technology"},
            {"asset_type": "bond", "ticker": "AGG", "allocation_percentage": 30, "sector": "Fixed Income"},
            {"asset_type": "etf", "ticker": "SPY", "allocation_percentage": 20, "sector": "Diversified"},
            {"asset_type": "stock", "ticker": "V", "allocation_percentage": 10, "sector": "Financial"},
            {"asset_type": "etf", "ticker": "VTI", "allocation_percentage": 5, "sector": "Diversified"}
        ]
