"""
Historical Data Service
Fetches and caches 3 years of historical stock data using Yahoo Finance
"""
import yfinance as yf
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
import logging
from utils.database import db

logger = logging.getLogger(__name__)


class HistoricalDataService:
    """Service for fetching and managing historical stock data"""
    
    def __init__(self):
        self.cache_duration_days = 7  # Refresh data weekly
    
    async def get_stock_data(self, symbol: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive historical data for a stock
        Returns cached data if available and fresh, otherwise fetches new data
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
            force_refresh: If True, ignore cache and fetch fresh data
            
        Returns:
            Dictionary with historical data or None if fetch fails
        """
        # Check cache first
        if not force_refresh:
            cached_data = await self._get_cached_data(symbol)
            if cached_data:
                logger.info(f"Using cached data for {symbol}")
                return cached_data
        
        # Fetch fresh data
        logger.info(f"Fetching fresh historical data for {symbol}")
        try:
            historical_data = await self._fetch_historical_data(symbol)
            
            if historical_data:
                # Store in cache
                await self._cache_data(symbol, historical_data)
                return historical_data
            else:
                logger.warning(f"No data fetched for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    async def _get_cached_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Check if we have fresh cached data"""
        try:
            cached = await db.historical_data.find_one({"symbol": symbol})
            
            if not cached:
                return None
            
            # Check if data is still fresh
            last_updated = cached.get("last_updated")
            if isinstance(last_updated, str):
                last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)
            
            age_days = (datetime.now(timezone.utc) - last_updated).days
            
            if age_days < self.cache_duration_days:
                return cached
            else:
                logger.info(f"Cached data for {symbol} is {age_days} days old, refreshing")
                return None
                
        except Exception as e:
            logger.error(f"Error reading cache for {symbol}: {e}")
            return None
    
    async def _cache_data(self, symbol: str, data: Dict[str, Any]):
        """Store historical data in cache"""
        try:
            data["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            await db.historical_data.update_one(
                {"symbol": symbol},
                {"$set": data},
                upsert=True
            )
            logger.info(f"Cached historical data for {symbol}")
        except Exception as e:
            logger.error(f"Error caching data for {symbol}: {e}")
    
    async def _fetch_historical_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch comprehensive historical data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get company info
            info = ticker.info
            
            # Get 3 years of price history
            end_date = datetime.now()
            start_date = end_date - timedelta(days=3*365)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                logger.warning(f"No price history for {symbol}")
                return None
            
            # Calculate price metrics
            current_price = float(hist['Close'].iloc[-1]) if len(hist) > 0 else 0
            year_high = float(hist['High'].max())
            year_low = float(hist['Low'].min())
            
            # Calculate returns
            one_year_return = self._calculate_return(hist, 252)  # ~252 trading days in a year
            three_year_return = self._calculate_return(hist, 756)  # ~3 years
            
            # Get quarterly earnings (if available)
            earnings = []
            try:
                if hasattr(ticker, 'quarterly_earnings') and ticker.quarterly_earnings is not None:
                    quarterly_earnings = ticker.quarterly_earnings
                    for date, row in quarterly_earnings.head(12).iterrows():  # Last 3 years (12 quarters)
                        earnings.append({
                            "date": date.isoformat() if hasattr(date, 'isoformat') else str(date),
                            "earnings": float(row.get('Earnings', 0)) if 'Earnings' in row else None,
                            "revenue": float(row.get('Revenue', 0)) if 'Revenue' in row else None
                        })
            except Exception as e:
                logger.warning(f"Could not fetch earnings for {symbol}: {e}")
            
            # Build comprehensive data structure
            historical_data = {
                "symbol": symbol,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                
                # Company Info
                "company_info": {
                    "name": info.get('longName', symbol),
                    "sector": info.get('sector', 'Unknown'),
                    "industry": info.get('industry', 'Unknown'),
                    "description": info.get('longBusinessSummary', ''),
                    "market_cap": info.get('marketCap', 0),
                    "employees": info.get('fullTimeEmployees', 0),
                    "website": info.get('website', ''),
                    "country": info.get('country', ''),
                },
                
                # Current Metrics
                "current_metrics": {
                    "current_price": current_price,
                    "previous_close": float(info.get('previousClose', 0)),
                    "day_high": float(info.get('dayHigh', 0)),
                    "day_low": float(info.get('dayLow', 0)),
                    "volume": int(info.get('volume', 0)),
                    "average_volume": int(info.get('averageVolume', 0)),
                },
                
                # Price History (3 years)
                "price_history": {
                    "three_year_high": year_high,
                    "three_year_low": year_low,
                    "one_year_return": one_year_return,
                    "three_year_return": three_year_return,
                    "volatility": float(hist['Close'].pct_change().std() * (252 ** 0.5)) if len(hist) > 1 else 0,  # Annualized
                    "beta": float(info.get('beta', 1.0)),
                },
                
                # Fundamentals
                "fundamentals": {
                    "pe_ratio": float(info.get('trailingPE', 0)) if info.get('trailingPE') else None,
                    "forward_pe": float(info.get('forwardPE', 0)) if info.get('forwardPE') else None,
                    "dividend_yield": float(info.get('dividendYield', 0)) if info.get('dividendYield') else 0,
                    "earnings_growth": float(info.get('earningsGrowth', 0)) if info.get('earningsGrowth') else None,
                    "revenue_growth": float(info.get('revenueGrowth', 0)) if info.get('revenueGrowth') else None,
                },
                
                # Earnings History
                "earnings_history": earnings,
                
                # Analyst Ratings
                "analyst_info": {
                    "target_price": float(info.get('targetMeanPrice', 0)) if info.get('targetMeanPrice') else None,
                    "recommendation": info.get('recommendationKey', 'none'),
                    "number_of_analysts": int(info.get('numberOfAnalystOpinions', 0)),
                },
            }
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Error in _fetch_historical_data for {symbol}: {e}")
            return None
    
    def _calculate_return(self, hist, days: int) -> float:
        """Calculate percentage return over specified number of days"""
        try:
            if len(hist) < days:
                days = len(hist)
            
            if days < 2:
                return 0.0
            
            start_price = float(hist['Close'].iloc[-days])
            end_price = float(hist['Close'].iloc[-1])
            
            return round(((end_price - start_price) / start_price) * 100, 2)
        except Exception as e:
            logger.error(f"Error calculating return: {e}")
            return 0.0
    
    async def get_multiple_stocks(self, symbols: List[str], force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Get historical data for multiple stocks
        
        Args:
            symbols: List of stock ticker symbols
            force_refresh: If True, ignore cache for all symbols
            
        Returns:
            Dictionary mapping symbols to their historical data
        """
        results = {}
        
        for symbol in symbols:
            data = await self.get_stock_data(symbol, force_refresh)
            if data:
                results[symbol] = data
        
        return results
    
    async def search_stock(self, query: str) -> List[Dict[str, str]]:
        """
        Search for stocks by name or symbol
        Returns list of matching stocks with basic info
        """
        try:
            # For now, just validate if it's a valid ticker
            ticker = yf.Ticker(query.upper())
            info = ticker.info
            
            if info.get('longName'):
                return [{
                    "symbol": query.upper(),
                    "name": info.get('longName', query),
                    "sector": info.get('sector', 'Unknown'),
                    "market_cap": info.get('marketCap', 0)
                }]
            return []
        except Exception as e:
            logger.error(f"Error searching for {query}: {e}")
            return []


# Create singleton instance
historical_data_service = HistoricalDataService()
