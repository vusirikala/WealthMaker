"""
Live Data Service
Fetches real-time stock prices, today's news, and upcoming events
"""
import yfinance as yf
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import logging
import finnhub
import os
from utils.database import db

logger = logging.getLogger(__name__)

# Finnhub client for news
finnhub_client = finnhub.Client(api_key=os.environ.get('FINNHUB_API_KEY', ''))


class LiveDataService:
    """Service for fetching real-time market data"""
    
    def __init__(self):
        self.cache_duration_minutes = 5  # Refresh live data every 5 minutes
    
    async def get_live_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current live quote for a stock
        
        Returns:
        - Current price, change, volume
        - Intraday high/low
        - Pre/post market data if available
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current data
            info = ticker.info
            
            # Get today's history for intraday data
            hist_today = ticker.history(period="1d", interval="1m")
            
            current_price = float(info.get('currentPrice', 0)) or float(info.get('regularMarketPrice', 0))
            previous_close = float(info.get('previousClose', 0))
            
            change = current_price - previous_close if previous_close > 0 else 0
            change_percent = (change / previous_close * 100) if previous_close > 0 else 0
            
            live_data = {
                "symbol": symbol,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                
                # Current Price
                "current_price": current_price,
                "previous_close": previous_close,
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "currency": info.get('currency', 'USD'),
                
                # Intraday
                "day_high": float(info.get('dayHigh', 0)),
                "day_low": float(info.get('dayLow', 0)),
                "open_price": float(info.get('open', 0)) or float(info.get('regularMarketOpen', 0)),
                
                # Volume
                "volume": int(info.get('volume', 0)),
                "average_volume": int(info.get('averageVolume', 0)),
                
                # Market Status
                "market_state": info.get('marketState', 'REGULAR'),
                "exchange": info.get('exchange', ''),
                
                # After hours (if available)
                "post_market_price": float(info.get('postMarketPrice', 0)) if info.get('postMarketPrice') else None,
                "post_market_change": float(info.get('postMarketChange', 0)) if info.get('postMarketChange') else None,
            }
            
            return live_data
            
        except Exception as e:
            logger.error(f"Error fetching live quote for {symbol}: {e}")
            return None
    
    async def get_todays_news(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get today's news for a specific stock
        """
        news_items = []
        
        try:
            # Calculate today's date range
            today = datetime.now(timezone.utc)
            yesterday = today - timedelta(days=1)
            
            from_date = yesterday.strftime('%Y-%m-%d')
            to_date = today.strftime('%Y-%m-%d')
            
            # Fetch from Finnhub
            news = finnhub_client.company_news(symbol, _from=from_date, to=to_date)
            
            for item in news[:limit]:
                news_items.append({
                    "headline": item.get('headline', ''),
                    "summary": item.get('summary', ''),
                    "source": item.get('source', ''),
                    "url": item.get('url', ''),
                    "image": item.get('image', ''),
                    "datetime": datetime.fromtimestamp(item.get('datetime', 0), tz=timezone.utc).isoformat() if item.get('datetime') else None,
                    "sentiment": self._analyze_headline_sentiment(item.get('headline', ''))
                })
            
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
        
        return news_items
    
    def _analyze_headline_sentiment(self, headline: str) -> str:
        """Simple sentiment analysis based on keywords"""
        headline_lower = headline.lower()
        
        positive_keywords = ['surge', 'jump', 'rise', 'gain', 'beat', 'upgrade', 'buy', 'bullish', 'growth', 'profit']
        negative_keywords = ['fall', 'drop', 'decline', 'loss', 'downgrade', 'sell', 'bearish', 'concern', 'warning']
        
        positive_count = sum(1 for word in positive_keywords if word in headline_lower)
        negative_count = sum(1 for word in negative_keywords if word in headline_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    async def get_upcoming_events(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get upcoming events for a stock (earnings, dividends, etc.)
        """
        events = []
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Earnings date
            earnings_date = info.get('earningsTimestamp')
            if earnings_date:
                earnings_dt = datetime.fromtimestamp(earnings_date, tz=timezone.utc)
                if earnings_dt > datetime.now(timezone.utc):
                    events.append({
                        "type": "earnings",
                        "date": earnings_dt.isoformat(),
                        "title": f"{symbol} Earnings Report",
                        "impact": "high",
                        "description": "Quarterly earnings announcement"
                    })
            
            # Dividend date
            ex_dividend_date = info.get('exDividendDate')
            if ex_dividend_date:
                try:
                    div_dt = datetime.fromtimestamp(ex_dividend_date, tz=timezone.utc)
                    if div_dt > datetime.now(timezone.utc):
                        dividend_amount = info.get('dividendRate', 0)
                        events.append({
                            "type": "dividend",
                            "date": div_dt.isoformat(),
                            "title": f"{symbol} Ex-Dividend Date",
                            "impact": "low",
                            "description": f"Ex-dividend date - ${dividend_amount} per share"
                        })
                except:
                    pass
            
            # Sort by date
            events.sort(key=lambda x: x['date'])
            
        except Exception as e:
            logger.error(f"Error fetching events for {symbol}: {e}")
        
        return events
    
    async def get_market_context(self) -> Dict[str, Any]:
        """
        Get overall market context (indices, VIX, etc.)
        """
        try:
            # Get major indices
            sp500 = yf.Ticker("^GSPC")
            nasdaq = yf.Ticker("^IXIC")
            vix = yf.Ticker("^VIX")
            
            sp500_info = sp500.info
            nasdaq_info = nasdaq.info
            vix_info = vix.info
            
            context = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                
                "sp500": {
                    "price": float(sp500_info.get('regularMarketPrice', 0)),
                    "change": float(sp500_info.get('regularMarketChange', 0)),
                    "change_percent": float(sp500_info.get('regularMarketChangePercent', 0)),
                },
                
                "nasdaq": {
                    "price": float(nasdaq_info.get('regularMarketPrice', 0)),
                    "change": float(nasdaq_info.get('regularMarketChange', 0)),
                    "change_percent": float(nasdaq_info.get('regularMarketChangePercent', 0)),
                },
                
                "vix": {
                    "level": float(vix_info.get('regularMarketPrice', 0)),
                    "interpretation": self._interpret_vix(float(vix_info.get('regularMarketPrice', 0)))
                },
                
                "market_sentiment": self._determine_market_sentiment(
                    float(sp500_info.get('regularMarketChangePercent', 0)),
                    float(vix_info.get('regularMarketPrice', 0))
                )
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error fetching market context: {e}")
            return {}
    
    def _interpret_vix(self, vix_level: float) -> str:
        """Interpret VIX level"""
        if vix_level < 12:
            return "Very Low Volatility"
        elif vix_level < 20:
            return "Low Volatility"
        elif vix_level < 30:
            return "Moderate Volatility"
        else:
            return "High Volatility"
    
    def _determine_market_sentiment(self, sp500_change: float, vix_level: float) -> str:
        """Determine overall market sentiment"""
        if sp500_change > 1 and vix_level < 20:
            return "bullish"
        elif sp500_change < -1 and vix_level > 25:
            return "bearish"
        else:
            return "neutral"
    
    async def get_portfolio_live_data(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get live data for all stocks in a portfolio
        Returns aggregated live quotes, news, and events
        """
        live_quotes = {}
        all_news = []
        all_events = []
        
        for symbol in symbols:
            # Get live quote
            quote = await self.get_live_quote(symbol)
            if quote:
                live_quotes[symbol] = quote
            
            # Get today's news (limit to 2 per stock to avoid overload)
            news = await self.get_todays_news(symbol, limit=2)
            all_news.extend([{**item, "symbol": symbol} for item in news])
            
            # Get upcoming events
            events = await self.get_upcoming_events(symbol)
            all_events.extend([{**event, "symbol": symbol} for event in events])
        
        # Sort news by datetime
        all_news.sort(key=lambda x: x.get('datetime', ''), reverse=True)
        
        # Sort events by date
        all_events.sort(key=lambda x: x.get('date', ''))
        
        # Get market context
        market_context = await self.get_market_context()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "quotes": live_quotes,
            "recent_news": all_news[:20],  # Top 20 most recent
            "upcoming_events": all_events[:10],  # Next 10 events
            "market_context": market_context
        }


# Create singleton instance
live_data_service = LiveDataService()
