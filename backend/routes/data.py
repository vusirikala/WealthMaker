"""
Data routes - Historical and live market data
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from models.user import User
from utils.dependencies import require_auth
from services.shared_assets_db import shared_assets_service
import logging

router = APIRouter(prefix="/data", tags=["data"])
logger = logging.getLogger(__name__)


@router.get("/asset/{symbol}")
async def get_asset_data(
    symbol: str,
    user: User = Depends(require_auth)
):
    """
    Get complete asset data from shared database
    
    Returns:
    - Company information (fundamentals)
    - Historical data (3 years)
    - Live data (current prices, news, events)
    """
    symbol = symbol.upper()
    
    data = await shared_assets_service.get_single_asset(symbol)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found in database. Admin needs to add it.")
    
    return data


@router.post("/assets/batch")
async def get_assets_batch(
    symbols: List[str],
    user: User = Depends(require_auth)
):
    """
    Get complete data for multiple assets from shared database
    This is the main endpoint for fetching portfolio data
    
    Body:
    - symbols: List of ticker symbols (e.g., ["AAPL", "MSFT", "BTC-USD"])
    
    Returns dictionary mapping symbols to their complete asset data
    """
    symbols = [s.upper() for s in symbols]
    
    assets_data = await shared_assets_service.get_assets_data(symbols)
    
    return {
        "count": len(assets_data),
        "requested": len(symbols),
        "data": assets_data
    }


@router.get("/search")
async def search_assets(
    q: str = Query(..., min_length=1, description="Search query (symbol or company name)"),
    user: User = Depends(require_auth)
):
    """
    Search for assets in shared database by symbol or company name
    
    Returns list of matching assets with basic information
    """
    results = await shared_assets_service.search_assets(q)
    
    return {
        "query": q,
        "count": len(results),
        "results": results
    }


@router.post("/track")
async def add_asset_to_track(
    symbol: str,
    user: User = Depends(require_auth)
):
    """
    Add an asset to user's watchlist
    Asset must exist in shared database
    """
    from utils.database import db
    from datetime import datetime, timezone
    
    symbol = symbol.upper()
    
    # Check if asset exists in shared database
    asset_data = await shared_assets_service.get_single_asset(symbol)
    
    if not asset_data:
        raise HTTPException(
            status_code=404, 
            detail=f"Asset {symbol} not found in shared database. Contact admin to add it."
        )
    
    # Add to user's tracked symbols
    user_context = await db.user_context.find_one({"user_id": user.id})
    
    if not user_context:
        raise HTTPException(status_code=404, detail="User context not found")
    
    current_tracked = user_context.get('tracked_symbols', [])
    
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
        "message": f"Now tracking {asset_data['name']}",
        "asset": asset_data
    }


@router.get("/tracked")
async def get_tracked_assets(user: User = Depends(require_auth)):
    """
    Get all assets that user is tracking
    Returns complete data from shared database for each tracked asset
    """
    from utils.database import db
    
    user_context = await db.user_context.find_one({"user_id": user.id})
    
    if not user_context or not user_context.get('tracked_symbols'):
        return {"symbols": [], "count": 0, "data": {}}
    
    symbols = user_context.get('tracked_symbols', [])
    
    # Get data from shared database
    assets_data = await shared_assets_service.get_assets_data(symbols)
    
    return {
        "symbols": symbols,
        "count": len(assets_data),
        "data": assets_data
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






# ============= WATCHLIST ENDPOINTS =============

@router.get("/watchlist")
async def get_watchlist(user: User = Depends(require_auth)):
    """
    Get user's watchlist (stocks they're following but not owning)
    """
    from utils.database import db
    
    user_context = await db.user_context.find_one({"user_id": user.id})
    
    if not user_context or not user_context.get('watchlist'):
        return {"symbols": [], "count": 0, "data": {}}
    
    symbols = user_context.get('watchlist', [])
    
    # Get data from shared database
    assets_data = await shared_assets_service.get_assets_data(symbols)
    
    return {
        "symbols": symbols,
        "count": len(assets_data),
        "data": assets_data
    }


@router.post("/watchlist/add")
async def add_to_watchlist(
    symbol: str,
    user: User = Depends(require_auth)
):
    """
    Add a stock to watchlist
    """
    from utils.database import db
    from datetime import datetime, timezone
    
    symbol = symbol.upper()
    
    # Check if asset exists in shared database
    asset_data = await shared_assets_service.get_single_asset(symbol)
    
    if not asset_data:
        raise HTTPException(
            status_code=404,
            detail=f"Asset {symbol} not found in shared database. Contact admin to add it."
        )
    
    # Add to user's watchlist
    user_context = await db.user_context.find_one({"user_id": user.id})
    
    if not user_context:
        raise HTTPException(status_code=404, detail="User context not found")
    
    watchlist = user_context.get('watchlist', [])
    
    if symbol not in watchlist:
        watchlist.append(symbol)
        
        await db.user_context.update_one(
            {"user_id": user.id},
            {"$set": {
                "watchlist": watchlist,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
    
    return {
        "success": True,
        "symbol": symbol,
        "message": f"Added {asset_data['name']} to watchlist",
        "asset": asset_data
    }


@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    user: User = Depends(require_auth)
):
    """
    Remove a stock from watchlist
    """
    from utils.database import db
    from datetime import datetime, timezone
    
    symbol = symbol.upper()
    
    user_context = await db.user_context.find_one({"user_id": user.id})
    
    if not user_context:
        raise HTTPException(status_code=404, detail="User context not found")
    
    watchlist = user_context.get('watchlist', [])
    
    if symbol not in watchlist:
        raise HTTPException(status_code=404, detail=f"{symbol} is not in watchlist")
    
    watchlist.remove(symbol)
    
    await db.user_context.update_one(
        {"user_id": user.id},
        {"$set": {
            "watchlist": watchlist,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return {
        "success": True,
        "symbol": symbol,
        "message": f"Removed {symbol} from watchlist"
    }

# ============= LIVE DATA ENDPOINTS =============

@router.get("/live/{symbol}")
async def get_live_data(
    symbol: str,
    user: User = Depends(require_auth)
):
    """
    Get real-time live data for a stock
    
    Returns:
    - Current price, change, volume
    - Intraday high/low
    - Today's news
    - Upcoming events
    """
    symbol = symbol.upper()
    
    # Get live quote
    quote = await live_data_service.get_live_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Could not fetch live data for {symbol}")
    
    # Get today's news
    news = await live_data_service.get_todays_news(symbol, limit=5)
    
    # Get upcoming events
    events = await live_data_service.get_upcoming_events(symbol)
    
    return {
        "quote": quote,
        "recent_news": news,
        "upcoming_events": events
    }


@router.post("/live/portfolio")
async def get_portfolio_live_data(
    symbols: List[str],
    user: User = Depends(require_auth)
):
    """
    Get live data for all stocks in a portfolio
    
    Returns aggregated:
    - Live quotes for all symbols
    - Recent news across all stocks
    - Upcoming events
    - Market context (S&P 500, NASDAQ, VIX)
    """
    symbols = [s.upper() for s in symbols]
    
    data = await live_data_service.get_portfolio_live_data(symbols)
    
    return data


@router.get("/market/context")
async def get_market_context(user: User = Depends(require_auth)):
    """
    Get overall market context
    
    Returns:
    - S&P 500 performance
    - NASDAQ performance
    - VIX (volatility index)
    - Overall market sentiment
    """
    context = await live_data_service.get_market_context()
    
    return context


@router.get("/news/{symbol}")
async def get_stock_news(
    symbol: str,
    limit: int = Query(10, ge=1, le=50, description="Number of news items to return"),
    user: User = Depends(require_auth)
):
    """
    Get recent news for a specific stock
    """
    symbol = symbol.upper()
    
    news = await live_data_service.get_todays_news(symbol, limit=limit)
    
    return {
        "symbol": symbol,
        "count": len(news),
        "news": news
    }
