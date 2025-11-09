"""
Portfolio Context Builder
Builds comprehensive context for portfolio-specific LLM conversations
"""
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def build_portfolio_context(
    portfolio: Dict[str, Any],
    user_context: Dict[str, Any],
    chat_history: List[Dict[str, Any]],
    db
) -> str:
    """
    Build comprehensive context string for portfolio-specific LLM conversations
    
    Args:
        portfolio: Portfolio document from user_portfolios collection
        user_context: User context document
        chat_history: Recent chat messages for this portfolio
        db: Database instance
        
    Returns:
        Formatted context string for LLM
    """
    
    context_parts = []
    
    # ========== PORTFOLIO INFORMATION ==========
    context_parts.append("=== PORTFOLIO INFORMATION ===")
    context_parts.append(f"Portfolio Name: {portfolio.get('name', 'Unnamed Portfolio')}")
    
    if portfolio.get('goal'):
        context_parts.append(f"Portfolio Purpose/Goal: {portfolio['goal']}")
    
    context_parts.append(f"Portfolio Type: {portfolio.get('type', 'manual').upper()}")
    context_parts.append(f"Risk Tolerance: {portfolio.get('risk_tolerance', 'medium').upper()}")
    context_parts.append(f"Expected ROI: {portfolio.get('roi_expectations', 10)}% annually")
    
    if portfolio.get('investment_horizon'):
        context_parts.append(f"Investment Horizon: {portfolio['investment_horizon']}")
    
    context_parts.append("")
    
    # ========== USER DEMOGRAPHICS ==========
    context_parts.append("=== USER INFORMATION ===")
    
    if user_context:
        # Age
        if user_context.get('date_of_birth'):
            try:
                dob = user_context['date_of_birth']
                if isinstance(dob, str):
                    dob = datetime.fromisoformat(dob)
                age = (datetime.now() - dob).days // 365
                context_parts.append(f"User Age: {age} years old")
            except:
                pass
        elif user_context.get('age'):
            context_parts.append(f"User Age: {user_context['age']} years old")
        
        # Account Type
        if user_context.get('account_type'):
            context_parts.append(f"Account Type: {user_context['account_type']}")
        
        # Investment Experience
        if user_context.get('investment_experience'):
            context_parts.append(f"Investment Experience: {user_context['investment_experience']}")
        
        # Making for (self, family, institution)
        if user_context.get('making_for'):
            context_parts.append(f"Investing For: {user_context['making_for']}")
        
        context_parts.append("")
    
    # ========== INVESTMENT PREFERENCES ==========
    context_parts.append("=== INVESTMENT PREFERENCES ===")
    
    # Sector Preferences from portfolio or user context
    sector_prefs = []
    
    # Get from portfolio allocations
    if portfolio.get('allocations'):
        sectors = set()
        for alloc in portfolio['allocations']:
            if alloc.get('sector'):
                sectors.add(alloc['sector'])
        if sectors:
            sector_prefs.extend(list(sectors))
    
    # Get from user context
    if user_context:
        if user_context.get('sector_preferences'):
            prefs = user_context['sector_preferences']
            if isinstance(prefs, list):
                sector_prefs.extend(prefs)
            elif isinstance(prefs, str):
                sector_prefs.append(prefs)
        
        if user_context.get('preferred_sectors'):
            prefs = user_context['preferred_sectors']
            if isinstance(prefs, list):
                sector_prefs.extend(prefs)
    
    if sector_prefs:
        context_parts.append(f"Sector Preferences: {', '.join(set(sector_prefs))}")
    
    # Investment Strategy
    if user_context and user_context.get('investment_strategy'):
        context_parts.append(f"Investment Strategy: {user_context['investment_strategy']}")
    
    # Diversification Preference
    if user_context and user_context.get('diversification_preference'):
        context_parts.append(f"Diversification Preference: {user_context['diversification_preference']}")
    
    # Investment Style
    if user_context and user_context.get('investment_style'):
        context_parts.append(f"Investment Style: {user_context['investment_style']}")
    
    # Activity Level
    if user_context and user_context.get('activity_level'):
        context_parts.append(f"Activity Level: {user_context['activity_level']}")
    
    context_parts.append("")
    
    # ========== CURRENT PORTFOLIO COMPOSITION ==========
    context_parts.append("=== CURRENT PORTFOLIO COMPOSITION ===")
    
    # Target Allocations
    if portfolio.get('allocations'):
        context_parts.append("Target Allocations:")
        for alloc in portfolio['allocations']:
            ticker = alloc.get('ticker', 'Unknown')
            pct = alloc.get('allocation_percentage', 0)
            sector = alloc.get('sector', 'Unknown')
            asset_type = alloc.get('asset_type', 'stock')
            context_parts.append(f"  • {ticker}: {pct}% ({sector}, {asset_type})")
    
    context_parts.append("")
    
    # Actual Holdings (if invested)
    if portfolio.get('holdings') and len(portfolio['holdings']) > 0:
        context_parts.append("Actual Holdings:")
        for holding in portfolio['holdings']:
            ticker = holding.get('ticker', 'Unknown')
            shares = holding.get('shares', 0)
            current_price = holding.get('current_price', 0)
            cost_basis = holding.get('cost_basis', 0)
            current_value = holding.get('current_value', 0)
            
            gain_loss = current_value - cost_basis
            gain_loss_pct = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0
            
            context_parts.append(
                f"  • {ticker}: {shares:.4f} shares @ ${current_price:.2f} "
                f"(Value: ${current_value:.2f}, Return: {gain_loss_pct:+.2f}%)"
            )
        
        context_parts.append("")
        context_parts.append(f"Total Invested: ${portfolio.get('total_invested', 0):,.2f}")
        context_parts.append(f"Current Value: ${portfolio.get('current_value', 0):,.2f}")
        context_parts.append(f"Total Return: ${portfolio.get('total_return', 0):,.2f} ({portfolio.get('total_return_percentage', 0):.2f}%)")
    else:
        context_parts.append("Status: No investments yet (allocations only)")
    
    context_parts.append("")
    
    # ========== FINANCIAL GOALS & LIQUIDITY ==========
    if user_context and user_context.get('liquidity_requirements'):
        context_parts.append("=== FINANCIAL GOALS & LIQUIDITY NEEDS ===")
        
        liq_reqs = user_context['liquidity_requirements']
        if isinstance(liq_reqs, list):
            for req in liq_reqs:
                if isinstance(req, str):
                    context_parts.append(f"  • {req}")
                elif isinstance(req, dict):
                    goal_name = req.get('goal_name', req.get('goal', 'Goal'))
                    target_amount = req.get('target_amount', 0)
                    target_date = req.get('target_date', 'TBD')
                    context_parts.append(f"  • {goal_name}: ${target_amount:,.0f} by {target_date}")
        
        context_parts.append("")
    
    # ========== RECENT CHAT CONTEXT ==========
    if chat_history and len(chat_history) > 0:
        context_parts.append("=== RECENT CONVERSATION CONTEXT ===")
        context_parts.append(f"(Last {min(len(chat_history), 5)} messages)")
        
        # Get last 5 messages for context
        recent_messages = chat_history[-5:]
        for msg in recent_messages:
            role = msg.get('role', 'unknown')
            message = msg.get('message', '')
            # Truncate long messages
            if len(message) > 150:
                message = message[:150] + "..."
            context_parts.append(f"{role.upper()}: {message}")
        
        context_parts.append("")
    
    # ========== ADDITIONAL CONTEXT ==========
    if user_context:
        additional = []
        
        if user_context.get('monthly_investment'):
            additional.append(f"Monthly Investment: ${user_context['monthly_investment']}")
        
        if user_context.get('annual_investment'):
            additional.append(f"Annual Investment: ${user_context['annual_investment']}")
        
        if user_context.get('retirement_age'):
            additional.append(f"Target Retirement Age: {user_context['retirement_age']}")
        
        if additional:
            context_parts.append("=== ADDITIONAL INFORMATION ===")
            for item in additional:
                context_parts.append(item)
            context_parts.append("")
    
    # Join all parts
    full_context = "\n".join(context_parts)
    
    logger.info(f"Built portfolio context ({len(full_context)} characters)")
    
    return full_context


