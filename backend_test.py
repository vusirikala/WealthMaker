#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for WealthMaker Financial App
Tests authentication, shared assets database, admin endpoints, and data endpoints
"""

import requests
import sys
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

class WealthMakerAPITester:
    def __init__(self, base_url="https://dataflow-finance.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def setup_test_user(self) -> bool:
        """Create test user and session in MongoDB"""
        print("\n🔧 Setting up test user and session...")
        
        try:
            import subprocess
            timestamp = int(time.time())
            user_id = f"test-user-{timestamp}"
            session_token = f"test_session_{timestamp}"
            
            # Create MongoDB script
            mongo_script = f'''
use('test_database');
var userId = '{user_id}';
var sessionToken = '{session_token}';
db.users.insertOne({{
  _id: userId,
  email: 'test.user.{timestamp}@example.com',
  name: 'Test User {timestamp}',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date()
}});
db.user_sessions.insertOne({{
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
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
                self.session_token = session_token
                self.user_id = user_id
                print(f"✅ Test user created: {user_id}")
                print(f"✅ Session token: {session_token}")
                return True
            else:
                print(f"❌ MongoDB setup failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Setup error: {str(e)}")
            return False

    def make_request(self, method: str, endpoint: str, data: Dict = None, use_auth: bool = True) -> tuple:
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if use_auth and self.session_token:
            headers['Authorization'] = f'Bearer {self.session_token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            return response.status_code, response_data
            
        except requests.exceptions.Timeout:
            return 408, {"error": "Request timeout"}
        except requests.exceptions.ConnectionError:
            return 503, {"error": "Connection error"}
        except Exception as e:
            return 500, {"error": str(e)}

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication Endpoints...")
        
        # Test /auth/me with valid token
        status, data = self.make_request('GET', 'auth/me')
        success = status == 200 and 'email' in data
        self.log_test(
            "GET /auth/me (authenticated)", 
            success,
            f"Status: {status}" if not success else "",
            data
        )
        
        # Test /auth/me without token
        status, data = self.make_request('GET', 'auth/me', use_auth=False)
        success = status == 401
        self.log_test(
            "GET /auth/me (unauthenticated)", 
            success,
            f"Expected 401, got {status}" if not success else "",
            data
        )

    def test_logout_endpoint(self):
        """Test logout endpoint separately to avoid invalidating session"""
        print("\n🚪 Testing Logout Endpoint...")
        
        # Test logout
        status, data = self.make_request('POST', 'auth/logout')
        success = status == 200
        self.log_test(
            "POST /auth/logout", 
            success,
            f"Status: {status}" if not success else "",
            data
        )

    def test_admin_endpoints(self):
        """Test admin endpoints for shared assets database management"""
        print("\n🔧 Testing Admin Endpoints...")
        
        # Test database stats (should work before initialization)
        status, data = self.make_request('GET', 'admin/database-stats')
        success = status == 200 and 'total_assets' in data
        self.log_test(
            "GET /admin/database-stats", 
            success,
            f"Status: {status}" if not success else "",
            data
        )
        
        # Store initial stats for comparison
        initial_stats = data if success else {}
        
        # Test initialize database with small set of symbols
        test_symbols = ["AAPL", "MSFT", "GOOGL", "BTC-USD", "GC=F"]
        status, data = self.make_request('POST', 'admin/initialize-database', test_symbols)
        success = status == 200 and ('processing' in data.get('status', '') or 'already initialized' in data.get('message', ''))
        self.log_test(
            "POST /admin/initialize-database", 
            success,
            f"Status: {status}" if not success else "",
            data
        )
        
        # Wait for initialization to process
        if success and 'processing' in data.get('status', ''):
            print("⏳ Waiting 30 seconds for database initialization...")
            time.sleep(30)
            
            # Check stats again after initialization
            status, data = self.make_request('GET', 'admin/database-stats')
            success = status == 200 and data.get('total_assets', 0) > 0
            self.log_test(
                "GET /admin/database-stats (after init)", 
                success,
                f"Status: {status}, Assets: {data.get('total_assets', 0)}" if not success else "",
                data
            )
        
        # Test list assets
        status, data = self.make_request('GET', 'admin/list-assets')
        success = status == 200 and 'assets' in data
        self.log_test(
            "GET /admin/list-assets", 
            success,
            f"Status: {status}" if not success else "",
            {"asset_count": len(data.get('assets', [])) if isinstance(data, dict) else 0}
        )
        
        # Test add single asset
        status, data = self.make_request('POST', 'admin/add-asset?symbol=TSLA')
        success = status == 200 and ('processing' in data.get('status', '') or 'already exists' in data.get('message', ''))
        self.log_test(
            "POST /admin/add-asset (TSLA)", 
            success,
            f"Status: {status}" if not success else "",
            data
        )
        
        # Test update live data
        status, data = self.make_request('POST', 'admin/update-live-data')
        success = status == 200 and 'processing' in data.get('status', '')
        self.log_test(
            "POST /admin/update-live-data", 
            success,
            f"Status: {status}" if not success else "",
            data
        )

    def test_data_endpoints(self):
        """Test user data endpoints for querying shared database"""
        print("\n📊 Testing Data Endpoints...")
        
        # Test search assets
        status, data = self.make_request('GET', 'data/search?q=AAPL')
        success = status == 200 and 'results' in data
        self.log_test(
            "GET /data/search?q=AAPL", 
            success,
            f"Status: {status}" if not success else "",
            {"result_count": len(data.get('results', [])) if isinstance(data, dict) else 0}
        )
        
        # Test get single asset (AAPL should be initialized)
        status, data = self.make_request('GET', 'data/asset/AAPL')
        success = status == 200 and 'symbol' in data and 'fundamentals' in data and 'historical' in data and 'live' in data
        self.log_test(
            "GET /data/asset/AAPL", 
            success,
            f"Status: {status}" if not success else "",
            {
                "has_fundamentals": 'fundamentals' in data if isinstance(data, dict) else False,
                "has_historical": 'historical' in data if isinstance(data, dict) else False,
                "has_live": 'live' in data if isinstance(data, dict) else False
            }
        )
        
        # Validate asset data structure if successful
        if success and isinstance(data, dict):
            self.validate_asset_structure(data)
        
        # Test batch assets request
        batch_request = {"symbols": ["AAPL", "MSFT"]}
        status, data = self.make_request('POST', 'data/assets/batch', batch_request)
        success = status == 200 and 'data' in data
        self.log_test(
            "POST /data/assets/batch", 
            success,
            f"Status: {status}" if not success else "",
            {"assets_returned": len(data.get('data', {})) if isinstance(data, dict) else 0}
        )
        
        # Test track asset
        status, data = self.make_request('POST', 'data/track?symbol=AAPL')
        success = status == 200 and data.get('success') == True
        self.log_test(
            "POST /data/track?symbol=AAPL", 
            success,
            f"Status: {status}" if not success else "",
            data
        )
        
        # Test get tracked assets
        status, data = self.make_request('GET', 'data/tracked')
        success = status == 200 and 'symbols' in data
        self.log_test(
            "GET /data/tracked", 
            success,
            f"Status: {status}" if not success else "",
            {"tracked_count": len(data.get('symbols', [])) if isinstance(data, dict) else 0}
        )
        
        # Test untrack asset
        status, data = self.make_request('DELETE', 'data/track/AAPL')
        success = status == 200 and data.get('success') == True
        self.log_test(
            "DELETE /data/track/AAPL", 
            success,
            f"Status: {status}" if not success else "",
            data
        )

    def validate_asset_structure(self, asset_data: Dict[str, Any]):
        """Validate that asset data contains expected structure"""
        print("\n🔍 Validating Asset Data Structure...")
        
        required_fields = ['symbol', 'name', 'assetType']
        for field in required_fields:
            success = field in asset_data
            self.log_test(
                f"Asset has {field}", 
                success,
                f"Missing required field: {field}" if not success else ""
            )
        
        # Validate fundamentals section
        fundamentals = asset_data.get('fundamentals', {})
        fundamental_fields = ['sector', 'industry', 'description', 'marketCap']
        for field in fundamental_fields:
            success = field in fundamentals
            self.log_test(
                f"Fundamentals has {field}", 
                success,
                f"Missing fundamental field: {field}" if not success else ""
            )
        
        # Validate historical section
        historical = asset_data.get('historical', {})
        historical_fields = ['earnings', 'priceHistory', 'majorEvents', 'patterns']
        for field in historical_fields:
            success = field in historical
            self.log_test(
                f"Historical has {field}", 
                success,
                f"Missing historical field: {field}" if not success else ""
            )
        
        # Validate live section
        live = asset_data.get('live', {})
        live_fields = ['currentPrice', 'recentNews', 'analystRatings', 'upcomingEvents']
        for field in live_fields:
            success = field in live
            self.log_test(
                f"Live has {field}", 
                success,
                f"Missing live field: {field}" if not success else ""
            )

    def test_chat_endpoints(self):
        """Test chat functionality"""
        print("\n💬 Testing Chat Endpoints...")
        
        # Test get chat messages
        status, data = self.make_request('GET', 'chat/messages')
        success = status == 200 and isinstance(data, list)
        self.log_test(
            "GET /chat/messages", 
            success,
            f"Status: {status}, Type: {type(data)}" if not success else "",
            {"message_count": len(data) if isinstance(data, list) else 0}
        )
        
        # Test send message
        test_message = {
            "message": "I'm looking for a medium risk portfolio with 10% ROI expectations. I want to invest in technology stocks and some bonds."
        }
        
        status, data = self.make_request('POST', 'chat/send', test_message)
        success = status == 200 and 'message' in data
        self.log_test(
            "POST /chat/send", 
            success,
            f"Status: {status}" if not success else "",
            {"has_response": 'message' in data if isinstance(data, dict) else False}
        )
        
        # Wait a moment for AI processing
        if success:
            print("⏳ Waiting for AI response processing...")
            time.sleep(3)
        
        # Test get messages again to verify persistence
        status, data = self.make_request('GET', 'chat/messages')
        success = status == 200 and isinstance(data, list) and len(data) >= 2
        self.log_test(
            "GET /chat/messages (after send)", 
            success,
            f"Status: {status}, Messages: {len(data) if isinstance(data, list) else 0}" if not success else "",
            {"message_count": len(data) if isinstance(data, list) else 0}
        )

    def test_portfolio_endpoints(self):
        """Test portfolio functionality"""
        print("\n📊 Testing Portfolio Endpoints...")
        
        # Test get portfolio
        status, data = self.make_request('GET', 'portfolio')
        success = status == 200 and 'allocations' in data
        self.log_test(
            "GET /portfolio", 
            success,
            f"Status: {status}" if not success else "",
            {
                "risk_tolerance": data.get('risk_tolerance') if isinstance(data, dict) else None,
                "roi_expectations": data.get('roi_expectations') if isinstance(data, dict) else None,
                "allocation_count": len(data.get('allocations', [])) if isinstance(data, dict) else 0
            }
        )

    def test_news_endpoints(self):
        """Test news functionality"""
        print("\n📰 Testing News Endpoints...")
        
        # Test get news
        status, data = self.make_request('GET', 'news')
        success = status == 200 and isinstance(data, list)
        self.log_test(
            "GET /news", 
            success,
            f"Status: {status}, Type: {type(data)}" if not success else "",
            {"news_count": len(data) if isinstance(data, list) else 0}
        )

    def test_error_handling(self):
        """Test error handling"""
        print("\n🚨 Testing Error Handling...")
        
        # Test invalid endpoint
        status, data = self.make_request('GET', 'invalid/endpoint')
        success = status == 404
        self.log_test(
            "GET /invalid/endpoint", 
            success,
            f"Expected 404, got {status}" if not success else "",
            data
        )
        
        # Test malformed chat request
        status, data = self.make_request('POST', 'chat/send', {"invalid": "data"})
        success = status in [400, 422]  # Bad request or validation error
        self.log_test(
            "POST /chat/send (malformed)", 
            success,
            f"Expected 400/422, got {status}" if not success else "",
            data
        )

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting SmartFolio Backend API Tests")
        print("=" * 50)
        
        # Setup test user
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return False
        
        # Run test suites
        self.test_auth_endpoints()
        self.test_chat_endpoints()
        self.test_portfolio_endpoints()
        self.test_news_endpoints()
        self.test_error_handling()
        self.test_logout_endpoint()  # Test logout last to avoid session invalidation
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Print failed tests
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = SmartFolioAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "success_rate": (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
        "test_details": tester.test_results
    }
    
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/backend_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())