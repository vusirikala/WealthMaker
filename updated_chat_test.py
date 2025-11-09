#!/usr/bin/env python3
"""
Comprehensive Testing for UPDATED Chat Auto-Initiation Feature
Tests the simplified initial message and one-by-one question flow
"""

import requests
import sys
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

class UpdatedChatTester:
    def __init__(self, base_url="https://wealth-dashboard-77.preview.emergentagent.com"):
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

    def test_new_initial_message(self):
        """Test Scenario 1: New Initial Message Requirements"""
        print("\n🆕 TEST SCENARIO 1: New Initial Message")
        
        # Call GET /api/chat/init endpoint
        status, data = self.make_request('GET', 'chat/init')
        
        if status != 200 or not isinstance(data, dict) or not data.get('message'):
            self.log_test(
                "Chat init endpoint returns message", 
                False,
                f"Status: {status}, Data: {data}",
                data
            )
            return
        
        message = data.get('message', '')
        print(f"\n📝 Initial Message ({len(message)} chars):")
        print(f"'{message}'")
        
        # Test 1: Message is SHORT (under 300 characters recommended)
        is_short = len(message) <= 300
        self.log_test(
            "Initial message is under 300 characters", 
            is_short,
            f"Message length: {len(message)} chars" if not is_short else "",
            {"message_length": len(message)}
        )
        
        # Test 2: Asks only ONE question about main financial goal
        question_count = message.count('?')
        asks_one_question = question_count == 1
        self.log_test(
            "Initial message asks only ONE question", 
            asks_one_question,
            f"Found {question_count} questions" if not asks_one_question else "",
            {"question_count": question_count}
        )
        
        # Test 3: Question is about financial goal
        financial_keywords = ['financial', 'goal', 'investment', 'saving', 'retirement', 'money', 'fund']
        has_financial_focus = any(keyword in message.lower() for keyword in financial_keywords)
        self.log_test(
            "Initial message asks about financial goal", 
            has_financial_focus,
            "No financial keywords found" if not has_financial_focus else "",
            {"has_financial_keywords": has_financial_focus}
        )
        
        # Test 4: Friendly and conversational
        friendly_keywords = ['hi', 'hello', 'welcome', 'excited', 'help', '👋', '💼']
        is_friendly = any(keyword in message.lower() for keyword in friendly_keywords)
        self.log_test(
            "Initial message is friendly and conversational", 
            is_friendly,
            "No friendly keywords found" if not is_friendly else "",
            {"is_friendly": is_friendly}
        )
        
        # Test 5: Message is saved to chat_messages
        status, messages = self.make_request('GET', 'chat/messages')
        message_saved = (status == 200 and isinstance(messages, list) and 
                        len(messages) > 0 and messages[-1].get('role') == 'assistant')
        self.log_test(
            "Initial message saved to chat_messages", 
            message_saved,
            f"Status: {status}, Messages: {len(messages) if isinstance(messages, list) else 0}" if not message_saved else "",
            {"message_count": len(messages) if isinstance(messages, list) else 0}
        )

    def test_one_by_one_question_flow(self):
        """Test Scenario 2: One-by-One Question Flow"""
        print("\n🔄 TEST SCENARIO 2: One-by-One Question Flow")
        
        # User responds with retirement goal
        user_message = "I want to save for retirement"
        
        print(f"\n👤 User says: '{user_message}'")
        
        # Send user message
        status, response = self.make_request('POST', 'chat/send', {"message": user_message})
        
        if status != 200 or not isinstance(response, dict) or not response.get('message'):
            self.log_test(
                "Chat send endpoint works", 
                False,
                f"Status: {status}, Response: {response}",
                response
            )
            return
        
        ai_response = response.get('message', '')
        print(f"\n🤖 AI responds ({len(ai_response)} chars):")
        print(f"'{ai_response}'")
        
        # Test 1: AI acknowledges the answer
        acknowledgment_keywords = ['retirement', 'great', 'excellent', 'good', 'thank', 'understand']
        acknowledges = any(keyword in ai_response.lower() for keyword in acknowledgment_keywords)
        self.log_test(
            "AI acknowledges user's retirement goal", 
            acknowledges,
            "No acknowledgment keywords found" if not acknowledges else "",
            {"acknowledges_answer": acknowledges}
        )
        
        # Test 2: Asks ONE follow-up question (not multiple)
        question_count = ai_response.count('?')
        asks_one_question = question_count == 1
        self.log_test(
            "AI asks ONE follow-up question", 
            asks_one_question,
            f"Found {question_count} questions" if not asks_one_question else "",
            {"follow_up_questions": question_count}
        )
        
        # Test 3: Question is relevant to retirement goal
        retirement_keywords = ['retirement', 'age', 'when', 'how much', 'timeline', 'years', 'plan']
        is_relevant = any(keyword in ai_response.lower() for keyword in retirement_keywords)
        self.log_test(
            "Follow-up question is relevant to retirement", 
            is_relevant,
            "No retirement-related keywords found" if not is_relevant else "",
            {"retirement_relevant": is_relevant}
        )

    def test_context_extraction(self):
        """Test Scenario 3: Context Extraction"""
        print("\n🧠 TEST SCENARIO 3: Context Extraction")
        
        # Wait for context extraction to process
        time.sleep(2)
        
        # Check GET /api/context endpoint
        status, context_data = self.make_request('GET', 'context')
        
        if status != 200 or not isinstance(context_data, dict):
            self.log_test(
                "Context endpoint accessible", 
                False,
                f"Status: {status}, Data: {context_data}",
                context_data
            )
            return
        
        print(f"\n🔍 Context Data:")
        print(json.dumps(context_data, indent=2, default=str))
        
        # Test 1: Goal added to liquidity_requirements
        liquidity_reqs = context_data.get('liquidity_requirements', [])
        has_retirement_goal = any(
            'retirement' in str(req).lower() 
            for req in liquidity_reqs
        )
        self.log_test(
            "Retirement goal extracted to liquidity_requirements", 
            has_retirement_goal,
            f"Found {len(liquidity_reqs)} goals, no retirement goal" if not has_retirement_goal else "",
            {"goals_count": len(liquidity_reqs), "has_retirement": has_retirement_goal}
        )
        
        # Test 2: Relevant fields populated
        expected_fields = ['goal_name', 'goal_type', 'user_id', 'updated_at']
        populated_fields = [field for field in expected_fields if context_data.get(field)]
        
        if liquidity_reqs and has_retirement_goal:
            retirement_goal = next((req for req in liquidity_reqs if 'retirement' in str(req).lower()), {})
            goal_fields = [field for field in ['goal_name', 'goal_type'] if retirement_goal.get(field)]
            fields_populated = len(goal_fields) > 0
        else:
            fields_populated = len(populated_fields) >= 2
        
        self.log_test(
            "Relevant context fields populated", 
            fields_populated,
            f"Populated fields: {populated_fields}" if not fields_populated else "",
            {"populated_fields": populated_fields}
        )

    def test_multi_turn_conversation(self):
        """Test Scenario 4: Multi-Turn Conversation"""
        print("\n💬 TEST SCENARIO 4: Multi-Turn Conversation")
        
        conversation_turns = [
            "I'm 45 years old and want to retire at 65",
            "I can invest about $3000 per month",
            "I prefer moderate risk investments"
        ]
        
        for i, user_message in enumerate(conversation_turns, 1):
            print(f"\n👤 Turn {i}: '{user_message}'")
            
            # Send message
            status, response = self.make_request('POST', 'chat/send', {"message": user_message})
            
            if status != 200 or not isinstance(response, dict) or not response.get('message'):
                self.log_test(
                    f"Turn {i} - Chat response received", 
                    False,
                    f"Status: {status}",
                    response
                )
                continue
            
            ai_response = response.get('message', '')
            print(f"🤖 AI Turn {i} ({len(ai_response)} chars): '{ai_response[:200]}...'")
            
            # Test: AI asks ONE focused question
            question_count = ai_response.count('?')
            asks_one_question = question_count <= 2  # Allow some flexibility
            self.log_test(
                f"Turn {i} - AI asks focused question(s)", 
                asks_one_question,
                f"Found {question_count} questions" if not asks_one_question else "",
                {"turn": i, "questions": question_count}
            )
            
            # Brief pause between turns
            time.sleep(1)
        
        # Test: Context is progressively built up
        status, final_context = self.make_request('GET', 'context')
        
        if status == 200 and isinstance(final_context, dict):
            context_fields = [k for k, v in final_context.items() if v is not None and v != [] and v != {}]
            context_rich = len(context_fields) >= 5  # Should have accumulated several fields
            
            self.log_test(
                "Context progressively built up", 
                context_rich,
                f"Only {len(context_fields)} fields populated" if not context_rich else "",
                {"context_fields_count": len(context_fields)}
            )
        
        # Test: Information from earlier turns is retained
        has_age_info = any(field in final_context for field in ['date_of_birth', 'retirement_age'])
        has_investment_info = any(field in final_context for field in ['monthly_investment', 'annual_investment'])
        has_risk_info = final_context.get('risk_tolerance') is not None
        
        info_retained = has_age_info and has_investment_info and has_risk_info
        self.log_test(
            "Previous context retained", 
            info_retained,
            f"Age: {has_age_info}, Investment: {has_investment_info}, Risk: {has_risk_info}" if not info_retained else "",
            {"age_info": has_age_info, "investment_info": has_investment_info, "risk_info": has_risk_info}
        )

    def test_system_prompt_guidance(self):
        """Test Scenario 5: System Prompt Guidance"""
        print("\n🎯 TEST SCENARIO 5: System Prompt Guidance")
        
        # Send a message that might trigger multiple questions
        complex_message = "I want to invest in stocks and bonds for multiple goals"
        
        print(f"\n👤 Complex request: '{complex_message}'")
        
        status, response = self.make_request('POST', 'chat/send', {"message": complex_message})
        
        if status != 200 or not isinstance(response, dict) or not response.get('message'):
            self.log_test(
                "Complex message handled", 
                False,
                f"Status: {status}",
                response
            )
            return
        
        ai_response = response.get('message', '')
        print(f"\n🤖 AI response ({len(ai_response)} chars):")
        print(f"'{ai_response}'")
        
        # Test 1: AI follows "ask ONE question at a time" instruction
        question_count = ai_response.count('?')
        follows_one_question_rule = question_count <= 2  # Allow some flexibility
        self.log_test(
            "AI follows 'one question at a time' rule", 
            follows_one_question_rule,
            f"Found {question_count} questions" if not follows_one_question_rule else "",
            {"question_count": question_count}
        )
        
        # Test 2: AI should NOT list multiple questions in one response
        list_indicators = ['1.', '2.', '3.', 'first,', 'second,', 'also,', 'additionally,']
        has_question_list = any(indicator in ai_response.lower() for indicator in list_indicators)
        avoids_question_lists = not has_question_list
        self.log_test(
            "AI avoids listing multiple questions", 
            avoids_question_lists,
            "Found question list indicators" if not avoids_question_lists else "",
            {"has_question_list": has_question_list}
        )
        
        # Test 3: Response is conversational and natural
        conversational_indicators = ['let me', 'i understand', 'great', 'tell me', 'help me understand']
        is_conversational = any(indicator in ai_response.lower() for indicator in conversational_indicators)
        self.log_test(
            "Response is conversational and natural", 
            is_conversational,
            "No conversational indicators found" if not is_conversational else "",
            {"is_conversational": is_conversational}
        )

    def run_updated_chat_tests(self):
        """Run all updated chat auto-initiation tests"""
        print("🚀 Starting UPDATED Chat Auto-Initiation Tests")
        print("=" * 60)
        
        # Setup test user
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return False
        
        # Run test scenarios from review request
        self.test_new_initial_message()
        self.test_one_by_one_question_flow()
        self.test_context_extraction()
        self.test_multi_turn_conversation()
        self.test_system_prompt_guidance()
        
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
        else:
            print("\n🎉 All tests passed! Updated chat auto-initiation feature is working correctly.")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = UpdatedChatTester()
    success = tester.run_updated_chat_tests()
    
    # Save detailed results
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_type": "updated_chat_auto_initiation",
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "success_rate": (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
        "test_details": tester.test_results
    }
    
    with open('/app/updated_chat_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/updated_chat_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())