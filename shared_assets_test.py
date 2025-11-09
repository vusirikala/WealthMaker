#!/usr/bin/env python3
"""
Focused test for WealthMaker Shared Assets Database System
Tests only the new shared assets functionality
"""

import requests
import sys
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

class SharedAssetsAPITester:
    def __init__(self, base_url="https://app-preview-89.preview.emergentagent.com"):
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
db.user_context.insertOne({{
  user_id: userId,
  tracked_symbols: [],
  risk_tolerance: "medium",
  roi_expectations: 10,
  portfolio_type: "personal",
  investment_goals: ["growth"],
  created_at: new Date(),
  updated_at: new Date()
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

    def make_request(self, method: str, endpoint: str, data: Any = None, use_auth: bool = True) -> tuple:
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
        
        # Test batch assets request (expects list directly, not dict)
        batch_request = ["AAPL", "MSFT"]
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

    def test_authentication_requirements(self):
        """Test that endpoints require authentication"""
        print("\n🔐 Testing Authentication Requirements...")
        
        # Test admin endpoints without auth
        endpoints_to_test = [
            ('GET', 'admin/database-stats'),
            ('POST', 'admin/initialize-database'),
            ('GET', 'admin/list-assets'),
            ('POST', 'admin/update-live-data'),
            ('GET', 'data/search?q=AAPL'),
            ('GET', 'data/asset/AAPL'),
            ('POST', 'data/assets/batch'),
            ('GET', 'data/tracked'),
            ('POST', 'data/track?symbol=AAPL')
        ]
        
        for method, endpoint in endpoints_to_test:
            status, data = self.make_request(method, endpoint, use_auth=False)
            success = status == 401
            self.log_test(
                f"{method} /{endpoint} (no auth)", 
                success,
                f"Expected 401, got {status}" if not success else "",
                data
            )

    def run_all_tests(self):
        """Run comprehensive test suite for shared assets system"""
        print("🚀 Starting WealthMaker Shared Assets Database Tests")
        print("=" * 60)
        
        # Setup test user
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return False
        
        # Run test suites
        self.test_admin_endpoints()
        self.test_data_endpoints()
        self.test_authentication_requirements()
        
        # Print summary
        print("\n" + "=" * 60)
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
    tester = SharedAssetsAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "success_rate": (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
        "test_details": tester.test_results
    }
    
    with open('/app/shared_assets_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/shared_assets_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())