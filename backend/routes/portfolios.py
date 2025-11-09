"""Portfolio management routes"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Dict, Any
import uuid
from models.user import User
from models.portfolio import Portfolio
from models.chat import AcceptPortfolioRequest
from utils.database import db
from utils.dependencies import require_auth

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


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
