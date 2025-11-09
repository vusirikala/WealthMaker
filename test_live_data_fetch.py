#!/usr/bin/env python3
"""
Test live data fetching for specific symbols
"""
import yfinance as yf
from datetime import datetime, timezone, timedelta

def test_symbol_data(symbol):
    print(f"\n=== Testing {symbol} ===")
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        print(f"Symbol: {symbol}")
        print(f"Name: {info.get('longName', 'N/A')}")
        
        # Test current price extraction
        current_price = float(info.get('currentPrice', 0)) or float(info.get('regularMarketPrice', 0))
        print(f"Current price: {current_price}")
        
        # Test 52-week high/low extraction with multiple keys
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
        
        print(f"52-week high (from API): {fifty_two_week_high}")
        print(f"52-week low (from API): {fifty_two_week_low}")
        
        # Try to get historical data for calculation
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            hist_52w = ticker.history(start=start_date, end=end_date)
            
            if not hist_52w.empty:
                hist_high = float(hist_52w['High'].max())
                hist_low = float(hist_52w['Low'].min())
                print(f"52-week high (from history): {hist_high}")
                print(f"52-week low (from history): {hist_low}")
                
                # Use historical if API values are None
                if fifty_two_week_high is None:
                    fifty_two_week_high = hist_high
                if fifty_two_week_low is None:
                    fifty_two_week_low = hist_low
                    
                print(f"Final 52-week high: {fifty_two_week_high}")
                print(f"Final 52-week low: {fifty_two_week_low}")
            else:
                print("❌ No historical data available")
        except Exception as e:
            print(f"❌ Error getting historical data: {e}")
        
        # Print some key info fields to debug
        print(f"Available info keys: {list(info.keys())[:20]}...")  # First 20 keys
        
        # Look for 52-week related keys
        week_keys = [k for k in info.keys() if '52' in str(k).lower() or 'week' in str(k).lower() or 'year' in str(k).lower()]
        print(f"52-week related keys: {week_keys}")
        
    except Exception as e:
        print(f"❌ Error testing {symbol}: {e}")

if __name__ == "__main__":
    # Test the failing symbols
    test_symbols = ["SPY", "V", "PLTR"]
    
    for symbol in test_symbols:
        test_symbol_data(symbol)