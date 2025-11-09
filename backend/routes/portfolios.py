"""Portfolio management routes"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Dict, Any
import uuid
import logging
from models.user import User
from models.portfolio import Portfolio
from models.chat import AcceptPortfolioRequest
from utils.database import db
from utils.dependencies import require_auth

router = APIRouter(prefix="/portfolios", tags=["portfolios"])
logger = logging.getLogger(__name__)


# Existing portfolios management
@router.get("/existing")
async def get_existing_portfolios(user: User = Depends(require_auth)):
    """Get all existing portfolios for the user"""
    context = await db.user_context.find_one({"user_id": user.id})
    if not context or not context.get('existing_portfolios'):
        return {"portfolios": []}
    return {"portfolios": context.get('existing_portfolios', [])}


@router.post("/existing")
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


@router.put("/existing/{portfolio_id}")
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


@router.delete("/existing/{portfolio_id}")
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


@router.get("/existing/{portfolio_id}")
async def get_portfolio_by_id(portfolio_id: str, user: User = Depends(require_auth)):
    """Get a specific portfolio by ID"""
    context = await db.user_context.find_one({"user_id": user.id})
    
    if not context or not context.get('existing_portfolios'):
        raise HTTPException(status_code=404, detail="No portfolios found")
    
    for portfolio in context.get('existing_portfolios', []):
        if portfolio.get('portfolio_id') == portfolio_id:
            return {"portfolio": portfolio}
    
    raise HTTPException(status_code=404, detail="Portfolio not found")


# AI-generated portfolio management
@router.post("/accept")
async def accept_portfolio(accept_request: AcceptPortfolioRequest, user: User = Depends(require_auth)):
    """Accept an AI-generated portfolio suggestion"""
    portfolio_data = accept_request.portfolio_data
    portfolio_data["user_id"] = user.id
    portfolio_data["created_at"] = datetime.now(timezone.utc)
    portfolio_data["updated_at"] = datetime.now(timezone.utc)
    
    # Check if portfolio exists
    existing = await db.portfolios.find_one({"user_id": user.id})
    
    if existing:
        # Update existing portfolio
        await db.portfolios.update_one(
            {"user_id": user.id},
            {"$set": portfolio_data}
        )
    else:
        # Create new portfolio
        portfolio_data["_id"] = str(uuid.uuid4())
        await db.portfolios.insert_one(portfolio_data)
    
    return {"success": True, "message": "Portfolio saved successfully"}


@router.get("")
async def get_portfolio(user: User = Depends(require_auth)):
    """Get user's AI-generated portfolio"""
    portfolio = await db.portfolios.find_one({"user_id": user.id})
    if not portfolio:
        return None
    return portfolio



