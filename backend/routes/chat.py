"""Chat and AI conversation routes"""
from fastapi import APIRouter, Depends
from datetime import datetime, timezone, timedelta
from typing import List
import logging
import uuid
import json
import os
from emergentintegrations.llm.chat import LlmChat, UserMessage
from dateutil.relativedelta import relativedelta

from models.user import User
from models.chat import ChatRequest, ChatResponse, PortfolioSuggestion
from utils.database import db
from utils.dependencies import require_auth
from services.chat_helpers import (
    extract_and_update_context,
    analyze_context_completeness,
    generate_smart_question,
    get_default_allocations
)

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.get("/messages")
async def get_chat_messages(user: User = Depends(require_auth)):
    """Get chat history for user"""
    messages = await db.chat_messages.find(
        {"user_id": user.id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    
    for msg in messages:
        if isinstance(msg['timestamp'], str):
            msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
    
    return messages


@router.post("/send", response_model=ChatResponse)
async def send_message(chat_request: ChatRequest, user: User = Depends(require_auth)):
    """Send a message and get AI response"""
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
    
    # Build context string for AI
    context_info = build_context_string(user_context)
    
    # Analyze context completeness
    context_analysis = analyze_context_completeness(user_context)
    
    # Add completeness status
    context_info += "\n\n=== INFORMATION GATHERING STATUS ==="
    context_info += f"\n- Profile Completeness: {context_analysis['completeness_percentage']}%"
    context_info += f"\n- Ready for Portfolio Creation: {'YES' if context_analysis['is_ready_for_portfolio'] else 'NO - More information needed'}"
    
    if context_analysis['missing_critical']:
        context_info += f"\n- CRITICAL Missing Info: {len(context_analysis['missing_critical'])} fields"
    if context_analysis['missing_high']:
        context_info += f"\n- HIGH Priority Missing: {len(context_analysis['missing_high'])} fields"
    if context_analysis['missing_medium']:
        context_info += f"\n- OPTIONAL Missing: {len(context_analysis['missing_medium'])} fields"
    
    # Get current AI-generated portfolio
    portfolio_doc = await db.portfolios.find_one({"user_id": user.id})
    if portfolio_doc:
        context_info += f"\n\nCurrent Portfolio:\n- Risk Tolerance: {portfolio_doc.get('risk_tolerance', 'Not set')}\n- ROI Expectations: {portfolio_doc.get('roi_expectations', 'Not set')}%\n- Allocations: {len(portfolio_doc.get('allocations', []))} assets"
    
    # Check if we should ask a smart question
    smart_question = await generate_smart_question(user.id, user_context, chat_history)
    
    # Build system message
    system_message = build_system_message(context_info, context_analysis, user_context)
    
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
            ).with_model("openai", "gpt-5")
            
            llm_message = UserMessage(text=user_message)
            ai_response = await chat.send_message(llm_message)
        else:
            # Normal conversation flow
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


def build_context_string(user_context):
    """Build context information string for AI"""
    context_info = "\n\n=== USER CONTEXT & MEMORY ==="
    
    if user_context.get('portfolio_type'):
        context_info += f"\n- Portfolio Type: {user_context['portfolio_type']}"
    
    if user_context['portfolio_type'] == 'personal':
        if user_context.get('date_of_birth'):
            # Calculate age from date of birth
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
    
    # Add financial goals
    if user_context.get('liquidity_requirements'):
        context_info += "\n\n- FINANCIAL GOALS & LIQUIDITY NEEDS:"
        for req in user_context['liquidity_requirements']:
            goal_name = req.get('goal_name', req.get('goal', 'Goal'))
            target_amount = req.get('target_amount', req.get('amount', 0))
            amount_saved = req.get('amount_saved', 0)
            amount_needed = req.get('amount_needed', target_amount - amount_saved)
            target_date = req.get('target_date', req.get('when', 'TBD'))
            priority = req.get('priority', 'medium')
            progress = req.get('progress_percentage', 0)
            
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
    
    return context_info


def build_system_message(context_info, context_analysis, user_context):
    """Build comprehensive system message for AI"""
    # Determine portfolio type guidance
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
        conversation_mode = f"""
=== CURRENT MODE: INFORMATION GATHERING ===

You are in INFORMATION GATHERING mode. Your primary task is to collect essential information before making any portfolio recommendations.

CRITICAL RULES FOR THIS MODE:
1. DO NOT suggest any portfolio allocations yet - you don't have enough information
2. **ASK EXACTLY ONE (1) QUESTION PER MESSAGE** - This is mandatory, not a suggestion
3. NEVER list multiple questions in one response (no bullet points with multiple questions)
4. If you need multiple pieces of information, ask for them ONE AT A TIME across multiple messages
5. Keep your messages SHORT and CONVERSATIONAL (2-4 sentences max before your single question)
6. Acknowledge the user's previous answer briefly (1 sentence), then ask your next question
7. If the user mentions a complex goal (like retirement), give a brief 1-2 sentence acknowledgment, then ask the FIRST most important question only
8. If user asks about portfolios, explain you need more information first, then ask your next single question

CONVERSATION FLOW EXAMPLE:
- User: "I want to retire"
- You: "Great! Retirement planning is one of the most important goals. To help you create a solid plan, I need to understand a few key details. Let's start with the first one: What age are you hoping to retire at?"
- [Wait for response]
- User: "Age 65"
- You: "Perfect, age 65 gives us a clear timeline to work with. Next question: What annual income would you need in retirement to maintain your desired lifestyle?"
- [Continue one question at a time...]

YOUR NEXT QUESTION SHOULD BE ABOUT: {context_analysis['next_question']['field'] if context_analysis['next_question'] else 'general financial situation'}

DO NOT write lists like:
❌ "Here are the questions I need to ask: 1) ... 2) ... 3) ..."
✅ Instead, give brief context (1-2 sentences) and ask ONE question only
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
    
    # Create comprehensive system message
    system_message = f"""You are an expert financial advisor helping users build and manage their investment portfolio.{context_info}

{conversation_mode}

{portfolio_type_guidance}

Your role:
1. Understand user's investment preferences and continuously build their context/memory
2. Extract and remember key information about their financial situation, goals, and preferences
3. Ask smart, contextual questions based on what information is missing
4. **CRITICAL: Ask ONLY ONE question per response when gathering information** - Never list multiple questions
5. ONLY recommend portfolios when you have sufficient information (Ready for Portfolio Creation: YES)
6. Explain your recommendations in clear, simple terms
7. Keep responses concise and conversational (avoid long paragraphs or lists of questions)

When recommending portfolios:
- For LOW risk: 60-70% bonds, 20-30% blue-chip stocks, 5-10% index funds
- For MEDIUM risk: 40% stocks, 30% bonds, 20% index funds, 10% alternative investments
- For HIGH risk: 50-60% growth stocks, 20% crypto, 10-15% emerging markets, 10% bonds

IMPORTANT INSTRUCTIONS:
1. ONLY create a portfolio suggestion when:
   - Profile Completeness is at least 70% AND Ready for Portfolio Creation is YES
   - User explicitly requests a portfolio (new or updated)
   - You have enough information about their goals, risk tolerance, and investment amount
   
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

3. For general questions, portfolio discussions, or clarifications, respond normally WITHOUT the portfolio suggestion marker.

Always provide specific ticker symbols (e.g., AAPL, MSFT, BTC-USD, SPY) and allocation percentages when making recommendations.

Respond in a friendly, professional tone. Keep responses concise but informative."""
    
    return system_message
