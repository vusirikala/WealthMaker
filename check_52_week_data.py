#!/usr/bin/env python3
"""
Check 52-week high/low data for specific symbols
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

async def check_52_week_data():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    # Test symbols that failed
    test_symbols = ["SPY", "V", "PLTR"]
    
    for symbol in test_symbols:
        print(f"\n=== Checking {symbol} ===")
        
        # Get asset from database
        asset = await db.shared_assets.find_one({"symbol": symbol})
        
        if asset:
            live_data = asset.get('live', {})
            current_price = live_data.get('currentPrice', {})
            
            print(f"Asset found: {asset.get('name', 'Unknown')}")
            print(f"Asset type: {asset.get('assetType', 'Unknown')}")
            print(f"Last updated: {asset.get('lastUpdated', 'Unknown')}")
            
            print(f"Current price: {current_price.get('price', 'N/A')}")
            print(f"52-week high: {current_price.get('fiftyTwoWeekHigh', 'N/A')}")
            print(f"52-week low: {current_price.get('fiftyTwoWeekLow', 'N/A')}")
            
            # Check if live data exists
            if not live_data:
                print("❌ No live data found")
            elif not current_price:
                print("❌ No current price data found")
            else:
                high = current_price.get('fiftyTwoWeekHigh')
                low = current_price.get('fiftyTwoWeekLow')
                
                if high is None or low is None:
                    print("❌ 52-week high/low values are None")
                elif high == 0 or low == 0:
                    print("❌ 52-week high/low values are 0")
                else:
                    print("✅ 52-week high/low values look good")
        else:
            print("❌ Asset not found in database")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_52_week_data())