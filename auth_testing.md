# Auth-Gated App Testing Playbook

## Step 1: Create Test User & Session

```bash
mongosh --eval "
use('test_database');
var userId = 'test-user-' + Date.now();
var sessionToken = 'test_session_' + Date.now();
db.users.insertOne({
  _id: userId,
  email: 'test.user.' + Date.now() + '@example.com',
  name: 'Test User',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date()
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
});
print('Session token: ' + sessionToken);
print('User ID: ' + userId);
"
```

## Step 2: Test Backend API

```bash
# Test auth endpoint
curl -X GET "https://wealth-dashboard-77.preview.emergentagent.com/api/auth/me" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"

# Test portfolio endpoint
curl -X GET "https://wealth-dashboard-77.preview.emergentagent.com/api/portfolio" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

## Step 3: Browser Testing

```javascript
// Set cookie and navigate
await page.context.add_cookies([{
    "name": "session_token",
    "value": "YOUR_SESSION_TOKEN",
    "domain": "smartfolio-20.preview.emergentagent.com",
    "path": "/",
    "httpOnly": true,
    "secure": true,
    "sameSite": "None"
}]);
await page.goto("https://wealth-dashboard-77.preview.emergentagent.com");
```

## Critical Fix: ID Schema

MongoDB + Pydantic ID Mapping - User document uses `_id` field which maps to Pydantic `id` field.

## Success Indicators
- ✅ /api/auth/me returns user data
- ✅ Dashboard loads without redirect
- ✅ Chat interface works
- ✅ Portfolio displays correctly
- ✅ News feed loads

## Failure Indicators
- ❌ "User not found" errors
- ❌ 401 Unauthorized responses
- ❌ Redirect to login page
