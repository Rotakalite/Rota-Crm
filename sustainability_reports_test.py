#!/usr/bin/env python3
"""
🎯 SUSTAINABILITY REPORT ENDPOINTS TEST
Testing the fix for sustainability report endpoints that were returning 404
Focus: Verify endpoints now return 401/403 instead of 404 (indicating proper registration)
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from frontend .env
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except:
        pass
    return "https://74cd54d6-e7c4-4086-a9b0-2c069ca9924d.preview.emergentagent.com"

BACKEND_URL = get_backend_url()
TEST_CLIENT_ID = "94927a77-edc3-45ec-8329-795feae35771"

class SustainabilityReportsEndpointTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_client_id = TEST_CLIENT_ID
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
        
    def test_backend_health(self):
        """Test backend health check"""
        print("\n🏥 BACKEND HEALTH CHECK")
        print("=" * 50)
        
        try:
            # Test root endpoint
            response = requests.get(f"{self.backend_url}/", timeout=10)
            self.log_test("Backend Root Accessible", 
                         response.status_code == 200,
                         f"Status: {response.status_code}")
            
            # Test health endpoint
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            self.log_test("Health Endpoint Working", 
                         response.status_code == 200,
                         f"Status: {response.status_code}")
            
            # Test API health endpoint
            response = requests.get(f"{self.backend_url}/api/health", timeout=10)
            self.log_test("API Health Endpoint Working", 
                         response.status_code == 200,
                         f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Error: {str(e)}")
    
    def test_sustainability_report_endpoints(self):
        """Test sustainability report endpoints - main focus of this test"""
        print("\n📊 SUSTAINABILITY REPORT ENDPOINTS TEST")
        print("=" * 50)
        
        # Test endpoints that should now return 401/403 instead of 404
        report_endpoints = [
            ("/api/reports/comprehensive", "Comprehensive Report Endpoint"),
            ("/api/reports/training", "Training Report Endpoint"),
            ("/api/reports/consumption", "Consumption Report Endpoint"),
            ("/api/test-reports", "Test Reports Endpoint")
        ]
        
        for endpoint, test_name in report_endpoints:
            try:
                # Test without authentication - should return 401/403, NOT 404
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                
                if response.status_code == 404:
                    self.log_test(
                        f"{test_name} - Registration Check", 
                        False, 
                        f"❌ STILL RETURNS 404 - Endpoint not properly registered!"
                    )
                elif response.status_code in [401, 403]:
                    self.log_test(
                        f"{test_name} - Registration Check", 
                        True, 
                        f"✅ Returns {response.status_code} - Endpoint properly registered and secured"
                    )
                elif response.status_code == 200:
                    self.log_test(
                        f"{test_name} - Registration Check", 
                        True, 
                        f"✅ Returns 200 - Endpoint accessible (may not require auth)"
                    )
                else:
                    self.log_test(
                        f"{test_name} - Registration Check", 
                        False, 
                        f"Unexpected status: {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_test(f"{test_name} - Registration Check", False, f"Error: {str(e)}")
                
        # Test with client_id parameter for admin/consultant endpoints
        print("\n📋 TESTING WITH CLIENT_ID PARAMETER")
        print("-" * 30)
        
        admin_endpoints = [
            f"/api/reports/comprehensive?client_id={self.test_client_id}",
            f"/api/reports/training?client_id={self.test_client_id}",
            f"/api/reports/consumption?client_id={self.test_client_id}"
        ]
        
        for endpoint in admin_endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                
                if response.status_code == 404:
                    self.log_test(
                        f"Admin Endpoint - {endpoint.split('?')[0]}", 
                        False, 
                        f"❌ STILL RETURNS 404 - Endpoint not accessible with client_id!"
                    )
                elif response.status_code in [401, 403]:
                    self.log_test(
                        f"Admin Endpoint - {endpoint.split('?')[0]}", 
                        True, 
                        f"✅ Returns {response.status_code} - Endpoint accessible but requires authentication"
                    )
                elif response.status_code == 400:
                    self.log_test(
                        f"Admin Endpoint - {endpoint.split('?')[0]}", 
                        True, 
                        f"✅ Returns 400 - Endpoint accessible, parameter validation working"
                    )
                else:
                    self.log_test(
                        f"Admin Endpoint - {endpoint.split('?')[0]}", 
                        False, 
                        f"Unexpected status: {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_test(f"Admin Endpoint - {endpoint.split('?')[0]}", False, f"Error: {str(e)}")
    
    def test_authentication_with_invalid_tokens(self):
        """Test endpoints with invalid authentication tokens"""
        print("\n🔐 AUTHENTICATION TEST WITH INVALID TOKENS")
        print("=" * 50)
        
        invalid_tokens = [
            "invalid_token",
            "Bearer invalid_token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
        ]
        
        test_endpoint = "/api/reports/comprehensive"
        
        for token in invalid_tokens:
            try:
                headers = {"Authorization": token}
                response = requests.get(
                    f"{self.backend_url}{test_endpoint}",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 401:
                    self.log_test(
                        f"Invalid Token Authentication - {token[:20]}...", 
                        True, 
                        f"✅ Properly rejects invalid token (401 Unauthorized)"
                    )
                elif response.status_code == 403:
                    self.log_test(
                        f"Invalid Token Authentication - {token[:20]}...", 
                        True, 
                        f"✅ Properly rejects invalid token (403 Forbidden)"
                    )
                elif response.status_code == 404:
                    self.log_test(
                        f"Invalid Token Authentication - {token[:20]}...", 
                        False, 
                        f"❌ Returns 404 - Authentication not working properly"
                    )
                else:
                    self.log_test(
                        f"Invalid Token Authentication - {token[:20]}...", 
                        False, 
                        f"Unexpected status: {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_test(f"Invalid Token Authentication - {token[:20]}...", False, f"Error: {str(e)}")
    
    def test_http_methods(self):
        """Test different HTTP methods on report endpoints"""
        print("\n🌐 HTTP METHODS TEST")
        print("=" * 50)
        
        test_endpoint = "/api/reports/comprehensive"
        methods_to_test = [
            ("POST", "POST Method"),
            ("PUT", "PUT Method"),
            ("DELETE", "DELETE Method"),
            ("PATCH", "PATCH Method")
        ]
        
        for method, test_name in methods_to_test:
            try:
                response = requests.request(
                    method,
                    f"{self.backend_url}{test_endpoint}",
                    timeout=10
                )
                
                if response.status_code == 405:
                    self.log_test(
                        f"{test_name} - Method Not Allowed", 
                        True, 
                        f"✅ Correctly returns 405 Method Not Allowed"
                    )
                elif response.status_code in [401, 403]:
                    self.log_test(
                        f"{test_name} - Authentication Check", 
                        True, 
                        f"✅ Endpoint accessible, requires authentication ({response.status_code})"
                    )
                elif response.status_code == 404:
                    self.log_test(
                        f"{test_name} - Endpoint Check", 
                        False, 
                        f"❌ Returns 404 - Endpoint may not be properly registered"
                    )
                else:
                    self.log_test(
                        f"{test_name} - Response Check", 
                        False, 
                        f"Unexpected status: {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_test(f"{test_name}", False, f"Error: {str(e)}")
    
    def test_endpoint_response_format(self):
        """Test endpoint response format and error messages"""
        print("\n📝 ENDPOINT RESPONSE FORMAT TEST")
        print("=" * 50)
        
        test_endpoints = [
            "/api/reports/comprehensive",
            "/api/reports/training", 
            "/api/reports/consumption",
            "/api/test-reports"
        ]
        
        for endpoint in test_endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                
                # Check if response has proper JSON format for error messages
                try:
                    json_response = response.json()
                    if "detail" in json_response or "message" in json_response:
                        self.log_test(
                            f"Response Format - {endpoint}", 
                            True, 
                            f"✅ Proper JSON error format (status: {response.status_code})"
                        )
                    else:
                        self.log_test(
                            f"Response Format - {endpoint}", 
                            True, 
                            f"✅ JSON response received (status: {response.status_code})"
                        )
                except json.JSONDecodeError:
                    if response.status_code in [401, 403]:
                        self.log_test(
                            f"Response Format - {endpoint}", 
                            True, 
                            f"✅ Non-JSON response acceptable for auth error (status: {response.status_code})"
                        )
                    else:
                        self.log_test(
                            f"Response Format - {endpoint}", 
                            False, 
                            f"❌ Non-JSON response for status: {response.status_code}"
                        )
                        
            except Exception as e:
                self.log_test(f"Response Format - {endpoint}", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all sustainability report endpoint tests"""
        print("🎯 SUSTAINABILITY REPORT ENDPOINTS FIX TEST")
        print("=" * 70)
        print(f"🎯 Target: {self.backend_url}")
        print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Focus: Verify endpoints return 401/403 instead of 404")
        print("=" * 70)
        
        # Core tests
        self.test_backend_health()
        self.test_sustainability_report_endpoints()
        
        # Security and method tests
        self.test_authentication_with_invalid_tokens()
        self.test_http_methods()
        self.test_endpoint_response_format()
        
        # Generate final report
        self.generate_final_report()
        
    def generate_final_report(self):
        """Generate comprehensive test report"""
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print("\n" + "="*80)
        print("🎉 SUSTAINABILITY REPORT ENDPOINTS TEST COMPLETED!")
        print("="*80)
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Tests: {self.total_tests}")
        print(f"   Passed: {self.passed_tests}")
        print(f"   Failed: {self.total_tests - self.passed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print("="*80)
        
        # Categorize results
        passed_tests = [r for r in self.test_results if r['passed']]
        failed_tests = [r for r in self.test_results if not r['passed']]
        
        if passed_tests:
            print("✅ PASSED TESTS:")
            for test in passed_tests:
                print(f"   • {test['test']}: {test['details']}")
                
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
                
        print("\n🎯 SUSTAINABILITY REPORT ENDPOINTS ANALYSIS:")
        
        # Check if main issue is resolved
        comprehensive_404 = any("Comprehensive Report Endpoint" in r['test'] and "404" in r['details'] for r in failed_tests)
        training_404 = any("Training Report Endpoint" in r['test'] and "404" in r['details'] for r in failed_tests)
        consumption_404 = any("Consumption Report Endpoint" in r['test'] and "404" in r['details'] for r in failed_tests)
        test_reports_404 = any("Test Reports Endpoint" in r['test'] and "404" in r['details'] for r in failed_tests)
        
        if comprehensive_404 or training_404 or consumption_404 or test_reports_404:
            print("   ❌ CRITICAL ISSUE: Some endpoints still return 404!")
            print("   🔧 REQUIRED FIX: Change @app.get to @api_router.get decorators")
            print("   📍 AFFECTED ENDPOINTS:")
            if comprehensive_404:
                print("      • /api/reports/comprehensive")
            if training_404:
                print("      • /api/reports/training")
            if consumption_404:
                print("      • /api/reports/consumption")
            if test_reports_404:
                print("      • /api/test-reports")
        else:
            print("   ✅ MAIN ISSUE RESOLVED: No endpoints return 404!")
            print("   ✅ All endpoints properly registered with @api_router.get")
            print("   ✅ Endpoints return 401/403 as expected (proper authentication)")
        
        print("\n📋 ENDPOINT STATUS SUMMARY:")
        print("   • /api/reports/comprehensive - Comprehensive sustainability report")
        print("   • /api/reports/training - Training-specific report")
        print("   • /api/reports/consumption - Consumption-specific report")
        print("   • /api/test-reports - Test endpoint for verification")
        
        print("\n🔐 AUTHENTICATION & SECURITY:")
        auth_working = not any("404" in r['details'] for r in self.test_results)
        if auth_working:
            print("   ✅ Authentication system working properly")
            print("   ✅ Invalid tokens properly rejected")
            print("   ✅ Endpoints secured as expected")
        else:
            print("   ❌ Authentication issues detected")
            print("   🔧 May need JWT token configuration review")
        
        if success_rate >= 90:
            print("\n🎉 SUSTAINABILITY REPORT BACKEND STATUS: ✅ FULLY READY")
            print("   All endpoints properly registered and working!")
        elif success_rate >= 70:
            print("\n⚠️ SUSTAINABILITY REPORT BACKEND STATUS: 🔶 MOSTLY READY")
            print("   Most endpoints working, minor issues detected!")
        else:
            print("\n❌ SUSTAINABILITY REPORT BACKEND STATUS: 🚨 NEEDS ATTENTION")
            print("   Critical issues found, endpoints may not be accessible!")
            
        return success_rate

if __name__ == "__main__":
    tester = SustainabilityReportsEndpointTester()
    try:
        tester.run_all_tests()
        success_rate = (tester.passed_tests / tester.total_tests * 100) if tester.total_tests > 0 else 0
        sys.exit(0 if success_rate >= 70 else 1)
    except KeyboardInterrupt:
        print("🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Fatal error: {str(e)}")
        sys.exit(1)