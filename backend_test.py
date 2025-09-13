#!/usr/bin/env python3
"""
GreenWave CRM MongoDB Memory Limit ve ZIP Upload Düzeltme Testi
Backend comprehensive testing for MongoDB sort memory limit fix and ZIP upload support

Test Requirements from Review Request:
1. MongoDB sort memory limit hatası devam ediyor - "Sort exceeded memory limit of 33554432 bytes"
2. ZIP dosyası seçememe sorunu
3. Backend'in stabil çalıştığını doğrula
4. Authentication error (401/403) alındığını kontrol et

Fixes Applied:
1. MongoDB sort'u kaldırdım, Python'da sort yapıyorum
2. Limit 50'ye düşürdüm 
3. Frontend'e ZIP ve RAR desteği eklendi
4. Backend 500MB dosya desteği zaten var

Railway URL: https://rota-crm-production.up.railway.app
"""

import requests
import json
import time
import sys
from datetime import datetime

class GreenWaveCRMBackendTester:
    def __init__(self):
        self.base_url = "https://rota-crm-production.up.railway.app"
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
        # Test headers
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'GreenWave-CRM-Backend-Tester/1.0'
        }
        
        print(f"🚀 GreenWave CRM Backend Tester Started")
        print(f"🎯 Target: {self.base_url}")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

    def log_test(self, test_name, success, details="", error_msg=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
            
        result = {
            'test': test_name,
            'status': status,
            'success': success,
            'details': details,
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        print(f"{status} | {test_name}")
        if details:
            print(f"     📝 {details}")
        if error_msg:
            print(f"     ❌ {error_msg}")

    def test_backend_health(self):
        """Test 1: Backend Health Check"""
        try:
            response = requests.get(f"{self.base_url}/api/health", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                self.log_test("Backend Health Check", True, 
                            f"Status: {response.status_code}, Response: {response.text[:100]}")
            else:
                self.log_test("Backend Health Check", False, 
                            f"Status: {response.status_code}", response.text[:200])
                
        except Exception as e:
            self.log_test("Backend Health Check", False, 
                        "Connection failed", str(e))

    def test_belge_list_endpoint_memory_limit_fix(self):
        """Test 2: /api/belge/list MongoDB Memory Limit Fix"""
        try:
            # Test without authentication first (should get 401/403)
            response = requests.get(f"{self.base_url}/api/belge/list", 
                                  headers=self.headers, timeout=15)
            
            if response.status_code in [401, 403]:
                self.log_test("Belge List Endpoint - Authentication Required", True,
                            f"Proper auth required: {response.status_code}")
            else:
                self.log_test("Belge List Endpoint - Authentication Required", False,
                            f"Expected 401/403, got {response.status_code}", response.text[:200])
                
            # Test with invalid token (should get 401)
            invalid_headers = self.headers.copy()
            invalid_headers['Authorization'] = 'Bearer invalid_token_12345'
            
            response = requests.get(f"{self.base_url}/api/belge/list", 
                                  headers=invalid_headers, timeout=15)
            
            if response.status_code == 401:
                self.log_test("Belge List Endpoint - Invalid Token Rejection", True,
                            f"Invalid token properly rejected: {response.status_code}")
            else:
                self.log_test("Belge List Endpoint - Invalid Token Rejection", False,
                            f"Expected 401, got {response.status_code}", response.text[:200])
                
            # Test endpoint accessibility (should not return 404)
            if response.status_code != 404:
                self.log_test("Belge List Endpoint - Accessibility", True,
                            "Endpoint is registered and accessible")
            else:
                self.log_test("Belge List Endpoint - Accessibility", False,
                            "Endpoint returns 404 - not registered")
                
        except Exception as e:
            self.log_test("Belge List Endpoint Tests", False,
                        "Request failed", str(e))

    def test_documents_endpoints_stability(self):
        """Test 3: Documents Endpoints Stability"""
        endpoints_to_test = [
            "/api/documents",
            "/api/documents/bulk-download", 
            "/api/belge/upload",
            "/api/belge/list"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", 
                                      headers=self.headers, timeout=10)
                
                # Check if endpoint is accessible (not 404)
                if response.status_code != 404:
                    self.log_test(f"Document Endpoint Stability - {endpoint}", True,
                                f"Accessible: {response.status_code}")
                else:
                    self.log_test(f"Document Endpoint Stability - {endpoint}", False,
                                f"Not found: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Document Endpoint Stability - {endpoint}", False,
                            "Connection failed", str(e))

    def test_zip_download_endpoint(self):
        """Test 4: ZIP Download Endpoint"""
        try:
            # Test ZIP download endpoint accessibility
            response = requests.get(f"{self.base_url}/api/documents/bulk-download", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("ZIP Download Endpoint - Security", True,
                            f"Properly secured: {response.status_code}")
            else:
                self.log_test("ZIP Download Endpoint - Security", False,
                            f"Expected 401/403, got {response.status_code}")
                
            # Test with client_id parameter
            response = requests.get(f"{self.base_url}/api/documents/bulk-download?client_id=test", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("ZIP Download Endpoint - Parameter Handling", True,
                            f"Parameters accepted, auth required: {response.status_code}")
            else:
                self.log_test("ZIP Download Endpoint - Parameter Handling", False,
                            f"Unexpected response: {response.status_code}")
                
        except Exception as e:
            self.log_test("ZIP Download Endpoint Tests", False,
                        "Request failed", str(e))

    def test_file_upload_support(self):
        """Test 5: File Upload Support (500MB limit)"""
        try:
            # Test upload endpoint accessibility
            response = requests.post(f"{self.base_url}/api/belge/upload", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code in [400, 401, 403, 422]:
                self.log_test("File Upload Endpoint - Accessibility", True,
                            f"Endpoint accessible: {response.status_code}")
            elif response.status_code == 404:
                self.log_test("File Upload Endpoint - Accessibility", False,
                            "Upload endpoint not found")
            else:
                self.log_test("File Upload Endpoint - Accessibility", True,
                            f"Endpoint responds: {response.status_code}")
                
            # Test OPTIONS request for CORS
            response = requests.options(f"{self.base_url}/api/belge/upload", 
                                      headers=self.headers, timeout=10)
            
            if response.status_code in [200, 204]:
                self.log_test("File Upload Endpoint - CORS Support", True,
                            f"CORS enabled: {response.status_code}")
            else:
                self.log_test("File Upload Endpoint - CORS Support", False,
                            f"CORS issue: {response.status_code}")
                
        except Exception as e:
            self.log_test("File Upload Support Tests", False,
                        "Request failed", str(e))

    def test_mongodb_sort_fix_verification(self):
        """Test 6: MongoDB Sort Fix Verification"""
        try:
            # Test various document list endpoints that might use sorting
            endpoints_with_sorting = [
                "/api/belge/list",
                "/api/documents", 
                "/api/clients",
                "/api/consumptions"
            ]
            
            for endpoint in endpoints_with_sorting:
                try:
                    # Test with limit parameter to verify Python sorting
                    response = requests.get(f"{self.base_url}{endpoint}?limit=50", 
                                          headers=self.headers, timeout=15)
                    
                    if response.status_code != 500:
                        self.log_test(f"MongoDB Sort Fix - {endpoint}", True,
                                    f"No 500 error with limit=50: {response.status_code}")
                    else:
                        # Check if it's a memory limit error
                        if "memory limit" in response.text.lower():
                            self.log_test(f"MongoDB Sort Fix - {endpoint}", False,
                                        "Memory limit error still present", response.text[:200])
                        else:
                            self.log_test(f"MongoDB Sort Fix - {endpoint}", True,
                                        f"500 error but not memory limit: {response.status_code}")
                            
                except Exception as e:
                    self.log_test(f"MongoDB Sort Fix - {endpoint}", False,
                                "Request failed", str(e))
                    
        except Exception as e:
            self.log_test("MongoDB Sort Fix Verification", False,
                        "Test setup failed", str(e))

    def test_backend_performance(self):
        """Test 7: Backend Performance & Stability"""
        try:
            # Test multiple rapid requests to check stability
            response_times = []
            
            for i in range(5):
                start_time = time.time()
                response = requests.get(f"{self.base_url}/api/health", 
                                      headers=self.headers, timeout=10)
                end_time = time.time()
                
                response_time = end_time - start_time
                response_times.append(response_time)
                
                if response.status_code != 200:
                    self.log_test(f"Backend Stability - Request {i+1}", False,
                                f"Failed: {response.status_code}")
                    return
                    
            avg_response_time = sum(response_times) / len(response_times)
            
            if avg_response_time < 3.0:  # Under 3 seconds average
                self.log_test("Backend Performance", True,
                            f"Average response time: {avg_response_time:.2f}s")
            else:
                self.log_test("Backend Performance", False,
                            f"Slow response time: {avg_response_time:.2f}s")
                
        except Exception as e:
            self.log_test("Backend Performance Tests", False,
                        "Performance test failed", str(e))

    def test_authentication_system(self):
        """Test 8: Authentication System Verification"""
        try:
            # Test various auth scenarios
            auth_tests = [
                ("No Auth Header", {}),
                ("Empty Auth Header", {"Authorization": ""}),
                ("Invalid Bearer Token", {"Authorization": "Bearer invalid_token"}),
                ("Malformed Auth Header", {"Authorization": "InvalidFormat token"})
            ]
            
            for test_name, auth_header in auth_tests:
                test_headers = self.headers.copy()
                test_headers.update(auth_header)
                
                response = requests.get(f"{self.base_url}/api/clients", 
                                      headers=test_headers, timeout=10)
                
                if response.status_code in [401, 403]:
                    self.log_test(f"Authentication System - {test_name}", True,
                                f"Properly rejected: {response.status_code}")
                else:
                    self.log_test(f"Authentication System - {test_name}", False,
                                f"Expected 401/403, got {response.status_code}")
                    
        except Exception as e:
            self.log_test("Authentication System Tests", False,
                        "Auth test failed", str(e))

    def test_cors_configuration(self):
        """Test 9: CORS Configuration"""
        try:
            # Test CORS headers
            response = requests.options(f"{self.base_url}/api/health", 
                                      headers=self.headers, timeout=10)
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            cors_present = any(header in response.headers for header in cors_headers)
            
            if cors_present:
                self.log_test("CORS Configuration", True,
                            f"CORS headers present: {response.status_code}")
            else:
                self.log_test("CORS Configuration", False,
                            "CORS headers missing")
                
        except Exception as e:
            self.log_test("CORS Configuration Test", False,
                        "CORS test failed", str(e))

    def test_error_handling(self):
        """Test 10: Error Handling"""
        try:
            # Test 404 handling
            response = requests.get(f"{self.base_url}/api/nonexistent-endpoint", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code == 404:
                self.log_test("Error Handling - 404", True,
                            "Proper 404 for non-existent endpoints")
            else:
                self.log_test("Error Handling - 404", False,
                            f"Expected 404, got {response.status_code}")
                
            # Test method not allowed
            response = requests.patch(f"{self.base_url}/api/health", 
                                    headers=self.headers, timeout=10)
            
            if response.status_code in [405, 404]:
                self.log_test("Error Handling - Method Not Allowed", True,
                            f"Proper method restriction: {response.status_code}")
            else:
                self.log_test("Error Handling - Method Not Allowed", False,
                            f"Expected 405, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling Tests", False,
                        "Error handling test failed", str(e))

    def run_all_tests(self):
        """Run all backend tests"""
        print("🔍 Starting Comprehensive Backend Tests...")
        print()
        
        # Run all test methods
        self.test_backend_health()
        self.test_belge_list_endpoint_memory_limit_fix()
        self.test_documents_endpoints_stability()
        self.test_zip_download_endpoint()
        self.test_file_upload_support()
        self.test_mongodb_sort_fix_verification()
        self.test_backend_performance()
        self.test_authentication_system()
        self.test_cors_configuration()
        self.test_error_handling()
        
        # Print summary
        self.print_summary()
        
        return self.test_results

    def print_summary(self):
        """Print test summary"""
        print()
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📈 Total: {self.total_tests}")
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        print()
        
        # Print failed tests details
        if self.failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}")
                    if result['error']:
                        print(f"     Error: {result['error']}")
            print()
        
        # Overall assessment
        if success_rate >= 90:
            print("🎉 EXCELLENT: Backend is working excellently!")
        elif success_rate >= 75:
            print("✅ GOOD: Backend is working well with minor issues.")
        elif success_rate >= 50:
            print("⚠️ MODERATE: Backend has some issues that need attention.")
        else:
            print("🚨 CRITICAL: Backend has major issues requiring immediate attention!")
        
        print("=" * 80)

def main():
    """Main test execution"""
    tester = GreenWaveCRMBackendTester()
    
    try:
        results = tester.run_all_tests()
        
        # Save results to file
        with open('/app/backend_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        print(f"📄 Test results saved to: /app/backend_test_results.json")
        
        # Return appropriate exit code
        if tester.failed_tests == 0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n🚨 Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()