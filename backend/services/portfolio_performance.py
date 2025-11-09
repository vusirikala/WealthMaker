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


def calculate_portfolio_historical_returns(
    allocations: List[Dict[str, Any]],
    time_period: str = "1y"
) -> Dict[str, Any]:
    """
    Calculate historical portfolio returns based on allocations
    
    Args:
        allocations: List of {ticker, allocation_percentage} dicts
        time_period: '6m', '1y', '3y', or '5y'
        
    Returns:
        Dict with return_percentage, time_series data, and period stats
    """
    
    # Determine date range
    end_date = datetime.now()
    
    if time_period == '6m':
        start_date = end_date - timedelta(days=180)
        days = 180
    elif time_period == '1y':
        start_date = end_date - timedelta(days=365)
        days = 365
    elif time_period == '3y':
        start_date = end_date - timedelta(days=1095)
        days = 1095
    elif time_period == '5y':
        start_date = end_date - timedelta(days=1825)
        days = 1825
    else:
        start_date = end_date - timedelta(days=365)
        days = 365
    
    logger.info(f"Calculating returns from {start_date.date()} to {end_date.date()}")
    
    # Fetch historical data for all tickers
    ticker_data = {}
    valid_allocations = []
    
    for alloc in allocations:
        ticker = alloc['ticker']
        allocation_pct = alloc['allocation_percentage'] / 100.0
        
        try:
            logger.info(f"Fetching data for {ticker}")
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            
            if hist.empty:
                logger.warning(f"No data for {ticker}, skipping")
                continue
            
            # Use adjusted close for accurate returns
            ticker_data[ticker] = hist['Close']
            valid_allocations.append({
                'ticker': ticker,
                'allocation': allocation_pct
            })
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            continue
    
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
    df = df.fillna(method='ffill')
    
    # Calculate portfolio value over time (starting at 100)
    portfolio_values = pd.Series(0, index=df.index)
    
    for alloc in valid_allocations:
        ticker = alloc['ticker']
        allocation = alloc['allocation']
        
        # Normalize to start at 100 for this ticker
        normalized_prices = (df[ticker] / df[ticker].iloc[0]) * 100
        
        # Add weighted contribution to portfolio
        portfolio_values += normalized_prices * allocation
    
    # Calculate returns (portfolio starts at 100, so return is (current - 100))
    returns = ((portfolio_values - 100) / 100) * 100
    
    # Build time series for charting
    time_series = []
    for date, return_pct in returns.items():
        time_series.append({
            'date': date.strftime('%Y-%m-%d'),
            'return_percentage': round(float(return_pct), 2)
        })
    
    # Calculate period returns
    current_return = float(returns.iloc[-1])
    
    period_stats = {}
    
    # 6 month return
    if len(returns) >= 126:  # ~6 months of trading days
        six_month_return = float(returns.iloc[-1] - returns.iloc[-126])
        period_stats['6m_return'] = round(six_month_return, 2)
    else:
        period_stats['6m_return'] = round(current_return, 2)
    
    # 1 year return
    if len(returns) >= 252:  # ~1 year of trading days
        one_year_return = float(returns.iloc[-1] - returns.iloc[-252])
        period_stats['1y_return'] = round(one_year_return, 2)
    else:
        period_stats['1y_return'] = round(current_return, 2)
    
    # 3 year return
    if len(returns) >= 756:  # ~3 years of trading days
        three_year_return = float(returns.iloc[-1] - returns.iloc[-756])
        period_stats['3y_return'] = round(three_year_return, 2)
    else:
        period_stats['3y_return'] = None
    
    # 5 year return
    if len(returns) >= 1260:  # ~5 years of trading days
        five_year_return = float(returns.iloc[-1] - returns.iloc[-1260])
        period_stats['5y_return'] = round(five_year_return, 2)
    else:
        period_stats['5y_return'] = None
    
    logger.info(f"Calculated returns: {current_return:.2f}% for {time_period}")
    
    return {
        'return_percentage': round(current_return, 2),
        'time_series': time_series,
        'period_stats': period_stats,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d')
    }
