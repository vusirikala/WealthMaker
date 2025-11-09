# Shared Assets Database - Setup & Management

## 🎯 Architecture Overview

**One Shared Database for All Users:**
- Pre-populated with top 50 S&P 500 stocks + BTC + ETH + Gold
- Updated 2x daily (morning & evening)
- All users read from this single source
- No user-level database management needed

## 📋 Initial Setup (One-Time)

### Step 1: Initialize Database
```bash
cd /app/backend
python3 initialize_db.py
```

This will:
- Fetch 3 years of historical data for 50+ stocks
- Takes 5-10 minutes
- Only needs to be done ONCE

### Step 2: Update Live Data
```bash
cd /app/backend
python3 update_live_data.py
```

This will:
- Fetch current prices
- Fetch today's news
- Update analyst ratings
- Get upcoming events
- Takes 1-2 minutes

## 🔄 Regular Maintenance

### Update Live Data (2x Daily Recommended)

**Morning Update (9 AM ET):**
```bash
cd /app/backend && python3 update_live_data.py
```

**Evening Update (4 PM ET):**
```bash
cd /app/backend && python3 update_live_data.py
```

### Future: Automated Updates with Cron

Add to crontab:
```bash
# Update at 9 AM ET (14:00 UTC)
0 14 * * * cd /app/backend && python3 update_live_data.py >> /var/log/live_data.log 2>&1

# Update at 4 PM ET (21:00 UTC)  
0 21 * * * cd /app/backend && python3 update_live_data.py >> /var/log/live_data.log 2>&1
```

## 📊 Available Assets

### Top 50 S&P 500 Stocks:
**Technology:** AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, ADBE, NFLX, CRM, INTC, AMD, TXN, CSCO, QCOM

**Healthcare:** JNJ, UNH, LLY, ABBV, PFE, MRK, TMO, DHR, ABT, BMY

**Finance:** V, JPM, MA, BAC, WFC

**Consumer:** WMT, PG, HD, DIS, COST, KO, PEP, NKE, MCD, UPS, PM

**Energy:** XOM, CVX, NEE

**Industrials:** RTX, HON, ACN

### Cryptocurrency:
- BTC-USD (Bitcoin)
- ETH-USD (Ethereum)

### Commodities:
- GC=F (Gold Futures)

## 🔧 Admin Operations

### Check Database Status
```bash
cd /app/backend
python3 -c "
import asyncio
from services.shared_assets_db import shared_assets_service

async def check():
    stats = await shared_assets_service.get_database_stats()
    print(f'Total Assets: {stats[\"total_assets\"]}')
    print(f'Stocks: {stats[\"by_type\"][\"stocks\"]}')
    print(f'Crypto: {stats[\"by_type\"][\"crypto\"]}')
    print(f'Commodities: {stats[\"by_type\"][\"commodities\"]}')
    print(f'Last Updated: {stats[\"last_updated\"]}')

asyncio.run(check())
"
```

### Add a New Stock
```bash
cd /app/backend
python3 -c "
import asyncio
from services.shared_assets_db import shared_assets_service

async def add_stock():
    result = await shared_assets_service.initialize_database(['TSLA'])
    print(f'Added TSLA: {result}')

asyncio.run(add_stock())
"
```

### Re-Initialize Everything
```bash
cd /app/backend
python3 initialize_db.py
# When prompted, type 'yes' to confirm
```

## 🚫 What Users DON'T See

Users should NEVER see:
- ❌ "Initialize Database" buttons
- ❌ "Update News" buttons
- ❌ Admin controls

Users should ONLY:
- ✅ Add stocks to their portfolio
- ✅ Add stocks to their watchlist
- ✅ View data from shared database
- ✅ See news for their stocks

## 🎯 User Experience Flow

1. User adds AAPL to portfolio
2. System fetches AAPL data from **shared database**
3. User sees:
   - Current price
   - 3-year history
   - Recent news
   - Upcoming events
4. No database initialization needed!

## 📝 Data Structure

Each asset in shared database contains:

```javascript
{
  symbol: "AAPL",
  name: "Apple Inc.",
  assetType: "stock",
  
  fundamentals: {
    sector: "Technology",
    industry: "Consumer Electronics",
    marketCap: 3000000000000,
    // ... more static data
  },
  
  historical: {
    earnings: [], // 12 quarters
    priceHistory: {}, // 3 years
    patterns: []
  },
  
  live: {
    currentPrice: {
      price: 195.23,
      change: 2.45,
      changePercent: 1.27
    },
    recentNews: [], // Last 30 days
    upcomingEvents: []
  }
}
```

## 🔐 Future: Admin Panel

For later implementation:
- Separate admin role
- UI for managing database
- Add/remove stocks
- Force refresh specific stocks
- View system health

For now, use command-line scripts above.

## ✅ Quick Checklist

Initial Setup:
- [ ] Run `initialize_db.py` (once)
- [ ] Run `update_live_data.py` (daily)
- [ ] Verify users can add stocks
- [ ] Verify news appears for added stocks

Daily Maintenance:
- [ ] Morning update (9 AM)
- [ ] Evening update (4 PM)
- [ ] Check logs for errors

## 🎉 You're Done!

The shared database is now:
- ✅ Populated with 50+ stocks
- ✅ Updated with live prices & news
- ✅ Ready for all users
- ✅ No user-facing admin buttons

Users can now add stocks and see data immediately!
