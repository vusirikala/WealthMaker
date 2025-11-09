#!/usr/bin/env python3
"""
Update live data for all assets in the shared database
Run this 2x per day (morning & evening) to keep prices and news fresh
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.shared_assets_db import shared_assets_service


async def main():
    print("="*60)
    print("🔄 Updating Live Data for All Assets")
    print("="*60)
    print()
    
    # Get current stats
    stats = await shared_assets_service.get_database_stats()
    
    if stats["total_assets"] == 0:
        print("❌ Database is empty. Please run initialize_db.py first")
        return
    
    print(f"📊 Updating {stats['total_assets']} assets...")
    print(f"   - Stocks: {stats['by_type']['stocks']}")
    print(f"   - Crypto: {stats['by_type']['crypto']}")
    print(f"   - Commodities: {stats['by_type']['commodities']}")
    print()
    print("⏱️  This will take approximately 1-2 minutes...")
    print()
    
    # Update live data
    result = await shared_assets_service.update_live_data()
    
    print()
    print("="*60)
    print("✅ Live Data Update Complete!")
    print("="*60)
    print(f"Updated: {result['updated']}/{result['total']} assets")
    print()
    print("📰 Latest prices and news are now available!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
