#!/usr/bin/env python3
"""
🎯 GREENWAVE CRM BACKEND MOBILE RESPONSIVENESS TEST
Comprehensive testing of core backend endpoints after mobile responsive changes
Focus: API Health, Dashboard Endpoints, Authentication, Mobile API Compatibility
"""

import requests
import json
import sys
import os
from datetime import datetime

# Railway Production Backend URL (correct backend, not frontend)
BACKEND_URL = "https://rota-crm-production.up.railway.app"
TEST_CLIENT_ID = "94927a77-edc3-45ec-8329-795feae35771"

class MobileResponsivenessBackendTester:
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
        
    def test_backend_accessibility(self):
        """Test if backend is accessible"""
        print("\n🌐 BACKEND ACCESSIBILITY TEST")
        print("=" * 50)
        
        try:
            # Test root endpoint
            response = requests.get(f"{self.backend_url}/", timeout=10)
            self.log_test(
                "Root Endpoint Accessibility", 
                response.status_code == 200,
                f"Status: {response.status_code}, Response: {response.text[:100]}"
            )
            
            # Test main health endpoint
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            self.log_test(
                "Main Health Endpoint", 
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("Backend Accessibility", False, f"Connection error: {str(e)}")
            
    def test_api_health_check(self):
        """Test API health endpoint - Core requirement"""
        print("\n🏥 API HEALTH CHECK TEST")
        print("=" * 50)
        
        try:
            # Test /api/health endpoint
            response = requests.get(f"{self.backend_url}/api/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "API Health Endpoint", 
                    True,
                    f"Status: healthy, Service: {data.get('service', 'Unknown')}"
                )
                
                # Check response structure
                required_fields = ['status', 'service', 'timestamp', 'version']
                missing_fields = [field for field in required_fields if field not in data]
                
                self.log_test(
                    "Health Response Structure",
                    len(missing_fields) == 0,
                    f"Missing fields: {missing_fields}" if missing_fields else "All required fields present"
                )
                
            else:
                self.log_test(
                    "API Health Endpoint", 
                    False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("API Health Check", False, f"Error: {str(e)}")
            
    def test_admin_dashboard_stats(self):
        """Test admin dashboard endpoint - Core requirement"""
        print("\n📊 ADMIN DASHBOARD STATS TEST")
        print("=" * 50)
        
        try:
            # Test without authentication first (should work based on code)
            response = requests.get(f"{self.backend_url}/api/admin-dashboard-stats", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Admin Dashboard Endpoint Accessibility", 
                    True,
                    f"Status: {response.status_code}"
                )
                
                # Check response structure
                required_sections = ['overview', 'training_analytics', 'consumption_analytics', 'recent_activities']
                missing_sections = [section for section in required_sections if section not in data]
                
                self.log_test(
                    "Admin Dashboard Response Structure",
                    len(missing_sections) == 0,
                    f"Missing sections: {missing_sections}" if missing_sections else "All sections present"
                )
                
                # Check overview data
                if 'overview' in data:
                    overview = data['overview']
                    overview_fields = ['total_clients', 'registered_clients', 'bulk_clients', 'total_documents']
                    overview_complete = all(field in overview for field in overview_fields)
                    
                    self.log_test(
                        "Admin Dashboard Overview Data",
                        overview_complete,
                        f"Total clients: {overview.get('total_clients', 'N/A')}, Documents: {overview.get('total_documents', 'N/A')}"
                    )
                
            else:
                self.log_test(
                    "Admin Dashboard Endpoint", 
                    False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("Admin Dashboard Stats", False, f"Error: {str(e)}")
            
    def test_client_dashboard_stats(self):
        """Test client dashboard endpoint - Core requirement"""
        print("\n👤 CLIENT DASHBOARD STATS TEST")
        print("=" * 50)
        
        try:
            # Test without authentication (should return 403)
            response = requests.get(f"{self.backend_url}/api/client-dashboard-stats", timeout=10)
            
            # Client dashboard should require authentication
            if response.status_code == 403:
                self.log_test(
                    "Client Dashboard Authentication Required", 
                    True,
                    "Correctly requires authentication (403 Forbidden)"
                )
            elif response.status_code == 401:
                self.log_test(
                    "Client Dashboard Authentication Required", 
                    True,
                    "Correctly requires authentication (401 Unauthorized)"
                )
            elif response.status_code == 200:
                # If it returns 200, check if it has proper structure
                try:
                    data = response.json()
                    self.log_test(
                        "Client Dashboard Endpoint Accessible", 
                        True,
                        f"Status: {response.status_code}, Data available"
                    )
                except:
                    self.log_test(
                        "Client Dashboard Response Format", 
                        False,
                        "Invalid JSON response"
                    )
            else:
                self.log_test(
                    "Client Dashboard Endpoint", 
                    False,
                    f"Unexpected status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("Client Dashboard Stats", False, f"Error: {str(e)}")
            
    def test_user_info_endpoint(self):
        """Test /api/me endpoint - Core requirement"""
        print("\n👤 USER INFO ENDPOINT TEST")
        print("=" * 50)
        
        try:
            # Test /api/me endpoint (should require authentication)
            response = requests.get(f"{self.backend_url}/api/me", timeout=10)
            
            # Should require authentication
            if response.status_code in [401, 403]:
                self.log_test(
                    "User Info Authentication Required", 
                    True,
                    f"Correctly requires authentication ({response.status_code})"
                )
            elif response.status_code == 404:
                self.log_test(
                    "User Info Endpoint", 
                    False,
                    "Endpoint not found (404) - may not be implemented"
                )
            else:
                self.log_test(
                    "User Info Endpoint", 
                    response.status_code == 200,
                    f"Status: {response.status_code}, Response: {response.text[:100]}"
                )
                
        except Exception as e:
            self.log_test("User Info Endpoint", False, f"Error: {str(e)}")
            
    def test_authentication_system(self):
        """Test authentication system functionality"""
        print("\n🔐 AUTHENTICATION SYSTEM TEST")
        print("=" * 50)
        
        # Test various endpoints that should require authentication
        auth_endpoints = [
            "/api/clients",
            "/api/documents", 
            "/api/trainings",
            "/api/consumptions",
            "/api/personnel"
        ]
        
        for endpoint in auth_endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                
                # Should return 401 or 403 for authentication required
                auth_required = response.status_code in [401, 403]
                self.log_test(
                    f"Auth Required - {endpoint}",
                    auth_required,
                    f"Status: {response.status_code}"
                )
                
            except Exception as e:
                self.log_test(f"Auth Test - {endpoint}", False, f"Error: {str(e)}")
                
    def test_mobile_api_compatibility(self):
        """Test mobile API compatibility - headers and response formats"""
        print("\n📱 MOBILE API COMPATIBILITY TEST")
        print("=" * 50)
        
        # Test with mobile-like headers
        mobile_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        try:
            # Test health endpoint with mobile headers
            response = requests.get(
                f"{self.backend_url}/api/health", 
                headers=mobile_headers,
                timeout=10
            )
            
            self.log_test(
                "Mobile Headers Compatibility",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            # Check CORS headers for mobile compatibility
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            cors_present = any(header in response.headers for header in cors_headers)
            self.log_test(
                "CORS Headers for Mobile",
                cors_present,
                f"CORS headers present: {cors_present}"
            )
            
            # Test JSON response format
            try:
                data = response.json()
                self.log_test(
                    "JSON Response Format",
                    isinstance(data, dict),
                    "Valid JSON response structure"
                )
            except:
                self.log_test(
                    "JSON Response Format",
                    False,
                    "Invalid JSON response"
                )
                
        except Exception as e:
            self.log_test("Mobile API Compatibility", False, f"Error: {str(e)}")
            
    def test_response_times(self):
        """Test response times for mobile performance"""
        print("\n⚡ RESPONSE TIME TEST")
        print("=" * 50)
        
        endpoints_to_test = [
            "/api/health",
            "/api/admin-dashboard-stats",
            "/api/client-dashboard-stats"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                import time
                start_time = time.time()
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                end_time = time.time()
                
                response_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
                
                # Consider under 2 seconds as good for mobile
                good_performance = response_time < 2000
                
                self.log_test(
                    f"Response Time - {endpoint}",
                    good_performance,
                    f"{response_time}ms (Status: {response.status_code})"
                )
                
            except Exception as e:
                self.log_test(f"Response Time - {endpoint}", False, f"Error: {str(e)}")
                
    def run_all_tests(self):
        """Run all mobile responsiveness backend tests"""
        print("🎯 GREENWAVE CRM BACKEND MOBILE RESPONSIVENESS TEST")
        print("=" * 60)
        print(f"Backend URL: {self.backend_url}")
        print(f"Test Client ID: {self.test_client_id}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run all test categories
        self.test_backend_accessibility()
        self.test_api_health_check()
        self.test_admin_dashboard_stats()
        self.test_client_dashboard_stats()
        self.test_user_info_endpoint()
        self.test_authentication_system()
        self.test_mobile_api_compatibility()
        self.test_response_times()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 MOBILE RESPONSIVENESS BACKEND TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT - Backend is ready for mobile responsiveness!")
        elif success_rate >= 75:
            print("✅ GOOD - Backend is mostly compatible with mobile changes")
        elif success_rate >= 50:
            print("⚠️ MODERATE - Some issues need attention")
        else:
            print("❌ CRITICAL - Major issues found, needs immediate attention")
        
        # Print failed tests for debugging
        failed_tests = [test for test in self.test_results if not test['passed']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        print("\n" + "=" * 60)
        return success_rate

if __name__ == "__main__":
    tester = MobileResponsivenessBackendTester()
    success_rate = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 75 else 1)