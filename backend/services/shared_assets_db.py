"""
Shared Assets Database Service
Manages a shared database of financial assets (S&P 500 + Crypto + Commodities)
All users reference this shared data instead of fetching individually
"""
import yfinance as yf
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import logging
import os
from utils.database import db

logger = logging.getLogger(__name__)


class SharedAssetsService:
    """Manages shared financial assets database"""
    
    # Asset universes
    TOP_SP500 = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B",
        "V", "JNJ", "WMT", "JPM", "MA", "PG", "UNH", "HD", "DIS", "BAC",
        "XOM", "CVX", "LLY", "AVGO", "COST", "ABBV", "PFE", "MRK", "KO",
        "CSCO", "PEP", "ADBE", "NFLX", "TMO", "ACN", "NKE", "MCD", "DHR",
        "ABT", "VZ", "INTC", "CRM", "CMCSA", "AMD", "TXN", "NEE", "WFC",
        "UPS", "QCOM", "BMY", "PM", "RTX", "HON"  # Top 50 for demo
    ]
    
    CRYPTO = ["BTC-USD", "ETH-USD"]
    COMMODITIES = ["GC=F"]  # Gold futures
    
    ALL_ASSETS = TOP_SP500 + CRYPTO + COMMODITIES
    
    def __init__(self):
        self.collection = db.shared_assets  # MongoDB collection for shared data
    
    async def initialize_database(self, symbols: Optional[List[str]] = None):
        """
        One-time initialization of shared assets database
        Fetches 3 years of historical data for all assets
        
        Args:
            symbols: List of symbols to initialize. If None, uses ALL_ASSETS
        """
        if symbols is None:
            symbols = self.ALL_ASSETS
        
        logger.info(f"🚀 Initializing shared assets database for {len(symbols)} symbols")
        
        initialized_count = 0
        failed_count = 0
        
        for symbol in symbols:
            try:
                logger.info(f"⏳ Processing {symbol}...")
                
                asset_data = await self._fetch_complete_asset_data(symbol)
                
                if asset_data:
                    # Store in shared database
                    await self.collection.update_one(
                        {"symbol": symbol},
                        {"$set": asset_data},
                        upsert=True
                    )
                    initialized_count += 1
                    logger.info(f"✅ {symbol} initialized")
                else:
                    failed_count += 1
                    logger.warning(f"⚠️ {symbol} failed - no data")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ Error initializing {symbol}: {e}")
        
        logger.info(f"🎉 Initialization complete! Success: {initialized_count}, Failed: {failed_count}")
        
        return {
            "success": True,
            "initialized": initialized_count,
            "failed": failed_count,
            "total": len(symbols)
        }
    
    async def _fetch_complete_asset_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch all historical and fundamental data for an asset"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get 3 years of price history
            end_date = datetime.now()
            start_date = end_date - timedelta(days=3*365)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                return None
            
            # Determine asset type
            asset_type = self._get_asset_type(symbol)
            
            # Build complete asset structure
            asset_data = {
                "symbol": symbol,
                "name": info.get('longName', symbol),
                "assetType": asset_type,
                "lastUpdated": datetime.now(timezone.utc).isoformat(),
                
                # ═══════════════════════════════════════
                # FUNDAMENTALS (Static)
                # ═══════════════════════════════════════
                "fundamentals": {
                    # Common fields
                    "sector": info.get('sector', 'Unknown'),
                    "industry": info.get('industry', 'Unknown'),
                    "description": info.get('longBusinessSummary', ''),
                    "longBusinessSummary": info.get('longBusinessSummary', ''),
                    "marketCap": info.get('marketCap', 0),
                    "employees": info.get('fullTimeEmployees', 0),
                    "website": info.get('website', ''),
                    "country": info.get('country', ''),
                    "quoteType": info.get('quoteType', ''),
                    
                    # Fund-specific fields (for ETFs, Index Funds, Bond Funds)
                    "category": info.get('category', ''),
                    "totalAssets": info.get('totalAssets', 0),
                    "expenseRatio": info.get('annualReportExpenseRatio', 0),
                    "yield": info.get('yield', 0),
                    "ytdReturn": info.get('ytdReturn', 0),
                    "threeYearAverageReturn": info.get('threeYearAverageReturn', 0),
                    "fiveYearAverageReturn": info.get('fiveYearAverageReturn', 0),
                    "fundFamily": info.get('fundFamily', ''),
                    "fundInceptionDate": info.get('fundInceptionDate', ''),
                },
                
                # ═══════════════════════════════════════
                # HISTORICAL (Loaded once)
                # ═══════════════════════════════════════
                "historical": {
                    "lastUpdated": datetime.now(timezone.utc).isoformat(),
                    
                    # Earnings history (12 quarters if available)
                    "earnings": self._get_earnings_history(ticker),
                    
                    # 3-year price metrics
                    "priceHistory": {
                        "threeYearReturn": self._calculate_return(hist, len(hist)),
                        "oneYearReturn": self._calculate_return(hist, 252),
                        "sixMonthReturn": self._calculate_return(hist, 126),
                        "volatility": float(hist['Close'].pct_change().std() * (252 ** 0.5)) if len(hist) > 1 else 0,
                        "beta": float(info.get('beta', 1.0)),
                        "allTimeHigh": {
                            "price": float(hist['High'].max()),
                            "date": hist['High'].idxmax().isoformat() if len(hist) > 0 else None
                        },
                        "allTimeLow": {
                            "price": float(hist['Low'].min()),
                            "date": hist['Low'].idxmin().isoformat() if len(hist) > 0 else None
                        },
                        "monthlyPrices": self._get_monthly_prices(hist)
                    },
                    
                    # Major events (simplified for demo)
                    "majorEvents": [],
                    
                    # Patterns (to be generated by AI later)
                    "patterns": []
                },
                
                # ═══════════════════════════════════════
                # LIVE (Updated daily)
                # ═══════════════════════════════════════
                "live": {
                    "currentPrice": {},
                    "recentNews": [],
                    "analystRatings": {},
                    "upcomingEvents": []
                }
            }
            
            return asset_data
            
        except Exception as e:
            logger.error(f"Error fetching complete data for {symbol}: {e}")
            return None
    
    def _get_asset_type(self, symbol: str) -> str:
        """Determine asset type from symbol"""
        if symbol in self.CRYPTO:
            return "crypto"
        elif symbol in self.COMMODITIES:
            return "commodity"
        else:
            return "stock"
    
    def _get_earnings_history(self, ticker) -> List[Dict[str, Any]]:
        """Get earnings history (up to 12 quarters)"""
        earnings = []
        try:
            if hasattr(ticker, 'quarterly_earnings') and ticker.quarterly_earnings is not None:
                quarterly_earnings = ticker.quarterly_earnings
                for date, row in quarterly_earnings.head(12).iterrows():
                    earnings.append({
                        "date": date.isoformat() if hasattr(date, 'isoformat') else str(date),
                        "earnings": float(row.get('Earnings', 0)) if 'Earnings' in row else None,
                        "revenue": float(row.get('Revenue', 0)) if 'Revenue' in row else None
                    })
        except Exception as e:
            logger.warning(f"Could not fetch earnings: {e}")
        
        return earnings
    
    def _calculate_return(self, hist, days: int) -> float:
        """Calculate percentage return over specified trading days"""
        try:
            if len(hist) < days:
                days = len(hist)
            
            if days < 2:
                return 0.0
            
            start_price = float(hist['Close'].iloc[-days])
            end_price = float(hist['Close'].iloc[-1])
            
            return round(((end_price - start_price) / start_price) * 100, 2)
        except:
            return 0.0
    
    def _get_monthly_prices(self, hist) -> List[Dict[str, Any]]:
        """Get monthly closing prices"""
        try:
            monthly = hist.resample('M')['Close'].last()
            return [
                {
                    "month": date.strftime('%Y-%m'),
                    "close": float(price)
                }
                for date, price in monthly.items()
            ]
        except:
            return []
    
    async def update_live_data(self, symbols: Optional[List[str]] = None):
        """
        Update live data (prices, news, events) for all assets
        Should be run 2x daily (morning & afternoon)
        
        Args:
            symbols: List of symbols to update. If None, updates all in database
        """
        if symbols is None:
            # Get all symbols from database
            cursor = self.collection.find({}, {"symbol": 1})
            symbols = [doc["symbol"] async for doc in cursor]
        
        logger.info(f"🔄 Updating live data for {len(symbols)} assets")
        
        updated_count = 0
        
        for symbol in symbols:
            try:
                live_data = await self._fetch_live_data(symbol)
                
                if live_data:
                    await self.collection.update_one(
                        {"symbol": symbol},
                        {
                            "$set": {
                                "live": live_data,
                                "lastUpdated": datetime.now(timezone.utc).isoformat()
                            }
                        }
                    )
                    updated_count += 1
                    
            except Exception as e:
                logger.error(f"Error updating live data for {symbol}: {e}")
        
        logger.info(f"✅ Live data updated for {updated_count}/{len(symbols)} assets")
        
        return {
            "success": True,
            "updated": updated_count,
            "total": len(symbols)
        }
    
    async def _fetch_live_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch current live data for an asset"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            current_price = float(info.get('currentPrice', 0)) or float(info.get('regularMarketPrice', 0))
            previous_close = float(info.get('previousClose', 0))
            
            change = current_price - previous_close if previous_close > 0 else 0
            change_percent = (change / previous_close * 100) if previous_close > 0 else 0
            
            # Get 52-week history to calculate high/low if not provided by API
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                hist_52w = ticker.history(start=start_date, end=end_date)
            except:
                hist_52w = None
            
            # Fetch news from Finnhub
            news_items = []
            try:
                import finnhub
                import os
                finnhub_client = finnhub.Client(api_key=os.environ.get('FINNHUB_API_KEY', ''))
                
                today = datetime.now(timezone.utc)
                week_ago = today - timedelta(days=7)
                from_date = week_ago.strftime('%Y-%m-%d')
                to_date = today.strftime('%Y-%m-%d')
                
                news = finnhub_client.company_news(symbol, _from=from_date, to=to_date)
                
                for item in news[:10]:  # Keep last 10 news items
                    news_items.append({
                        "headline": item.get('headline', ''),
                        "title": item.get('headline', ''),
                        "summary": item.get('summary', ''),
                        "source": item.get('source', ''),
                        "url": item.get('url', ''),
                        "image": item.get('image', ''),
                        "datetime": datetime.fromtimestamp(item.get('datetime', 0), tz=timezone.utc).isoformat() if item.get('datetime') else None,
                        "timestamp": datetime.fromtimestamp(item.get('datetime', 0), tz=timezone.utc).isoformat() if item.get('datetime') else None,
                        "sentiment": self._analyze_sentiment(item.get('headline', ''))
                    })
            except Exception as e:
                logger.warning(f"Could not fetch news for {symbol}: {e}")
            
            # Extract 52-week high/low with multiple key variations
            fifty_two_week_high = (
                info.get('fiftyTwoWeekHigh') or 
                info.get('52WeekHigh') or 
                info.get('yearHigh') or 
                None
            )
            fifty_two_week_low = (
                info.get('fiftyTwoWeekLow') or 
                info.get('52WeekLow') or 
                info.get('yearLow') or 
                None
            )
            
            # Convert to float, handle None values
            try:
                fifty_two_week_high = float(fifty_two_week_high) if fifty_two_week_high else None
            except (ValueError, TypeError):
                fifty_two_week_high = None
                
            try:
                fifty_two_week_low = float(fifty_two_week_low) if fifty_two_week_low else None
            except (ValueError, TypeError):
                fifty_two_week_low = None
            
            # Calculate from historical data if not available from API
            if (fifty_two_week_high is None or fifty_two_week_low is None) and hist_52w is not None and not hist_52w.empty:
                try:
                    if fifty_two_week_high is None:
                        fifty_two_week_high = float(hist_52w['High'].max())
                    if fifty_two_week_low is None:
                        fifty_two_week_low = float(hist_52w['Low'].min())
                except Exception as e:
                    logger.warning(f"Could not calculate 52-week high/low from history for {symbol}: {e}")
            
            # Set to 0 if still None
            fifty_two_week_high = fifty_two_week_high or 0
            fifty_two_week_low = fifty_two_week_low or 0
            
            live_data = {
                "currentPrice": {
                    "price": current_price,
                    "change": round(change, 2),
                    "changePercent": round(change_percent, 2),
                    "volume": int(info.get('volume', 0)),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "dayHigh": float(info.get('dayHigh', 0)) if info.get('dayHigh') else 0,
                    "dayLow": float(info.get('dayLow', 0)) if info.get('dayLow') else 0,
                    "fiftyTwoWeekHigh": fifty_two_week_high,
                    "fiftyTwoWeekLow": fifty_two_week_low
                },
                
                "recentNews": news_items,
                
                "analystRatings": {
                    "lastUpdated": datetime.now(timezone.utc).isoformat(),
                    "targetPrice": float(info.get('targetMeanPrice', 0)) if info.get('targetMeanPrice') else None,
                    "recommendation": info.get('recommendationKey', 'none'),
                    "numberOfAnalysts": int(info.get('numberOfAnalystOpinions', 0))
                },
                
                "upcomingEvents": []  # To be populated from events service
            }
            
            return live_data
            
        except Exception as e:
            logger.error(f"Error fetching live data for {symbol}: {e}")
            return {}
    
    def _analyze_sentiment(self, headline: str) -> str:
        """Simple sentiment analysis based on keywords"""
        headline_lower = headline.lower()
        
        positive_keywords = ['surge', 'jump', 'rise', 'gain', 'beat', 'upgrade', 'buy', 'bullish', 'growth', 'profit', 'soar', 'rally']
        negative_keywords = ['fall', 'drop', 'decline', 'loss', 'downgrade', 'sell', 'bearish', 'concern', 'warning', 'plunge', 'crash']
        
        positive_count = sum(1 for word in positive_keywords if word in headline_lower)
        negative_count = sum(1 for word in negative_keywords if word in headline_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    async def get_assets_data(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get complete data for multiple assets from shared database
        This is what users call to get data for their portfolio
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbols to their complete asset data
        """
        assets_data = {}
        
        for symbol in symbols:
            asset = await self.collection.find_one({"symbol": symbol})
            if asset:
                # Remove MongoDB _id field
                asset.pop('_id', None)
                assets_data[symbol] = asset
        
        return assets_data
    
    async def get_single_asset(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get data for a single asset"""
        asset = await self.collection.find_one({"symbol": symbol})
        if asset:
            asset.pop('_id', None)
            return asset
        return None
    
    async def search_assets(self, query: str) -> List[Dict[str, str]]:
        """
        Search for assets by symbol or name
        Returns basic info for matching assets
        """
        query_upper = query.upper()
        
        # Search in database
        cursor = self.collection.find({
            "$or": [
                {"symbol": {"$regex": query_upper, "$options": "i"}},
                {"name": {"$regex": query, "$options": "i"}}
            ]
        }, {"symbol": 1, "name": 1, "assetType": 1, "fundamentals.sector": 1, "fundamentals.marketCap": 1})
        
        results = []
        async for doc in cursor:
            results.append({
                "symbol": doc.get("symbol"),
                "name": doc.get("name"),
                "assetType": doc.get("assetType"),
                "sector": doc.get("fundamentals", {}).get("sector", "Unknown"),
                "marketCap": doc.get("fundamentals", {}).get("marketCap", 0)
            })
        
        return results[:10]  # Limit to 10 results
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the shared assets database"""
        total_assets = await self.collection.count_documents({})
        
        # Count by asset type
        stocks = await self.collection.count_documents({"assetType": "stock"})
        crypto = await self.collection.count_documents({"assetType": "crypto"})
        commodities = await self.collection.count_documents({"assetType": "commodity"})
        
        # Get last update time
        latest = await self.collection.find_one({}, sort=[("lastUpdated", -1)])
        last_updated = latest.get("lastUpdated") if latest else None
        
        return {
            "total_assets": total_assets,
            "by_type": {
                "stocks": stocks,
                "crypto": crypto,
                "commodities": commodities
            },
            "last_updated": last_updated,
            "status": "active" if total_assets > 0 else "needs_initialization"
        }


# Create singleton instance
shared_assets_service = SharedAssetsService()
