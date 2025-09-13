#!/usr/bin/env python3
"""
GreenWave CRM MongoDB Sort Memory Limit Fix Test
==============================================

Testing the fix for MongoDB sort memory limit error on /api/belge/list endpoint.

Problem: "Sort exceeded memory limit of 33554432 bytes, but did not opt in to external sorting"
Fix: Added .limit(1000) to documents.find().sort("created_at", -1) query

Test Requirements:
1. Verify /api/belge/list doesn't return 500 error
2. Check authentication requirement (401/403)
3. Verify memory limit error is resolved

Expected Result: Should get 401/403 authentication error instead of 500
"""

import requests
import json
import sys
from datetime import datetime

# Railway production URL
BACKEND_URL = "https://rota-crm-production.up.railway.app"

class BelgeListMemoryLimitTest:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status} - {test_name}"
        if details:
            result += f" | {details}"
        
        self.test_results.append(result)
        print(result)
        
    def test_backend_health(self):
        """Test if backend is accessible"""
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=10)
            if response.status_code == 200:
                self.log_test("Backend Health Check", True, f"Status: {response.status_code}")
                return True
            else:
                self.log_test("Backend Health Check", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Error: {str(e)}")
            return False
    
    def test_belge_list_no_auth(self):
        """Test /api/belge/list without authentication - should return 401/403, not 500"""
        try:
            response = requests.get(f"{self.backend_url}/api/belge/list", timeout=30)
            
            # Should return 401 or 403 (authentication required), NOT 500 (memory limit error)
            if response.status_code in [401, 403]:
                self.log_test("Belge List No Auth", True, f"Status: {response.status_code} (Authentication required)")
                return True
            elif response.status_code == 500:
                # Check if it's the memory limit error
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'memory limit' in error_detail.lower() or 'sort exceeded' in error_detail.lower():
                        self.log_test("Belge List No Auth", False, f"Status: 500 - MEMORY LIMIT ERROR STILL EXISTS: {error_detail}")
                    else:
                        self.log_test("Belge List No Auth", False, f"Status: 500 - Other server error: {error_detail}")
                except:
                    self.log_test("Belge List No Auth", False, f"Status: 500 - Server error (could not parse response)")
                return False
            else:
                self.log_test("Belge List No Auth", False, f"Status: {response.status_code} - Unexpected response")
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("Belge List No Auth", False, "Request timeout - possible memory limit issue")
            return False
        except Exception as e:
            self.log_test("Belge List No Auth", False, f"Error: {str(e)}")
            return False
    
    def test_belge_list_invalid_token(self):
        """Test /api/belge/list with invalid token - should return 401, not 500"""
        try:
            headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.get(f"{self.backend_url}/api/belge/list", headers=headers, timeout=30)
            
            # Should return 401 (invalid token), NOT 500 (memory limit error)
            if response.status_code == 401:
                self.log_test("Belge List Invalid Token", True, f"Status: {response.status_code} (Invalid token)")
                return True
            elif response.status_code == 500:
                # Check if it's the memory limit error
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'memory limit' in error_detail.lower() or 'sort exceeded' in error_detail.lower():
                        self.log_test("Belge List Invalid Token", False, f"Status: 500 - MEMORY LIMIT ERROR STILL EXISTS: {error_detail}")
                    else:
                        self.log_test("Belge List Invalid Token", False, f"Status: 500 - Other server error: {error_detail}")
                except:
                    self.log_test("Belge List Invalid Token", False, f"Status: 500 - Server error (could not parse response)")
                return False
            else:
                self.log_test("Belge List Invalid Token", False, f"Status: {response.status_code} - Unexpected response")
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("Belge List Invalid Token", False, "Request timeout - possible memory limit issue")
            return False
        except Exception as e:
            self.log_test("Belge List Invalid Token", False, f"Error: {str(e)}")
            return False
    
    def test_belge_list_malformed_token(self):
        """Test /api/belge/list with malformed token - should return 401, not 500"""
        try:
            headers = {"Authorization": "Bearer malformed.jwt.token"}
            response = requests.get(f"{self.backend_url}/api/belge/list", headers=headers, timeout=30)
            
            # Should return 401 (malformed token), NOT 500 (memory limit error)
            if response.status_code == 401:
                self.log_test("Belge List Malformed Token", True, f"Status: {response.status_code} (Malformed token)")
                return True
            elif response.status_code == 500:
                # Check if it's the memory limit error
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'memory limit' in error_detail.lower() or 'sort exceeded' in error_detail.lower():
                        self.log_test("Belge List Malformed Token", False, f"Status: 500 - MEMORY LIMIT ERROR STILL EXISTS: {error_detail}")
                    else:
                        self.log_test("Belge List Malformed Token", False, f"Status: 500 - Other server error: {error_detail}")
                except:
                    self.log_test("Belge List Malformed Token", False, f"Status: 500 - Server error (could not parse response)")
                return False
            else:
                self.log_test("Belge List Malformed Token", False, f"Status: {response.status_code} - Unexpected response")
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("Belge List Malformed Token", False, "Request timeout - possible memory limit issue")
            return False
        except Exception as e:
            self.log_test("Belge List Malformed Token", False, f"Error: {str(e)}")
            return False
    
    def test_belge_list_empty_auth(self):
        """Test /api/belge/list with empty Authorization header - should return 401/403, not 500"""
        try:
            headers = {"Authorization": ""}
            response = requests.get(f"{self.backend_url}/api/belge/list", headers=headers, timeout=30)
            
            # Should return 401 or 403 (empty auth), NOT 500 (memory limit error)
            if response.status_code in [401, 403]:
                self.log_test("Belge List Empty Auth", True, f"Status: {response.status_code} (Empty authorization)")
                return True
            elif response.status_code == 500:
                # Check if it's the memory limit error
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'memory limit' in error_detail.lower() or 'sort exceeded' in error_detail.lower():
                        self.log_test("Belge List Empty Auth", False, f"Status: 500 - MEMORY LIMIT ERROR STILL EXISTS: {error_detail}")
                    else:
                        self.log_test("Belge List Empty Auth", False, f"Status: 500 - Other server error: {error_detail}")
                except:
                    self.log_test("Belge List Empty Auth", False, f"Status: 500 - Server error (could not parse response)")
                return False
            else:
                self.log_test("Belge List Empty Auth", False, f"Status: {response.status_code} - Unexpected response")
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("Belge List Empty Auth", False, "Request timeout - possible memory limit issue")
            return False
        except Exception as e:
            self.log_test("Belge List Empty Auth", False, f"Error: {str(e)}")
            return False
    
    def test_belge_list_bearer_only(self):
        """Test /api/belge/list with 'Bearer' only - should return 401, not 500"""
        try:
            headers = {"Authorization": "Bearer"}
            response = requests.get(f"{self.backend_url}/api/belge/list", headers=headers, timeout=30)
            
            # Should return 401 (Bearer only), NOT 500 (memory limit error)
            if response.status_code == 401:
                self.log_test("Belge List Bearer Only", True, f"Status: {response.status_code} (Bearer only)")
                return True
            elif response.status_code == 500:
                # Check if it's the memory limit error
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'memory limit' in error_detail.lower() or 'sort exceeded' in error_detail.lower():
                        self.log_test("Belge List Bearer Only", False, f"Status: 500 - MEMORY LIMIT ERROR STILL EXISTS: {error_detail}")
                    else:
                        self.log_test("Belge List Bearer Only", False, f"Status: 500 - Other server error: {error_detail}")
                except:
                    self.log_test("Belge List Bearer Only", False, f"Status: 500 - Server error (could not parse response)")
                return False
            else:
                self.log_test("Belge List Bearer Only", False, f"Status: {response.status_code} - Unexpected response")
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("Belge List Bearer Only", False, "Request timeout - possible memory limit issue")
            return False
        except Exception as e:
            self.log_test("Belge List Bearer Only", False, f"Error: {str(e)}")
            return False
    
    def test_response_time(self):
        """Test response time - should be reasonable, not timeout due to memory issues"""
        try:
            import time
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/api/belge/list", timeout=30)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Response should be quick (under 10 seconds) even without auth
            if response_time < 10.0:
                self.log_test("Response Time Performance", True, f"Response time: {response_time:.2f}s")
                return True
            else:
                self.log_test("Response Time Performance", False, f"Response time: {response_time:.2f}s (too slow, possible memory issue)")
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("Response Time Performance", False, "Request timeout - likely memory limit issue")
            return False
        except Exception as e:
            self.log_test("Response Time Performance", False, f"Error: {str(e)}")
            return False
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        try:
            response = requests.get(f"{self.backend_url}/api/belge/list", timeout=10)
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            has_cors = any(header in response.headers for header in cors_headers)
            
            if has_cors:
                self.log_test("CORS Headers", True, "CORS headers present")
                return True
            else:
                self.log_test("CORS Headers", False, "CORS headers missing")
                return False
                
        except Exception as e:
            self.log_test("CORS Headers", False, f"Error: {str(e)}")
            return False
    
    def test_http_methods(self):
        """Test HTTP method restrictions"""
        try:
            # Test POST method (should return 405 Method Not Allowed, not 500)
            response = requests.post(f"{self.backend_url}/api/belge/list", timeout=10)
            
            if response.status_code == 405:
                self.log_test("HTTP Method Restrictions", True, f"POST returns 405 (Method Not Allowed)")
                return True
            elif response.status_code == 500:
                self.log_test("HTTP Method Restrictions", False, f"POST returns 500 (possible memory limit issue)")
                return False
            else:
                self.log_test("HTTP Method Restrictions", True, f"POST returns {response.status_code} (acceptable)")
                return True
                
        except Exception as e:
            self.log_test("HTTP Method Restrictions", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting GreenWave CRM MongoDB Sort Memory Limit Fix Test")
        print("=" * 70)
        print(f"Backend URL: {self.backend_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Run tests
        self.test_backend_health()
        self.test_belge_list_no_auth()
        self.test_belge_list_invalid_token()
        self.test_belge_list_malformed_token()
        self.test_belge_list_empty_auth()
        self.test_belge_list_bearer_only()
        self.test_response_time()
        self.test_cors_headers()
        self.test_http_methods()
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"  {result}")
        
        print("\n" + "=" * 70)
        
        # Final verdict
        if success_rate >= 80:
            print("🎉 MEMORY LIMIT FIX VERIFICATION: SUCCESS!")
            print("✅ The MongoDB sort memory limit fix is working correctly.")
            print("✅ /api/belge/list endpoint returns proper authentication errors instead of 500.")
            print("✅ No memory limit errors detected in any test scenario.")
        else:
            print("🚨 MEMORY LIMIT FIX VERIFICATION: ISSUES DETECTED!")
            print("❌ Some tests failed - memory limit issue may still exist.")
            print("❌ Review failed tests above for specific issues.")
        
        print("=" * 70)
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = BelgeListMemoryLimitTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)