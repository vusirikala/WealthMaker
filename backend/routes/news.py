"""News and market data routes"""
from fastapi import APIRouter, Depends
from datetime import datetime, timezone
import logging
import os
import finnhub

from models.user import User
from utils.database import db
from utils.dependencies import require_auth

router = APIRouter(prefix="/news", tags=["news"])
logger = logging.getLogger(__name__)

# Finnhub client
finnhub_client = finnhub.Client(api_key=os.environ.get('FINNHUB_API_KEY', ''))


@router.get("")
async def get_portfolio_news(user: User = Depends(require_auth)):
    """Get news for stocks in user's portfolio"""
    portfolio = await db.portfolios.find_one({"user_id": user.id})
    
    if not portfolio or not portfolio.get('allocations'):
        return []
    
    # Get unique tickers
    tickers = list(set([alloc['ticker'] for alloc in portfolio['allocations'] if alloc['asset_type'] == 'Stocks']))
    
    all_news = []
    try:
        for ticker in tickers[:5]:  # Limit to 5 stocks to avoid rate limits
            try:
                news = finnhub_client.company_news(ticker, _from="2025-01-01", to="2025-12-31")
                for item in news[:3]:  # Top 3 news per stock
                    all_news.append({
                        "ticker": ticker,
                        "headline": item.get('headline', ''),
                        "summary": item.get('summary', ''),
                        "url": item.get('url', ''),
                        "image": item.get('image', ''),
                        "source": item.get('source', ''),
                        "datetime": datetime.fromtimestamp(item.get('datetime', 0), tz=timezone.utc) if item.get('datetime') else None
                    })
            except Exception as e:
                logger.error(f"Error fetching news for {ticker}: {e}")
                continue
    except Exception as e:
        logger.error(f"Finnhub error: {e}")
    
    # Sort by datetime
    all_news.sort(key=lambda x: x['datetime'] if x['datetime'] else datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    
    return all_news[:20]  # Return top 20 news items
