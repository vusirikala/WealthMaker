#!/usr/bin/env python3
"""
Specific test for WealthMaker Chat Auto-Initiation Feature
Tests all scenarios mentioned in the review request
"""

import requests
import sys
import json
import time
import subprocess
from datetime import datetime, timezone

class ChatInitTester:
    def __init__(self, base_url="https://money-grow-app.preview.emergentagent.com"):
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
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")

    def setup_test_user(self) -> bool:
        """Create test user and session in MongoDB"""
        print("\n🔧 Setting up test user and session...")
        
        try:
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
                return True
            else:
                print(f"❌ MongoDB setup failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Setup error: {str(e)}")
            return False

    def make_request(self, method: str, endpoint: str, data: dict = None) -> tuple:
        """Make HTTP request with proper headers"""
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

    def test_scenario_1_new_user_init(self):
        """Test Chat Init Endpoint for New User"""
        print("\n📋 SCENARIO 1: Test Chat Init Endpoint for New User")
        
        # Verify no existing messages
        status, messages = self.make_request('GET', 'chat/messages')
        initial_count = len(messages) if isinstance(messages, list) else 0
        success = status == 200 and initial_count == 0
        self.log_test("No existing messages for new user", success, f"Status: {status}, Count: {initial_count}")
        
        # Call chat init endpoint
        status, data = self.make_request('GET', 'chat/init')
        success = status == 200 and isinstance(data, dict) and data.get('message') is not None
        self.log_test("GET /api/chat/init returns greeting", success, f"Status: {status}")
        
        if success and data.get('message'):
            message = data.get('message', '')
            
            # Verify personalized greeting
            has_name = 'Test User' in message
            self.log_test("Message includes user name", has_name, f"Name found: {has_name}")
            
            # Verify questions about financial goals
            financial_keywords = ['financial', 'goals', 'investment', 'risk', 'portfolio', 'saving', 'retirement']
            has_financial_questions = any(keyword in message.lower() for keyword in financial_keywords)
            self.log_test("Message asks about financial goals", has_financial_questions)
            
            # Verify questions about risk tolerance
            risk_keywords = ['risk', 'tolerance', 'conservative', 'moderate', 'aggressive']
            has_risk_questions = any(keyword in message.lower() for keyword in risk_keywords)
            self.log_test("Message asks about risk tolerance", has_risk_questions)
            
            # Verify questions about sectors
            sector_keywords = ['sector', 'industry', 'technology', 'healthcare', 'prefer']
            has_sector_questions = any(keyword in message.lower() for keyword in sector_keywords)
            self.log_test("Message asks about sector preferences", has_sector_questions)
            
            # Verify message length (should be comprehensive)
            adequate_length = len(message) > 500
            self.log_test("Message is comprehensive (>500 chars)", adequate_length, f"Length: {len(message)}")
        
        # Verify message saved to chat_messages collection
        status, messages = self.make_request('GET', 'chat/messages')
        success = status == 200 and isinstance(messages, list) and len(messages) == 1
        self.log_test("Initial message saved to chat history", success, f"Message count: {len(messages) if isinstance(messages, list) else 0}")
        
        if success and len(messages) > 0:
            saved_message = messages[0]
            is_assistant_message = saved_message.get('role') == 'assistant'
            self.log_test("Saved message has correct role (assistant)", is_assistant_message)
        
        # Verify first_chat_initiated flag set to true
        status, context = self.make_request('GET', 'context')
        success = status == 200 and isinstance(context, dict) and context.get('first_chat_initiated') is True
        self.log_test("first_chat_initiated flag set to true", success, f"Flag value: {context.get('first_chat_initiated') if isinstance(context, dict) else 'N/A'}")

    def test_scenario_2_idempotency(self):
        """Test Chat Init Idempotency"""
        print("\n📋 SCENARIO 2: Test Chat Init Idempotency")
        
        # Get current message count
        status, messages = self.make_request('GET', 'chat/messages')
        initial_count = len(messages) if isinstance(messages, list) else 0
        
        # Call chat init again
        status, data = self.make_request('GET', 'chat/init')
        success = status == 200 and isinstance(data, dict) and data.get('message') is None
        self.log_test("Second call returns null message", success, f"Status: {status}, Message: {data.get('message') if isinstance(data, dict) else 'N/A'}")
        
        # Verify no duplicate messages created
        status, messages = self.make_request('GET', 'chat/messages')
        final_count = len(messages) if isinstance(messages, list) else 0
        success = status == 200 and final_count == initial_count
        self.log_test("No duplicate messages created", success, f"Before: {initial_count}, After: {final_count}")

    def test_scenario_3_existing_messages(self):
        """Test Chat Init with Existing Messages"""
        print("\n📋 SCENARIO 3: Test Chat Init with Existing Messages")
        
        # Send a user message first
        test_message = {"message": "Hello, I want to start investing"}
        status, response = self.make_request('POST', 'chat/send', test_message)
        success = status == 200
        self.log_test("User message sent successfully", success, f"Status: {status}")
        
        # Wait for AI processing
        time.sleep(2)
        
        # Get message count
        status, messages = self.make_request('GET', 'chat/messages')
        message_count = len(messages) if isinstance(messages, list) else 0
        
        # Call chat init - should return null since messages exist
        status, data = self.make_request('GET', 'chat/init')
        success = status == 200 and isinstance(data, dict) and data.get('message') is None
        self.log_test("Chat init returns null for existing messages", success, f"Status: {status}, Message: {data.get('message') if isinstance(data, dict) else 'N/A'}")
        
        # Verify first_chat_initiated is still true
        status, context = self.make_request('GET', 'context')
        success = status == 200 and isinstance(context, dict) and context.get('first_chat_initiated') is True
        self.log_test("first_chat_initiated remains true", success)

    def test_scenario_4_chat_messages_endpoint(self):
        """Test Chat Messages Endpoint"""
        print("\n📋 SCENARIO 4: Test Chat Messages Endpoint")
        
        # Get chat messages
        status, messages = self.make_request('GET', 'chat/messages')
        success = status == 200 and isinstance(messages, list)
        self.log_test("GET /api/chat/messages works", success, f"Status: {status}")
        
        if success and len(messages) > 0:
            # Verify initial greeting message is returned
            has_greeting = any(msg.get('role') == 'assistant' and len(msg.get('message', '')) > 500 for msg in messages)
            self.log_test("Initial greeting message present", has_greeting)
            
            # Verify message format is correct
            first_message = messages[0]
            has_required_fields = all(field in first_message for field in ['id', 'user_id', 'role', 'message', 'timestamp'])
            self.log_test("Message format is correct", has_required_fields)

    def test_scenario_5_full_user_flow(self):
        """Test Full User Flow"""
        print("\n📋 SCENARIO 5: Test Full User Flow")
        
        # Get initial message count
        status, messages = self.make_request('GET', 'chat/messages')
        initial_count = len(messages) if isinstance(messages, list) else 0
        
        # Send user response to greeting
        user_response = {
            "message": "I'm 30 years old, want to invest $1000 monthly for retirement. I prefer moderate risk and am interested in technology and healthcare sectors."
        }
        
        status, response = self.make_request('POST', 'chat/send', user_response)
        success = status == 200 and isinstance(response, dict) and 'message' in response
        self.log_test("User can respond to greeting", success, f"Status: {status}")
        
        # Wait for AI processing
        if success:
            time.sleep(3)
        
        # Verify conversation continues normally
        status, messages = self.make_request('GET', 'chat/messages')
        final_count = len(messages) if isinstance(messages, list) else 0
        success = status == 200 and final_count > initial_count
        self.log_test("Conversation continues normally", success, f"Messages: {initial_count} -> {final_count}")
        
        if success and isinstance(messages, list) and len(messages) >= 2:
            # Verify AI responded appropriately
            last_message = messages[-1]
            is_ai_response = last_message.get('role') == 'assistant' and len(last_message.get('message', '')) > 50
            self.log_test("AI responds appropriately", is_ai_response)

    def run_all_tests(self):
        """Run all test scenarios"""
        print("🚀 Starting WealthMaker Chat Auto-Initiation Tests")
        print("=" * 60)
        
        # Setup test user
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return False
        
        # Run all scenarios
        self.test_scenario_1_new_user_init()
        self.test_scenario_2_idempotency()
        self.test_scenario_3_existing_messages()
        self.test_scenario_4_chat_messages_endpoint()
        self.test_scenario_5_full_user_flow()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = ChatInitTester()
    success = tester.run_all_tests()
    
    print(f"\n🎯 OVERALL RESULT: {'PASS' if success else 'FAIL'}")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())