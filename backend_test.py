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

    def test_52_week_high_low_fix(self):
        """Test 52-week high/low fix for stock detail modal as per review request"""
        print("\n📈 Testing 52-Week High/Low Fix (Review Request)...")
        
        # Test 1: Large-cap stocks
        print("\n🏢 Test 1: Large-cap stocks (AAPL, MSFT, GOOGL)...")
        large_cap_stocks = ["AAPL", "MSFT", "GOOGL"]
        
        for symbol in large_cap_stocks:
            status, data = self.make_request('GET', f'data/asset/{symbol}')
            success = status == 200 and isinstance(data, dict)
            
            if success:
                live_data = data.get('live', {})
                current_price_data = live_data.get('currentPrice', {})
                
                fifty_two_week_high = current_price_data.get('fiftyTwoWeekHigh')
                fifty_two_week_low = current_price_data.get('fiftyTwoWeekLow')
                
                # Validate 52-week high/low values
                high_valid = isinstance(fifty_two_week_high, (int, float)) and fifty_two_week_high > 0
                low_valid = isinstance(fifty_two_week_low, (int, float)) and fifty_two_week_low > 0
                logical_check = high_valid and low_valid and fifty_two_week_high > fifty_two_week_low
                reasonable_values = high_valid and low_valid and fifty_two_week_high < 10000 and fifty_two_week_low > 0.01
                
                success = high_valid and low_valid and logical_check and reasonable_values
                details = f"High: {fifty_two_week_high} (valid: {high_valid}), Low: {fifty_two_week_low} (valid: {low_valid}), Logical: {logical_check}, Reasonable: {reasonable_values}"
            else:
                details = f"Status: {status}"
            
            self.log_test(
                f"52-week high/low for {symbol} (large-cap)", 
                success,
                details if not success else "",
                {
                    "symbol": symbol,
                    "fiftyTwoWeekHigh": fifty_two_week_high if success else None,
                    "fiftyTwoWeekLow": fifty_two_week_low if success else None,
                    "valid": success
                }
            )
        
        # Test 2: Mid-cap stocks
        print("\n🏭 Test 2: Mid-cap stocks (AMD, NVDA)...")
        mid_cap_stocks = ["AMD", "NVDA"]
        
        for symbol in mid_cap_stocks:
            status, data = self.make_request('GET', f'data/asset/{symbol}')
            success = status == 200 and isinstance(data, dict)
            
            if success:
                live_data = data.get('live', {})
                current_price_data = live_data.get('currentPrice', {})
                
                fifty_two_week_high = current_price_data.get('fiftyTwoWeekHigh')
                fifty_two_week_low = current_price_data.get('fiftyTwoWeekLow')
                
                # Validate values
                high_valid = isinstance(fifty_two_week_high, (int, float)) and fifty_two_week_high > 0
                low_valid = isinstance(fifty_two_week_low, (int, float)) and fifty_two_week_low > 0
                logical_check = high_valid and low_valid and fifty_two_week_high > fifty_two_week_low
                
                success = high_valid and low_valid and logical_check
                details = f"High: {fifty_two_week_high}, Low: {fifty_two_week_low}, Valid: {high_valid and low_valid}, Logical: {logical_check}"
            else:
                details = f"Status: {status}"
            
            self.log_test(
                f"52-week high/low for {symbol} (mid-cap)", 
                success,
                details if not success else "",
                {
                    "symbol": symbol,
                    "fiftyTwoWeekHigh": fifty_two_week_high if success else None,
                    "fiftyTwoWeekLow": fifty_two_week_low if success else None
                }
            )
        
        # Test 3: ETFs/Bonds
        print("\n📊 Test 3: ETFs/Bonds (SPY, BND)...")
        etf_bonds = ["SPY", "BND"]
        
        for symbol in etf_bonds:
            status, data = self.make_request('GET', f'data/asset/{symbol}')
            success = status == 200 and isinstance(data, dict)
            
            if success:
                live_data = data.get('live', {})
                current_price_data = live_data.get('currentPrice', {})
                
                fifty_two_week_high = current_price_data.get('fiftyTwoWeekHigh')
                fifty_two_week_low = current_price_data.get('fiftyTwoWeekLow')
                
                # Validate values
                high_valid = isinstance(fifty_two_week_high, (int, float)) and fifty_two_week_high > 0
                low_valid = isinstance(fifty_two_week_low, (int, float)) and fifty_two_week_low > 0
                logical_check = high_valid and low_valid and fifty_two_week_high > fifty_two_week_low
                
                success = high_valid and low_valid and logical_check
                details = f"High: {fifty_two_week_high}, Low: {fifty_two_week_low}"
            else:
                details = f"Status: {status}"
            
            self.log_test(
                f"52-week high/low for {symbol} (ETF/Bond)", 
                success,
                details if not success else "",
                {
                    "symbol": symbol,
                    "fiftyTwoWeekHigh": fifty_two_week_high if success else None,
                    "fiftyTwoWeekLow": fifty_two_week_low if success else None
                }
            )
        
        # Test 4: Crypto
        print("\n₿ Test 4: Crypto (BTC-USD)...")
        crypto_symbols = ["BTC-USD"]
        
        for symbol in crypto_symbols:
            status, data = self.make_request('GET', f'data/asset/{symbol}')
            success = status == 200 and isinstance(data, dict)
            
            if success:
                live_data = data.get('live', {})
                current_price_data = live_data.get('currentPrice', {})
                
                fifty_two_week_high = current_price_data.get('fiftyTwoWeekHigh')
                fifty_two_week_low = current_price_data.get('fiftyTwoWeekLow')
                
                # Validate values (crypto can have higher ranges)
                high_valid = isinstance(fifty_two_week_high, (int, float)) and fifty_two_week_high > 0
                low_valid = isinstance(fifty_two_week_low, (int, float)) and fifty_two_week_low > 0
                logical_check = high_valid and low_valid and fifty_two_week_high > fifty_two_week_low
                reasonable_crypto = high_valid and low_valid and fifty_two_week_high < 200000 and fifty_two_week_low > 1000
                
                success = high_valid and low_valid and logical_check and reasonable_crypto
                details = f"High: {fifty_two_week_high}, Low: {fifty_two_week_low}, Reasonable: {reasonable_crypto}"
            else:
                details = f"Status: {status}"
            
            self.log_test(
                f"52-week high/low for {symbol} (crypto)", 
                success,
                details if not success else "",
                {
                    "symbol": symbol,
                    "fiftyTwoWeekHigh": fifty_two_week_high if success else None,
                    "fiftyTwoWeekLow": fifty_two_week_low if success else None
                }
            )
        
        # Test 5: Auto-initialization with 52-week data
        print("\n🆕 Test 5: Auto-initialization with 52-week data (BA, JPM, V)...")
        new_stocks = ["BA", "JPM", "V"]
        
        for symbol in new_stocks:
            status, data = self.make_request('GET', f'data/asset/{symbol}')
            success = status == 200 and isinstance(data, dict)
            
            if success:
                # Verify asset was created with proper structure
                has_symbol = data.get('symbol') == symbol
                has_live_data = 'live' in data and isinstance(data['live'], dict)
                
                if has_live_data:
                    live_data = data.get('live', {})
                    current_price_data = live_data.get('currentPrice', {})
                    
                    fifty_two_week_high = current_price_data.get('fiftyTwoWeekHigh')
                    fifty_two_week_low = current_price_data.get('fiftyTwoWeekLow')
                    
                    # Check if 52-week values are calculated from historical data
                    high_valid = isinstance(fifty_two_week_high, (int, float)) and fifty_two_week_high > 0
                    low_valid = isinstance(fifty_two_week_low, (int, float)) and fifty_two_week_low > 0
                    
                    success = has_symbol and has_live_data and high_valid and low_valid
                    details = f"Symbol: {has_symbol}, LiveData: {has_live_data}, High: {fifty_two_week_high}, Low: {fifty_two_week_low}"
                else:
                    success = False
                    details = "Missing live data structure"
            else:
                details = f"Status: {status}"
            
            self.log_test(
                f"Auto-initialize {symbol} with 52-week data", 
                success,
                details if not success else "",
                {
                    "symbol": symbol,
                    "auto_initialized": success,
                    "has_52_week_data": success
                }
            )
        
        # Test 6: Data persistence
        print("\n💾 Test 6: Data persistence...")
        
        # Fetch a stock's data twice to verify persistence
        test_symbol = "AAPL"
        
        # First fetch
        status1, data1 = self.make_request('GET', f'data/asset/{test_symbol}')
        success1 = status1 == 200 and isinstance(data1, dict)
        
        if success1:
            high1 = data1.get('live', {}).get('currentPrice', {}).get('fiftyTwoWeekHigh')
            low1 = data1.get('live', {}).get('currentPrice', {}).get('fiftyTwoWeekLow')
            
            # Second fetch (should return same values from database)
            time.sleep(1)  # Small delay
            status2, data2 = self.make_request('GET', f'data/asset/{test_symbol}')
            success2 = status2 == 200 and isinstance(data2, dict)
            
            if success2:
                high2 = data2.get('live', {}).get('currentPrice', {}).get('fiftyTwoWeekHigh')
                low2 = data2.get('live', {}).get('currentPrice', {}).get('fiftyTwoWeekLow')
                
                # Values should be consistent (saved in database)
                values_consistent = high1 == high2 and low1 == low2
                success = values_consistent and high1 is not None and low1 is not None
                details = f"First: High={high1}, Low={low1}; Second: High={high2}, Low={low2}; Consistent: {values_consistent}"
            else:
                success = False
                details = f"Second fetch failed: Status {status2}"
        else:
            success = False
            details = f"First fetch failed: Status {status1}"
        
        self.log_test(
            "52-week data persistence in shared_assets collection", 
            success,
            details if not success else "",
            {
                "symbol": test_symbol,
                "persistent": success,
                "first_high": high1 if success1 else None,
                "second_high": high2 if success1 and success2 else None
            }
        )
        
        # Test 7: Edge cases
        print("\n⚠️ Test 7: Edge cases...")
        
        # Test with a stock that might have limited history (recent IPO simulation)
        edge_case_symbols = ["PLTR"]  # Palantir - relatively newer stock
        
        for symbol in edge_case_symbols:
            status, data = self.make_request('GET', f'data/asset/{symbol}')
            success = status == 200 and isinstance(data, dict)
            
            if success:
                live_data = data.get('live', {})
                current_price_data = live_data.get('currentPrice', {})
                
                fifty_two_week_high = current_price_data.get('fiftyTwoWeekHigh')
                fifty_two_week_low = current_price_data.get('fiftyTwoWeekLow')
                
                # Should handle gracefully without crashes
                no_crash = True  # If we got here, no crash occurred
                has_values = fifty_two_week_high is not None and fifty_two_week_low is not None
                
                success = no_crash and has_values
                details = f"No crash: {no_crash}, Has values: {has_values}, High: {fifty_two_week_high}, Low: {fifty_two_week_low}"
            else:
                success = status != 500  # Should not crash with 500 error
                details = f"Status: {status} (should not be 500)"
            
            self.log_test(
                f"Edge case handling for {symbol} (graceful handling)", 
                success,
                details if not success else "",
                {
                    "symbol": symbol,
                    "graceful_handling": success,
                    "status": status
                }
            )

    def test_stock_detail_auto_initialization(self):
        """Test stock detail auto-initialization fix as per review request"""
        print("\n🔧 Testing Stock Detail Auto-Initialization Fix...")
        
        # Test Scenario 1: Stock NOT in Database (should auto-initialize)
        print("\n📊 Test Scenario 1: Stock NOT in Database (Auto-Initialize)...")
        
        # Test with NVDA (likely not in database)
        status, data = self.make_request('GET', 'data/asset/NVDA')
        success = status == 200 and isinstance(data, dict)
        
        if success:
            # Verify complete asset data structure
            has_symbol = 'symbol' in data and data['symbol'] == 'NVDA'
            has_name = 'name' in data and len(data.get('name', '')) > 0
            has_asset_type = 'assetType' in data
            has_fundamentals = 'fundamentals' in data and isinstance(data['fundamentals'], dict)
            has_historical = 'historical' in data and isinstance(data['historical'], dict)
            has_live = 'live' in data and isinstance(data['live'], dict)
            
            # Check fundamentals structure
            fundamentals = data.get('fundamentals', {})
            has_sector = 'sector' in fundamentals
            has_industry = 'industry' in fundamentals
            has_market_cap = 'marketCap' in fundamentals
            
            # Check historical structure
            historical = data.get('historical', {})
            has_price_history = 'priceHistory' in historical
            
            # Check live structure
            live = data.get('live', {})
            has_current_price = 'currentPrice' in live
            has_recent_news = 'recentNews' in live
            
            complete_structure = (has_symbol and has_name and has_asset_type and 
                                has_fundamentals and has_historical and has_live and
                                has_sector and has_industry and has_market_cap and
                                has_price_history and has_current_price and has_recent_news)
            
            success = complete_structure
            details = f"Symbol: {has_symbol}, Name: {has_name}, AssetType: {has_asset_type}, Fundamentals: {has_fundamentals}, Historical: {has_historical}, Live: {has_live}, Sector: {has_sector}, Industry: {has_industry}, MarketCap: {has_market_cap}, PriceHistory: {has_price_history}, CurrentPrice: {has_current_price}, RecentNews: {has_recent_news}"
        else:
            details = f"Status: {status}, Response type: {type(data)}"
        
        self.log_test(
            "GET /data/asset/NVDA (auto-initialize new stock)", 
            success,
            details if not success else "",
            {
                "symbol": data.get('symbol') if isinstance(data, dict) else None,
                "name": data.get('name') if isinstance(data, dict) else None,
                "has_complete_structure": success
            }
        )
        
        # Test with AMD (another likely new stock)
        status, data = self.make_request('GET', 'data/asset/AMD')
        success = status == 200 and isinstance(data, dict) and data.get('symbol') == 'AMD'
        self.log_test(
            "GET /data/asset/AMD (auto-initialize new stock)", 
            success,
            f"Status: {status}" if not success else "",
            {"symbol": data.get('symbol') if isinstance(data, dict) else None}
        )
        
        # Test with BA (Boeing - another test stock)
        status, data = self.make_request('GET', 'data/asset/BA')
        success = status == 200 and isinstance(data, dict) and data.get('symbol') == 'BA'
        self.log_test(
            "GET /data/asset/BA (auto-initialize new stock)", 
            success,
            f"Status: {status}" if not success else "",
            {"symbol": data.get('symbol') if isinstance(data, dict) else None}
        )
        
        # Test Scenario 2: Stock Already in Database (should return immediately)
        print("\n📈 Test Scenario 2: Stock Already in Database...")
        
        # Test with AAPL (should already exist from previous tests)
        start_time = time.time()
        status, data = self.make_request('GET', 'data/asset/AAPL')
        response_time = time.time() - start_time
        
        success = status == 200 and isinstance(data, dict) and data.get('symbol') == 'AAPL'
        fast_response = response_time < 5.0  # Should be fast since already in DB
        
        self.log_test(
            "GET /data/asset/AAPL (existing stock - fast response)", 
            success and fast_response,
            f"Status: {status}, Response time: {response_time:.2f}s" if not (success and fast_response) else "",
            {
                "symbol": data.get('symbol') if isinstance(data, dict) else None,
                "response_time": response_time,
                "fast_response": fast_response
            }
        )
        
        # Test Scenario 3: Invalid Symbol (should return 404)
        print("\n❌ Test Scenario 3: Invalid Symbol...")
        
        status, data = self.make_request('GET', 'data/asset/INVALIDXYZ123')
        success = status == 404
        
        if success and isinstance(data, dict):
            # Check for user-friendly error message
            error_detail = data.get('detail', '')
            user_friendly = 'Invalid ticker symbol' in error_detail or 'not found' in error_detail
            success = user_friendly
            details = f"Error message: {error_detail}" if not user_friendly else ""
        else:
            details = f"Status: {status}, Expected 404"
        
        self.log_test(
            "GET /data/asset/INVALIDXYZ123 (invalid symbol - 404 error)", 
            success,
            details if not success else "",
            {"status": status, "error_detail": data.get('detail') if isinstance(data, dict) else None}
        )
        
        # Test Scenario 4: Multiple New Stocks (batch auto-initialization)
        print("\n🔄 Test Scenario 4: Multiple New Stocks...")
        
        # Test three different new stocks in sequence
        test_symbols = ["TSLA", "NFLX", "AMZN"]
        successful_initializations = 0
        
        for symbol in test_symbols:
            status, data = self.make_request('GET', f'data/asset/{symbol}')
            success = status == 200 and isinstance(data, dict) and data.get('symbol') == symbol
            
            if success:
                successful_initializations += 1
            
            self.log_test(
                f"GET /data/asset/{symbol} (multiple new stocks test)", 
                success,
                f"Status: {status}" if not success else "",
                {"symbol": data.get('symbol') if isinstance(data, dict) else None}
            )
        
        # Verify all stocks were successfully initialized
        all_successful = successful_initializations == len(test_symbols)
        self.log_test(
            "Multiple new stocks auto-initialization (all successful)", 
            all_successful,
            f"Only {successful_initializations}/{len(test_symbols)} stocks initialized successfully" if not all_successful else "",
            {"successful_count": successful_initializations, "total_count": len(test_symbols)}
        )
        
        # Test Scenario 5: Verify stocks are now saved in shared_assets collection
        print("\n💾 Test Scenario 5: Verify Stocks Saved in Database...")
        
        # Test that previously auto-initialized stocks now return quickly (cached)
        for symbol in ["NVDA", "AMD", "BA"]:
            start_time = time.time()
            status, data = self.make_request('GET', f'data/asset/{symbol}')
            response_time = time.time() - start_time
            
            success = status == 200 and response_time < 3.0  # Should be fast now
            self.log_test(
                f"GET /data/asset/{symbol} (now cached - fast response)", 
                success,
                f"Status: {status}, Response time: {response_time:.2f}s" if not success else "",
                {"response_time": response_time, "cached": success}
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

    def test_multi_portfolio_management_system(self):
        """Test comprehensive multi-portfolio management system as per review request"""
        print("\n🏦 Testing Multi-Portfolio Management System (Review Request)...")
        
        # Test 1: Portfolio CRUD Operations
        print("\n📊 Test 1: Portfolio CRUD Operations...")
        
        # Test 1a: Create Manual Portfolio
        create_request = {
            "name": "Test Growth Portfolio",
            "goal": "Long-term wealth building",
            "type": "manual",
            "risk_tolerance": "medium",
            "roi_expectations": 12.0,
            "allocations": [
                {"ticker": "AAPL", "allocation_percentage": 40, "sector": "Technology", "asset_type": "stock"},
                {"ticker": "GOOGL", "allocation_percentage": 35, "sector": "Technology", "asset_type": "stock"},
                {"ticker": "BND", "allocation_percentage": 25, "sector": "Bonds", "asset_type": "bond"}
            ]
        }
        
        status, data = self.make_request('POST', 'portfolios-v2/create', create_request)
        success = status == 200 and data.get('success') == True and 'portfolio' in data
        
        if success:
            created_portfolio = data['portfolio']
            portfolio_id = created_portfolio.get('portfolio_id')
            
            # Verify portfolio structure
            has_name = created_portfolio.get('name') == "Test Growth Portfolio"
            has_goal = created_portfolio.get('goal') == "Long-term wealth building"
            has_risk = created_portfolio.get('risk_tolerance') == "medium"
            has_roi = created_portfolio.get('roi_expectations') == 12.0
            has_allocations = len(created_portfolio.get('allocations', [])) == 3
            
            success = has_name and has_goal and has_risk and has_roi and has_allocations and portfolio_id
            details = f"Name: {has_name}, Goal: {has_goal}, Risk: {has_risk}, ROI: {has_roi}, Allocations: {has_allocations}, ID: {bool(portfolio_id)}"
        else:
            details = f"Status: {status}, Response: {data}"
            portfolio_id = None
        
        self.log_test(
            "POST /api/portfolios-v2/create (manual portfolio)", 
            success,
            details if not success else "",
            {
                "portfolio_id": portfolio_id,
                "allocations_count": len(created_portfolio.get('allocations', [])) if success else 0
            }
        )
        
        if not success or not portfolio_id:
            print("❌ Portfolio creation failed, skipping remaining tests")
            return
        
        # Test 1b: List All Portfolios
        status, data = self.make_request('GET', 'portfolios-v2/list')
        success = status == 200 and 'portfolios' in data and 'count' in data
        
        if success:
            portfolios = data.get('portfolios', [])
            count = data.get('count', 0)
            found_portfolio = any(p.get('portfolio_id') == portfolio_id for p in portfolios)
            
            success = count > 0 and found_portfolio
            details = f"Count: {count}, Found created portfolio: {found_portfolio}"
        else:
            details = f"Status: {status}"
        
        self.log_test(
            "GET /api/portfolios-v2/list", 
            success,
            details if not success else "",
            {"portfolio_count": data.get('count', 0) if isinstance(data, dict) else 0}
        )
        
        # Test 1c: Get Specific Portfolio
        status, data = self.make_request('GET', f'portfolios-v2/{portfolio_id}')
        success = status == 200 and 'portfolio' in data
        
        if success:
            portfolio = data['portfolio']
            correct_id = portfolio.get('portfolio_id') == portfolio_id
            correct_name = portfolio.get('name') == "Test Growth Portfolio"
            has_allocations = len(portfolio.get('allocations', [])) == 3
            
            success = correct_id and correct_name and has_allocations
            details = f"ID match: {correct_id}, Name match: {correct_name}, Allocations: {has_allocations}"
        else:
            details = f"Status: {status}"
        
        self.log_test(
            f"GET /api/portfolios-v2/{portfolio_id}", 
            success,
            details if not success else "",
            {"portfolio_found": success}
        )
        
        # Test 1d: Update Portfolio
        update_request = {
            "name": "Updated Growth Portfolio",
            "goal": "Updated goal",
            "type": "manual",
            "risk_tolerance": "high",
            "roi_expectations": 15.0,
            "allocations": [
                {"ticker": "AAPL", "allocation_percentage": 50, "sector": "Technology", "asset_type": "stock"},
                {"ticker": "MSFT", "allocation_percentage": 30, "sector": "Technology", "asset_type": "stock"},
                {"ticker": "BND", "allocation_percentage": 20, "sector": "Bonds", "asset_type": "bond"}
            ]
        }
        
        status, data = self.make_request('PUT', f'portfolios-v2/{portfolio_id}', update_request)
        success = status == 200 and data.get('success') == True
        
        self.log_test(
            f"PUT /api/portfolios-v2/{portfolio_id}", 
            success,
            f"Status: {status}, Response: {data}" if not success else "",
            {"updated": success}
        )
        
        # Test 2: Investment Feature
        print("\n💰 Test 2: Investment Feature...")
        
        # First, create a fresh portfolio with specific allocations for investment testing
        investment_portfolio_request = {
            "name": "Investment Test Portfolio",
            "goal": "Investment testing",
            "type": "manual",
            "risk_tolerance": "medium",
            "roi_expectations": 10.0,
            "allocations": [
                {"ticker": "AAPL", "allocation_percentage": 40, "sector": "Technology", "asset_type": "stock"},
                {"ticker": "GOOGL", "allocation_percentage": 35, "sector": "Technology", "asset_type": "stock"},
                {"ticker": "BND", "allocation_percentage": 25, "sector": "Bonds", "asset_type": "bond"}
            ]
        }
        
        status, data = self.make_request('POST', 'portfolios-v2/create', investment_portfolio_request)
        if status == 200 and data.get('success'):
            investment_portfolio_id = data['portfolio']['portfolio_id']
            
            # Test 2a: Invest $10,000 in Portfolio
            investment_request = {"amount": 10000.0}
            
            status, data = self.make_request('POST', f'portfolios-v2/{investment_portfolio_id}/invest', investment_request)
            success = status == 200 and data.get('success') == True
            
            if success:
                investments = data.get('investments', [])
                portfolio_summary = data.get('portfolio_summary', {})
                
                # Verify investment calculations
                has_three_investments = len(investments) == 3
                total_invested = portfolio_summary.get('total_invested', 0)
                investment_close_to_10k = abs(total_invested - 10000) < 100  # Allow for rounding
                
                # Verify allocations match expected percentages
                aapl_investment = next((inv for inv in investments if inv['ticker'] == 'AAPL'), None)
                googl_investment = next((inv for inv in investments if inv['ticker'] == 'GOOGL'), None)
                bnd_investment = next((inv for inv in investments if inv['ticker'] == 'BND'), None)
                
                aapl_amount_correct = aapl_investment and abs(aapl_investment['amount_allocated'] - 4000) < 100  # 40% of $10k
                googl_amount_correct = googl_investment and abs(googl_investment['amount_allocated'] - 3500) < 100  # 35% of $10k
                bnd_amount_correct = bnd_investment and abs(bnd_investment['amount_allocated'] - 2500) < 100  # 25% of $10k
                
                # Verify shares were calculated
                has_shares = all(inv.get('shares_purchased', 0) > 0 for inv in investments)
                has_prices = all(inv.get('current_price', 0) > 0 for inv in investments)
                
                success = (has_three_investments and investment_close_to_10k and 
                          aapl_amount_correct and googl_amount_correct and bnd_amount_correct and
                          has_shares and has_prices)
                
                details = f"Investments: {len(investments)}, Total: ${total_invested:.2f}, AAPL: {aapl_amount_correct}, GOOGL: {googl_amount_correct}, BND: {bnd_amount_correct}, Shares: {has_shares}, Prices: {has_prices}"
            else:
                details = f"Status: {status}, Response: {data}"
            
            self.log_test(
                f"POST /api/portfolios-v2/{investment_portfolio_id}/invest ($10,000)", 
                success,
                details if not success else "",
                {
                    "total_invested": portfolio_summary.get('total_invested', 0) if success else 0,
                    "investments_count": len(investments) if success else 0,
                    "aapl_allocation": aapl_investment.get('amount_allocated', 0) if success and aapl_investment else 0
                }
            )
            
            # Test 2b: Verify Holdings Created
            if success:
                status, data = self.make_request('GET', f'portfolios-v2/{investment_portfolio_id}')
                if status == 200 and 'portfolio' in data:
                    portfolio = data['portfolio']
                    holdings = portfolio.get('holdings', [])
                    
                    has_holdings = len(holdings) == 3
                    holdings_have_shares = all(h.get('shares', 0) > 0 for h in holdings)
                    holdings_have_cost_basis = all(h.get('cost_basis', 0) > 0 for h in holdings)
                    portfolio_totals_updated = portfolio.get('total_invested', 0) > 0
                    
                    success = has_holdings and holdings_have_shares and holdings_have_cost_basis and portfolio_totals_updated
                    details = f"Holdings: {len(holdings)}, Shares: {holdings_have_shares}, Cost basis: {holdings_have_cost_basis}, Totals: {portfolio_totals_updated}"
                else:
                    success = False
                    details = f"Failed to fetch portfolio: Status {status}"
                
                self.log_test(
                    "Holdings created with correct shares and cost_basis", 
                    success,
                    details if not success else "",
                    {
                        "holdings_count": len(holdings) if success else 0,
                        "total_invested": portfolio.get('total_invested', 0) if success else 0
                    }
                )
        else:
            self.log_test(
                "Create investment test portfolio", 
                False,
                f"Failed to create portfolio for investment testing: Status {status}",
                {}
            )
        
        # Test 3: AI Portfolio Generation
        print("\n🤖 Test 3: AI Portfolio Generation...")
        
        ai_portfolio_request = {
            "portfolio_name": "Test Growth Portfolio",
            "goal": "Long-term wealth building",
            "risk_tolerance": "medium",
            "investment_amount": 50000,
            "time_horizon": "5-10",
            "roi_expectations": 12,
            "sector_preferences": "Technology and Healthcare focus"
        }
        
        status, data = self.make_request('POST', 'chat/generate-portfolio', ai_portfolio_request)
        success = status == 200 and data.get('success') == True and 'portfolio_suggestion' in data
        
        if success:
            portfolio_suggestion = data['portfolio_suggestion']
            has_reasoning = 'reasoning' in portfolio_suggestion and len(portfolio_suggestion['reasoning']) > 10
            has_allocations = 'allocations' in portfolio_suggestion and len(portfolio_suggestion['allocations']) > 0
            
            # Verify allocations sum to 100%
            allocations = portfolio_suggestion.get('allocations', [])
            total_allocation = sum(alloc.get('allocation_percentage', 0) for alloc in allocations)
            allocations_sum_to_100 = abs(total_allocation - 100) < 1  # Allow small rounding errors
            
            # Verify ticker symbols are valid (basic check)
            valid_tickers = all(
                isinstance(alloc.get('ticker'), str) and 
                len(alloc.get('ticker', '')) > 0 and
                alloc.get('ticker', '').isupper()
                for alloc in allocations
            )
            
            success = has_reasoning and has_allocations and allocations_sum_to_100 and valid_tickers
            details = f"Reasoning: {has_reasoning}, Allocations: {len(allocations)}, Sum to 100%: {allocations_sum_to_100} (total: {total_allocation}%), Valid tickers: {valid_tickers}"
        else:
            details = f"Status: {status}, Response: {data}"
        
        self.log_test(
            "POST /api/chat/generate-portfolio", 
            success,
            details if not success else "",
            {
                "has_portfolio_suggestion": 'portfolio_suggestion' in data if isinstance(data, dict) else False,
                "allocations_count": len(portfolio_suggestion.get('allocations', [])) if success else 0,
                "total_allocation": total_allocation if success else 0
            }
        )
        
        # Test 4: Allocation Updates
        print("\n📊 Test 4: Allocation Updates...")
        
        # Test 4a: Valid allocation update (sums to 100%)
        valid_allocation_update = {
            "allocations": [
                {"ticker": "AAPL", "allocation_percentage": 45, "sector": "Technology", "asset_type": "stock"},
                {"ticker": "MSFT", "allocation_percentage": 35, "sector": "Technology", "asset_type": "stock"},
                {"ticker": "BND", "allocation_percentage": 20, "sector": "Bonds", "asset_type": "bond"}
            ]
        }
        
        status, data = self.make_request('PUT', f'portfolios-v2/{portfolio_id}/allocations', valid_allocation_update)
        success = status == 200 and data.get('success') == True
        
        self.log_test(
            f"PUT /api/portfolios-v2/{portfolio_id}/allocations (valid - sums to 100%)", 
            success,
            f"Status: {status}, Response: {data}" if not success else "",
            {"allocation_update_success": success}
        )
        
        # Test 4b: Invalid allocation update (doesn't sum to 100%)
        invalid_allocation_update = {
            "allocations": [
                {"ticker": "AAPL", "allocation_percentage": 45, "sector": "Technology", "asset_type": "stock"},
                {"ticker": "MSFT", "allocation_percentage": 35, "sector": "Technology", "asset_type": "stock"},
                {"ticker": "BND", "allocation_percentage": 30, "sector": "Bonds", "asset_type": "bond"}  # Total = 110%
            ]
        }
        
        status, data = self.make_request('PUT', f'portfolios-v2/{portfolio_id}/allocations', invalid_allocation_update)
        success = status == 400  # Should return 400 Bad Request
        
        if success:
            error_message = data.get('detail', '') if isinstance(data, dict) else str(data)
            mentions_100_percent = '100' in error_message
            success = mentions_100_percent
            details = f"Error message mentions 100%: {mentions_100_percent}, Message: {error_message}"
        else:
            details = f"Expected 400, got {status}"
        
        self.log_test(
            f"PUT /api/portfolios-v2/{portfolio_id}/allocations (invalid - sums to 110%)", 
            success,
            details if not success else "",
            {"proper_validation": success}
        )
        
        # Test 5: Delete Portfolio (Soft Delete)
        print("\n🗑️ Test 5: Delete Portfolio...")
        
        status, data = self.make_request('DELETE', f'portfolios-v2/{portfolio_id}')
        success = status == 200 and data.get('success') == True
        
        self.log_test(
            f"DELETE /api/portfolios-v2/{portfolio_id} (soft delete)", 
            success,
            f"Status: {status}, Response: {data}" if not success else "",
            {"deleted": success}
        )
        
        # Verify portfolio is no longer in list (soft deleted)
        if success:
            status, data = self.make_request('GET', 'portfolios-v2/list')
            if status == 200 and 'portfolios' in data:
                portfolios = data.get('portfolios', [])
                portfolio_not_in_list = not any(p.get('portfolio_id') == portfolio_id for p in portfolios)
                
                self.log_test(
                    "Deleted portfolio not in list (soft delete verified)", 
                    portfolio_not_in_list,
                    f"Portfolio still found in list" if not portfolio_not_in_list else "",
                    {"soft_delete_working": portfolio_not_in_list}
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
        
        # Test 52-week high/low fix (PRIORITY TEST from review request)
        self.test_52_week_high_low_fix()
        
        # Test stock detail auto-initialization fix (PRIORITY TEST)
        self.test_stock_detail_auto_initialization()
        
        # Test multi-portfolio management system (PRIORITY TEST from review request)
        self.test_multi_portfolio_management_system()
        
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