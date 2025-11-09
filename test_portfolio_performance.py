#!/usr/bin/env python3
"""
Quick test for portfolio performance endpoint
"""

import requests
import json
import time
import uuid
import subprocess

def setup_test_data():
    """Setup test user and portfolio"""
    timestamp = int(time.time())
    user_id = f"test-user-{timestamp}"
    session_token = f"test_session_{timestamp}"
    portfolio_id = str(uuid.uuid4())
    
    # Create MongoDB script
    mongo_script = f'''
use('test_database');
var userId = '{user_id}';
var sessionToken = '{session_token}';
var portfolioId = '{portfolio_id}';

// Create user
db.users.insertOne({{
  _id: userId,
  email: 'test.user.{timestamp}@example.com',
  name: 'Test User {timestamp}',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date()
}});

// Create session
db.user_sessions.insertOne({{
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
}});

// Create portfolio
db.user_portfolios.insertOne({{
  _id: portfolioId,
  user_id: userId,
  name: "Test Performance Portfolio",
  goal: "Growth and Income",
  type: "manual",
  risk_tolerance: "moderate",
  roi_expectations: 12,
  allocations: [
    {{
      "ticker": "AAPL",
      "allocation_percentage": 40,
      "sector": "Technology",
      "asset_type": "stock"
    }},
    {{
      "ticker": "GOOGL", 
      "allocation_percentage": 35,
      "sector": "Technology",
      "asset_type": "stock"
    }},
    {{
      "ticker": "MSFT",
      "allocation_percentage": 25,
      "sector": "Technology", 
      "asset_type": "stock"
    }}
  ],
  holdings: [],
  total_invested: 0,
  current_value: 0,
  total_return: 0,
  total_return_percentage: 0,
  is_active: true,
  created_at: new Date(),
  updated_at: new Date(),
  last_invested_at: null
}});

print('Setup complete');
'''
    
    # Execute MongoDB script
    result = subprocess.run(
        ['mongosh', '--eval', mongo_script],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        return user_id, session_token, portfolio_id
    else:
        print(f"Setup failed: {result.stderr}")
        return None, None, None

def test_performance_endpoint():
    """Test the portfolio performance endpoint"""
    print("🔧 Setting up test data...")
    user_id, session_token, portfolio_id = setup_test_data()
    
    if not all([user_id, session_token, portfolio_id]):
        print("❌ Failed to setup test data")
        return
    
    print(f"✅ Created test portfolio: {portfolio_id}")
    
    base_url = "https://app-preview-89.preview.emergentagent.com"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_token}'
    }
    
    # Test 1-year performance
    print("\n📊 Testing 1-year performance...")
    url = f"{base_url}/api/portfolios-v2/{portfolio_id}/performance?time_period=1y"
    
    try:
        response = requests.get(url, headers=headers, timeout=60)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Response structure:")
            print(f"  - return_percentage: {data.get('return_percentage')}")
            print(f"  - time_series length: {len(data.get('time_series', []))}")
            print(f"  - period_stats: {data.get('period_stats')}")
            print(f"  - sp500_comparison: {data.get('sp500_comparison', {}).keys()}")
            print(f"  - sp500_time_series length: {len(data.get('sp500_comparison', {}).get('time_series', []))}")
            print(f"  - sp500_current_return: {data.get('sp500_comparison', {}).get('current_return')}")
            print(f"  - start_date: {data.get('start_date')}")
            print(f"  - end_date: {data.get('end_date')}")
            
            # Test if we have actual data
            if len(data.get('time_series', [])) > 0:
                print("✅ Portfolio time series data available")
            else:
                print("❌ No portfolio time series data")
                
            if len(data.get('sp500_comparison', {}).get('time_series', [])) > 0:
                print("✅ S&P 500 time series data available")
            else:
                print("❌ No S&P 500 time series data")
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_performance_endpoint()