def build_portfolio_system_message(portfolio_context: str) -> str:
    """
    Build system message for portfolio-specific conversations
    
    Args:
        portfolio_context: Full context string from build_portfolio_context
        
    Returns:
        System message for LLM
    """
    
    system_message = f"""You are an expert financial advisor specializing in personalized portfolio management. You are currently advising on a specific portfolio with the following comprehensive context:

{portfolio_context}

YOUR ROLE:
- Provide personalized investment advice based on this specific portfolio
- Consider the user's age, risk tolerance, and financial goals
- Recommend adjustments to allocations when appropriate
- Explain your reasoning clearly and concisely
- Ask clarifying questions when needed
- Track the conversation context to provide continuity

GUIDELINES:
- Always reference the specific portfolio you're discussing
- Consider current holdings and their performance
- Align recommendations with stated goals and risk tolerance
- Be mindful of sector preferences and investment style
- Provide actionable, specific advice
- If suggesting changes, explain why and how to implement them

RESPONSE STYLE:
- Be conversational but professional
- Keep responses concise (2-4 paragraphs typically)
- Use bullet points for lists of recommendations
- Include specific tickers and percentages when suggesting changes
- Reference previous conversation points for continuity

Remember: You are advising on THIS specific portfolio with its unique goals, not providing general financial advice."""

    return system_message
