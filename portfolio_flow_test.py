#!/usr/bin/env python3
"""
Focused test for portfolio accept and load flow as requested in review
Tests the EXACT flow: Accept via /api/portfolio/accept → Load via /api/portfolio
"""

import requests
import sys
import json
import time
import uuid
import subprocess
from datetime import datetime, timezone, timedelta

class PortfolioFlowTester:
    def __init__(self, base_url="https://portfolio-genius-28.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")

    def setup_test_user(self) -> bool:
        """Create test user and session"""
        try:
            timestamp = int(time.time())
            self.user_id = f"test-portfolio-{timestamp}"
            self.session_token = f"test_session_{timestamp}"
            
            mongo_script = f'''
use('test_database');
var userId = '{self.user_id}';
var sessionToken = '{self.session_token}';
db.users.insertOne({{
  _id: userId,
  email: 'portfolio.test.{timestamp}@example.com',
  name: 'Portfolio Test User {timestamp}',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date()
}});
db.user_sessions.insertOne({{
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
}});
print('User setup complete');
'''
            
            result = subprocess.run(
                ['mongosh', '--eval', mongo_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"✅ Test user created: {self.user_id}")
                return True
            else:
                print(f"❌ User setup failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Setup error: {str(e)}")
            return False

    def make_request(self, method: str, endpoint: str, data=None):
        """Make HTTP request"""
        url = f"{self.api_url}/{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}'
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            return response.status_code, response_data
            
        except Exception as e:
            return 500, {"error": str(e)}

    def test_complete_portfolio_flow(self):
        """Test the complete portfolio accept and load flow"""
        print("\n🎯 Testing Complete Portfolio Accept and Load Flow")
        print("=" * 60)
        
        # Step 1: Create Test User and Portfolio Suggestion
        print("\n📝 Step 1: Create test user and portfolio suggestion")
        
        suggestion_id = str(uuid.uuid4())
        
        try:
            mongo_script = f'''
use('test_database');
var suggestionId = '{suggestion_id}';
var userId = '{self.user_id}';
db.portfolio_suggestions.insertOne({{
  _id: suggestionId,
  user_id: userId,
  risk_tolerance: "moderate",
  roi_expectations: 12,
  allocations: [
    {{
      "ticker": "AAPL",
      "asset_type": "stock", 
      "allocation": 30,
      "sector": "Technology"
    }},
    {{
      "ticker": "GOOGL",
      "asset_type": "stock",
      "allocation": 25, 
      "sector": "Technology"
    }},
    {{
      "ticker": "MSFT",
      "asset_type": "stock",
      "allocation": 20,
      "sector": "Technology"
    }},
    {{
      "ticker": "BND",
      "asset_type": "bond",
      "allocation": 25,
      "sector": "Fixed Income"
    }}
  ],
  reasoning: "Balanced tech-focused portfolio with bond allocation for stability",
  created_at: new Date(),
  expires_at: new Date(Date.now() + 24*60*60*1000)
}});
print('Portfolio suggestion created');
'''
            
            result = subprocess.run(
                ['mongosh', '--eval', mongo_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log_test("Create portfolio suggestion", True)
                print(f"   Suggestion ID: {suggestion_id}")
            else:
                self.log_test("Create portfolio suggestion", False, result.stderr)
                return False
                
        except Exception as e:
            self.log_test("Create portfolio suggestion", False, str(e))
            return False
        
        # Step 2: Accept Portfolio via Chat
        print("\n💼 Step 2: Accept portfolio via /api/portfolio/accept")
        
        accept_request = {
            "suggestion_id": suggestion_id,
            "portfolio_data": {
                "risk_tolerance": "moderate",
                "roi_expectations": 12,
                "allocations": [
                    {
                        "ticker": "AAPL",
                        "asset_type": "stock",
                        "allocation": 30,
                        "sector": "Technology"
                    },
                    {
                        "ticker": "GOOGL", 
                        "asset_type": "stock",
                        "allocation": 25,
                        "sector": "Technology"
                    },
                    {
                        "ticker": "MSFT",
                        "asset_type": "stock", 
                        "allocation": 20,
                        "sector": "Technology"
                    },
                    {
                        "ticker": "BND",
                        "asset_type": "bond",
                        "allocation": 25,
                        "sector": "Fixed Income"
                    }
                ]
            }
        }
        
        status, data = self.make_request('POST', 'portfolio/accept', accept_request)
        success = status == 200 and isinstance(data, dict) and data.get('success') == True
        
        if success:
            self.log_test("POST /api/portfolio/accept", True)
            print(f"   Response: {data.get('message', 'Success')}")
        else:
            self.log_test("POST /api/portfolio/accept", False, f"Status: {status}, Response: {data}")
            return False
        
        # Verify portfolio saved to portfolios collection
        print("\n🔍 Step 2b: Verify portfolio saved to portfolios collection")
        
        try:
            mongo_script = f'''
use('test_database');
var userId = '{self.user_id}';
var portfolio = db.portfolios.findOne({{"user_id": userId}});
if (portfolio) {{
  print('Portfolio found in database');
  print('Risk tolerance: ' + portfolio.risk_tolerance);
  print('ROI expectations: ' + portfolio.roi_expectations);
  print('Allocations count: ' + portfolio.allocations.length);
}} else {{
  print('No portfolio found');
}}
'''
            
            result = subprocess.run(
                ['mongosh', '--eval', mongo_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and 'Portfolio found in database' in result.stdout:
                self.log_test("Portfolio saved to portfolios collection", True)
                print(f"   Database verification: {result.stdout.strip()}")
            else:
                self.log_test("Portfolio saved to portfolios collection", False, "Portfolio not found in database")
                
        except Exception as e:
            self.log_test("Portfolio saved to portfolios collection", False, str(e))
        
        # Step 3: Load Portfolio via Legacy Endpoint (what frontend actually calls)
        print("\n📈 Step 3: Load portfolio via GET /api/portfolio")
        
        status, data = self.make_request('GET', 'portfolio')
        success = status == 200 and isinstance(data, dict)
        
        if success:
            # Verify 200 response
            self.log_test("GET /api/portfolio returns 200", True)
            
            # Verify portfolio data returned
            has_risk = 'risk_tolerance' in data
            has_roi = 'roi_expectations' in data
            has_allocations = 'allocations' in data
            
            self.log_test("Portfolio data returned", has_risk and has_roi and has_allocations, 
                         f"risk: {has_risk}, roi: {has_roi}, allocations: {has_allocations}")
            
            # Verify _id is a string (not ObjectId)
            id_is_string = isinstance(data.get('_id'), str)
            self.log_test("_id is string (ObjectId serialization fix)", id_is_string,
                         f"_id type: {type(data.get('_id'))}")
            
            # Verify all portfolio fields present
            allocations = data.get('allocations', [])
            allocations_valid = isinstance(allocations, list) and len(allocations) == 4
            self.log_test("All portfolio fields present", allocations_valid,
                         f"allocations count: {len(allocations)}")
            
            print(f"   Portfolio data: risk={data.get('risk_tolerance')}, roi={data.get('roi_expectations')}, allocations={len(allocations)}")
            
        else:
            self.log_test("GET /api/portfolio returns 200", False, f"Status: {status}")
            return False
        
        # Step 4: Verify Data Integrity
        print("\n🔍 Step 4: Verify data integrity")
        
        if isinstance(data, dict):
            # Compare accepted portfolio data with loaded portfolio data
            risk_match = data.get('risk_tolerance') == accept_request['portfolio_data']['risk_tolerance']
            roi_match = data.get('roi_expectations') == accept_request['portfolio_data']['roi_expectations']
            allocations_match = len(data.get('allocations', [])) == len(accept_request['portfolio_data']['allocations'])
            
            self.log_test("Risk tolerance matches", risk_match,
                         f"Expected: {accept_request['portfolio_data']['risk_tolerance']}, Got: {data.get('risk_tolerance')}")
            self.log_test("ROI expectations match", roi_match,
                         f"Expected: {accept_request['portfolio_data']['roi_expectations']}, Got: {data.get('roi_expectations')}")
            self.log_test("Allocations count matches", allocations_match,
                         f"Expected: {len(accept_request['portfolio_data']['allocations'])}, Got: {len(data.get('allocations', []))}")
            
            # Confirm allocations array is intact
            allocations_intact = True
            if allocations_match and isinstance(data.get('allocations'), list):
                for i, allocation in enumerate(data.get('allocations', [])):
                    original = accept_request['portfolio_data']['allocations'][i]
                    if (allocation.get('ticker') != original.get('ticker') or
                        allocation.get('allocation') != original.get('allocation')):
                        allocations_intact = False
                        break
            
            self.log_test("Allocations array intact", allocations_intact)
            
            # Confirm no serialization errors
            try:
                json_str = json.dumps(data)
                self.log_test("No JSON serialization errors", True)
            except Exception as e:
                self.log_test("No JSON serialization errors", False, str(e))
        
        # Step 5: Test Error Cases
        print("\n🚨 Step 5: Test error cases")
        
        # Clear portfolio to test no portfolio case
        try:
            mongo_script = f'''
use('test_database');
var userId = '{self.user_id}';
db.portfolios.deleteMany({{"user_id": userId}});
print('Portfolio cleared');
'''
            
            result = subprocess.run(
                ['mongosh', '--eval', mongo_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Test GET /api/portfolio when no portfolio exists
                status, data = self.make_request('GET', 'portfolio')
                
                # Should return proper error handling (not 500 error)
                success = status == 200 and isinstance(data, dict) and data.get('portfolio') is None
                
                self.log_test("GET /api/portfolio when no portfolio exists", success,
                             f"Status: {status}, Response: {data}")
            
        except Exception as e:
            self.log_test("Error case test", False, str(e))
        
        print(f"\n📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    print("🚀 Portfolio Accept and Load Flow Test")
    print("Testing the EXACT flow the frontend uses:")
    print("Accept via /api/portfolio/accept → Load via /api/portfolio")
    
    tester = PortfolioFlowTester()
    
    # Setup test user
    if not tester.setup_test_user():
        print("❌ Failed to setup test user. Aborting tests.")
        return 1
    
    # Run the complete flow test
    success = tester.test_complete_portfolio_flow()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())