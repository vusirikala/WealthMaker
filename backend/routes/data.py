"""
Data routes - Historical and live market data
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from models.user import User
from utils.dependencies import require_auth
from services.historical_data import historical_data_service
from services.live_data import live_data_service
import logging

router = APIRouter(prefix="/data", tags=["data"])
logger = logging.getLogger(__name__)


@router.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    force_refresh: bool = Query(False, description="Force refresh data from source"),
    user: User = Depends(require_auth)
):
    """
    Get comprehensive historical data for a stock (3 years)
    
    Returns:
    - Company information
    - 3-year price history and metrics
    - Earnings history
    - Analyst ratings
    - Fundamental ratios
    """
    symbol = symbol.upper()
    
    data = await historical_data_service.get_stock_data(symbol, force_refresh)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"Could not fetch data for symbol {symbol}")
    
    return data


@router.post("/historical/batch")
async def get_historical_data_batch(
    symbols: List[str],
    force_refresh: bool = False,
    user: User = Depends(require_auth)
):
    """
    Get historical data for multiple stocks at once
    
    Body:
    - symbols: List of stock ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
    - force_refresh: Whether to force refresh data
    
    Returns dictionary mapping symbols to their historical data
    """
    symbols = [s.upper() for s in symbols]
    
    results = await historical_data_service.get_multiple_stocks(symbols, force_refresh)
    
    return {
        "count": len(results),
        "data": results
    }


@router.get("/search")
async def search_stocks(
    q: str = Query(..., min_length=1, description="Search query (symbol or company name)"),
    user: User = Depends(require_auth)
):
    """
    Search for stocks by symbol or company name
    
    Returns list of matching stocks with basic information
    """
    results = await historical_data_service.search_stock(q)
    
    return {
        "query": q,
        "results": results
    }


@router.post("/track")
async def add_stock_to_track(
    symbol: str,
    user: User = Depends(require_auth)
):
    """
    Add a stock to track for this user
    This triggers initial historical data fetch and adds to user's watchlist
    """
    from utils.database import db
    import uuid
    from datetime import datetime, timezone
    
    symbol = symbol.upper()
    
    # Fetch historical data (this will cache it)
    data = await historical_data_service.get_stock_data(symbol)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"Could not find stock data for {symbol}")
    
    # Add to user's tracked stocks
    tracked_stocks = await db.user_context.find_one({"user_id": user.id})
    
    if not tracked_stocks:
        raise HTTPException(status_code=404, detail="User context not found")
    
    # Initialize tracked_symbols if not exists
    current_tracked = tracked_stocks.get('tracked_symbols', [])
    
    if symbol not in current_tracked:
        current_tracked.append(symbol)
        
        await db.user_context.update_one(
            {"user_id": user.id},
            {"$set": {
                "tracked_symbols": current_tracked,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
    
    return {
        "success": True,
        "symbol": symbol,
        "message": f"Now tracking {data['company_info']['name']}",
        "data": data
    }


@router.get("/tracked")
async def get_tracked_stocks(user: User = Depends(require_auth)):
    """
    Get all stocks that user is tracking
    Returns historical data for each tracked stock
    """
    from utils.database import db
    
    user_context = await db.user_context.find_one({"user_id": user.id})
    
    if not user_context or not user_context.get('tracked_symbols'):
        return {"symbols": [], "data": {}}
    
    symbols = user_context.get('tracked_symbols', [])
    
    # Get data for all tracked symbols
    data = await historical_data_service.get_multiple_stocks(symbols)
    
    return {
        "symbols": symbols,
        "count": len(symbols),
        "data": data
    }


@router.delete("/track/{symbol}")
async def remove_tracked_stock(
    symbol: str,
    user: User = Depends(require_auth)
):
    """
    Remove a stock from user's tracked list
    """
    from utils.database import db
    from datetime import datetime, timezone
    
    symbol = symbol.upper()
    
    user_context = await db.user_context.find_one({"user_id": user.id})
    
    if not user_context:
        raise HTTPException(status_code=404, detail="User context not found")
    
    tracked_symbols = user_context.get('tracked_symbols', [])
    
    if symbol not in tracked_symbols:
        raise HTTPException(status_code=404, detail=f"{symbol} is not in tracked list")
    
    tracked_symbols.remove(symbol)
    
    await db.user_context.update_one(
        {"user_id": user.id},
        {"$set": {
            "tracked_symbols": tracked_symbols,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return {
        "success": True,
        "symbol": symbol,
        "message": f"Stopped tracking {symbol}"
    }
