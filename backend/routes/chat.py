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
from services.portfolio_context_builder import (
    build_portfolio_context,
    build_portfolio_system_message
)

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.get("/messages")
async def get_chat_messages(
    portfolio_id: str = None,
    user: User = Depends(require_auth)
):
    """Get chat history for user, optionally filtered by portfolio_id"""
    query = {"user_id": user.id}
    
    # Filter by portfolio_id if provided
    if portfolio_id:
        logger.info(f"Loading chat messages for user {user.id}, portfolio {portfolio_id}")
        query["portfolio_id"] = portfolio_id
    else:
        logger.info(f"Loading global chat messages for user {user.id}")
        # Get global chat messages (messages without portfolio_id)
        query["portfolio_id"] = {"$exists": False}
    
    messages = await db.chat_messages.find(
        query,
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    
    logger.info(f"Found {len(messages)} messages for query: {query}")
    
    for msg in messages:
        if isinstance(msg['timestamp'], str):
            msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
    
    return messages


@router.post("/send", response_model=ChatResponse)
async def send_message(chat_request: ChatRequest, user: User = Depends(require_auth)):
    """Send a message and get AI response"""
    user_message = chat_request.message
    portfolio_id = chat_request.portfolio_id
    
    logger.info(f"CHAT SEND - User: {user.id}, Portfolio ID: {portfolio_id}, Message: {user_message[:50]}...")
    
    # Build query for chat history (portfolio-specific or global)
    history_query = {"user_id": user.id}
    if portfolio_id:
        logger.info(f"Building query for portfolio-specific chat: {portfolio_id}")
        history_query["portfolio_id"] = portfolio_id
    else:
        logger.info("Building query for global chat (no portfolio)")
        history_query["portfolio_id"] = {"$exists": False}
    
    # Get chat history FIRST to check if this is first message
    chat_history = await db.chat_messages.find(
        history_query,
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
    
    # Add portfolio_id if provided
    if portfolio_id:
        user_msg_doc["portfolio_id"] = portfolio_id
        logger.info(f"Saving user message WITH portfolio_id: {portfolio_id}")
    else:
        logger.info("Saving user message WITHOUT portfolio_id (global chat)")
    
    await db.chat_messages.insert_one(user_msg_doc)
    logger.info(f"User message saved to database")
    
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
    
    # Check if this is portfolio-specific chat
    portfolio_doc = None
    if portfolio_id:
        logger.info(f"Loading portfolio context for portfolio_id: {portfolio_id}")
        portfolio_doc = await db.user_portfolios.find_one({
            "_id": portfolio_id,
            "user_id": user.id,
            "is_active": True
        })
        
        if portfolio_doc:
            logger.info(f"Found portfolio: {portfolio_doc.get('name')}")
    
    # Build context string for AI
    if portfolio_doc:
        # Portfolio-specific context
        logger.info("Building portfolio-specific context")
        context_info = await build_portfolio_context(
            portfolio=portfolio_doc,
            user_context=user_context,
            chat_history=chat_history,
            db=db
        )
    else:
        # Global chat context
        logger.info("Building global chat context")
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
    
    # Check if we should ask a smart question (only for global chat)
    smart_question = None
    if not portfolio_doc:
        smart_question = await generate_smart_question(user.id, user_context, chat_history)
    
    # Build system message
    if portfolio_doc:
        # Portfolio-specific system message
        logger.info("Using portfolio-specific system message")
        system_message = build_portfolio_system_message(context_info)
    else:
        # Global chat system message
        logger.info("Using global chat system message")
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
    
    # Add portfolio_id if provided
    if portfolio_id:
        ai_msg_doc["portfolio_id"] = portfolio_id
        logger.info(f"Saving AI response WITH portfolio_id: {portfolio_id}")
    else:
        logger.info("Saving AI response WITHOUT portfolio_id (global chat)")
    
    await db.chat_messages.insert_one(ai_msg_doc)
    logger.info(f"AI response saved to database")
    
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
    
    if user_context.get('portfolio_type') == 'personal':
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
    
    # Add financial goals
    if user_context.get('liquidity_requirements'):
        context_info += "\n\n- FINANCIAL GOALS & LIQUIDITY NEEDS:"
        for req in user_context['liquidity_requirements']:
            # Handle both dict and string formats
            if isinstance(req, str):
                context_info += f"\n  * {req}"
                continue
            
            if not isinstance(req, dict):
                continue
                
            goal_name = req.get('goal_name', req.get('goal', 'Goal'))
            target_amount = req.get('target_amount', req.get('amount', 0)) or 0
            amount_saved = req.get('amount_saved', 0) or 0
            amount_needed = req.get('amount_needed', target_amount - amount_saved) or 0
            target_date = req.get('target_date', req.get('when', 'TBD'))
            priority = req.get('priority', 'medium')
            progress = req.get('progress_percentage', 0) or 0
            
            context_info += f"\n  * {goal_name} ({priority} priority)"
            if target_amount > 0:
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

**FORMATTING RULES:**
- When gathering information: Brief context (1-2 sentences) + ONE single question
- Never use numbered lists of questions (e.g., "1) What is... 2) When do... 3) How much...")
- Never say "Quick questions:" or "Key questions:" followed by multiple questions
- If you have many things to ask about, choose the MOST IMPORTANT one and ask only that
- Wait for the user's answer before asking the next question

Always provide specific ticker symbols (e.g., AAPL, MSFT, BTC-USD, SPY) and allocation percentages when making recommendations.

Respond in a friendly, professional tone. Keep responses SHORT and CONVERSATIONAL - avoid overwhelming users with information."""
    
    return system_message



@router.post("/generate-portfolio")
async def generate_portfolio(
    request: dict,
    user: User = Depends(require_auth)
):
    """
    Generate AI portfolio suggestions based on user preferences
    Used by AI Portfolio Builder
    """
    portfolio_name = request.get('portfolio_name', 'My Portfolio')
    goal = request.get('goal', '')
    risk_tolerance = request.get('risk_tolerance', 'medium')
    investment_amount = request.get('investment_amount', 0)
    time_horizon = request.get('time_horizon', '5-10')
    roi_expectations = request.get('roi_expectations', 10)
    sector_preferences = request.get('sector_preferences', '')
    
    # Build prompt for AI
    prompt = f"""Based on the following portfolio requirements, generate a diversified investment portfolio:

Portfolio Details:
- Name: {portfolio_name}
- Goal: {goal}
- Risk Tolerance: {risk_tolerance}
- Investment Amount: ${investment_amount}
- Time Horizon: {time_horizon} years
- Expected ROI: {roi_expectations}% annually
- Sector Preferences: {sector_preferences if sector_preferences else 'No specific preferences'}

Please provide:
1. A brief reasoning (2-3 sentences) explaining the strategy
2. 5-8 specific stock/ETF allocations with:
   - Ticker symbol (e.g., AAPL, MSFT, SPY, BND)
   - Allocation percentage (must sum to 100%)
   - Sector
   - Asset type (stock, bond, etf, crypto, etc.)

Format your response EXACTLY as JSON like this:
{{
  "reasoning": "Your brief explanation here",
  "allocations": [
    {{"ticker": "AAPL", "allocation_percentage": 25, "sector": "Technology", "asset_type": "stock"}},
    {{"ticker": "MSFT", "allocation_percentage": 20, "sector": "Technology", "asset_type": "stock"}}
  ]
}}

Based on risk tolerance:
- LOW risk: Focus on bonds (60-70%), blue-chip stocks (20-30%), minimal volatility
- MEDIUM risk: Balanced mix of stocks (40%), bonds (30%), ETFs (20%), alternatives (10%)
- HIGH risk: Growth stocks (50-60%), emerging markets (20%), crypto (10%), bonds (10%)

IMPORTANT: Return ONLY valid JSON, no additional text."""

    try:
        # Call LLM to generate portfolio
        llm_chat = LlmChat()
        response = llm_chat.generate(
            [UserMessage(content=prompt)],
            model="gpt-4o",
            temperature=0.7
        )
        
        ai_response = response.content
        
        # Try to extract JSON from response
        try:
            # Find JSON in response (between { and })
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx]
                portfolio_data = json.loads(json_str)
                
                # Validate allocations sum to ~100%
                total = sum(alloc.get('allocation_percentage', 0) for alloc in portfolio_data.get('allocations', []))
                if abs(total - 100) > 1:
                    logger.warning(f"Portfolio allocations sum to {total}%, adjusting...")
                    # Normalize to 100%
                    for alloc in portfolio_data['allocations']:
                        alloc['allocation_percentage'] = round(alloc['allocation_percentage'] * 100 / total, 1)
                
                logger.info(f"Generated AI portfolio for user {user.id}: {len(portfolio_data.get('allocations', []))} allocations")
                
                return {
                    "success": True,
                    "portfolio_suggestion": portfolio_data
                }
            else:
                raise ValueError("No valid JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"AI Response: {ai_response}")
            
            # Fallback to default allocation based on risk tolerance
            default_allocations = get_default_allocations(risk_tolerance)
            
            return {
                "success": True,
                "portfolio_suggestion": {
                    "reasoning": f"Based on your {risk_tolerance} risk tolerance and {time_horizon} year time horizon, here's a balanced portfolio.",
                    "allocations": default_allocations
                }
            }
            
    except Exception as e:
        logger.error(f"Error generating portfolio: {e}")
        
        # Return default allocations as fallback
        default_allocations = get_default_allocations(risk_tolerance)
        
        return {
            "success": True,
            "portfolio_suggestion": {
                "reasoning": f"Based on your {risk_tolerance} risk tolerance, here's a recommended portfolio allocation.",
                "allocations": default_allocations
            }
        }



@router.post("/portfolio-recommendations")
async def get_portfolio_recommendations(
    request: dict,
    user: User = Depends(require_auth)
):
    """
    Get AI-powered recommendations for investment sectors and strategies
    based on user's portfolio preferences
    """
    try:
        # Extract parameters
        goal = request.get("goal", "")
        risk_tolerance = request.get("risk_tolerance", "medium")
        roi_expectations = request.get("roi_expectations", 10)
        time_horizon = request.get("time_horizon", "5-10")
        investment_amount = request.get("investment_amount", 0)
        monitoring_frequency = request.get("monitoring_frequency", "monthly")
        
        # Build comprehensive prompt for LLM with detailed context
        prompt = f"""You are an expert financial advisor with deep knowledge of portfolio management, asset allocation, and investment strategies. Analyze the user's specific situation and provide highly personalized investment recommendations.

USER PROFILE:
- Investment Goal: "{goal}"
- Risk Tolerance: {risk_tolerance.upper()}
- Expected Annual Return Target: {roi_expectations}%
- Time Horizon: {time_horizon} years
- Initial Investment Amount: ${investment_amount:,.2f}
- Portfolio Monitoring Frequency: {monitoring_frequency}

YOUR TASK:
Provide a tailored sector allocation and strategy recommendation that directly addresses this user's specific goal and constraints.

SECTOR ALLOCATION GUIDELINES:
1. Stocks & Equities (8-12% historical average, high volatility 20-40% swings)
   - Use for growth, long time horizons, higher risk tolerance
   - Key consideration: Market volatility, company-specific risks

2. Bonds & Fixed Income (3-6% returns, low-medium volatility 5-15% swings)
   - Use for stability, income generation, capital preservation
   - Key consideration: Interest rate risk, inflation protection

3. Cryptocurrency (-50% to +300% annual range, extreme 50-100%+ volatility)
   - Only for very high risk tolerance, typically 0-10% of portfolio
   - Key consideration: Regulatory uncertainty, extreme volatility

4. Real Estate & REITs (6-10% with income, medium 10-25% volatility)
   - Good for diversification, inflation hedge, income
   - Key consideration: Interest rate sensitivity, liquidity

5. Commodities & Precious Metals (3-8% variable, high 20-40% volatility)
   - Portfolio diversification, inflation protection
   - Key consideration: No income generation, storage costs

6. Foreign Exchange/Forex (highly variable, very high risk)
   - Typically 0% for most investors (professional traders only)
   - Key consideration: Extreme leverage risk, requires active management

STRATEGY ALIGNMENT (Select 2-3 that best match user profile):
- value_investing: Low-Medium risk, 8-15% ROI, 3-10 year horizon, requires patience and analysis skills
  * Best for: Patient investors, long-term holders, those who understand fundamentals
  * Monitoring: Monthly/Quarterly sufficient
  
- growth_investing: Medium-High risk, 15-30% ROI, 3-7 year horizon, for capital appreciation
  * Best for: Risk-tolerant investors, believers in innovation, tech-focused
  * Monitoring: Weekly/Monthly recommended
  
- income_investing: Low-Medium risk, 5-10% ROI + dividends, 5+ years, for steady income
  * Best for: Retirees, income seekers, conservative investors
  * Monitoring: Quarterly/Annually sufficient
  
- index_funds: Low-Medium risk, 8-12% ROI, 5+ years, passive approach, lowest effort
  * Best for: Beginners, passive investors, those seeking market returns
  * Monitoring: Quarterly/Annually sufficient
  
- dollar_cost_averaging: Low risk, matches underlying assets, 5+ years, reduces timing risk
  * Best for: Regular savers, those with consistent income, risk-averse
  * Monitoring: Set-and-forget (automated)
  
- momentum_investing: High risk, 20-50% ROI (volatile), 6mo-3yr, requires active monitoring
  * Best for: Active traders, experienced investors, those with time to monitor
  * Monitoring: Daily/Weekly REQUIRED

ANALYSIS FRAMEWORK:
1. Parse the user's goal to understand specific objective (retirement, home purchase, wealth building, etc.)
2. Match time horizon with appropriate asset allocation (longer = more stocks, shorter = more bonds)
3. Align risk tolerance with volatility exposure
4. Ensure ROI expectations are realistic given the allocation
5. Match monitoring frequency to strategy complexity:
   - Daily/Weekly → Can handle momentum_investing, growth_investing
   - Monthly → growth_investing, value_investing, index_funds work well
   - Quarterly/Annually → ONLY passive strategies (index_funds, income_investing, dollar_cost_averaging)
6. Select strategies that complement the sector allocation:
   - High stocks allocation → growth_investing or value_investing
   - High bonds allocation → income_investing
   - Balanced allocation → index_funds + dollar_cost_averaging
   - Crypto/volatile mix → momentum_investing (only if daily/weekly monitoring)
7. Consider investment amount for diversification requirements

OUTPUT FORMAT (JSON only, no markdown):
{{
  "sector_allocation": {{
    "stocks": <percentage 0-100>,
    "bonds": <percentage 0-100>,
    "crypto": <percentage 0-100>,
    "real_estate": <percentage 0-100>,
    "commodities": <percentage 0-100>,
    "forex": <percentage 0-100>
  }},
  "recommended_strategies": ["strategy_id_1", "strategy_id_2"],
  "reasoning": "2-3 sentences explaining how this allocation specifically addresses the user's goal '{goal}', matches their {risk_tolerance} risk tolerance, targets {roi_expectations}% return over {time_horizon} years, and aligns with {monitoring_frequency} monitoring. Be specific about why each sector percentage was chosen.",
  "strategy_reasoning": "1-2 sentences explaining specifically WHY these {len(recommended_strategies)} strategies were chosen. Mention: 1) how they match the monitoring frequency ({monitoring_frequency}), 2) how they complement the sector allocation, 3) how they align with the user's goal and risk profile."
}}

CRITICAL REQUIREMENTS:
- Sector percentages MUST sum to exactly 100
- Reasoning MUST reference the user's specific goal and all key parameters
- Recommend 2-3 strategies that match risk tolerance, time horizon, AND monitoring frequency
- Strategy selection MUST respect monitoring frequency constraints:
  * Quarterly/Annually monitoring → CANNOT recommend momentum_investing
  * Daily/Weekly monitoring → CAN recommend any strategy
  * Monthly → Can recommend all except momentum_investing (unless very active goal)
- Be realistic: Don't promise 20% returns with low risk or conservative allocations
- Forex should be 0% unless user explicitly mentions currency trading experience
- Crypto should be 0-10% max, higher only for high/very high risk tolerance
- Provide specific, actionable reasoning tied to the user's situation
- strategy_reasoning must explain the logical connection between strategies and user's monitoring capability"""

        # Call LLM
        llm = LlmChat(
            api_key=os.environ.get("EMERGENT_LLM_KEY"),
            model="gpt-4o-mini"
        )
        
        messages = [UserMessage(content=prompt)]
        ai_response = llm.chat(messages=messages)
        
        logger.info(f"LLM recommendation response: {ai_response}")
        
        # Parse JSON from response
        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in ai_response:
                json_str = ai_response.split("```json")[1].split("```")[0].strip()
            elif "```" in ai_response:
                json_str = ai_response.split("```")[1].split("```")[0].strip()
            else:
                json_str = ai_response.strip()
            
            recommendations = json.loads(json_str)
            
            # Validate sector allocation sums to 100
            sector_total = sum(recommendations["sector_allocation"].values())
            if abs(sector_total - 100) > 1:  # Allow 1% tolerance
                # Normalize to 100
                factor = 100 / sector_total
                for sector in recommendations["sector_allocation"]:
                    recommendations["sector_allocation"][sector] = round(
                        recommendations["sector_allocation"][sector] * factor, 1
                    )
            
            logger.info(f"Generated recommendations for user {user.id}")
            
            return {
                "success": True,
                "recommendations": recommendations
            }
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"LLM Response: {ai_response}")
            
            # Sophisticated fallback recommendations based on all parameters
            time_years = 5  # default
            if time_horizon == "0-3":
                time_years = 2
            elif time_horizon == "3-5":
                time_years = 4
            elif time_horizon == "5-10":
                time_years = 7
            elif time_horizon == "10+":
                time_years = 15
            
            # Calculate allocation based on multiple factors
            if risk_tolerance == "low":
                # Conservative allocation
                stocks_pct = min(40, 20 + time_years * 1)  # More stocks for longer horizon
                bonds_pct = 60 - stocks_pct
                sector_allocation = {
                    "stocks": stocks_pct,
                    "bonds": bonds_pct,
                    "crypto": 0,
                    "real_estate": 15,
                    "commodities": 5,
                    "forex": 0
                }
                strategies = ["income_investing", "dollar_cost_averaging"]
                reason = f"Conservative allocation emphasizing bonds ({bonds_pct}%) for stability while maintaining some growth through stocks ({stocks_pct}%). Real estate (15%) provides diversification and income. Suitable for your {risk_tolerance} risk profile and {goal}."
                
            elif risk_tolerance == "high":
                # Aggressive allocation
                stocks_pct = min(75, 50 + time_years * 2)  # More aggressive with longer time
                crypto_pct = 10 if time_years >= 5 else 5
                bonds_pct = 100 - stocks_pct - crypto_pct - 10 - 5  # remainder after other allocations
                sector_allocation = {
                    "stocks": stocks_pct,
                    "bonds": max(5, bonds_pct),
                    "crypto": crypto_pct,
                    "real_estate": 10,
                    "commodities": 5,
                    "forex": 0
                }
                strategies = ["growth_investing", "momentum_investing"] if monitoring_frequency in ["daily", "weekly"] else ["growth_investing", "index_funds"]
                reason = f"Aggressive allocation with {stocks_pct}% stocks for maximum growth potential over your {time_horizon} horizon. Crypto ({crypto_pct}%) adds high-risk/high-reward exposure. Targets your {roi_expectations}% return goal with acceptance of higher volatility. Matches your {monitoring_frequency} monitoring capability."
                
            else:  # medium
                # Balanced allocation
                stocks_pct = min(60, 40 + time_years * 2)
                bonds_pct = 35 - (time_years - 5) if time_years > 5 else 35
                crypto_pct = 5 if roi_expectations > 10 else 0
                sector_allocation = {
                    "stocks": stocks_pct,
                    "bonds": bonds_pct,
                    "crypto": crypto_pct,
                    "real_estate": 10,
                    "commodities": 5,
                    "forex": 0
                }
                strategies = ["index_funds", "dollar_cost_averaging"]
                reason = f"Balanced 60/40-style allocation with {stocks_pct}% stocks for growth and {bonds_pct}% bonds for stability. Well-suited for your {time_horizon} time frame and {roi_expectations}% return target. Real estate (10%) and commodities (5%) provide additional diversification to help achieve your goal: {goal}."
            
            return {
                "success": True,
                "recommendations": {
                    "sector_allocation": sector_allocation,
                    "recommended_strategies": strategies,
                    "reasoning": reason
                }
            }
            
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        
        # Return personalized fallback based on available data
        risk_level = request.get("risk_tolerance", "medium")
        time_frame = request.get("time_horizon", "5-10")
        user_goal = request.get("goal", "build wealth")
        
        if risk_level == "low":
            allocation = {"stocks": 35, "bonds": 45, "crypto": 0, "real_estate": 15, "commodities": 5, "forex": 0}
            strats = ["income_investing", "dollar_cost_averaging"]
        elif risk_level == "high":
            allocation = {"stocks": 65, "bonds": 10, "crypto": 10, "real_estate": 10, "commodities": 5, "forex": 0}
            strats = ["growth_investing", "index_funds"]
        else:
            allocation = {"stocks": 50, "bonds": 30, "crypto": 5, "real_estate": 10, "commodities": 5, "forex": 0}
            strats = ["index_funds", "dollar_cost_averaging"]
        
        return {
            "success": True,
            "recommendations": {
                "sector_allocation": allocation,
                "recommended_strategies": strats,
                "reasoning": f"Based on your {risk_level} risk tolerance over a {time_frame} timeframe, this balanced allocation aims to help you achieve your goal: {user_goal}. The mix provides growth potential while managing risk appropriately."
            }
        }

