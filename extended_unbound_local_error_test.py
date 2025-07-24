#!/usr/bin/env python3
"""
🔧 Extended UnboundLocalError Fix Test - Railway Production
Additional tests for specific scenarios and edge cases

Focus on:
- Specific folder ID: e160e1fa-6dea-49cf-ab85-b0e5e3d15aee
- Edge cases that might trigger UnboundLocalError
- Memory and timeout error handling
- Production stability under various conditions
"""

import requests
import json
import sys
import time
from datetime import datetime

# Railway Production Backend URL
BACKEND_URL = "https://rota-crm-production.up.railway.app"

class ExtendedUnboundLocalErrorTester:
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
        
        print(result)
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def test_specific_folder_id_scenarios(self):
        """Test specific folder ID scenarios that might trigger UnboundLocalError"""
        folder_id = "e160e1fa-6dea-49cf-ab85-b0e5e3d15aee"
        
        # Test 1: Folder ID only, no auth
        try:
            params = {"folder_id": folder_id}
            response = requests.get(
                f"{self.backend_url}/api/documents/bulk-download",
                params=params,
                timeout=15
            )
            
            if response.status_code == 403:
                self.log_test("Specific Folder ID No Auth", True, f"Proper 403 for folder {folder_id[:8]}...")
            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'UnboundLocalError' in error_detail or 'target_client_id' in error_detail:
                        self.log_test("Specific Folder ID No Auth", False, f"UnboundLocalError detected: {error_detail}")
                    else:
                        self.log_test("Specific Folder ID No Auth", True, f"Different 500 error (not UnboundLocalError): {error_detail}")
                except:
                    self.log_test("Specific Folder ID No Auth", False, "500 error but can't parse response")
            else:
                self.log_test("Specific Folder ID No Auth", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Specific Folder ID No Auth", False, f"Request error: {str(e)}")
        
        # Test 2: Folder ID with invalid token
        try:
            headers = {"Authorization": "Bearer invalid_token_for_folder_test"}
            params = {"folder_id": folder_id}
            response = requests.get(
                f"{self.backend_url}/api/documents/bulk-download",
                headers=headers,
                params=params,
                timeout=15
            )
            
            if response.status_code == 401:
                self.log_test("Specific Folder ID Invalid Token", True, f"Proper 401 for folder {folder_id[:8]}...")
            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'UnboundLocalError' in error_detail or 'target_client_id' in error_detail:
                        self.log_test("Specific Folder ID Invalid Token", False, f"UnboundLocalError detected: {error_detail}")
                    else:
                        self.log_test("Specific Folder ID Invalid Token", True, f"Different 500 error (not UnboundLocalError): {error_detail}")
                except:
                    self.log_test("Specific Folder ID Invalid Token", False, "500 error but can't parse response")
            else:
                self.log_test("Specific Folder ID Invalid Token", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Specific Folder ID Invalid Token", False, f"Request error: {str(e)}")
        
        # Test 3: Folder ID with client ID, no auth
        try:
            params = {
                "folder_id": folder_id,
                "client_id": "test_client_with_folder"
            }
            response = requests.get(
                f"{self.backend_url}/api/documents/bulk-download",
                params=params,
                timeout=15
            )
            
            if response.status_code == 403:
                self.log_test("Specific Folder+Client ID No Auth", True, f"Proper 403 for combined params")
            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'UnboundLocalError' in error_detail or 'target_client_id' in error_detail:
                        self.log_test("Specific Folder+Client ID No Auth", False, f"UnboundLocalError detected: {error_detail}")
                    else:
                        self.log_test("Specific Folder+Client ID No Auth", True, f"Different 500 error (not UnboundLocalError): {error_detail}")
                except:
                    self.log_test("Specific Folder+Client ID No Auth", False, "500 error but can't parse response")
            else:
                self.log_test("Specific Folder+Client ID No Auth", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Specific Folder+Client ID No Auth", False, f"Request error: {str(e)}")
    
    def test_edge_case_parameters(self):
        """Test edge case parameters that might trigger UnboundLocalError"""
        
        edge_cases = [
            {"client_id": "", "folder_id": ""},  # Empty strings
            {"client_id": None, "folder_id": None},  # None values (will be converted to strings)
            {"client_id": "null", "folder_id": "null"},  # String "null"
            {"client_id": "undefined", "folder_id": "undefined"},  # String "undefined"
            {"client_id": " ", "folder_id": " "},  # Whitespace
            {"client_id": "0", "folder_id": "0"},  # Zero strings
            {"client_id": "false", "folder_id": "false"},  # String "false"
        ]
        
        for i, params in enumerate(edge_cases):
            try:
                response = requests.get(
                    f"{self.backend_url}/api/documents/bulk-download",
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 403:
                    self.log_test(f"Edge Case {i+1} (403 Expected)", True, f"Proper 403 for params: {params}")
                elif response.status_code == 500:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', '')
                        if 'UnboundLocalError' in error_detail or 'target_client_id' in error_detail:
                            self.log_test(f"Edge Case {i+1} (UnboundLocalError Check)", False, f"UnboundLocalError detected: {error_detail}")
                        else:
                            self.log_test(f"Edge Case {i+1} (500 but not UnboundLocalError)", True, f"Different 500 error: {error_detail}")
                    except:
                        self.log_test(f"Edge Case {i+1} (500 Unknown)", False, "500 error but can't parse response")
                else:
                    self.log_test(f"Edge Case {i+1}", False, f"Unexpected status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Edge Case {i+1}", False, f"Request error: {str(e)}")
    
    def test_concurrent_requests(self):
        """Test concurrent requests to check for race conditions that might cause UnboundLocalError"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def make_request(request_id):
            try:
                response = requests.get(
                    f"{self.backend_url}/api/documents/bulk-download",
                    timeout=10
                )
                results_queue.put({
                    "id": request_id,
                    "status": response.status_code,
                    "error": None
                })
            except Exception as e:
                results_queue.put({
                    "id": request_id,
                    "status": None,
                    "error": str(e)
                })
        
        # Start 5 concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Analyze results
        all_403 = all(r["status"] == 403 for r in results if r["status"] is not None)
        any_500 = any(r["status"] == 500 for r in results if r["status"] is not None)
        
        if all_403 and not any_500:
            self.log_test("Concurrent Requests", True, f"All {len(results)} requests returned 403 (no 500 errors)")
        elif any_500:
            self.log_test("Concurrent Requests", False, f"Some requests returned 500 errors - potential race condition")
        else:
            self.log_test("Concurrent Requests", False, f"Unexpected status codes in concurrent requests")
    
    def test_malformed_requests(self):
        """Test malformed requests that might trigger UnboundLocalError"""
        
        # Test with invalid JSON in request body (even though it's GET)
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.get(
                f"{self.backend_url}/api/documents/bulk-download",
                headers=headers,
                data="invalid json {",
                timeout=10
            )
            
            if response.status_code == 403:
                self.log_test("Malformed JSON Request", True, "Proper 403 despite malformed JSON")
            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'UnboundLocalError' in error_detail or 'target_client_id' in error_detail:
                        self.log_test("Malformed JSON Request", False, f"UnboundLocalError detected: {error_detail}")
                    else:
                        self.log_test("Malformed JSON Request", True, f"Different 500 error: {error_detail}")
                except:
                    self.log_test("Malformed JSON Request", False, "500 error but can't parse response")
            else:
                self.log_test("Malformed JSON Request", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Malformed JSON Request", False, f"Request error: {str(e)}")
        
        # Test with very long parameter values
        try:
            long_value = "a" * 10000  # 10KB string
            params = {"client_id": long_value, "folder_id": long_value}
            response = requests.get(
                f"{self.backend_url}/api/documents/bulk-download",
                params=params,
                timeout=15
            )
            
            if response.status_code == 403:
                self.log_test("Long Parameter Values", True, "Proper 403 despite long parameters")
            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'UnboundLocalError' in error_detail or 'target_client_id' in error_detail:
                        self.log_test("Long Parameter Values", False, f"UnboundLocalError detected: {error_detail}")
                    else:
                        self.log_test("Long Parameter Values", True, f"Different 500 error: {error_detail}")
                except:
                    self.log_test("Long Parameter Values", False, "500 error but can't parse response")
            else:
                self.log_test("Long Parameter Values", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Long Parameter Values", False, f"Request error: {str(e)}")
    
    def test_production_stability(self):
        """Test production stability under various conditions"""
        
        # Test 1: Multiple rapid requests
        rapid_request_success = True
        for i in range(10):
            try:
                response = requests.get(
                    f"{self.backend_url}/api/documents/bulk-download",
                    timeout=5
                )
                if response.status_code not in [403, 401]:  # Expected auth errors
                    rapid_request_success = False
                    break
                time.sleep(0.1)  # Small delay between requests
            except Exception:
                rapid_request_success = False
                break
        
        self.log_test("Production Stability - Rapid Requests", rapid_request_success, "10 rapid requests handled properly")
        
        # Test 2: Request with timeout simulation
        try:
            response = requests.get(
                f"{self.backend_url}/api/documents/bulk-download",
                timeout=1  # Very short timeout
            )
            # If we get here, the server responded quickly
            if response.status_code == 403:
                self.log_test("Production Stability - Quick Response", True, "Server responds quickly under timeout pressure")
            else:
                self.log_test("Production Stability - Quick Response", False, f"Unexpected status: {response.status_code}")
        except requests.exceptions.Timeout:
            self.log_test("Production Stability - Quick Response", False, "Server too slow (timeout)")
        except Exception as e:
            self.log_test("Production Stability - Quick Response", False, f"Request error: {str(e)}")
    
    def run_extended_tests(self):
        """Run all extended UnboundLocalError fix tests"""
        print("🔧 EXTENDED UNBOUNDLOCALERROR FIX TEST - RAILWAY PRODUCTION")
        print("=" * 70)
        print(f"Backend URL: {self.backend_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Specific folder ID tests
        print("\n📁 SPECIFIC FOLDER ID TESTS")
        print("-" * 40)
        self.test_specific_folder_id_scenarios()
        
        # Edge case parameter tests
        print("\n🎯 EDGE CASE PARAMETER TESTS")
        print("-" * 40)
        self.test_edge_case_parameters()
        
        # Concurrent request tests
        print("\n🔄 CONCURRENT REQUEST TESTS")
        print("-" * 40)
        self.test_concurrent_requests()
        
        # Malformed request tests
        print("\n🚫 MALFORMED REQUEST TESTS")
        print("-" * 40)
        self.test_malformed_requests()
        
        # Production stability tests
        print("\n🏭 PRODUCTION STABILITY TESTS")
        print("-" * 40)
        self.test_production_stability()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 EXTENDED TEST SUMMARY")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"Total Extended Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT - UnboundLocalError fix handles all edge cases!")
        elif success_rate >= 75:
            print("✅ GOOD - UnboundLocalError fix is robust")
        elif success_rate >= 50:
            print("⚠️ PARTIAL - Some edge cases may still cause issues")
        else:
            print("❌ CRITICAL - UnboundLocalError fix needs more work")
        
        # Detailed results
        print("\n📋 DETAILED EXTENDED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   └─ {result['details']}")
        
        return success_rate

if __name__ == "__main__":
    tester = ExtendedUnboundLocalErrorTester()
    success_rate = tester.run_extended_tests()
    
    # Exit with appropriate code
    if success_rate >= 75:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure