"""
Portfolio Performance Calculator
Calculates historical returns based on portfolio allocations
"""
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


async def get_cached_price_data(ticker: str, start_date: datetime, end_date: datetime, db):
    """Get cached price data or fetch from Yahoo Finance"""
    from utils.database import db as database
    
    # Check cache
    cache_key = f"{ticker}_{start_date.date()}_{end_date.date()}"
    cached = await database.price_cache.find_one({"cache_key": cache_key})
    
    if cached and (datetime.now() - cached['updated_at']).days < 1:
        logger.info(f"Using cached data for {ticker}")
        # Convert to DataFrame
        data = cached['data']
        df = pd.DataFrame(data)
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        return df['Close']
    
    # Fetch from Yahoo Finance
    logger.info(f"Fetching fresh data for {ticker} from Yahoo Finance")
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start_date, end=end_date)
    
    if not hist.empty:
        # Cache the data
        cache_doc = {
            "cache_key": cache_key,
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "data": hist['Close'].reset_index().to_dict('records'),
            "updated_at": datetime.now()
        }
        await database.price_cache.update_one(
            {"cache_key": cache_key},
            {"$set": cache_doc},
            upsert=True
        )
        logger.info(f"Cached data for {ticker}")
    
    return hist['Close']


async def calculate_portfolio_historical_returns(
    allocations: List[Dict[str, Any]],
    time_period: str = "1y",
    db = None
) -> Dict[str, Any]:
    """
    Calculate historical portfolio returns based on allocations
    Includes S&P 500 benchmark comparison
    
    Args:
        allocations: List of {ticker, allocation_percentage} dicts
        time_period: '6m', '1y', '3y', or '5y'
        db: Database instance for caching
        
    Returns:
        Dict with return_percentage, time_series data, period stats, and S&P 500 comparison
    """
    
    # Always fetch maximum history (5 years) for accurate period calculations
    end_date = datetime.now()
    max_start_date = end_date - timedelta(days=1825)  # 5 years
    
    # Determine display range based on time_period
    if time_period == '6m':
        display_start_date = end_date - timedelta(days=180)
    elif time_period == '1y':
        display_start_date = end_date - timedelta(days=365)
    elif time_period == '3y':
        display_start_date = end_date - timedelta(days=1095)
    elif time_period == '5y':
        display_start_date = max_start_date
    else:
        display_start_date = end_date - timedelta(days=365)
    
    logger.info(f"Fetching max history from {max_start_date.date()}, displaying from {display_start_date.date()} to {end_date.date()}")
    
    # Fetch historical data for all tickers (with caching if db available)
    ticker_data = {}
    valid_allocations = []
    
    # Use synchronous approach since yfinance is synchronous
    import asyncio
    
    for alloc in allocations:
        ticker = alloc['ticker']
        allocation_pct = alloc['allocation_percentage'] / 100.0
        
        try:
            logger.info(f"Fetching data for {ticker}")
            
            # Try to use cache if db is available
            if db is not None:
                try:
                    price_series = asyncio.run(get_cached_price_data(ticker, max_start_date, end_date, db))
                except:
                    # Fallback to direct fetch
                    stock = yf.Ticker(ticker)
                    hist = stock.history(start=max_start_date, end=end_date)
                    price_series = hist['Close'] if not hist.empty else None
            else:
                stock = yf.Ticker(ticker)
                hist = stock.history(start=max_start_date, end=end_date)
                price_series = hist['Close'] if not hist.empty else None
            
            if price_series is None or len(price_series) == 0:
                logger.warning(f"No data for {ticker}, skipping")
                continue
            
            ticker_data[ticker] = price_series
            valid_allocations.append({
                'ticker': ticker,
                'allocation': allocation_pct
            })
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            continue
    
    # Fetch S&P 500 for comparison
    sp500_data = None
    try:
        logger.info("Fetching S&P 500 benchmark data")
        if db is not None:
            try:
                sp500_data = asyncio.run(get_cached_price_data('^GSPC', max_start_date, end_date, db))
            except:
                sp500 = yf.Ticker('^GSPC')
                sp500_hist = sp500.history(start=max_start_date, end=end_date)
                sp500_data = sp500_hist['Close'] if not sp500_hist.empty else None
        else:
            sp500 = yf.Ticker('^GSPC')
            sp500_hist = sp500.history(start=max_start_date, end=end_date)
            sp500_data = sp500_hist['Close'] if not sp500_hist.empty else None
    except Exception as e:
        logger.error(f"Error fetching S&P 500 data: {e}")
    
    if not ticker_data:
        logger.error("No valid ticker data available")
        return {
            'return_percentage': 0,
            'time_series': [],
            'period_stats': {
                '6m_return': 0,
                '1y_return': 0,
                '3y_return': 0,
                '5y_return': 0
            }
        }
    
    # Normalize allocations (in case some tickers failed)
    total_allocation = sum(a['allocation'] for a in valid_allocations)
    if total_allocation > 0:
        for alloc in valid_allocations:
            alloc['allocation'] = alloc['allocation'] / total_allocation
    
    # Create DataFrame with all tickers
    df = pd.DataFrame(ticker_data)
    
    # Forward fill missing data
    df = df.ffill()
    
    # Calculate portfolio value over time (starting at 100)
    portfolio_values = pd.Series(0, index=df.index)
    
    for alloc in valid_allocations:
        ticker = alloc['ticker']
        allocation = alloc['allocation']
        
        # Normalize to start at 100 for this ticker
        normalized_prices = (df[ticker] / df[ticker].iloc[0]) * 100
        
        # Add weighted contribution to portfolio
        portfolio_values += normalized_prices * allocation
    
    # Calculate portfolio returns (portfolio starts at 100, so return is (current - 100))
    portfolio_returns = ((portfolio_values - 100) / 100) * 100
    
    # Calculate S&P 500 returns for comparison
    sp500_returns = None
    if sp500_data is not None and len(sp500_data) > 0:
        # Add to DataFrame
        df['SP500'] = sp500_data
        df['SP500'] = df['SP500'].ffill()
        
        # Normalize S&P 500 to start at 100
        sp500_normalized = (df['SP500'] / df['SP500'].iloc[0]) * 100
        sp500_returns = ((sp500_normalized - 100) / 100) * 100
    
    # Filter to display range
    display_mask = df.index >= display_start_date
    portfolio_returns_display = portfolio_returns[display_mask]
    
    if sp500_returns is not None:
        sp500_returns_display = sp500_returns[display_mask]
    
    # Build time series for charting
    time_series = []
    for date, return_pct in portfolio_returns_display.items():
        time_series.append({
            'date': date.strftime('%Y-%m-%d'),
            'return_percentage': round(float(return_pct), 2)
        })
    
    # Calculate period returns
    current_return = float(portfolio_returns_display.iloc[-1])
    
    period_stats = {}
    
    # 6 month return
    if len(portfolio_returns) >= 126:  # ~6 months of trading days
        six_month_return = float(portfolio_returns.iloc[-1] - portfolio_returns.iloc[-126])
        period_stats['6m_return'] = round(six_month_return, 2)
    else:
        period_stats['6m_return'] = round(current_return, 2)
    
    # 1 year return
    if len(portfolio_returns) >= 252:  # ~1 year of trading days
        one_year_return = float(portfolio_returns.iloc[-1] - portfolio_returns.iloc[-252])
        period_stats['1y_return'] = round(one_year_return, 2)
    else:
        period_stats['1y_return'] = round(current_return, 2)
    
    # 3 year return
    if len(portfolio_returns) >= 756:  # ~3 years of trading days
        three_year_return = float(portfolio_returns.iloc[-1] - portfolio_returns.iloc[-756])
        period_stats['3y_return'] = round(three_year_return, 2)
    else:
        period_stats['3y_return'] = None
    
    # 5 year return
    if len(portfolio_returns) >= 1260:  # ~5 years of trading days
        five_year_return = float(portfolio_returns.iloc[-1] - portfolio_returns.iloc[-1260])
        period_stats['5y_return'] = round(five_year_return, 2)
    else:
        period_stats['5y_return'] = None
    
    logger.info(f"Calculated returns: {current_return:.2f}% for {time_period}")
    
    # Build S&P 500 time series for comparison
    sp500_time_series = []
    if sp500_returns is not None:
        for date, return_pct in sp500_returns_display.items():
            sp500_time_series.append({
                'date': date.strftime('%Y-%m-%d'),
                'return_percentage': round(float(return_pct), 2)
            })
    
    return {
        'return_percentage': round(current_return, 2),
        'time_series': time_series,
        'period_stats': period_stats,
        'sp500_comparison': {
            'time_series': sp500_time_series,
            'current_return': round(float(sp500_returns_display.iloc[-1]), 2) if sp500_returns is not None else None
        },
        'start_date': display_start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d')
    }
