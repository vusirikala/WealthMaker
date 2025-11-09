#!/usr/bin/env python3
"""
Initialize the shared assets database
Run this once to populate the database with top 50 stocks
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.shared_assets_db import shared_assets_service
from utils.database import db


async def main():
    print("="*60)
    print("🚀 Initializing WealthMaker Shared Assets Database")
    print("="*60)
    print()
    
    # Check if already initialized
    stats = await shared_assets_service.get_database_stats()
    
    if stats["total_assets"] > 0:
        print(f"✅ Database already initialized with {stats['total_assets']} assets")
        print(f"   - Stocks: {stats['by_type']['stocks']}")
        print(f"   - Crypto: {stats['by_type']['crypto']}")
        print(f"   - Commodities: {stats['by_type']['commodities']}")
        print(f"   - Last updated: {stats['last_updated']}")
        print()
        
        response = input("Do you want to re-initialize? (yes/no): ")
        if response.lower() != 'yes':
            print("Skipping initialization.")
            return
        print()
    
    # Initialize with top 50 S&P 500 + crypto + commodities
    print("📊 Initializing with:")
    print(f"   - Top 50 S&P 500 stocks")
    print(f"   - 2 Cryptocurrencies (BTC, ETH)")
    print(f"   - 1 Commodity (Gold)")
    print(f"   - Total: {len(shared_assets_service.ALL_ASSETS)} assets")
    print()
    print("⏱️  This will take approximately 5-10 minutes...")
    print("    Fetching 3 years of historical data for each asset...")
    print()
    
    # Run initialization
    result = await shared_assets_service.initialize_database()
    
    print()
    print("="*60)
    print("🎉 Initialization Complete!")
    print("="*60)
    print(f"✅ Successfully initialized: {result['initialized']} assets")
    print(f"❌ Failed: {result['failed']} assets")
    print()
    
    # Show stats
    stats = await shared_assets_service.get_database_stats()
    print("📈 Database Statistics:")
    print(f"   - Total assets: {stats['total_assets']}")
    print(f"   - Stocks: {stats['by_type']['stocks']}")
    print(f"   - Crypto: {stats['by_type']['crypto']}")
    print(f"   - Commodities: {stats['by_type']['commodities']}")
    print()
    
    print("💡 Next step: Update live data with:")
    print("   python update_live_data.py")
    print()


if __name__ == "__main__":
    asyncio.run(main())