# Simple portfolio management - Add stocks easily
@router.post("/add-stock")
async def add_stock_to_portfolio(
    symbol: str,
    quantity: float,
    purchase_price: float,
    purchase_date: str = None,
    user: User = Depends(require_auth)
):
    """
    Simple endpoint to add a stock to user's portfolio
    
    Args:
        symbol: Stock ticker (e.g., AAPL, MSFT, BTC-USD)
        quantity: Number of shares
        purchase_price: Price per share when purchased
        purchase_date: Date of purchase (YYYY-MM-DD) - defaults to today
    
    This creates/updates a "My Portfolio" in existing_portfolios
    """
    from services.shared_assets_db import shared_assets_service
    
    symbol = symbol.upper()
    
    # Check if stock exists in shared database, if not add it
    asset_data = await shared_assets_service.get_single_asset(symbol)
    if not asset_data:
        # Auto-add this stock to shared database
        logger.info(f"Stock {symbol} not in database, adding it now...")
        result = await shared_assets_service.initialize_database([symbol])
        
        if result['initialized'] > 0:
            # Fetch the newly added asset
            asset_data = await shared_assets_service.get_single_asset(symbol)
            if not asset_data:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to add {symbol} to database"
                )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Stock {symbol} not found. Invalid ticker symbol."
            )
    
    # Get current price from asset data
    current_price = asset_data.get('live', {}).get('currentPrice', {}).get('price', purchase_price)
    
    # Calculate values
    cost_basis = quantity * purchase_price
    total_value = quantity * current_price
    unrealized_gain_loss = total_value - cost_basis
    unrealized_gain_loss_pct = ((total_value - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0
    
    # Create holding object
    new_holding = {
        "asset_id": str(uuid.uuid4()),
        "symbol": symbol,
        "asset_name": asset_data.get('name', symbol),
        "asset_type": asset_data.get('assetType', 'stock'),
        "sector": asset_data.get('fundamentals', {}).get('sector', 'Unknown'),
        "quantity": quantity,
        "purchase_price": purchase_price,
        "current_price": current_price,
        "total_value": total_value,
        "cost_basis": cost_basis,
        "unrealized_gain_loss": unrealized_gain_loss,
        "unrealized_gain_loss_percentage": round(unrealized_gain_loss_pct, 2),
        "allocation_percentage": 0,  # Will be calculated below
        "purchase_date": purchase_date or datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        "notes": ""
    }
    
    # Get user's context
    context = await db.user_context.find_one({"user_id": user.id})
    if not context:
        raise HTTPException(status_code=404, detail="User context not found")
    
    existing_portfolios = context.get('existing_portfolios', [])
    
    # Find or create "My Portfolio"
    my_portfolio = None
    portfolio_idx = -1
    
    for idx, portfolio in enumerate(existing_portfolios):
        if portfolio.get('portfolio_name') == 'My Portfolio':
            my_portfolio = portfolio
            portfolio_idx = idx
            break
    
    if not my_portfolio:
        # Create new portfolio
        my_portfolio = {
            "portfolio_id": str(uuid.uuid4()),
            "portfolio_name": "My Portfolio",
            "goal_name": "General Investment",
            "total_value": 0,
            "cost_basis": 0,
            "unrealized_gain_loss": 0,
            "unrealized_gain_loss_percentage": 0,
            "account_type": "brokerage",
            "account_provider": "WealthMaker",
            "is_tax_advantaged": False,
            "holdings": [],
            "allocation_summary": {},
            "sector_allocation": {},
            "performance_metrics": {},
            "last_rebalanced": None,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "notes": "Main investment portfolio"
        }
        existing_portfolios.append(my_portfolio)
        portfolio_idx = len(existing_portfolios) - 1
    
    # Check if symbol already exists in portfolio
    existing_holding_idx = -1
    for idx, holding in enumerate(my_portfolio.get('holdings', [])):
        if holding.get('symbol') == symbol:
            existing_holding_idx = idx
            break
    
    if existing_holding_idx >= 0:
        # Update existing holding (add to quantity)
        old_holding = my_portfolio['holdings'][existing_holding_idx]
        old_quantity = old_holding.get('quantity', 0)
        old_cost_basis = old_holding.get('cost_basis', 0)
        
        new_quantity = old_quantity + quantity
        new_cost_basis = old_cost_basis + cost_basis
        new_avg_price = new_cost_basis / new_quantity if new_quantity > 0 else purchase_price
        
        new_holding['quantity'] = new_quantity
        new_holding['cost_basis'] = new_cost_basis
        new_holding['purchase_price'] = new_avg_price  # Average price
        new_holding['total_value'] = new_quantity * current_price
        new_holding['unrealized_gain_loss'] = new_holding['total_value'] - new_cost_basis
        new_holding['unrealized_gain_loss_percentage'] = round(
            ((new_holding['total_value'] - new_cost_basis) / new_cost_basis * 100), 2
        ) if new_cost_basis > 0 else 0
        
        my_portfolio['holdings'][existing_holding_idx] = new_holding
    else:
        # Add new holding
        my_portfolio['holdings'].append(new_holding)
    
    # Recalculate portfolio totals
    total_value = sum(h.get('total_value', 0) for h in my_portfolio['holdings'])
    total_cost_basis = sum(h.get('cost_basis', 0) for h in my_portfolio['holdings'])
    
    my_portfolio['total_value'] = total_value
    my_portfolio['cost_basis'] = total_cost_basis
    my_portfolio['unrealized_gain_loss'] = total_value - total_cost_basis
    my_portfolio['unrealized_gain_loss_percentage'] = round(
        ((total_value - total_cost_basis) / total_cost_basis * 100), 2
    ) if total_cost_basis > 0 else 0
    
    # Recalculate allocation percentages
    for holding in my_portfolio['holdings']:
        holding['allocation_percentage'] = round(
            (holding.get('total_value', 0) / total_value * 100), 2
        ) if total_value > 0 else 0
    
    # Recalculate allocation summary
    allocation_summary = {}
    for holding in my_portfolio['holdings']:
        asset_type = holding.get('asset_type', 'other')
        allocation_pct = holding.get('allocation_percentage', 0)
        allocation_summary[asset_type] = allocation_summary.get(asset_type, 0) + allocation_pct
    my_portfolio['allocation_summary'] = allocation_summary
    
    # Recalculate sector allocation
    sector_allocation = {}
    for holding in my_portfolio['holdings']:
        sector = holding.get('sector', 'other')
        allocation_pct = holding.get('allocation_percentage', 0)
        sector_allocation[sector] = sector_allocation.get(sector, 0) + allocation_pct
    my_portfolio['sector_allocation'] = sector_allocation
    
    my_portfolio['last_updated'] = datetime.now(timezone.utc).isoformat()
    
    # Update in database
    existing_portfolios[portfolio_idx] = my_portfolio
    
    await db.user_context.update_one(
        {"user_id": user.id},
        {"$set": {
            "existing_portfolios": existing_portfolios,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return {
        "success": True,
        "message": f"Added {quantity} shares of {symbol} to your portfolio",
        "holding": new_holding,
        "portfolio_summary": {
            "total_value": total_value,
            "total_gain_loss": my_portfolio['unrealized_gain_loss'],
            "total_gain_loss_percentage": my_portfolio['unrealized_gain_loss_percentage']
        }
    }


@router.get("/my-portfolio")
async def get_my_portfolio(user: User = Depends(require_auth)):
    """
    Get user's main portfolio (created by add-stock endpoint)
    Returns complete portfolio with all holdings and current values
    """
    from services.shared_assets_db import shared_assets_service
    
    context = await db.user_context.find_one({"user_id": user.id})
    if not context:
        return {"portfolio": None, "message": "No portfolio found"}
    
    existing_portfolios = context.get('existing_portfolios', [])
    
    # Find "My Portfolio"
    my_portfolio = None
    for portfolio in existing_portfolios:
        if portfolio.get('portfolio_name') == 'My Portfolio':
            my_portfolio = portfolio
            break
    
    if not my_portfolio:
        return {
            "portfolio": None,
            "message": "No portfolio found. Use POST /portfolios/add-stock to add stocks."
        }
    
    # Get current prices for all holdings
    symbols = [h.get('symbol') for h in my_portfolio.get('holdings', [])]
    if symbols:
        assets_data = await shared_assets_service.get_assets_data(symbols)
        
        # Update current prices
        for holding in my_portfolio['holdings']:
            symbol = holding.get('symbol')
            if symbol in assets_data:
                asset = assets_data[symbol]
                current_price = asset.get('live', {}).get('currentPrice', {}).get('price', holding.get('current_price', 0))
                holding['current_price'] = current_price
                holding['total_value'] = holding.get('quantity', 0) * current_price
                
                # Recalculate gain/loss
                cost_basis = holding.get('cost_basis', 0)
                holding['unrealized_gain_loss'] = holding['total_value'] - cost_basis
                holding['unrealized_gain_loss_percentage'] = round(
                    ((holding['total_value'] - cost_basis) / cost_basis * 100), 2
                ) if cost_basis > 0 else 0
        
        # Recalculate portfolio totals
        total_value = sum(h.get('total_value', 0) for h in my_portfolio['holdings'])
        total_cost_basis = my_portfolio.get('cost_basis', 0)
        
        my_portfolio['total_value'] = total_value
        my_portfolio['unrealized_gain_loss'] = total_value - total_cost_basis
        my_portfolio['unrealized_gain_loss_percentage'] = round(
            ((total_value - total_cost_basis) / total_cost_basis * 100), 2
        ) if total_cost_basis > 0 else 0
    
    return {
        "portfolio": my_portfolio,
        "assets_data": assets_data if symbols else {}
    }
