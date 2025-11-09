# Quick Start - Add Stocks to Your Portfolio

## 🚀 Easy Way: Using Browser Console

### Step 1: Login to the App
Go to: https://portfolio-genius-28.preview.emergentagent.com
Login with any OAuth provider (Google, GitHub, etc.)

### Step 2: Open Browser DevTools
- Press **F12** (or Right-click → Inspect)
- Go to **Console** tab

### Step 3: Add Stocks to Your Portfolio

Copy and paste these commands **one at a time** in the console:

```javascript
// Add Apple stock (10 shares bought at $150)
fetch('/api/portfolios/add-stock?symbol=AAPL&quantity=10&purchase_price=150&purchase_date=2023-01-15', {
  method: 'POST',
  credentials: 'include'
}).then(r => r.json()).then(data => {
  console.log('✅ Added AAPL:', data);
})

// Add Microsoft (5 shares bought at $300)
fetch('/api/portfolios/add-stock?symbol=MSFT&quantity=5&purchase_price=300&purchase_date=2023-06-20', {
  method: 'POST',
  credentials: 'include'
}).then(r => r.json()).then(data => {
  console.log('✅ Added MSFT:', data);
})

// Add Google (3 shares bought at $120)
fetch('/api/portfolios/add-stock?symbol=GOOGL&quantity=3&purchase_price=120&purchase_date=2024-01-10', {
  method: 'POST',
  credentials: 'include'
}).then(r => r.json()).then(data => {
  console.log('✅ Added GOOGL:', data);
})

// Add Bitcoin (0.5 BTC bought at $40,000)
fetch('/api/portfolios/add-stock?symbol=BTC-USD&quantity=0.5&purchase_price=40000&purchase_date=2024-03-10', {
  method: 'POST',
  credentials: 'include'
}).then(r => r.json()).then(data => {
  console.log('✅ Added BTC-USD:', data);
})
```

### Step 4: View Your Portfolio

```javascript
// Get your complete portfolio with current prices
fetch('/api/portfolios/my-portfolio', {
  credentials: 'include'
}).then(r => r.json()).then(data => {
  console.log('📊 Your Portfolio:', data);
  console.table(data.portfolio.holdings);
})
```

## 📝 What Each Command Does

**add-stock endpoint:**
- `symbol` - Stock ticker (AAPL, MSFT, BTC-USD, etc.)
- `quantity` - Number of shares you own
- `purchase_price` - Price per share when you bought it
- `purchase_date` - When you bought it (optional, defaults to today)

The endpoint automatically:
- ✅ Fetches current price from shared database
- ✅ Calculates your gain/loss
- ✅ Updates portfolio totals
- ✅ Calculates allocation percentages
- ✅ Groups by sector

## 🎯 What You'll See

After adding stocks, you'll have:

```
My Portfolio
├── Total Value: $X,XXX
├── Cost Basis: $X,XXX  
├── Gain/Loss: $XXX (+X.X%)
└── Holdings:
    ├── AAPL - 10 shares
    ├── MSFT - 5 shares
    ├── GOOGL - 3 shares
    └── BTC-USD - 0.5 shares
```

Each holding shows:
- Current price
- Total value
- Your gain/loss
- Allocation % in portfolio
- Sector

## ⚠️ Important Notes

**Before adding stocks, the shared database must be initialized!**

If you get "Stock not found in database", run this first:

```javascript
// Initialize database with top stocks (takes 2-3 minutes)
fetch('/api/admin/initialize-database', {
  method: 'POST',
  credentials: 'include'
}).then(r => r.json()).then(data => {
  console.log('Database initialization started:', data);
  console.log('Wait 2-3 minutes, then add stocks');
})

// Check initialization progress
fetch('/api/admin/database-stats', {
  credentials: 'include'
}).then(r => r.json()).then(data => {
  console.log('Database status:', data);
})
```

## 🔧 Alternative: Using cURL

If you prefer command line:

```bash
# Get your session token from browser cookies first
SESSION_TOKEN="your_token_here"

# Add Apple stock
curl -X POST "https://portfolio-genius-28.preview.emergentagent.com/api/portfolios/add-stock?symbol=AAPL&quantity=10&purchase_price=150&purchase_date=2023-01-15" \
  -H "Authorization: Bearer $SESSION_TOKEN"

# View portfolio
curl "https://portfolio-genius-28.preview.emergentagent.com/api/portfolios/my-portfolio" \
  -H "Authorization: Bearer $SESSION_TOKEN"
```

## 🎨 Next Steps

Once you have stocks in your portfolio:

1. **View in UI** - The dashboard will show your holdings
2. **Get Insights** - AI will analyze your portfolio
3. **See Recommendations** - Get personalized action items
4. **Track Performance** - Monitor gains/losses

## 💡 Pro Tips

- You can add the same stock multiple times (it combines quantities)
- Use realistic purchase prices for accurate gain/loss
- Add dates from the past to see historical performance
- Mix stocks, crypto, and commodities for diversification

---

**Ready to test?** Login, open console, paste commands, and you're done! 🚀
