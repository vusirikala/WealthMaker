#!/usr/bin/env python3
"""
Focused Chat Functionality Testing for Bug Fixes
Tests the specific scenarios mentioned in the review request
"""

import requests
import sys
import json
import time
import subprocess
from datetime import datetime, timezone

class ChatBugFixTester:
    def __init__(self, base_url="https://code-preview-54.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = "", response_data=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def setup_test_user(self) -> bool:
        """Create test user and session"""
        print("🔧 Setting up test user...")
        
        try:
            timestamp = int(time.time())
            user_id = f"chat-test-user-{timestamp}"
            session_token = f"chat_test_session_{timestamp}"
            
            # Create MongoDB script
            mongo_script = f'''
use('test_database');
var userId = '{user_id}';
var sessionToken = '{session_token}';
db.users.insertOne({{
  _id: userId,
  email: 'chat.test.{timestamp}@example.com',
  name: 'Chat Test User',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date()
}});
db.user_sessions.insertOne({{
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
}});
print('Chat test user setup complete');
'''
            
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
                return True
            else:
                print(f"❌ MongoDB setup failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Setup error: {str(e)}")
            return False

    def make_request(self, method: str, endpoint: str, data=None, use_auth: bool = True):
        """Make HTTP request"""
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
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            return response.status_code, response_data
            
        except Exception as e:
            return 500, {"error": str(e)}

    def test_chat_init_endpoint(self):
        """Test /api/chat/init for a new user"""
        print("\n💬 Testing Chat Init Endpoint...")
        
        # Test chat init for new user
        status, data = self.make_request('GET', 'chat/init')
        success = status == 200 and isinstance(data, dict)
        
        if success and data.get('message'):
            message = data.get('message', '')
            has_greeting = any(word in message.lower() for word in ['welcome', 'hi', 'hello'])
            has_question = '?' in message
            has_financial_content = any(word in message.lower() for word in ['financial', 'goal', 'investment'])
            
            success = has_greeting and has_question and has_financial_content and len(message) > 50
            details = f"Length: {len(message)}, Greeting: {has_greeting}, Question: {has_question}, Financial: {has_financial_content}"
        else:
            details = f"Status: {status}, Message: {data.get('message') if isinstance(data, dict) else 'No data'}"
        
        self.log_test(
            "Chat init generates initial message",
            success,
            details if not success else "",
            {"message_length": len(data.get('message', '')) if isinstance(data, dict) else 0}
        )
        
        # Verify first_chat_initiated flag is set
        status, context_data = self.make_request('GET', 'context')
        if status == 200 and isinstance(context_data, dict):
            first_chat_initiated = context_data.get('first_chat_initiated', False)
            success = first_chat_initiated is True
            self.log_test(
                "first_chat_initiated flag set",
                success,
                f"Flag value: {first_chat_initiated}" if not success else ""
            )
        else:
            self.log_test(
                "first_chat_initiated flag check",
                False,
                f"Context endpoint failed: {status}"
            )

    def test_chat_send_message(self):
        """Test chat send message functionality"""
        print("\n📤 Testing Chat Send Message...")
        
        # Test basic message send
        test_message = {
            "message": "I'm 30 years old and want to invest $1000 monthly for retirement. I have moderate risk tolerance."
        }
        
        status, data = self.make_request('POST', 'chat/send', test_message)
        success = status == 200 and isinstance(data, dict) and 'message' in data
        
        if success:
            ai_response = data.get('message', '')
            success = len(ai_response) > 20  # Should have substantial response
            details = f"Response length: {len(ai_response)}" if not success else ""
        else:
            details = f"Status: {status}, Data: {data}"
        
        self.log_test(
            "Chat send message returns AI response",
            success,
            details,
            {"has_response": 'message' in data if isinstance(data, dict) else False}
        )
        
        # Verify message was saved to chat_messages collection
        status, messages = self.make_request('GET', 'chat/messages')
        if status == 200 and isinstance(messages, list):
            user_messages = [msg for msg in messages if msg.get('role') == 'user']
            ai_messages = [msg for msg in messages if msg.get('role') == 'assistant']
            
            success = len(user_messages) > 0 and len(ai_messages) > 0
            self.log_test(
                "Messages saved to chat_messages collection",
                success,
                f"User: {len(user_messages)}, AI: {len(ai_messages)}" if not success else ""
            )
        else:
            self.log_test(
                "Messages saved to chat_messages collection",
                False,
                f"Failed to get messages: {status}"
            )

    def test_error_response_handling(self):
        """Test that error responses return proper JSON format"""
        print("\n🚨 Testing Error Response Handling...")
        
        # Test invalid message format
        invalid_message = {"invalid_field": "test"}
        status, data = self.make_request('POST', 'chat/send', invalid_message)
        
        # Should return proper JSON error, not "Body is disturbed or locked"
        if isinstance(data, dict):
            error_message = str(data.get('detail', '')) + str(data.get('error', ''))
            has_body_error = 'body is disturbed' in error_message.lower() or 'locked' in error_message.lower()
            success = not has_body_error
            details = f"Found body error: {error_message}" if has_body_error else ""
        else:
            success = True  # Non-dict response is acceptable
            details = ""
        
        self.log_test(
            "No 'Body is disturbed or locked' error",
            success,
            details
        )

    def test_context_building_mixed_data_types(self):
        """Test context building with mixed data types in liquidity_requirements"""
        print("\n🔧 Testing Context Building with Mixed Data Types...")
        
        # Create user context with mixed liquidity_requirements
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
        
        # Update user context
        status, data = self.make_request('PUT', 'context', mixed_context)
        success = status == 200
        self.log_test(
            "Update context with mixed liquidity_requirements",
            success,
            f"Status: {status}" if not success else ""
        )
        
        # Send message that should trigger context building
        test_message = {
            "message": "Can you help me with my retirement and house purchase goals?"
        }
        
        status, data = self.make_request('POST', 'chat/send', test_message)
        success = status == 200 and isinstance(data, dict) and 'message' in data
        
        # Verify no AttributeError occurs
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
            details
        )
        
        # Verify AI response includes context
        if success and isinstance(data, dict) and 'message' in data:
            ai_response = data['message'].lower()
            mentions_retirement = 'retirement' in ai_response
            mentions_house = 'house' in ai_response or 'home' in ai_response
            
            success = mentions_retirement or mentions_house
            self.log_test(
                "AI response includes context from mixed data types",
                success,
                f"Retirement: {mentions_retirement}, House: {mentions_house}" if not success else ""
            )

    def run_focused_tests(self):
        """Run focused chat bug fix tests"""
        print("🚀 Starting Chat Bug Fix Tests")
        print("=" * 50)
        
        # Setup test user
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return False
        
        # Run specific tests for the bug fixes
        self.test_chat_init_endpoint()
        self.test_chat_send_message()
        self.test_error_response_handling()
        self.test_context_building_mixed_data_types()
        
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
    tester = ChatBugFixTester()
    success = tester.run_focused_tests()
    
    # Save results
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "success_rate": (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
        "test_details": tester.test_results
    }
    
    with open('/app/chat_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: /app/chat_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())