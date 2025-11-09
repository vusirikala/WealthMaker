"""
Portfolio Analytics Service
Calculates risk metrics, correlations, and distributions
"""
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PortfolioAnalytics:
    """Service for calculating portfolio analytics"""
    
    @staticmethod
    async def calculate_risk_metrics(allocations: List[Dict[str, Any]], db=None) -> Dict[str, Any]:
        """
        Calculate portfolio risk metrics:
        - Beta (vs S&P 500)
        - Sharpe Ratio
        - Volatility (Standard Deviation)
        - Max Drawdown
        """
        if not allocations:
            return {
                "beta": 0,
                "sharpe_ratio": 0,
                "volatility": 0,
                "max_drawdown": 0
            }
        
        # Fetch 1 year of historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Get stock data
        tickers = [alloc['ticker'] for alloc in allocations]
        weights = np.array([alloc['allocation_percentage'] / 100.0 for alloc in allocations])
        
        try:
            # Fetch portfolio stocks data
            stock_data = {}
            for ticker in tickers:
                stock = yf.Ticker(ticker)
                hist = stock.history(start=start_date, end=end_date)
                if not hist.empty:
                    stock_data[ticker] = hist['Close']
            
            # Fetch S&P 500 data
            sp500 = yf.Ticker('^GSPC')
            sp500_hist = sp500.history(start=start_date, end=end_date)
            
            if not stock_data or sp500_hist.empty:
                logger.warning("Insufficient data for risk calculations")
                return {
                    "beta": None,
                    "sharpe_ratio": None,
                    "volatility": None,
                    "max_drawdown": None
                }
            
            # Create DataFrame
            df = pd.DataFrame(stock_data)
            df = df.ffill()
            
            # Calculate daily returns
            returns = df.pct_change().dropna()
            
            # Calculate portfolio returns (weighted average)
            portfolio_returns = (returns * weights).sum(axis=1)
            
            # S&P 500 returns
            sp500_returns = sp500_hist['Close'].pct_change().dropna()
            
            # Align dates
            common_dates = portfolio_returns.index.intersection(sp500_returns.index)
            portfolio_returns = portfolio_returns.loc[common_dates]
            sp500_returns = sp500_returns.loc[common_dates]
            
            # 1. Beta calculation
            covariance = np.cov(portfolio_returns, sp500_returns)[0][1]
            sp500_variance = np.var(sp500_returns)
            beta = covariance / sp500_variance if sp500_variance > 0 else 1.0
            
            # 2. Sharpe Ratio (assuming 2% risk-free rate)
            risk_free_rate = 0.02
            daily_rf_rate = risk_free_rate / 252  # Daily risk-free rate
            excess_returns = portfolio_returns - daily_rf_rate
            sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252) if excess_returns.std() > 0 else 0
            
            # 3. Volatility (Annualized Standard Deviation)
            volatility = portfolio_returns.std() * np.sqrt(252) * 100  # As percentage
            
            # 4. Max Drawdown
            cumulative_returns = (1 + portfolio_returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min() * 100  # As percentage
            
            return {
                "beta": round(float(beta), 2),
                "sharpe_ratio": round(float(sharpe_ratio), 2),
                "volatility": round(float(volatility), 2),
                "max_drawdown": round(float(max_drawdown), 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {
                "beta": None,
                "sharpe_ratio": None,
                "volatility": None,
                "max_drawdown": None
            }
    
    @staticmethod
    async def calculate_correlation_matrix(allocations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate correlation matrix between portfolio stocks
        """
        if len(allocations) < 2:
            return {"correlations": [], "tickers": []}
        
        # Fetch 6 months of data for correlation
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        tickers = [alloc['ticker'] for alloc in allocations]
        
        try:
            # Fetch data for all tickers
            stock_data = {}
            for ticker in tickers:
                stock = yf.Ticker(ticker)
                hist = stock.history(start=start_date, end=end_date)
                if not hist.empty:
                    stock_data[ticker] = hist['Close']
            
            if len(stock_data) < 2:
                return {"correlations": [], "tickers": []}
            
            # Create DataFrame and calculate returns
            df = pd.DataFrame(stock_data)
            df = df.ffill()
            returns = df.pct_change().dropna()
            
            # Calculate correlation matrix
            corr_matrix = returns.corr()
            
            # Convert to list format for frontend
            correlations = []
            ticker_list = list(corr_matrix.columns)
            
            for i, ticker1 in enumerate(ticker_list):
                row = []
                for j, ticker2 in enumerate(ticker_list):
                    row.append(round(float(corr_matrix.iloc[i, j]), 2))
                correlations.append(row)
            
            return {
                "correlations": correlations,
                "tickers": ticker_list
            }
            
        except Exception as e:
            logger.error(f"Error calculating correlations: {e}")
            return {"correlations": [], "tickers": []}
    
    @staticmethod
    async def calculate_distributions(allocations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate geographic and market cap distributions
        """
        if not allocations:
            return {
                "geography": [],
                "market_cap": []
            }
        
        geography_dist = {}
        market_cap_dist = {}
        
        try:
            for alloc in allocations:
                ticker = alloc['ticker']
                allocation_pct = alloc['allocation_percentage']
                
                # Fetch stock info
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Geography classification (simplified)
                country = info.get('country', 'Unknown')
                if country in ['United States', 'USA']:
                    geo_region = 'US'
                elif country in ['China', 'India', 'Brazil', 'Russia', 'South Africa', 'Mexico', 'Indonesia', 'Turkey']:
                    geo_region = 'Emerging Markets'
                elif country != 'Unknown':
                    geo_region = 'International Developed'
                else:
                    geo_region = 'Unknown'
                
                geography_dist[geo_region] = geography_dist.get(geo_region, 0) + allocation_pct
                
                # Market cap classification
                market_cap = info.get('marketCap', 0)
                if market_cap >= 200_000_000_000:  # $200B+
                    cap_category = 'Mega Cap'
                elif market_cap >= 10_000_000_000:  # $10B+
                    cap_category = 'Large Cap'
                elif market_cap >= 2_000_000_000:  # $2B+
                    cap_category = 'Mid Cap'
                elif market_cap > 0:
                    cap_category = 'Small Cap'
                else:
                    cap_category = 'Unknown'
                
                market_cap_dist[cap_category] = market_cap_dist.get(cap_category, 0) + allocation_pct
            
            # Convert to list format
            geography_list = [
                {"name": k, "value": round(v, 2)} 
                for k, v in geography_dist.items()
            ]
            
            market_cap_list = [
                {"name": k, "value": round(v, 2)} 
                for k, v in market_cap_dist.items()
            ]
            
            return {
                "geography": geography_list,
                "market_cap": market_cap_list
            }
            
        except Exception as e:
            logger.error(f"Error calculating distributions: {e}")
            return {
                "geography": [],
                "market_cap": []
            }
    
    @staticmethod
    async def calculate_dividend_info(allocations: List[Dict[str, Any]], holdings: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate dividend/income information
        """
        if not allocations:
            return {
                "total_annual_income": 0,
                "dividend_yield": 0,
                "dividend_stocks": []
            }
        
        try:
            dividend_stocks = []
            total_dividend_income = 0
            total_value = 0
            
            for alloc in allocations:
                ticker = alloc['ticker']
                
                # Get stock info
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Get dividend data
                dividend_rate = info.get('dividendRate', 0)  # Annual dividend per share
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                
                # Calculate dividend yield manually if we have the data
                if dividend_rate > 0 and current_price > 0:
                    dividend_yield = (dividend_rate / current_price) * 100
                else:
                    # Fallback to provided dividendYield (already in decimal form, needs * 100)
                    raw_yield = info.get('dividendYield', 0)
                    dividend_yield = raw_yield * 100 if raw_yield and raw_yield < 1 else raw_yield
                
                if holdings:
                    # Calculate actual dividend income based on holdings
                    holding = next((h for h in holdings if h['ticker'] == ticker), None)
                    if holding:
                        shares = holding.get('shares', 0)
                        current_value = holding.get('current_value', 0)
                        annual_income = dividend_rate * shares
                        
                        total_dividend_income += annual_income
                        total_value += current_value
                        
                        if dividend_rate > 0:
                            dividend_stocks.append({
                                "ticker": ticker,
                                "shares": shares,
                                "dividend_per_share": round(dividend_rate, 2),
                                "annual_income": round(annual_income, 2),
                                "yield": round(dividend_yield, 2)
                            })
                else:
                    # Estimate based on allocations (no actual holdings yet)
                    if dividend_rate > 0:
                        dividend_stocks.append({
                            "ticker": ticker,
                            "dividend_per_share": round(dividend_rate, 2),
                            "yield": round(dividend_yield, 2),
                            "allocation": alloc['allocation_percentage']
                        })
            
            # Calculate portfolio dividend yield
            portfolio_yield = (total_dividend_income / total_value * 100) if total_value > 0 else 0
            
            # Calculate monthly income
            monthly_income = total_dividend_income / 12
            
            return {
                "total_annual_income": round(total_dividend_income, 2),
                "monthly_income": round(monthly_income, 2),
                "dividend_yield": round(portfolio_yield, 2),
                "dividend_stocks": dividend_stocks
            }
            
        except Exception as e:
            logger.error(f"Error calculating dividend info: {e}")
            return {
                "total_annual_income": 0,
                "monthly_income": 0,
                "dividend_yield": 0,
                "dividend_stocks": []
            }
