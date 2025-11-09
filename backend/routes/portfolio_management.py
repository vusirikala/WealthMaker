"""
Enhanced Portfolio Management Routes
Supports multiple portfolios per user with manual and AI-based creation
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import List, Dict, Any
import uuid
import logging
from models.user import User
from models.portfolio import UserPortfolio, CreatePortfolioRequest, InvestmentRequest, UpdateAllocationRequest
from services.portfolio_performance import calculate_portfolio_historical_returns

from utils.database import db
from utils.dependencies import require_auth
from services.shared_assets_db import shared_assets_service

router = APIRouter(prefix="/portfolios-v2", tags=["portfolio-management"])
logger = logging.getLogger(__name__)


@router.get("/list")
async def list_user_portfolios(user: User = Depends(require_auth)):
    """Get all portfolios for the current user"""
    cursor = db.user_portfolios.find({"user_id": user.id, "is_active": True})
    portfolios = []
    
    async for portfolio in cursor:
        # Convert ObjectId to string
        if '_id' in portfolio:
            portfolio['portfolio_id'] = str(portfolio['_id'])
            portfolio.pop('_id')
        portfolios.append(portfolio)
    
    return {
        "portfolios": portfolios,
        "count": len(portfolios)
    }


@router.get("/{portfolio_id}")
async def get_portfolio(portfolio_id: str, user: User = Depends(require_auth)):
    """Get a specific portfolio by ID"""
    portfolio = await db.user_portfolios.find_one({
        "_id": portfolio_id,
        "user_id": user.id,
        "is_active": True
    })
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Convert ObjectId to string
    if '_id' in portfolio:
        portfolio['portfolio_id'] = str(portfolio['_id'])
        portfolio.pop('_id')
    
    # Update current prices and values
    await update_portfolio_values(portfolio)
    
    return {"portfolio": portfolio}


@router.post("/create")
async def create_portfolio(
    request: CreatePortfolioRequest,
    user: User = Depends(require_auth)
):
    """Create a new portfolio (manual or AI-based)"""
    
    # Validate allocations if provided
    if request.allocations:
        total_allocation = sum(alloc.get('allocation_percentage', 0) for alloc in request.allocations)
        if abs(total_allocation - 100) > 0.1:  # Allow small rounding errors
            raise HTTPException(
                status_code=400, 
                detail=f"Allocations must sum to 100%. Current total: {total_allocation}%"
            )
    
    # Create portfolio document
    portfolio_doc = {
        "_id": str(uuid.uuid4()),
        "user_id": user.id,
        "name": request.name,
        "goal": request.goal,
        "type": request.type,
        "risk_tolerance": request.risk_tolerance,
        "roi_expectations": request.roi_expectations,
        "allocations": request.allocations,
        "holdings": [],
        "total_invested": 0.0,
        "current_value": 0.0,
        "total_return": 0.0,
        "total_return_percentage": 0.0,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "last_invested_at": None
    }
    
    await db.user_portfolios.insert_one(portfolio_doc)
    
    logger.info(f"Created portfolio '{request.name}' for user {user.id}")
    
    # Return created portfolio
    portfolio_doc['portfolio_id'] = portfolio_doc.pop('_id')
    
    return {
        "success": True,
        "message": f"Portfolio '{request.name}' created successfully",
        "portfolio": portfolio_doc
    }


@router.put("/{portfolio_id}")
async def update_portfolio(
    portfolio_id: str,
    request: CreatePortfolioRequest,
    user: User = Depends(require_auth)
):
    """Update an existing portfolio"""
    
    # Verify portfolio exists and belongs to user
    existing = await db.user_portfolios.find_one({
        "_id": portfolio_id,
        "user_id": user.id,
        "is_active": True
    })
    
    if not existing:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Validate allocations if provided
    if request.allocations:
        total_allocation = sum(alloc.get('allocation_percentage', 0) for alloc in request.allocations)
        if abs(total_allocation - 100) > 0.1:
            raise HTTPException(
                status_code=400,
                detail=f"Allocations must sum to 100%. Current total: {total_allocation}%"
            )
    
    # Update portfolio
    update_doc = {
        "name": request.name,
        "goal": request.goal,
        "risk_tolerance": request.risk_tolerance,
        "roi_expectations": request.roi_expectations,
        "allocations": request.allocations,
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.user_portfolios.update_one(
        {"_id": portfolio_id, "user_id": user.id},
        {"$set": update_doc}
    )
    
    logger.info(f"Updated portfolio {portfolio_id} for user {user.id}")
    
    return {
        "success": True,
        "message": "Portfolio updated successfully"
    }


@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: str,
    user: User = Depends(require_auth)
):
    """Soft delete a portfolio (mark as inactive)"""
    
    result = await db.user_portfolios.update_one(
        {"_id": portfolio_id, "user_id": user.id, "is_active": True},
        {"$set": {
            "is_active": False,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    logger.info(f"Deleted portfolio {portfolio_id} for user {user.id}")
    
    return {
        "success": True,
        "message": "Portfolio deleted successfully"
    }


@router.post("/{portfolio_id}/invest")
async def invest_in_portfolio(
    portfolio_id: str,
    request: InvestmentRequest,
    user: User = Depends(require_auth)
):
    """
    Invest a specific amount in a portfolio
    Calculates shares to purchase based on allocations and current prices
    """
    
    # Get portfolio
    portfolio = await db.user_portfolios.find_one({
        "_id": portfolio_id,
        "user_id": user.id,
        "is_active": True
    })
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    allocations = portfolio.get('allocations', [])
    if not allocations:
        raise HTTPException(status_code=400, detail="Portfolio has no allocations")
    
    # Validate total allocation
    total_allocation = sum(alloc.get('allocation_percentage', 0) for alloc in allocations)
    if abs(total_allocation - 100) > 0.1:
        raise HTTPException(
            status_code=400,
            detail=f"Portfolio allocations must sum to 100%. Current: {total_allocation}%"
        )
    
    # Get current prices for all tickers
    tickers = [alloc['ticker'] for alloc in allocations]
    assets_data = await shared_assets_service.get_assets_data(tickers)
    
    # Calculate investment for each allocation
    investments = []
    total_allocated = 0.0
    
    for alloc in allocations:
        ticker = alloc['ticker']
        allocation_pct = alloc['allocation_percentage']
        
        # Get current price
        asset = assets_data.get(ticker)
        if not asset:
            raise HTTPException(
                status_code=404,
                detail=f"Could not get price data for {ticker}"
            )
        
        current_price = asset.get('live', {}).get('currentPrice', {}).get('price', 0)
        if current_price <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid price for {ticker}: {current_price}"
            )
        
        # Calculate amount to invest in this ticker
        amount_for_ticker = request.amount * (allocation_pct / 100.0)
        
        # Calculate shares (support fractional shares)
        shares = amount_for_ticker / current_price
        
        # Round to 4 decimal places for fractional shares
        shares = round(shares, 4)
        actual_amount = shares * current_price
        
        investments.append({
            "ticker": ticker,
            "allocation_percentage": allocation_pct,
            "amount_allocated": amount_for_ticker,
            "current_price": current_price,
            "shares_purchased": shares,
            "actual_amount": actual_amount,
            "sector": alloc.get('sector', 'Unknown'),
            "asset_type": alloc.get('asset_type', 'stock')
        })
        
        total_allocated += actual_amount
    
    # Update or add to existing holdings
    existing_holdings = portfolio.get('holdings', [])
    
    for investment in investments:
        ticker = investment['ticker']
        
        # Find existing holding
        existing_holding = None
        for holding in existing_holdings:
            if holding.get('ticker') == ticker:
                existing_holding = holding
                break
        
        if existing_holding:
            # Update existing holding
            old_shares = existing_holding.get('shares', 0)
            old_cost_basis = existing_holding.get('cost_basis', 0)
            
            new_shares = old_shares + investment['shares_purchased']
            new_cost_basis = old_cost_basis + investment['actual_amount']
            avg_purchase_price = new_cost_basis / new_shares if new_shares > 0 else 0
            
            existing_holding['shares'] = new_shares
            existing_holding['cost_basis'] = new_cost_basis
            existing_holding['purchase_price'] = avg_purchase_price
            existing_holding['current_price'] = investment['current_price']
            existing_holding['current_value'] = new_shares * investment['current_price']
        else:
            # Add new holding
            existing_holdings.append({
                "ticker": ticker,
                "shares": investment['shares_purchased'],
                "purchase_price": investment['current_price'],
                "current_price": investment['current_price'],
                "cost_basis": investment['actual_amount'],
                "current_value": investment['actual_amount'],
                "sector": investment['sector'],
                "asset_type": investment['asset_type']
            })
    
    # Update portfolio totals
    new_total_invested = portfolio.get('total_invested', 0) + total_allocated
    new_current_value = sum(h['current_value'] for h in existing_holdings)
    new_total_return = new_current_value - new_total_invested
    new_total_return_pct = (new_total_return / new_total_invested * 100) if new_total_invested > 0 else 0
    
    # Update database
    await db.user_portfolios.update_one(
        {"_id": portfolio_id, "user_id": user.id},
        {"$set": {
            "holdings": existing_holdings,
            "total_invested": new_total_invested,
            "current_value": new_current_value,
            "total_return": new_total_return,
            "total_return_percentage": new_total_return_pct,
            "last_invested_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    logger.info(f"Invested ${total_allocated:.2f} in portfolio {portfolio_id} for user {user.id}")
    
    return {
        "success": True,
        "message": f"Successfully invested ${total_allocated:.2f}",
        "investments": investments,
        "portfolio_summary": {
            "total_invested": new_total_invested,
            "current_value": new_current_value,
            "total_return": new_total_return,
            "total_return_percentage": new_total_return_pct
        }
    }


@router.put("/{portfolio_id}/allocations")
async def update_allocations(
    portfolio_id: str,
    request: UpdateAllocationRequest,
    user: User = Depends(require_auth)
):
    """Update portfolio allocations"""
    
    # Verify portfolio exists
    portfolio = await db.user_portfolios.find_one({
        "_id": portfolio_id,
        "user_id": user.id,
        "is_active": True
    })
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Validate allocations
    total_allocation = sum(alloc.get('allocation_percentage', 0) for alloc in request.allocations)
    if abs(total_allocation - 100) > 0.1:
        raise HTTPException(
            status_code=400,
            detail=f"Allocations must sum to 100%. Current total: {total_allocation}%"
        )
    
    # Update allocations
    await db.user_portfolios.update_one(
        {"_id": portfolio_id, "user_id": user.id},
        {"$set": {
            "allocations": request.allocations,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return {
        "success": True,
        "message": "Allocations updated successfully"
    }


async def update_portfolio_values(portfolio: Dict[str, Any]):
    """Helper function to update portfolio with current prices"""
    holdings = portfolio.get('holdings', [])
    
    if not holdings:
        return
    
    # Get current prices
    tickers = [h['ticker'] for h in holdings]
    assets_data = await shared_assets_service.get_assets_data(tickers)
    
    # Update each holding with current price
    total_current_value = 0.0
    
    for holding in holdings:
        ticker = holding['ticker']
        asset = assets_data.get(ticker)
        
        if asset:
            current_price = asset.get('live', {}).get('currentPrice', {}).get('price', holding.get('current_price', 0))
            holding['current_price'] = current_price
            holding['current_value'] = holding['shares'] * current_price
            total_current_value += holding['current_value']
    
    # Update portfolio totals
    total_invested = portfolio.get('total_invested', 0)
    total_return = total_current_value - total_invested
    total_return_pct = (total_return / total_invested * 100) if total_invested > 0 else 0
    
    portfolio['current_value'] = total_current_value
    portfolio['total_return'] = total_return
    portfolio['total_return_percentage'] = total_return_pct



@router.get("/{portfolio_id}/export/csv")
async def export_portfolio_csv(
    portfolio_id: str,
    user: User = Depends(require_auth)
):
    """Export portfolio to CSV format"""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    # Get portfolio
    portfolio = await db.user_portfolios.find_one({
        "_id": portfolio_id,
        "user_id": user.id,
        "is_active": True
    })
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Update current values
    await update_portfolio_values(portfolio)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Portfolio Report'])
    writer.writerow(['Name', portfolio.get('name', 'Unnamed Portfolio')])
    writer.writerow(['Goal', portfolio.get('goal', 'N/A')])
    writer.writerow(['Risk Tolerance', portfolio.get('risk_tolerance', 'N/A')])
    writer.writerow(['Expected ROI', f"{portfolio.get('roi_expectations', 0)}%"])
    writer.writerow(['Created', portfolio.get('created_at', 'N/A')])
    writer.writerow([])
    
    # Summary statistics
    writer.writerow(['Portfolio Summary'])
    writer.writerow(['Total Invested', f"${portfolio.get('total_invested', 0):,.2f}"])
    writer.writerow(['Current Value', f"${portfolio.get('current_value', 0):,.2f}"])
    writer.writerow(['Total Return', f"${portfolio.get('total_return', 0):,.2f}"])
    writer.writerow(['Return %', f"{portfolio.get('total_return_percentage', 0):.2f}%"])
    writer.writerow([])
    
    # Holdings
    if portfolio.get('holdings'):
        writer.writerow(['Holdings'])
        writer.writerow(['Ticker', 'Shares', 'Purchase Price', 'Current Price', 'Cost Basis', 'Current Value', 'Gain/Loss', 'Return %'])
        
        for holding in portfolio['holdings']:
            gain_loss = holding['current_value'] - holding['cost_basis']
            return_pct = (gain_loss / holding['cost_basis'] * 100) if holding['cost_basis'] > 0 else 0
            
            writer.writerow([
                holding['ticker'],
                f"{holding['shares']:.4f}",
                f"${holding['purchase_price']:.2f}",
                f"${holding['current_price']:.2f}",
                f"${holding['cost_basis']:.2f}",
                f"${holding['current_value']:.2f}",
                f"${gain_loss:.2f}",
                f"{return_pct:.2f}%"
            ])
    
    # Allocations
    writer.writerow([])
    writer.writerow(['Target Allocations'])
    writer.writerow(['Ticker', 'Allocation %', 'Sector', 'Asset Type'])
    
    for alloc in portfolio.get('allocations', []):
        writer.writerow([
            alloc['ticker'],
            f"{alloc['allocation_percentage']}%",
            alloc.get('sector', 'Unknown'),
            alloc.get('asset_type', 'stock')
        ])
    
    # Prepare response
    output.seek(0)
    filename = f"{portfolio.get('name', 'portfolio').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{portfolio_id}/export/json")
async def export_portfolio_json(
    portfolio_id: str,
    user: User = Depends(require_auth)
):
    """Export portfolio to JSON format (for PDF generation on frontend)"""
    # Get portfolio
    portfolio = await db.user_portfolios.find_one({
        "_id": portfolio_id,
        "user_id": user.id,
        "is_active": True
    })
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Update current values
    await update_portfolio_values(portfolio)
    
    # Convert ObjectId to string
    if '_id' in portfolio:
        portfolio['portfolio_id'] = str(portfolio['_id'])
        portfolio.pop('_id')
    



@router.get("/{portfolio_id}/performance")
async def get_portfolio_performance(
    portfolio_id: str,
    time_period: str = "1y",
    user: User = Depends(require_auth)
):
    """
    Get historical performance data for a portfolio
    
    Query params:
    - time_period: '6m', '1y', '3y', or '5y' (default: '1y')
    """
    # Get portfolio
    portfolio = await db.user_portfolios.find_one({
        "_id": portfolio_id,
        "user_id": user.id,
        "is_active": True
    })
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    allocations = portfolio.get('allocations', [])
    if not allocations:
        return {
            "return_percentage": 0,
            "time_series": [],
            "period_stats": {
                '6m_return': 0,
                '1y_return': 0,
                '3y_return': 0,
                '5y_return': 0
            }
        }
    
    # Calculate historical returns
    try:
        performance_data = calculate_portfolio_historical_returns(
            allocations=allocations,
            time_period=time_period
        )
        
        return performance_data
        
    except Exception as e:
        logger.error(f"Error calculating portfolio performance: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to calculate portfolio performance"
        )

    # Convert dates to strings
    if 'created_at' in portfolio:
        portfolio['created_at'] = portfolio['created_at'].isoformat()
    if 'updated_at' in portfolio:
        portfolio['updated_at'] = portfolio['updated_at'].isoformat()
    if 'last_invested_at' in portfolio and portfolio['last_invested_at']:
        portfolio['last_invested_at'] = portfolio['last_invested_at'].isoformat()
    
    return {
        "portfolio": portfolio,
        "export_date": datetime.now(timezone.utc).isoformat()
    }

