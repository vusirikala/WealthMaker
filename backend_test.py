#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for WealthMaker Financial App
Tests authentication, shared assets database, admin endpoints, and data endpoints
"""

import requests
import sys
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

class WealthMakerAPITester:
    def __init__(self, base_url="https://code-preview-54.preview.emergentagent.com"):
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

    def test_chat_init_new_user(self):
        """Test chat init endpoint for new user - comprehensive test"""
        print("\n🆕 Testing Chat Init for New User (Comprehensive)...")
        
        # First, ensure no existing messages
        status, data = self.make_request('GET', 'chat/messages')
        initial_message_count = len(data) if isinstance(data, list) else 0
        
        # Test chat init endpoint
        status, data = self.make_request('GET', 'chat/init')
        success = status == 200 and isinstance(data, dict)
        
        if success and data.get('message'):
            # Should return a greeting message
            message = data.get('message', '')
            has_greeting = any(word in message.lower() for word in ['welcome', 'hi', 'hello', 'greet'])
            has_financial_questions = any(word in message.lower() for word in ['financial', 'goals', 'investment', 'risk', 'portfolio', 'goal'])
            
            # Check for specific content based on the updated implementation
            has_user_name = 'Test User' in message  # Should include user's name
            has_question_mark = '?' in message  # Should ask a question
            
            success = has_greeting and has_financial_questions and len(message) > 50 and has_question_mark
            details = f"Length: {len(message)}, Greeting: {has_greeting}, Financial: {has_financial_questions}, Name: {has_user_name}, Question: {has_question_mark}"
        else:
            success = False
            details = f"Status: {status}, No message returned"
        
        self.log_test(
            "GET /chat/init (new user) - generates initial message", 
            success,
            details if not success else "",
            {"message_length": len(data.get('message', '')) if isinstance(data, dict) else 0}
        )
        
        # Verify message was saved to chat history
        status, messages = self.make_request('GET', 'chat/messages')
        new_message_count = len(messages) if isinstance(messages, list) else 0
        success = status == 200 and new_message_count == initial_message_count + 1
        
        if success and isinstance(messages, list) and len(messages) > 0:
            last_message = messages[-1]
            success = last_message.get('role') == 'assistant' and len(last_message.get('message', '')) > 50
        
        self.log_test(
            "Chat init message saved to history", 
            success,
            f"Messages before: {initial_message_count}, after: {new_message_count}" if not success else "",
            {"message_count": new_message_count}
        )
        
        # Verify first_chat_initiated flag is set
        status, context_data = self.make_request('GET', 'context')
        if status == 200 and isinstance(context_data, dict):
            first_chat_initiated = context_data.get('first_chat_initiated', False)
            success = first_chat_initiated is True
            self.log_test(
                "first_chat_initiated flag set to true", 
                success,
                f"first_chat_initiated: {first_chat_initiated}" if not success else "",
                {"first_chat_initiated": first_chat_initiated}
            )

    def test_chat_init_idempotency(self):
        """Test chat init idempotency - should not create duplicate messages"""
        print("\n🔄 Testing Chat Init Idempotency...")
        
        # Get current message count
        status, messages = self.make_request('GET', 'chat/messages')
        initial_count = len(messages) if isinstance(messages, list) else 0
        
        # Call chat init again
        status, data = self.make_request('GET', 'chat/init')
        success = status == 200 and isinstance(data, dict)
        
        if success:
            # Should return null message since chat already initiated
            success = data.get('message') is None
            details = f"Returned message: {data.get('message')}" if not success else ""
        else:
            details = f"Status: {status}"
        
        self.log_test(
            "GET /chat/init (idempotency)", 
            success,
            details if not success else "",
            data
        )
        
        # Verify no new messages were created
        status, messages = self.make_request('GET', 'chat/messages')
        final_count = len(messages) if isinstance(messages, list) else 0
        success = status == 200 and final_count == initial_count
        
        self.log_test(
            "No duplicate messages created", 
            success,
            f"Messages before: {initial_count}, after: {final_count}" if not success else "",
            {"message_count": final_count}
        )

    def test_chat_send_message_comprehensive(self):
        """Test chat send message functionality - comprehensive test for bug fixes"""
        print("\n💬 Testing Chat Send Message (Bug Fix Verification)...")
        
        # Test 1: Basic chat send message
        test_message = {
            "message": "I'm 35 years old, looking for a moderate risk portfolio with 10% ROI expectations. I want to invest $2000 monthly in technology stocks and some bonds for retirement planning."
        }
        
        status, data = self.make_request('POST', 'chat/send', test_message)
        success = status == 200 and 'message' in data
        self.log_test(
            "POST /chat/send (basic message)", 
            success,
            f"Status: {status}" if not success else "",
            {"has_response": 'message' in data if isinstance(data, dict) else False}
        )
        
        # Verify message was saved to chat_messages collection
        if success:
            status, messages = self.make_request('GET', 'chat/messages')
            user_messages = [msg for msg in messages if msg.get('role') == 'user'] if isinstance(messages, list) else []
            ai_messages = [msg for msg in messages if msg.get('role') == 'assistant'] if isinstance(messages, list) else []
            
            success = len(user_messages) > 0 and len(ai_messages) > 0
            self.log_test(
                "Message saved to chat_messages collection", 
                success,
                f"User messages: {len(user_messages)}, AI messages: {len(ai_messages)}" if not success else "",
                {"user_messages": len(user_messages), "ai_messages": len(ai_messages)}
            )
        
        # Test 2: Verify AI response is generated and returned
        if success and isinstance(data, dict) and 'message' in data:
            ai_response = data['message']
            success = len(ai_response) > 50  # AI should provide substantial response
            self.log_test(
                "AI response generated and returned", 
                success,
                f"Response length: {len(ai_response)}" if not success else "",
                {"response_length": len(ai_response)}
            )
        
        # Test 3: Verify no "Body is disturbed or locked" errors occur
        # This error was caused by reading response.json() multiple times
        if isinstance(data, dict):
            error_message = data.get('detail', '') or data.get('error', '') or str(data)
            has_body_error = 'body is disturbed' in error_message.lower() or 'locked' in error_message.lower()
            success = not has_body_error
            self.log_test(
                "No 'Body is disturbed or locked' error", 
                success,
                f"Found body error in response: {error_message}" if not success else "",
                {"has_body_error": has_body_error}
            )

    def test_context_building_mixed_data_types(self):
        """Test context building with mixed data types in liquidity_requirements"""
        print("\n🔧 Testing Context Building with Mixed Data Types...")
        
        # First, create a user context with mixed liquidity_requirements
        mixed_context = {
            "liquidity_requirements": [
                "Retirement planning",  # String format
                {
                    "goal_name": "House Down Payment", 
                    "target_amount": 50000,
                    "goal_type": "house_purchase",
                    "priority": "high"
                }  # Dict format
            ],
            "risk_tolerance": "moderate",
            "annual_income": 75000
        }
        
        # Update user context with mixed data
        status, data = self.make_request('PUT', 'context', mixed_context)
        success = status == 200
        self.log_test(
            "Update context with mixed liquidity_requirements", 
            success,
            f"Status: {status}" if not success else "",
            data
        )
        
        # Test sending a chat message that should trigger context building
        test_message = {
            "message": "Can you help me understand my current financial goals and suggest a portfolio based on my retirement and house purchase plans?"
        }
        
        status, data = self.make_request('POST', 'chat/send', test_message)
        success = status == 200 and 'message' in data
        
        # Verify no AttributeError occurs (the bug was 'str' object has no attribute 'get')
        if not success and isinstance(data, dict):
            error_message = str(data.get('detail', '')) + str(data.get('error', ''))
            has_attribute_error = 'attributeerror' in error_message.lower() or "has no attribute 'get'" in error_message.lower()
            success = not has_attribute_error
            details = f"AttributeError found: {error_message}" if has_attribute_error else f"Status: {status}"
        else:
            details = f"Status: {status}" if not success else ""
        
        self.log_test(
            "No AttributeError in build_context_string", 
            success,
            details,
            {"has_response": 'message' in data if isinstance(data, dict) else False}
        )
        
        # Verify AI response includes context properly
        if success and isinstance(data, dict) and 'message' in data:
            ai_response = data['message'].lower()
            mentions_retirement = 'retirement' in ai_response
            mentions_house = 'house' in ai_response or 'home' in ai_response
            
            success = mentions_retirement or mentions_house
            self.log_test(
                "AI response includes context from mixed data types", 
                success,
                f"Mentions retirement: {mentions_retirement}, Mentions house: {mentions_house}" if not success else "",
                {"mentions_retirement": mentions_retirement, "mentions_house": mentions_house}
            )

    def test_error_response_handling(self):
        """Test that error responses return proper JSON format"""
        print("\n🚨 Testing Error Response Handling...")
        
        # Test 1: Send invalid message format
        invalid_message = {"invalid_field": "test"}
        status, data = self.make_request('POST', 'chat/send', invalid_message)
        
        # Should return proper JSON error, not "Body is disturbed or locked"
        success = status in [400, 422] and isinstance(data, dict)
        if success:
            error_message = str(data.get('detail', '')) + str(data.get('error', ''))
            has_body_error = 'body is disturbed' in error_message.lower() or 'locked' in error_message.lower()
            success = not has_body_error
            details = f"Found body error: {error_message}" if has_body_error else ""
        else:
            details = f"Status: {status}, Type: {type(data)}"
        
        self.log_test(
            "Invalid message returns proper JSON error", 
            success,
            details,
            data
        )
        
        # Test 2: Send empty message
        empty_message = {"message": ""}
        status, data = self.make_request('POST', 'chat/send', empty_message)
        
        success = status in [400, 422] and isinstance(data, dict)
        if success:
            error_message = str(data.get('detail', '')) + str(data.get('error', ''))
            has_body_error = 'body is disturbed' in error_message.lower() or 'locked' in error_message.lower()
            success = not has_body_error
            details = f"Found body error: {error_message}" if has_body_error else ""
        else:
            details = f"Status: {status}, Type: {type(data)}"
        
        self.log_test(
            "Empty message returns proper JSON error", 
            success,
            details,
            data
        )
        
        # Test 3: Test with malformed JSON (if possible)
        # This tests the frontend bug fix where response.json() was called multiple times
        try:
            import requests
            url = f"{self.api_url}/chat/send"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.session_token}'
            }
            
            # Send malformed JSON
            response = requests.post(url, data='{"message": "test"', headers=headers, timeout=30)
            
            # Should not get "Body is disturbed or locked" error
            try:
                response_data = response.json()
                error_message = str(response_data.get('detail', '')) + str(response_data.get('error', ''))
            except:
                error_message = response.text
            
            has_body_error = 'body is disturbed' in error_message.lower() or 'locked' in error_message.lower()
            success = not has_body_error
            
            self.log_test(
                "Malformed JSON doesn't cause 'Body is disturbed' error", 
                success,
                f"Found body error: {error_message}" if has_body_error else "",
                {"status": response.status_code, "has_body_error": has_body_error}
            )
            
        except Exception as e:
            self.log_test(
                "Malformed JSON test", 
                False,
                f"Test failed with exception: {str(e)}",
                {"error": str(e)}
            )

    def test_chat_endpoints(self):
        """Test chat functionality - updated for bug fix verification"""
        print("\n💬 Testing Chat Endpoints (Updated for Bug Fixes)...")
        
        # Test get chat messages
        status, data = self.make_request('GET', 'chat/messages')
        success = status == 200 and isinstance(data, list)
        self.log_test(
            "GET /chat/messages", 
            success,
            f"Status: {status}, Type: {type(data)}" if not success else "",
            {"message_count": len(data) if isinstance(data, list) else 0}
        )
        
        # Run comprehensive chat send tests
        self.test_chat_send_message_comprehensive()
        
        # Test context building with mixed data types
        self.test_context_building_mixed_data_types()
        
        # Test error response handling
        self.test_error_response_handling()
        
        # Wait a moment for AI processing
        print("⏳ Waiting for AI response processing...")
        time.sleep(3)
        
        # Test get messages again to verify persistence
        status, data = self.make_request('GET', 'chat/messages')
        success = status == 200 and isinstance(data, list) and len(data) >= 2
        self.log_test(
            "GET /chat/messages (after comprehensive tests)", 
            success,
            f"Status: {status}, Messages: {len(data) if isinstance(data, list) else 0}" if not success else "",
            {"message_count": len(data) if isinstance(data, list) else 0}
        )

    def test_user_context_tracking(self):
        """Test that first_chat_initiated is properly tracked"""
        print("\n👤 Testing User Context Tracking...")
        
        # Get user context to check first_chat_initiated flag
        status, data = self.make_request('GET', 'context')
        success = status == 200 and isinstance(data, dict)
        
        if success:
            first_chat_initiated = data.get('first_chat_initiated', False)
            success = first_chat_initiated is True
            details = f"first_chat_initiated: {first_chat_initiated}" if not success else ""
        else:
            details = f"Status: {status}"
        
        self.log_test(
            "first_chat_initiated flag set", 
            success,
            details if not success else "",
            {"first_chat_initiated": data.get('first_chat_initiated') if isinstance(data, dict) else None}
        )

    def test_portfolio_accept_and_load_functionality(self):
        """Test complete portfolio accept and load flow with missing endpoint fix"""
        print("\n📊 Testing Complete Portfolio Accept and Load Flow (Review Request)...")
        
        # Test 1: Create Test User and Portfolio Suggestion
        print("\n🔧 Step 1: Creating test user and portfolio suggestion...")
        
        try:
            import subprocess
            suggestion_id = str(uuid.uuid4())
            
            # Create MongoDB script to insert portfolio suggestion
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
            
            # Execute MongoDB script
            result = subprocess.run(
                ['mongosh', '--eval', mongo_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"✅ Portfolio suggestion created: {suggestion_id}")
                self.log_test(
                    "Create portfolio suggestion in database", 
                    True,
                    "",
                    {"suggestion_id": suggestion_id}
                )
            else:
                print(f"❌ Failed to create portfolio suggestion: {result.stderr}")
                self.log_test(
                    "Create portfolio suggestion in database", 
                    False,
                    f"MongoDB error: {result.stderr}",
                    {}
                )
                return
                
        except Exception as e:
            print(f"❌ Setup error: {str(e)}")
            self.log_test(
                "Create portfolio suggestion in database", 
                False,
                f"Exception: {str(e)}",
                {}
            )
            return
        
        # Test 2: Accept Portfolio via Chat
        print("\n💼 Step 2: Accept Portfolio via /api/portfolio/accept...")
        
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
        success = status == 200 and data.get('success') == True
        self.log_test(
            "POST /api/portfolio/accept", 
            success,
            f"Status: {status}, Response: {data}" if not success else "",
            data
        )
        
        if not success:
            print(f"❌ Portfolio accept failed, skipping load tests")
            return
        
        # Verify portfolio saved to portfolios collection
        print("\n🔍 Step 2b: Verify portfolio saved to portfolios collection...")
        
        # Test 3: Load Portfolio via Legacy Endpoint (what frontend actually calls)
        print("\n📈 Step 3: Load Portfolio via GET /api/portfolio (frontend endpoint)...")
        
        status, data = self.make_request('GET', 'portfolio')
        success = status == 200 and isinstance(data, dict)
        
        if success:
            # Verify 200 response
            # Verify portfolio data returned
            has_risk_tolerance = 'risk_tolerance' in data
            has_roi_expectations = 'roi_expectations' in data  
            has_allocations = 'allocations' in data
            
            # Verify _id is a string (not ObjectId) - critical fix
            id_is_string = isinstance(data.get('_id'), str) if '_id' in data else False
            
            # Verify all portfolio fields present
            allocations = data.get('allocations', [])
            allocations_valid = isinstance(allocations, list) and len(allocations) == 4
            
            success = has_risk_tolerance and has_roi_expectations and has_allocations and id_is_string and allocations_valid
            details = f"risk_tolerance: {has_risk_tolerance}, roi_expectations: {has_roi_expectations}, allocations: {has_allocations}, id_string: {id_is_string}, allocations_count: {len(allocations)}"
        else:
            details = f"Status: {status}, Type: {type(data)}"
        
        self.log_test(
            "GET /api/portfolio - 200 response with portfolio data", 
            success,
            details if not success else "",
            {
                "status": status,
                "has_risk_tolerance": data.get('risk_tolerance') if isinstance(data, dict) else None,
                "has_roi_expectations": data.get('roi_expectations') if isinstance(data, dict) else None,
                "allocation_count": len(data.get('allocations', [])) if isinstance(data, dict) else 0,
                "id_type": type(data.get('_id')).__name__ if isinstance(data, dict) and '_id' in data else None
            }
        )
        
        # Test 4: Verify Data Integrity
        print("\n🔍 Step 4: Verify Data Integrity...")
        
        if success and isinstance(data, dict):
            # Check that _id is properly serialized as string (not ObjectId)
            portfolio_id = data.get('_id')
            id_serialization_ok = isinstance(portfolio_id, str) and len(portfolio_id) > 0
            
            self.log_test(
                "Portfolio _id is string (ObjectId serialization fix)", 
                id_serialization_ok,
                f"_id type: {type(portfolio_id)}, value: {portfolio_id}" if not id_serialization_ok else "",
                {"id_value": portfolio_id, "id_type": type(portfolio_id).__name__}
            )
            
            # Compare accepted portfolio data with loaded portfolio data
            risk_match = data.get('risk_tolerance') == accept_request['portfolio_data']['risk_tolerance']
            roi_match = data.get('roi_expectations') == accept_request['portfolio_data']['roi_expectations']
            allocations_match = len(data.get('allocations', [])) == len(accept_request['portfolio_data']['allocations'])
            
            # Confirm allocations array is intact
            allocations_intact = True
            if allocations_match and isinstance(data.get('allocations'), list):
                for i, allocation in enumerate(data.get('allocations', [])):
                    original_allocation = accept_request['portfolio_data']['allocations'][i]
                    if (allocation.get('ticker') != original_allocation.get('ticker') or
                        allocation.get('allocation') != original_allocation.get('allocation')):
                        allocations_intact = False
                        break
            
            data_integrity_ok = risk_match and roi_match and allocations_match and allocations_intact
            self.log_test(
                "Data integrity: accepted vs loaded portfolio match", 
                data_integrity_ok,
                f"risk: {risk_match}, roi: {roi_match}, allocations_count: {allocations_match}, allocations_intact: {allocations_intact}" if not data_integrity_ok else "",
                {
                    "accepted_risk": accept_request['portfolio_data']['risk_tolerance'],
                    "loaded_risk": data.get('risk_tolerance'),
                    "accepted_roi": accept_request['portfolio_data']['roi_expectations'],
                    "loaded_roi": data.get('roi_expectations'),
                    "accepted_allocations": len(accept_request['portfolio_data']['allocations']),
                    "loaded_allocations": len(data.get('allocations', []))
                }
            )
            
            # Confirm no serialization errors
            try:
                import json
                json_str = json.dumps(data)
                serialization_ok = True
            except Exception as e:
                serialization_ok = False
                
            self.log_test(
                "No JSON serialization errors", 
                serialization_ok,
                f"Serialization error: {str(e) if not serialization_ok else ''}" if not serialization_ok else "",
                {"serializable": serialization_ok}
            )
        
        # Test 5: Test Error Cases
        print("\n🚨 Step 5: Test Error Cases...")
        
        # Clear portfolio to test no portfolio case
        try:
            import subprocess
            mongo_script = f'''
use('test_database');
db.portfolios.deleteMany({{"user_id": "{self.user_id}"}});
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
                
                self.log_test(
                    "GET /api/portfolio when no portfolio exists", 
                    success,
                    f"Status: {status}, Response: {data}" if not success else "",
                    {"status": status, "response": data}
                )
            
        except Exception as e:
            self.log_test(
                "Error case test setup", 
                False,
                f"Failed to clear portfolio: {str(e)}",
                {}
            )
        
        # Test 6: End-to-End Flow Summary
        print("\n🎯 Step 6: End-to-End Flow Summary...")
        
        # Re-accept portfolio for final verification
        status, accept_data = self.make_request('POST', 'portfolio/accept', accept_request)
        if status == 200:
            status, load_data = self.make_request('GET', 'portfolio')
            
            if status == 200 and isinstance(load_data, dict):
                end_to_end_success = (
                    load_data.get('risk_tolerance') == 'moderate' and
                    load_data.get('roi_expectations') == 12 and
                    len(load_data.get('allocations', [])) == 4 and
                    isinstance(load_data.get('_id'), str)
                )
                
                self.log_test(
                    "Complete End-to-End Flow: Accept → Load via /api/portfolio", 
                    end_to_end_success,
                    f"Final verification failed" if not end_to_end_success else "",
                    {
                        "flow": "POST /api/portfolio/accept → GET /api/portfolio",
                        "risk_tolerance": load_data.get('risk_tolerance'),
                        "roi_expectations": load_data.get('roi_expectations'),
                        "allocations_count": len(load_data.get('allocations', [])),
                        "id_is_string": isinstance(load_data.get('_id'), str)
                    }
                )
            else:
                self.log_test(
                    "Complete End-to-End Flow: Accept → Load via /api/portfolio", 
                    False,
                    f"Load failed: Status {status}",
                    {"load_status": status}
                )
        else:
            self.log_test(
                "Complete End-to-End Flow: Accept → Load via /api/portfolio", 
                False,
                f"Accept failed: Status {status}",
                {"accept_status": status}
            )

    def test_portfolio_endpoints(self):
        """Test portfolio functionality - updated for bug fix verification"""
        print("\n📊 Testing Portfolio Endpoints...")
        
        # Run comprehensive portfolio accept and load tests
        self.test_portfolio_accept_and_load_functionality()
        
        # Test existing portfolio endpoints
        status, data = self.make_request('GET', 'portfolios/existing')
        success = status == 200 and 'portfolios' in data
        self.log_test(
            "GET /portfolios/existing", 
            success,
            f"Status: {status}" if not success else "",
            {
                "portfolio_count": len(data.get('portfolios', [])) if isinstance(data, dict) else 0
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
        
        # Test malformed batch request
        status, data = self.make_request('POST', 'data/assets/batch', {"invalid": "data"})
        success = status in [400, 422]  # Bad request or validation error
        self.log_test(
            "POST /data/assets/batch (malformed)", 
            success,
            f"Expected 400/422, got {status}" if not success else "",
            data
        )
        
        # Test non-existent asset
        status, data = self.make_request('GET', 'data/asset/NONEXISTENT')
        success = status == 404
        self.log_test(
            "GET /data/asset/NONEXISTENT", 
            success,
            f"Expected 404, got {status}" if not success else "",
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
        self.test_admin_endpoints()
        self.test_data_endpoints()
        self.test_authentication_requirements()
        
        # Test chat auto-initiation feature
        self.test_chat_init_new_user()
        self.test_chat_init_idempotency()
        self.test_user_context_tracking()
        
        # Test regular chat functionality
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
    tester = WealthMakerAPITester()
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