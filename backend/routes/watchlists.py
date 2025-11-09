"""
Multi-Watchlist Management Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import logging
from utils.dependencies import require_auth
from models.user import User
from utils.database import db
import yfinance as yf

router = APIRouter(prefix="/watchlists", tags=["watchlists"])
logger = logging.getLogger(__name__)


class CreateWatchlistRequest(BaseModel):
    name: str


class AddTickerRequest(BaseModel):
    ticker: str


@router.post("/create")
async def create_watchlist(
    request: CreateWatchlistRequest,
    user: User = Depends(require_auth)
):
    """Create a new watchlist"""
    watchlist_id = str(uuid.uuid4())
    
    watchlist = {
        "_id": watchlist_id,
        "user_id": user.id,
        "name": request.name,
        "tickers": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    
    await db.user_watchlists.insert_one(watchlist)
    
    return {
        "success": True,
        "watchlist": {
            "id": watchlist_id,
            "name": request.name,
            "tickers": []
        }
    }


@router.get("/list")
async def list_watchlists(user: User = Depends(require_auth)):
    """Get all watchlists for the user"""
    watchlists = await db.user_watchlists.find({
        "user_id": user.id,
        "is_active": True
    }).to_list(length=None)
    
    return {
        "watchlists": [
            {
                "id": w["_id"],
                "name": w["name"],
                "ticker_count": len(w.get("tickers", []))
            }
            for w in watchlists
        ]
    }


@router.get("/{watchlist_id}")
async def get_watchlist(
    watchlist_id: str,
    user: User = Depends(require_auth)
):
    """Get a specific watchlist with live data"""
    watchlist = await db.user_watchlists.find_one({
        "_id": watchlist_id,
        "user_id": user.id,
        "is_active": True
    })
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    # Fetch live data for all tickers
    tickers_data = []
    for ticker in watchlist.get("tickers", []):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1y")  # Get 1 year of data
            
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            prev_close = info.get('previousClose', current_price)
            
            # Calculate 24h change
            if prev_close > 0:
                price_change_24h = current_price - prev_close
                price_change_pct_24h = (price_change_24h / prev_close) * 100
            else:
                price_change_24h = 0
                price_change_pct_24h = 0
            
            # Calculate 1-month change (approx 21 trading days)
            price_change_pct_1m = 0
            if len(hist) >= 21:
                price_1m_ago = hist['Close'].iloc[-21]
                if price_1m_ago > 0:
                    price_change_pct_1m = ((current_price - price_1m_ago) / price_1m_ago) * 100
            
            # Calculate 1-year change
            price_change_pct_1y = 0
            if len(hist) >= 252:  # Approx 1 year trading days
                price_1y_ago = hist['Close'].iloc[0]
                if price_1y_ago > 0:
                    price_change_pct_1y = ((current_price - price_1y_ago) / price_1y_ago) * 100
            
            # Get 52-week high and low
            week_52_high = info.get('fiftyTwoWeekHigh', 0)
            week_52_low = info.get('fiftyTwoWeekLow', 0)
            
            # If not available in info, calculate from history
            if (week_52_high == 0 or week_52_low == 0) and len(hist) > 0:
                week_52_high = float(hist['High'].max())
                week_52_low = float(hist['Low'].min())
            
            # Calculate position in 52-week range (0-100%)
            range_position = 0
            if week_52_high > week_52_low:
                range_position = ((current_price - week_52_low) / (week_52_high - week_52_low)) * 100
            
            tickers_data.append({
                "ticker": ticker,
                "name": info.get('longName', ticker),
                "current_price": round(current_price, 2),
                "price_change_24h": round(price_change_24h, 2),
                "price_change_pct_24h": round(price_change_pct_24h, 2),
                "price_change_pct_1m": round(price_change_pct_1m, 2),
                "price_change_pct_1y": round(price_change_pct_1y, 2),
                "week_52_high": round(week_52_high, 2),
                "week_52_low": round(week_52_low, 2),
                "range_position": round(range_position, 2),
                "market_cap": info.get('marketCap', 0),
                "volume": info.get('volume', 0)
            })
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            tickers_data.append({
                "ticker": ticker,
                "name": ticker,
                "current_price": 0,
                "price_change_24h": 0,
                "price_change_pct_24h": 0,
                "price_change_pct_1m": 0,
                "price_change_pct_1y": 0,
                "week_52_high": 0,
                "week_52_low": 0,
                "range_position": 0,
                "market_cap": 0,
                "volume": 0
            })
    
    return {
        "watchlist": {
            "id": watchlist["_id"],
            "name": watchlist["name"],
            "tickers": tickers_data
        }
    }


@router.post("/{watchlist_id}/add-ticker")
async def add_ticker(
    watchlist_id: str,
    request: AddTickerRequest,
    user: User = Depends(require_auth)
):
    """Add a ticker to a watchlist"""
    ticker = request.ticker.upper()
    
    # Validate ticker exists
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info.get('regularMarketPrice') and not info.get('currentPrice'):
            raise HTTPException(status_code=400, detail="Invalid ticker symbol")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid ticker symbol")
    
    # Update watchlist
    result = await db.user_watchlists.update_one(
        {
            "_id": watchlist_id,
            "user_id": user.id,
            "is_active": True
        },
        {
            "$addToSet": {"tickers": ticker}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    return {"success": True, "ticker": ticker}


@router.delete("/{watchlist_id}/ticker/{ticker}")
async def remove_ticker(
    watchlist_id: str,
    ticker: str,
    user: User = Depends(require_auth)
):
    """Remove a ticker from a watchlist"""
    result = await db.user_watchlists.update_one(
        {
            "_id": watchlist_id,
            "user_id": user.id,
            "is_active": True
        },
        {
            "$pull": {"tickers": ticker.upper()}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    return {"success": True}


@router.put("/{watchlist_id}")
async def update_watchlist(
    watchlist_id: str,
    request: CreateWatchlistRequest,
    user: User = Depends(require_auth)
):
    """Update watchlist name"""
    result = await db.user_watchlists.update_one(
        {
            "_id": watchlist_id,
            "user_id": user.id,
            "is_active": True
        },
        {
            "$set": {"name": request.name}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    return {"success": True}


@router.delete("/{watchlist_id}")
async def delete_watchlist(
    watchlist_id: str,
    user: User = Depends(require_auth)
):
    """Delete a watchlist"""
    result = await db.user_watchlists.update_one(
        {
            "_id": watchlist_id,
            "user_id": user.id,
            "is_active": True
        },
        {
            "$set": {"is_active": False}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    return {"success": True}
