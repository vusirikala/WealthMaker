# Testing Guide - Shared Assets Database System

## ✅ Automated Testing (Just Completed)

The backend testing agent ran **35 comprehensive tests** - all passed! 

Results:
- ✅ Admin endpoints working
- ✅ User data endpoints working  
- ✅ Authentication enforced
- ✅ Data structure validation passed
- ✅ Database initialization working

## 🧪 Manual Testing Options

### Option 1: Using cURL (Command Line)

#### Step 1: Get Authentication Token
First, login through the UI at: https://app-preview-89.preview.emergentagent.com

Then extract your session token:
```bash
# In browser DevTools > Application > Cookies
# Copy the 'session_token' value
SESSION_TOKEN="your_token_here"
```

#### Step 2: Test Admin Endpoints

**Check Database Status:**
```bash
curl -H "Authorization: Bearer $SESSION_TOKEN" \
  https://app-preview-89.preview.emergentagent.com/api/admin/database-stats
```

Expected response:
```json
{
  "total_assets": 53,
  "by_type": {
    "stocks": 50,
    "crypto": 2,
    "commodities": 1
  },
  "last_updated": "2025-11-08T...",
  "status": "active"
}
```

**Initialize Database (if needed):**
```bash
curl -X POST \
  -H "Authorization: Bearer $SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  https://app-preview-89.preview.emergentagent.com/api/admin/initialize-database
```

This runs in background. Check status again after ~30 seconds.

**List All Assets:**
```bash
curl -H "Authorization: Bearer $SESSION_TOKEN" \
  https://app-preview-89.preview.emergentagent.com/api/admin/list-assets
```

#### Step 3: Test User Data Endpoints

**Search for a Stock:**
```bash
curl -H "Authorization: Bearer $SESSION_TOKEN" \
  "https://app-preview-89.preview.emergentagent.com/api/data/search?q=Apple"
```

**Get Single Asset (AAPL):**
```bash
curl -H "Authorization: Bearer $SESSION_TOKEN" \
  https://app-preview-89.preview.emergentagent.com/api/data/asset/AAPL
```

Expected response structure:
```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "assetType": "stock",
  "fundamentals": {
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "marketCap": 3000000000000,
    "...": "..."
  },
  "historical": {
    "earnings": [...],
    "priceHistory": {...},
    "patterns": [...]
  },
  "live": {
    "currentPrice": {
      "price": 195.23,
      "change": 2.45,
      "changePercent": 1.27
    },
    "recentNews": [...],
    "upcomingEvents": [...]
  }
}
```

**Get Multiple Assets (Batch):**
```bash
curl -X POST \
  -H "Authorization: Bearer $SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '["AAPL", "MSFT", "GOOGL"]' \
  https://app-preview-89.preview.emergentagent.com/api/data/assets/batch
```

**Track a Stock:**
```bash
curl -X POST \
  -H "Authorization: Bearer $SESSION_TOKEN" \
  "https://app-preview-89.preview.emergentagent.com/api/data/track?symbol=AAPL"
```

**Get Tracked Stocks:**
```bash
curl -H "Authorization: Bearer $SESSION_TOKEN" \
  https://app-preview-89.preview.emergentagent.com/api/data/tracked
```

### Option 2: Using Postman

1. **Import Collection:**
   - Base URL: `https://app-preview-89.preview.emergentagent.com/api`
   - Add Authorization header: `Bearer YOUR_SESSION_TOKEN`

2. **Test Endpoints:**
   - GET `/admin/database-stats`
   - POST `/admin/initialize-database`
   - GET `/data/search?q=AAPL`
   - GET `/data/asset/AAPL`
   - POST `/data/assets/batch` (body: `["AAPL", "MSFT"]`)
   - POST `/data/track?symbol=AAPL`

### Option 3: Browser DevTools (Easiest)

1. **Open the app:** https://app-preview-89.preview.emergentagent.com
2. **Login** with any OAuth provider
3. **Open DevTools** (F12)
4. **Go to Console tab**
5. **Run these commands:**

```javascript
// Check database status
fetch('/api/admin/database-stats', {
  credentials: 'include'
}).then(r => r.json()).then(console.log)

// Search for Apple
fetch('/api/data/search?q=Apple', {
  credentials: 'include'
}).then(r => r.json()).then(console.log)

// Get AAPL data
fetch('/api/data/asset/AAPL', {
  credentials: 'include'
}).then(r => r.json()).then(console.log)

// Track AAPL
fetch('/api/data/track?symbol=AAPL', {
  method: 'POST',
  credentials: 'include'
}).then(r => r.json()).then(console.log)

// Get tracked stocks
fetch('/api/data/tracked', {
  credentials: 'include'
}).then(r => r.json()).then(console.log)
```

## 🎯 What to Verify

### ✅ Admin Endpoints Working
- Database stats returns counts
- Initialize works (runs in background)
- List assets returns symbols
- Add single asset works

### ✅ Data Endpoints Working
- Search returns relevant results
- Single asset has all sections (fundamentals, historical, live)
- Batch request returns multiple assets
- Track/untrack updates user's watchlist

### ✅ Data Structure Valid
Each asset should have:
```
{
  fundamentals: { sector, industry, description, marketCap }
  historical: {
    earnings: [],
    priceHistory: { returns, volatility },
    patterns: []
  }
  live: {
    currentPrice: { price, change, changePercent },
    recentNews: [],
    upcomingEvents: []
  }
}
```

## 🐛 Troubleshooting

**"Asset not found in database"**
- Database needs initialization
- Run: POST `/api/admin/initialize-database`
- Wait 30-60 seconds, try again

**"Not authenticated"**
- Need to login through UI first
- Check session_token cookie exists
- Token expires after 7 days

**"Database empty"**
- Run initialization endpoint
- It populates top 50 S&P 500 + crypto + commodities
- Takes 5-10 minutes for full initialization

## 📊 Current Test Results

From automated testing:
```
✅ 35/35 tests passed (100%)
✅ Admin endpoints: 5/5 passed
✅ Data endpoints: 6/6 passed
✅ Data structure validation: 4/4 passed
✅ Authentication: 4/4 passed
✅ Edge cases: 16/16 passed
```

## 🚀 Next Steps After Testing

Once you verify endpoints work:

1. **Initialize database** (if not done): `POST /api/admin/initialize-database`
2. **Build AI Insights Engine** - fetches data from shared DB
3. **Build Action Recommendations** - uses shared data for analysis
4. **Update Frontend** - display data from new endpoints

Database is ready for production use! 🎉
