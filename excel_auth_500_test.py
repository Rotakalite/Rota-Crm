#!/usr/bin/env python3
"""
🚨 EXCEL REPORT AUTHENTICATED 500 ERROR TEST
============================================

This test specifically tries to reproduce the 500 error that occurs with 
authenticated requests to the Excel endpoint. The user reports getting 500 
errors when making authenticated requests, but our tests show 401/403 responses.

This test will:
1. Try various JWT token formats that might cause 500 errors during verification
2. Test edge cases in authentication that might cause exceptions
3. Monitor for specific error conditions that cause 500 vs 401/403
4. Test with malformed but valid-looking JWT tokens
"""

import requests
import json
import sys
import time
from datetime import datetime
import base64
import jwt

# Production URL from frontend .env
BACKEND_URL = "https://rota-crm-production.up.railway.app"

class ExcelAuth500Tester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.target_client_id = "ac2350e9-3896-4b0d-82a1-2bdaa9788ee3"
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0

    def log_test(self, test_name, success, details="", status_code=None, error_detail=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "status_code": status_code,
            "error_detail": error_detail,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   📝 {details}")
        if status_code:
            print(f"   📊 Status Code: {status_code}")
        if error_detail:
            print(f"   🔍 Error: {error_detail}")
        print()

    def create_malformed_jwt_tokens(self):
        """Create various malformed JWT tokens that might cause 500 errors"""
        tokens = []
        
        # 1. Valid JWT structure but invalid signature
        header = {"alg": "RS256", "kid": "ins_2abcdefghijklmnopqrstuvwxyz123456", "typ": "JWT"}
        payload = {
            "azp": "https://adapting-eft-6.clerk.accounts.dev",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
            "iss": "https://adapting-eft-6.clerk.accounts.dev",
            "nbf": int(time.time()) - 10,
            "sid": "sess_2abcdefghijklmnopqrstuvwxyz123456",
            "sub": "user_2abcdefghijklmnopqrstuvwxyz123456"
        }
        
        # Create JWT with invalid signature
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        invalid_signature = "invalid_signature_that_might_cause_500_error"
        
        tokens.append({
            "name": "Valid JWT Structure Invalid Signature",
            "token": f"Bearer {header_b64}.{payload_b64}.{invalid_signature}"
        })
        
        # 2. JWT with missing parts
        tokens.append({
            "name": "JWT Missing Signature",
            "token": f"Bearer {header_b64}.{payload_b64}."
        })
        
        # 3. JWT with extra parts
        tokens.append({
            "name": "JWT Extra Parts",
            "token": f"Bearer {header_b64}.{payload_b64}.{invalid_signature}.extra_part"
        })
        
        # 4. JWT with invalid base64 encoding
        tokens.append({
            "name": "JWT Invalid Base64",
            "token": "Bearer invalid_base64!@#$.invalid_base64!@#$.invalid_base64!@#$"
        })
        
        # 5. JWT with valid base64 but invalid JSON
        invalid_json_b64 = base64.urlsafe_b64encode(b"invalid_json{").decode().rstrip('=')
        tokens.append({
            "name": "JWT Invalid JSON",
            "token": f"Bearer {invalid_json_b64}.{invalid_json_b64}.{invalid_signature}"
        })
        
        # 6. JWT with expired token (might cause different error handling)
        expired_payload = payload.copy()
        expired_payload["exp"] = int(time.time()) - 3600  # Expired 1 hour ago
        expired_payload_b64 = base64.urlsafe_b64encode(json.dumps(expired_payload).encode()).decode().rstrip('=')
        tokens.append({
            "name": "JWT Expired Token",
            "token": f"Bearer {header_b64}.{expired_payload_b64}.{invalid_signature}"
        })
        
        # 7. JWT with future issued time
        future_payload = payload.copy()
        future_payload["iat"] = int(time.time()) + 3600  # Issued in future
        future_payload_b64 = base64.urlsafe_b64encode(json.dumps(future_payload).encode()).decode().rstrip('=')
        tokens.append({
            "name": "JWT Future Issued",
            "token": f"Bearer {header_b64}.{future_payload_b64}.{invalid_signature}"
        })
        
        # 8. JWT with missing required claims
        minimal_payload = {"sub": "user_123"}
        minimal_payload_b64 = base64.urlsafe_b64encode(json.dumps(minimal_payload).encode()).decode().rstrip('=')
        tokens.append({
            "name": "JWT Missing Claims",
            "token": f"Bearer {header_b64}.{minimal_payload_b64}.{invalid_signature}"
        })
        
        # 9. Very long JWT token (might cause memory issues)
        long_payload = payload.copy()
        long_payload["long_claim"] = "x" * 10000  # Very long claim
        long_payload_b64 = base64.urlsafe_b64encode(json.dumps(long_payload).encode()).decode().rstrip('=')
        tokens.append({
            "name": "JWT Very Long Token",
            "token": f"Bearer {header_b64}.{long_payload_b64}.{invalid_signature}"
        })
        
        # 10. JWT with null bytes (might cause parsing issues)
        tokens.append({
            "name": "JWT With Null Bytes",
            "token": f"Bearer {header_b64}.{payload_b64}.\x00invalid_signature"
        })
        
        return tokens

    def test_malformed_jwt_tokens(self):
        """Test Excel endpoint with malformed JWT tokens that might cause 500 errors"""
        print("🔐 Testing Malformed JWT Tokens for 500 Errors")
        print("=" * 60)
        
        tokens = self.create_malformed_jwt_tokens()
        error_500_found = False
        
        for token_info in tokens:
            try:
                response = requests.get(
                    f"{self.backend_url}/api/front-office/report/excel",
                    params={"client_id": self.target_client_id},
                    headers={"Authorization": token_info["token"]},
                    timeout=30
                )
                
                status_code = response.status_code
                
                # Get error details
                error_detail = ""
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        error_json = response.json()
                        error_detail = error_json.get('detail', 'No detail provided')
                    else:
                        error_detail = response.text[:200] if response.text else "No error content"
                except:
                    error_detail = "Could not parse error response"
                
                if status_code == 500:
                    error_500_found = True
                    self.log_test(
                        f"JWT Token Test - {token_info['name']}",
                        False,
                        f"🚨 500 ERROR REPRODUCED! Token type: {token_info['name']}",
                        status_code,
                        error_detail
                    )
                elif status_code in [401, 403]:
                    self.log_test(
                        f"JWT Token Test - {token_info['name']}",
                        True,
                        f"✅ Expected auth error. Token type: {token_info['name']}",
                        status_code,
                        error_detail
                    )
                elif status_code == 400:
                    self.log_test(
                        f"JWT Token Test - {token_info['name']}",
                        True,
                        f"✅ Bad request (expected for malformed token). Token type: {token_info['name']}",
                        status_code,
                        error_detail
                    )
                else:
                    self.log_test(
                        f"JWT Token Test - {token_info['name']}",
                        True,
                        f"✅ Other response. Token type: {token_info['name']}",
                        status_code,
                        error_detail
                    )
                    
            except requests.exceptions.Timeout:
                self.log_test(
                    f"JWT Token Test - {token_info['name']}",
                    False,
                    f"⏰ Request timeout - possible server error",
                    None,
                    "Request timed out after 30 seconds"
                )
            except Exception as e:
                self.log_test(
                    f"JWT Token Test - {token_info['name']}",
                    False,
                    f"Request exception: {str(e)}",
                    None,
                    str(e)
                )
        
        return error_500_found

    def test_edge_case_scenarios(self):
        """Test edge case scenarios that might cause 500 errors"""
        print("🧪 Testing Edge Case Scenarios")
        print("=" * 60)
        
        edge_cases = [
            {
                "name": "Very Long Client ID",
                "params": {"client_id": "x" * 1000},
                "headers": {"Authorization": "Bearer test_token"}
            },
            {
                "name": "Client ID with Special Characters",
                "params": {"client_id": "client_id_with_special_chars_!@#$%^&*()"},
                "headers": {"Authorization": "Bearer test_token"}
            },
            {
                "name": "Client ID with SQL Injection Attempt",
                "params": {"client_id": "'; DROP TABLE clients; --"},
                "headers": {"Authorization": "Bearer test_token"}
            },
            {
                "name": "Client ID with Unicode Characters",
                "params": {"client_id": "client_id_with_unicode_çğıöşü"},
                "headers": {"Authorization": "Bearer test_token"}
            },
            {
                "name": "Multiple Client IDs",
                "params": {"client_id": ["id1", "id2", "id3"]},
                "headers": {"Authorization": "Bearer test_token"}
            },
            {
                "name": "Invalid Date Format",
                "params": {
                    "client_id": self.target_client_id,
                    "start_date": "not_a_date",
                    "end_date": "also_not_a_date"
                },
                "headers": {"Authorization": "Bearer test_token"}
            },
            {
                "name": "Date Range Too Large",
                "params": {
                    "client_id": self.target_client_id,
                    "start_date": "1900-01-01",
                    "end_date": "2100-12-31"
                },
                "headers": {"Authorization": "Bearer test_token"}
            },
            {
                "name": "Negative Date Values",
                "params": {
                    "client_id": self.target_client_id,
                    "start_date": "-2024-01-01",
                    "end_date": "-2024-01-31"
                },
                "headers": {"Authorization": "Bearer test_token"}
            }
        ]
        
        error_500_found = False
        
        for case in edge_cases:
            try:
                response = requests.get(
                    f"{self.backend_url}/api/front-office/report/excel",
                    params=case["params"],
                    headers=case["headers"],
                    timeout=30
                )
                
                status_code = response.status_code
                
                # Get error details
                error_detail = ""
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        error_json = response.json()
                        error_detail = error_json.get('detail', 'No detail provided')
                    else:
                        error_detail = response.text[:200] if response.text else "No error content"
                except:
                    error_detail = "Could not parse error response"
                
                if status_code == 500:
                    error_500_found = True
                    self.log_test(
                        f"Edge Case - {case['name']}",
                        False,
                        f"🚨 500 ERROR REPRODUCED! Case: {case['name']}",
                        status_code,
                        error_detail
                    )
                elif status_code in [400, 401, 403, 422]:
                    self.log_test(
                        f"Edge Case - {case['name']}",
                        True,
                        f"✅ Expected error response. Case: {case['name']}",
                        status_code,
                        error_detail
                    )
                else:
                    self.log_test(
                        f"Edge Case - {case['name']}",
                        True,
                        f"✅ Other response. Case: {case['name']}",
                        status_code,
                        error_detail
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Edge Case - {case['name']}",
                    False,
                    f"Request exception: {str(e)}",
                    None,
                    str(e)
                )
        
        return error_500_found

    def run_auth_500_test(self):
        """Run comprehensive authentication 500 error test"""
        print("🚨 EXCEL REPORT AUTHENTICATED 500 ERROR TEST")
        print("=" * 70)
        print(f"🎯 Backend URL: {self.backend_url}")
        print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Target Client ID: {self.target_client_id}")
        print(f"🚨 Focus: Find authentication scenarios that cause 500 errors")
        print("=" * 70)
        print()
        
        # Test malformed JWT tokens
        error_500_jwt = self.test_malformed_jwt_tokens()
        
        print()
        
        # Test edge case scenarios
        error_500_edge = self.test_edge_case_scenarios()
        
        # Show results
        error_500_found = error_500_jwt or error_500_edge
        self.show_results(error_500_found)
        
        return error_500_found

    def show_results(self, error_500_found):
        """Show test results"""
        print("\n" + "=" * 70)
        print("📊 EXCEL AUTHENTICATED 500 ERROR TEST RESULTS")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"✅ Successful Tests: {self.passed_tests}")
        print(f"❌ Failed Tests: {self.total_tests - self.passed_tests}")
        print(f"📊 Total Tests: {self.total_tests}")
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        if error_500_found:
            print(f"\n🚨 500 ERROR REPRODUCED: YES")
            print("=" * 50)
            print("✅ Successfully reproduced 500 Internal Server Error!")
            
            # Show specific 500 errors
            error_500_tests = [r for r in self.test_results if r.get('status_code') == 500]
            if error_500_tests:
                print(f"\n🚨 500 ERROR DETAILS:")
                for error in error_500_tests:
                    print(f"   • {error['test']}")
                    print(f"     📝 {error['details']}")
                    print(f"     🔍 Error: {error['error_detail']}")
                    print()
        else:
            print(f"\n🚨 500 ERROR REPRODUCED: NO")
            print("=" * 50)
            print("⚠️ Could not reproduce 500 error with authentication scenarios")
            print("💡 The 500 error might be caused by:")
            print("   1. Specific valid authentication tokens")
            print("   2. Database-related issues during Excel generation")
            print("   3. Memory constraints with large datasets")
            print("   4. Specific client data that causes exceptions")
        
        # Save results
        results = {
            'test_summary': {
                'total_tests': self.total_tests,
                'passed_tests': self.passed_tests,
                'failed_tests': self.total_tests - self.passed_tests,
                'success_rate': success_rate,
                'error_500_reproduced': error_500_found,
                'test_timestamp': datetime.now().isoformat()
            },
            'test_results': self.test_results,
            'error_500_tests': [r for r in self.test_results if r.get('status_code') == 500]
        }
        
        with open('/app/excel_auth_500_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Test results saved: /app/excel_auth_500_test_results.json")

def main():
    """Main test function"""
    tester = ExcelAuth500Tester()
    error_500_found = tester.run_auth_500_test()
    
    if error_500_found:
        print("\n🚨 500 ERROR REPRODUCED!")
        print("✅ Found authentication scenarios that cause 500 errors")
        print("🔧 Check the detailed results for specific error conditions")
        sys.exit(0)
    else:
        print("\n🔍 NO 500 ERRORS REPRODUCED")
        print("⚠️ The 500 error might require valid authentication or specific conditions")
        print("💡 Consider testing with real user tokens or specific client data")
        sys.exit(0)

if __name__ == "__main__":
    main()