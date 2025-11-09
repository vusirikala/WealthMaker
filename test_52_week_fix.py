#!/usr/bin/env python3
"""
Focused test for 52-week high/low fix
"""
import requests
import sys
import json
import time
from datetime import datetime, timezone

class FiftyTwoWeekTester:
    def __init__(self, base_url="https://code-preview-54.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = "test_session_1762659524"  # Use new session
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
            
        except requests.exceptions.Timeout:
            return 408, {"error": "Request timeout"}
        except Exception as e:
            return 500, {"error": str(e)}

    def test_52_week_values(self, symbol: str, expected_type: str = "stock"):
        """Test 52-week high/low values for a specific symbol"""
        status, data = self.make_request('GET', f'data/asset/{symbol}')
        
        if status != 200 or not isinstance(data, dict):
            self.log_test(f"{symbol} - API Response", False, f"Status: {status}")
            return False
        
        # Extract 52-week data
        live_data = data.get('live', {})
        current_price_data = live_data.get('currentPrice', {})
        
        fifty_two_week_high = current_price_data.get('fiftyTwoWeekHigh')
        fifty_two_week_low = current_price_data.get('fiftyTwoWeekLow')
        
        # Validate values
        high_valid = isinstance(fifty_two_week_high, (int, float)) and fifty_two_week_high > 0
        low_valid = isinstance(fifty_two_week_low, (int, float)) and fifty_two_week_low > 0
        logical_check = high_valid and low_valid and fifty_two_week_high > fifty_two_week_low
        
        # Check for reasonable values (not absurdly high/low)
        if expected_type == "crypto":
            reasonable_values = high_valid and low_valid and fifty_two_week_high < 200000 and fifty_two_week_low > 100
        else:
            reasonable_values = high_valid and low_valid and fifty_two_week_high < 10000 and fifty_two_week_low > 0.01
        
        success = high_valid and low_valid and logical_check and reasonable_values
        
        details = f"High: {fifty_two_week_high}, Low: {fifty_two_week_low}, Valid: {high_valid and low_valid}, Logical: {logical_check}, Reasonable: {reasonable_values}"
        
        self.log_test(f"{symbol} - 52-week high/low values", success, details if not success else "")
        
        return success

    def run_comprehensive_52_week_tests(self):
        """Run comprehensive 52-week high/low tests"""
        print("🚀 Testing 52-Week High/Low Fix")
        print("=" * 50)
        
        # Test 1: Large-cap stocks
        print("\n🏢 Large-cap stocks...")
        large_cap_stocks = ["AAPL", "MSFT", "GOOGL"]
        for symbol in large_cap_stocks:
            self.test_52_week_values(symbol)
        
        # Test 2: Mid-cap stocks
        print("\n🏭 Mid-cap stocks...")
        mid_cap_stocks = ["AMD", "NVDA"]
        for symbol in mid_cap_stocks:
            self.test_52_week_values(symbol)
        
        # Test 3: ETFs/Bonds (after live data update)
        print("\n📊 ETFs/Bonds...")
        etf_bonds = ["SPY", "BND"]
        for symbol in etf_bonds:
            self.test_52_week_values(symbol)
        
        # Test 4: Crypto
        print("\n₿ Crypto...")
        crypto_symbols = ["BTC-USD"]
        for symbol in crypto_symbols:
            self.test_52_week_values(symbol, "crypto")
        
        # Test 5: Previously failing stocks (after live data update)
        print("\n🔧 Previously failing stocks...")
        previously_failing = ["V", "PLTR"]
        for symbol in previously_failing:
            self.test_52_week_values(symbol)
        
        # Test 6: Data persistence
        print("\n💾 Data persistence test...")
        test_symbol = "AAPL"
        
        # First fetch
        status1, data1 = self.make_request('GET', f'data/asset/{test_symbol}')
        if status1 == 200:
            high1 = data1.get('live', {}).get('currentPrice', {}).get('fiftyTwoWeekHigh')
            low1 = data1.get('live', {}).get('currentPrice', {}).get('fiftyTwoWeekLow')
            
            # Second fetch (should return same values)
            time.sleep(1)
            status2, data2 = self.make_request('GET', f'data/asset/{test_symbol}')
            if status2 == 200:
                high2 = data2.get('live', {}).get('currentPrice', {}).get('fiftyTwoWeekHigh')
                low2 = data2.get('live', {}).get('currentPrice', {}).get('fiftyTwoWeekLow')
                
                consistent = high1 == high2 and low1 == low2 and high1 is not None
                self.log_test("Data persistence", consistent, f"Values changed between requests" if not consistent else "")
            else:
                self.log_test("Data persistence", False, f"Second fetch failed: {status2}")
        else:
            self.log_test("Data persistence", False, f"First fetch failed: {status1}")
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 52-Week Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = FiftyTwoWeekTester()
    success = tester.run_comprehensive_52_week_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())