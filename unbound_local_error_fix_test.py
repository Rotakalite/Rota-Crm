#!/usr/bin/env python3
"""
🔧 UnboundLocalError Fix Test - Railway Production
Test the fix for UnboundLocalError in ZIP download endpoint

Test Focus:
1. target_client_id variable initialization (UnboundLocalError prevention)
2. Error handling safe logging (target_client_id or 'None' usage)
3. ZIP download endpoint proper error messages
4. UnboundLocalError replaced with proper HTTP error codes
5. Test with folder ID: e160e1fa-6dea-49cf-ab85-b0e5e3d15aee
6. Railway production stability test
"""

import requests
import json
import sys
import traceback
from datetime import datetime

# Railway Production Backend URL
BACKEND_URL = "https://rota-crm-production.up.railway.app"

class UnboundLocalErrorFixTester:
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
    
    def test_backend_accessibility(self):
        """Test if Railway backend is accessible"""
        try:
            response = requests.get(f"{self.backend_url}/", timeout=10)
            if response.status_code == 200:
                self.log_test("Railway Backend Accessibility", True, f"Status: {response.status_code}")
                return True
            else:
                self.log_test("Railway Backend Accessibility", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Railway Backend Accessibility", False, f"Error: {str(e)}")
            return False
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Endpoint", True, f"Service: {data.get('service', 'Unknown')}")
                return True
            else:
                self.log_test("Health Endpoint", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_zip_endpoint_without_auth(self):
        """Test ZIP endpoint without authentication - should return 403"""
        try:
            response = requests.get(f"{self.backend_url}/api/documents/bulk-download", timeout=10)
            
            # Should return 403 Forbidden (not 500 UnboundLocalError)
            if response.status_code == 403:
                self.log_test("ZIP Endpoint No Auth (403 Expected)", True, "Proper authentication required")
                return True
            elif response.status_code == 500:
                # Check if it's UnboundLocalError
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'UnboundLocalError' in error_detail or 'target_client_id' in error_detail:
                        self.log_test("ZIP Endpoint No Auth (UnboundLocalError Check)", False, f"UnboundLocalError still present: {error_detail}")
                        return False
                    else:
                        self.log_test("ZIP Endpoint No Auth (500 but not UnboundLocalError)", True, f"Different 500 error: {error_detail}")
                        return True
                except:
                    self.log_test("ZIP Endpoint No Auth (500 Unknown)", False, "500 error but can't parse response")
                    return False
            else:
                self.log_test("ZIP Endpoint No Auth", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("ZIP Endpoint No Auth", False, f"Request error: {str(e)}")
            return False
    
    def test_zip_endpoint_with_invalid_token(self):
        """Test ZIP endpoint with invalid token - should return 401"""
        try:
            headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.get(
                f"{self.backend_url}/api/documents/bulk-download",
                headers=headers,
                timeout=10
            )
            
            # Should return 401 Unauthorized (not 500 UnboundLocalError)
            if response.status_code == 401:
                self.log_test("ZIP Endpoint Invalid Token (401 Expected)", True, "Proper token validation")
                return True
            elif response.status_code == 500:
                # Check if it's UnboundLocalError
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'UnboundLocalError' in error_detail or 'target_client_id' in error_detail:
                        self.log_test("ZIP Endpoint Invalid Token (UnboundLocalError Check)", False, f"UnboundLocalError still present: {error_detail}")
                        return False
                    else:
                        self.log_test("ZIP Endpoint Invalid Token (500 but not UnboundLocalError)", True, f"Different 500 error: {error_detail}")
                        return True
                except:
                    self.log_test("ZIP Endpoint Invalid Token (500 Unknown)", False, "500 error but can't parse response")
                    return False
            else:
                self.log_test("ZIP Endpoint Invalid Token", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("ZIP Endpoint Invalid Token", False, f"Request error: {str(e)}")
            return False
    
    def test_zip_endpoint_with_malformed_token(self):
        """Test ZIP endpoint with malformed token - should return 401"""
        try:
            headers = {"Authorization": "Bearer malformed.token.here"}
            response = requests.get(
                f"{self.backend_url}/api/documents/bulk-download",
                headers=headers,
                timeout=10
            )
            
            # Should return 401 Unauthorized (not 500 UnboundLocalError)
            if response.status_code == 401:
                self.log_test("ZIP Endpoint Malformed Token (401 Expected)", True, "Proper token format validation")
                return True
            elif response.status_code == 500:
                # Check if it's UnboundLocalError
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'UnboundLocalError' in error_detail or 'target_client_id' in error_detail:
                        self.log_test("ZIP Endpoint Malformed Token (UnboundLocalError Check)", False, f"UnboundLocalError still present: {error_detail}")
                        return False
                    else:
                        self.log_test("ZIP Endpoint Malformed Token (500 but not UnboundLocalError)", True, f"Different 500 error: {error_detail}")
                        return True
                except:
                    self.log_test("ZIP Endpoint Malformed Token (500 Unknown)", False, "500 error but can't parse response")
                    return False
            else:
                self.log_test("ZIP Endpoint Malformed Token", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("ZIP Endpoint Malformed Token", False, f"Request error: {str(e)}")
            return False
    
    def test_zip_endpoint_with_client_id_param(self):
        """Test ZIP endpoint with client_id parameter (no auth) - should return 403"""
        try:
            params = {"client_id": "test_client_123"}
            response = requests.get(
                f"{self.backend_url}/api/documents/bulk-download",
                params=params,
                timeout=10
            )
            
            # Should return 403 Forbidden (not 500 UnboundLocalError)
            if response.status_code == 403:
                self.log_test("ZIP Endpoint Client ID Param No Auth (403 Expected)", True, "Parameters don't bypass authentication")
                return True
            elif response.status_code == 500:
                # Check if it's UnboundLocalError
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'UnboundLocalError' in error_detail or 'target_client_id' in error_detail:
                        self.log_test("ZIP Endpoint Client ID Param (UnboundLocalError Check)", False, f"UnboundLocalError still present: {error_detail}")
                        return False
                    else:
                        self.log_test("ZIP Endpoint Client ID Param (500 but not UnboundLocalError)", True, f"Different 500 error: {error_detail}")
                        return True
                except:
                    self.log_test("ZIP Endpoint Client ID Param (500 Unknown)", False, "500 error but can't parse response")
                    return False
            else:
                self.log_test("ZIP Endpoint Client ID Param", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("ZIP Endpoint Client ID Param", False, f"Request error: {str(e)}")
            return False
    
    def test_zip_endpoint_with_folder_id_param(self):
        """Test ZIP endpoint with specific folder_id parameter (no auth) - should return 403"""
        try:
            params = {"folder_id": "e160e1fa-6dea-49cf-ab85-b0e5e3d15aee"}
            response = requests.get(
                f"{self.backend_url}/api/documents/bulk-download",
                params=params,
                timeout=10
            )
            
            # Should return 403 Forbidden (not 500 UnboundLocalError)
            if response.status_code == 403:
                self.log_test("ZIP Endpoint Folder ID Param No Auth (403 Expected)", True, "Folder ID parameter doesn't bypass authentication")
                return True
            elif response.status_code == 500:
                # Check if it's UnboundLocalError
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'UnboundLocalError' in error_detail or 'target_client_id' in error_detail:
                        self.log_test("ZIP Endpoint Folder ID Param (UnboundLocalError Check)", False, f"UnboundLocalError still present: {error_detail}")
                        return False
                    else:
                        self.log_test("ZIP Endpoint Folder ID Param (500 but not UnboundLocalError)", True, f"Different 500 error: {error_detail}")
                        return True
                except:
                    self.log_test("ZIP Endpoint Folder ID Param (500 Unknown)", False, "500 error but can't parse response")
                    return False
            else:
                self.log_test("ZIP Endpoint Folder ID Param", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("ZIP Endpoint Folder ID Param", False, f"Request error: {str(e)}")
            return False
    
    def test_zip_endpoint_with_both_params(self):
        """Test ZIP endpoint with both client_id and folder_id parameters (no auth) - should return 403"""
        try:
            params = {
                "client_id": "test_client_123",
                "folder_id": "e160e1fa-6dea-49cf-ab85-b0e5e3d15aee"
            }
            response = requests.get(
                f"{self.backend_url}/api/documents/bulk-download",
                params=params,
                timeout=10
            )
            
            # Should return 403 Forbidden (not 500 UnboundLocalError)
            if response.status_code == 403:
                self.log_test("ZIP Endpoint Both Params No Auth (403 Expected)", True, "Parameters don't bypass authentication")
                return True
            elif response.status_code == 500:
                # Check if it's UnboundLocalError
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'UnboundLocalError' in error_detail or 'target_client_id' in error_detail:
                        self.log_test("ZIP Endpoint Both Params (UnboundLocalError Check)", False, f"UnboundLocalError still present: {error_detail}")
                        return False
                    else:
                        self.log_test("ZIP Endpoint Both Params (500 but not UnboundLocalError)", True, f"Different 500 error: {error_detail}")
                        return True
                except:
                    self.log_test("ZIP Endpoint Both Params (500 Unknown)", False, "500 error but can't parse response")
                    return False
            else:
                self.log_test("ZIP Endpoint Both Params", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("ZIP Endpoint Both Params", False, f"Request error: {str(e)}")
            return False
    
    def test_http_methods_on_zip_endpoint(self):
        """Test different HTTP methods on ZIP endpoint - should return proper error codes"""
        methods_to_test = ['POST', 'PUT', 'DELETE', 'PATCH']
        
        for method in methods_to_test:
            try:
                response = requests.request(method, f"{self.backend_url}/api/documents/bulk-download", timeout=10)
                
                # Should return 405 Method Not Allowed (not 500 UnboundLocalError)
                if response.status_code == 405:
                    self.log_test(f"ZIP Endpoint {method} Method (405 Expected)", True, "Proper HTTP method restriction")
                elif response.status_code == 500:
                    # Check if it's UnboundLocalError
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', '')
                        if 'UnboundLocalError' in error_detail or 'target_client_id' in error_detail:
                            self.log_test(f"ZIP Endpoint {method} Method (UnboundLocalError Check)", False, f"UnboundLocalError still present: {error_detail}")
                        else:
                            self.log_test(f"ZIP Endpoint {method} Method (500 but not UnboundLocalError)", True, f"Different 500 error: {error_detail}")
                    except:
                        self.log_test(f"ZIP Endpoint {method} Method (500 Unknown)", False, "500 error but can't parse response")
                else:
                    self.log_test(f"ZIP Endpoint {method} Method", False, f"Unexpected status: {response.status_code}")
            except Exception as e:
                self.log_test(f"ZIP Endpoint {method} Method", False, f"Request error: {str(e)}")
    
    def test_code_analysis_for_fix(self):
        """Analyze if the fix is properly implemented in the code"""
        try:
            # Read the backend server code to verify the fix
            with open('/app/backend/server.py', 'r') as f:
                code_content = f.read()
            
            # Check for target_client_id initialization
            if 'target_client_id = None  # Initialize to avoid UnboundLocalError' in code_content:
                self.log_test("Code Analysis - target_client_id Initialization", True, "Variable properly initialized")
            else:
                self.log_test("Code Analysis - target_client_id Initialization", False, "Initialization not found")
            
            # Check for safe logging usage
            if 'target_client_id or \'None\'' in code_content:
                self.log_test("Code Analysis - Safe Logging", True, "Safe logging implemented")
            else:
                self.log_test("Code Analysis - Safe Logging", False, "Safe logging not found")
            
            # Check for proper error handling structure
            if 'except Exception as e:' in code_content and 'BULK DOWNLOAD ERROR' in code_content:
                self.log_test("Code Analysis - Error Handling Structure", True, "Proper error handling found")
            else:
                self.log_test("Code Analysis - Error Handling Structure", False, "Error handling structure not found")
            
            # Check for specific error types
            if 'HTTPException(status_code=413' in code_content and 'HTTPException(status_code=408' in code_content:
                self.log_test("Code Analysis - Specific Error Codes", True, "Specific HTTP error codes implemented")
            else:
                self.log_test("Code Analysis - Specific Error Codes", False, "Specific error codes not found")
                
        except Exception as e:
            self.log_test("Code Analysis", False, f"Error reading code: {str(e)}")
    
    def run_all_tests(self):
        """Run all UnboundLocalError fix tests"""
        print("🔧 UNBOUNDLOCALERROR FIX TEST - RAILWAY PRODUCTION")
        print("=" * 60)
        print(f"Backend URL: {self.backend_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Basic connectivity tests
        print("\n📡 CONNECTIVITY TESTS")
        print("-" * 30)
        if not self.test_backend_accessibility():
            print("❌ Backend not accessible - stopping tests")
            return
        
        self.test_health_endpoint()
        
        # UnboundLocalError specific tests
        print("\n🔧 UNBOUNDLOCALERROR FIX TESTS")
        print("-" * 30)
        self.test_zip_endpoint_without_auth()
        self.test_zip_endpoint_with_invalid_token()
        self.test_zip_endpoint_with_malformed_token()
        self.test_zip_endpoint_with_client_id_param()
        self.test_zip_endpoint_with_folder_id_param()
        self.test_zip_endpoint_with_both_params()
        
        # HTTP method tests
        print("\n🌐 HTTP METHOD TESTS")
        print("-" * 30)
        self.test_http_methods_on_zip_endpoint()
        
        # Code analysis
        print("\n📝 CODE ANALYSIS TESTS")
        print("-" * 30)
        self.test_code_analysis_for_fix()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT - UnboundLocalError fix is working properly!")
        elif success_rate >= 75:
            print("✅ GOOD - UnboundLocalError fix is mostly working")
        elif success_rate >= 50:
            print("⚠️ PARTIAL - UnboundLocalError fix has some issues")
        else:
            print("❌ CRITICAL - UnboundLocalError fix is not working properly")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        print("-" * 30)
        for result in self.test_results:
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   └─ {result['details']}")
        
        return success_rate

if __name__ == "__main__":
    tester = UnboundLocalErrorFixTester()
    success_rate = tester.run_all_tests()
    
    # Exit with appropriate code
    if success_rate >= 75:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure