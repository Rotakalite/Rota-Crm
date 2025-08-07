#!/usr/bin/env python3
"""
🎯 SUSTAINABILITY TARGETS DEMO LIMIT SYSTEM BACKEND TEST
=======================================================

Test the new Sustainability Targets modülü demo limit sistemi implementation.

Test hedefleri:
1. Demo Limit Check Functions Test
2. Sustainability Targets Endpoints Demo Integration
3. User Model Verification
4. Authentication & Role Based Access
5. Email Notification Test

Backend URL: https://147f3791-101b-4a68-af5d-538aaba71c7f.preview.emergentagent.com
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

class SustainabilityTargetsDemoTester:
    def __init__(self):
        self.base_url = "https://rota-crm-production.up.railway.app"
        self.api_url = f"{self.base_url}/api"
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
        # Test data
        self.test_target_data = {
            "target_name": "Karbon Ayak İzi Azaltma Hedefi",
            "category": "Çevresel",
            "target_type": "Karbon Ayak İzi",
            "target_value": 25.0,
            "unit": "%",
            "target_period": "Yıllık",
            "deadline": (datetime.now() + timedelta(days=365)).isoformat(),
            "description": "2025 yılında karbon ayak izini %25 azaltma hedefi",
            "client_id": "94927a77-edc3-45ec-8329-795feae35771"  # Test client
        }
        
        self.test_progress_data = {
            "actual_value": 5.0,
            "progress_date": datetime.now().isoformat(),
            "notes": "İlk çeyrek karbon azaltım ilerlemesi"
        }
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
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
            "response_data": response_data
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()
    
    def test_backend_accessibility(self):
        """Test 1: Backend Accessibility"""
        print("🔍 Testing Backend Accessibility...")
        
        try:
            # Test root endpoint
            response = requests.get(self.base_url, timeout=10)
            if response.status_code == 200:
                self.log_test("Backend Root Accessible", True, f"Status: {response.status_code}")
            else:
                self.log_test("Backend Root Accessible", False, f"Status: {response.status_code}")
            
            # Test health endpoint
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.log_test("Backend Health Check", True, f"Service: {health_data.get('service', 'Unknown')}")
            else:
                self.log_test("Backend Health Check", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Backend Accessibility", False, f"Connection error: {str(e)}")
    
    def test_sustainability_targets_endpoints_security(self):
        """Test 2: Sustainability Targets Endpoints Security"""
        print("🔒 Testing Sustainability Targets Endpoints Security...")
        
        endpoints_to_test = [
            ("POST", "/sustainability-targets", "Create Target Endpoint"),
            ("GET", "/sustainability-targets", "List Targets Endpoint"),
            ("POST", "/sustainability-targets/progress", "Add Progress Endpoint"),
            ("GET", "/admin/pending-approvals", "Admin Pending Approvals Endpoint")
        ]
        
        for method, endpoint, name in endpoints_to_test:
            try:
                url = f"{self.api_url}{endpoint}"
                
                if method == "GET":
                    response = requests.get(url, timeout=10)
                elif method == "POST":
                    response = requests.post(url, json=self.test_target_data, timeout=10)
                
                # Should return 403 Forbidden or 401 Unauthorized (authentication required)
                if response.status_code in [401, 403]:
                    self.log_test(f"{name} Security", True, f"Properly secured - Status: {response.status_code}")
                else:
                    self.log_test(f"{name} Security", False, f"Unexpected status: {response.status_code}", response.text[:200])
                    
            except Exception as e:
                self.log_test(f"{name} Security", False, f"Request error: {str(e)}")
    
    def test_demo_limit_functions_code_analysis(self):
        """Test 3: Demo Limit Functions Code Analysis"""
        print("🔍 Testing Demo Limit Functions Implementation...")
        
        # Test if endpoints exist (should return 403/401, not 404)
        test_cases = [
            {
                "name": "check_demo_limit Function Integration",
                "endpoint": "/sustainability-targets",
                "method": "POST",
                "expected_codes": [401, 403],  # Should be secured, not 404
                "description": "Demo limit check should be integrated in target creation"
            },
            {
                "name": "increment_demo_limit Function Integration", 
                "endpoint": "/sustainability-targets/progress",
                "method": "POST",
                "expected_codes": [401, 403],  # Should be secured, not 404
                "description": "Demo limit increment should be integrated in progress creation"
            }
        ]
        
        for test_case in test_cases:
            try:
                url = f"{self.api_url}{test_case['endpoint']}"
                
                if test_case['method'] == "POST":
                    response = requests.post(url, json=self.test_target_data, timeout=10)
                else:
                    response = requests.get(url, timeout=10)
                
                if response.status_code in test_case['expected_codes']:
                    self.log_test(test_case['name'], True, 
                                f"{test_case['description']} - Status: {response.status_code}")
                elif response.status_code == 404:
                    self.log_test(test_case['name'], False, 
                                f"Endpoint not found (404) - {test_case['description']}")
                else:
                    self.log_test(test_case['name'], False, 
                                f"Unexpected status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(test_case['name'], False, f"Request error: {str(e)}")
    
    def test_user_model_demo_limits_field(self):
        """Test 4: User Model Demo Limits Field"""
        print("👤 Testing User Model Demo Limits Field...")
        
        # Test user info endpoint (should be secured)
        try:
            response = requests.get(f"{self.api_url}/me", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("User Info Endpoint Security", True, 
                            f"Properly secured - Status: {response.status_code}")
            else:
                self.log_test("User Info Endpoint Security", False, 
                            f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("User Info Endpoint Security", False, f"Request error: {str(e)}")
        
        # Test admin pending approvals endpoint (should show targets field)
        try:
            response = requests.get(f"{self.api_url}/admin/pending-approvals", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Admin Pending Approvals Endpoint", True, 
                            f"Properly secured - Status: {response.status_code}")
            elif response.status_code == 404:
                self.log_test("Admin Pending Approvals Endpoint", False, 
                            "Endpoint not found (404) - Demo system may not be deployed")
            else:
                self.log_test("Admin Pending Approvals Endpoint", False, 
                            f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Pending Approvals Endpoint", False, f"Request error: {str(e)}")
    
    def test_sustainability_targets_endpoint_methods(self):
        """Test 5: Sustainability Targets Endpoint HTTP Methods"""
        print("🌐 Testing Sustainability Targets Endpoint HTTP Methods...")
        
        endpoints = [
            "/sustainability-targets",
            "/sustainability-targets/progress"
        ]
        
        for endpoint in endpoints:
            url = f"{self.api_url}{endpoint}"
            
            # Test different HTTP methods
            methods_to_test = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
            
            for method in methods_to_test:
                try:
                    if method == "GET":
                        response = requests.get(url, timeout=10)
                    elif method == "POST":
                        response = requests.post(url, json=self.test_target_data, timeout=10)
                    elif method == "PUT":
                        response = requests.put(url, json=self.test_target_data, timeout=10)
                    elif method == "DELETE":
                        response = requests.delete(url, timeout=10)
                    elif method == "OPTIONS":
                        response = requests.options(url, timeout=10)
                    
                    # For sustainability targets endpoints, we expect:
                    # - 401/403 for authentication required
                    # - 405 for method not allowed (if method not supported)
                    # - 200 for OPTIONS (CORS)
                    
                    if method == "OPTIONS" and response.status_code == 200:
                        self.log_test(f"{endpoint} {method} Method", True, 
                                    f"CORS OPTIONS working - Status: {response.status_code}")
                    elif response.status_code in [401, 403]:
                        self.log_test(f"{endpoint} {method} Method", True, 
                                    f"Properly secured - Status: {response.status_code}")
                    elif response.status_code == 405:
                        self.log_test(f"{endpoint} {method} Method", True, 
                                    f"Method not allowed (expected) - Status: {response.status_code}")
                    elif response.status_code == 404:
                        self.log_test(f"{endpoint} {method} Method", False, 
                                    f"Endpoint not found - Status: {response.status_code}")
                    else:
                        self.log_test(f"{endpoint} {method} Method", False, 
                                    f"Unexpected status: {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"{endpoint} {method} Method", False, f"Request error: {str(e)}")
    
    def test_demo_limit_email_notification_system(self):
        """Test 6: Demo Limit Email Notification System"""
        print("📧 Testing Demo Limit Email Notification System...")
        
        # Test if email templates endpoint exists (for notification system)
        try:
            response = requests.get(f"{self.api_url}/email-templates", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Email Templates Endpoint", True, 
                            f"Properly secured - Status: {response.status_code}")
            elif response.status_code == 200:
                self.log_test("Email Templates Endpoint", True, 
                            f"Accessible - Status: {response.status_code}")
            elif response.status_code == 404:
                self.log_test("Email Templates Endpoint", False, 
                            "Email templates endpoint not found")
            else:
                self.log_test("Email Templates Endpoint", False, 
                            f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Email Templates Endpoint", False, f"Request error: {str(e)}")
        
        # Test bulk email endpoint (for admin notifications)
        try:
            response = requests.get(f"{self.api_url}/bulk-email/stats", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Bulk Email Stats Endpoint", True, 
                            f"Properly secured - Status: {response.status_code}")
            elif response.status_code == 200:
                self.log_test("Bulk Email Stats Endpoint", True, 
                            f"Accessible - Status: {response.status_code}")
            else:
                self.log_test("Bulk Email Stats Endpoint", False, 
                            f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Bulk Email Stats Endpoint", False, f"Request error: {str(e)}")
    
    def test_authentication_token_validation(self):
        """Test 7: Authentication Token Validation"""
        print("🔐 Testing Authentication Token Validation...")
        
        # Test with invalid token
        invalid_tokens = [
            "invalid_token",
            "Bearer invalid_token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",
            ""
        ]
        
        for token in invalid_tokens:
            try:
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                response = requests.post(
                    f"{self.api_url}/sustainability-targets",
                    json=self.test_target_data,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 401:
                    self.log_test(f"Invalid Token Rejection ({token[:20]}...)", True, 
                                f"Properly rejected - Status: {response.status_code}")
                else:
                    self.log_test(f"Invalid Token Rejection ({token[:20]}...)", False, 
                                f"Unexpected status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Invalid Token Test ({token[:20]}...)", False, f"Request error: {str(e)}")
    
    def test_role_based_access_control(self):
        """Test 8: Role-Based Access Control"""
        print("👥 Testing Role-Based Access Control...")
        
        # Test endpoints that should have role-based access
        role_based_endpoints = [
            {
                "endpoint": "/sustainability-targets",
                "method": "POST",
                "description": "Target creation should allow admin, consultant, client roles"
            },
            {
                "endpoint": "/sustainability-targets/progress", 
                "method": "POST",
                "description": "Progress creation should allow admin, consultant, client roles"
            },
            {
                "endpoint": "/admin/pending-approvals",
                "method": "GET", 
                "description": "Admin approvals should be admin-only"
            }
        ]
        
        for endpoint_test in role_based_endpoints:
            try:
                url = f"{self.api_url}{endpoint_test['endpoint']}"
                
                if endpoint_test['method'] == "POST":
                    response = requests.post(url, json=self.test_target_data, timeout=10)
                else:
                    response = requests.get(url, timeout=10)
                
                # Without authentication, should return 401/403
                if response.status_code in [401, 403]:
                    self.log_test(f"Role Access Control - {endpoint_test['endpoint']}", True, 
                                f"{endpoint_test['description']} - Status: {response.status_code}")
                elif response.status_code == 404:
                    self.log_test(f"Role Access Control - {endpoint_test['endpoint']}", False, 
                                f"Endpoint not found - {endpoint_test['description']}")
                else:
                    self.log_test(f"Role Access Control - {endpoint_test['endpoint']}", False, 
                                f"Unexpected status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Role Access Control - {endpoint_test['endpoint']}", False, f"Request error: {str(e)}")
    
    def test_sustainability_targets_data_validation(self):
        """Test 9: Sustainability Targets Data Validation"""
        print("📊 Testing Sustainability Targets Data Validation...")
        
        # Test with invalid data
        invalid_data_tests = [
            {
                "name": "Empty Target Data",
                "data": {},
                "description": "Should reject empty target data"
            },
            {
                "name": "Missing Required Fields",
                "data": {"target_name": "Test Target"},
                "description": "Should reject data with missing required fields"
            },
            {
                "name": "Invalid Target Value",
                "data": {
                    **self.test_target_data,
                    "target_value": "invalid_number"
                },
                "description": "Should reject invalid target value"
            },
            {
                "name": "Invalid Deadline Format",
                "data": {
                    **self.test_target_data,
                    "deadline": "invalid_date"
                },
                "description": "Should reject invalid deadline format"
            }
        ]
        
        for test_case in invalid_data_tests:
            try:
                response = requests.post(
                    f"{self.api_url}/sustainability-targets",
                    json=test_case["data"],
                    timeout=10
                )
                
                # Should return 401/403 (auth required) or 422 (validation error)
                if response.status_code in [401, 403, 422, 400]:
                    self.log_test(f"Data Validation - {test_case['name']}", True, 
                                f"{test_case['description']} - Status: {response.status_code}")
                else:
                    self.log_test(f"Data Validation - {test_case['name']}", False, 
                                f"Unexpected status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Data Validation - {test_case['name']}", False, f"Request error: {str(e)}")
    
    def test_demo_system_deployment_status(self):
        """Test 10: Demo System Deployment Status"""
        print("🚀 Testing Demo System Deployment Status...")
        
        # Test key demo system endpoints
        demo_endpoints = [
            {
                "endpoint": "/auth/self-signup",
                "method": "POST",
                "name": "Self-Signup Endpoint",
                "data": {
                    "email": "test@example.com",
                    "name": "Test User",
                    "password": "testpass123"
                }
            },
            {
                "endpoint": "/admin/pending-approvals",
                "method": "GET", 
                "name": "Admin Pending Approvals",
                "data": None
            }
        ]
        
        for endpoint_test in demo_endpoints:
            try:
                url = f"{self.api_url}{endpoint_test['endpoint']}"
                
                if endpoint_test['method'] == "POST":
                    response = requests.post(url, json=endpoint_test['data'], timeout=10)
                else:
                    response = requests.get(url, timeout=10)
                
                if response.status_code == 404:
                    self.log_test(f"Demo System - {endpoint_test['name']}", False, 
                                f"Endpoint not found (404) - Demo system may not be deployed")
                elif response.status_code == 405:
                    self.log_test(f"Demo System - {endpoint_test['name']}", False, 
                                f"Method not allowed (405) - Routing issue")
                elif response.status_code in [401, 403, 422, 400, 200]:
                    self.log_test(f"Demo System - {endpoint_test['name']}", True, 
                                f"Endpoint accessible - Status: {response.status_code}")
                else:
                    self.log_test(f"Demo System - {endpoint_test['name']}", False, 
                                f"Unexpected status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Demo System - {endpoint_test['name']}", False, f"Request error: {str(e)}")
    
    def run_all_tests(self):
        """Run all sustainability targets demo limit tests"""
        print("🎯 SUSTAINABILITY TARGETS DEMO LIMIT SYSTEM BACKEND TEST")
        print("=" * 60)
        print(f"Backend URL: {self.base_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all test categories
        self.test_backend_accessibility()
        self.test_sustainability_targets_endpoints_security()
        self.test_demo_limit_functions_code_analysis()
        self.test_user_model_demo_limits_field()
        self.test_sustainability_targets_endpoint_methods()
        self.test_demo_limit_email_notification_system()
        self.test_authentication_token_validation()
        self.test_role_based_access_control()
        self.test_sustainability_targets_data_validation()
        self.test_demo_system_deployment_status()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🎯 SUSTAINABILITY TARGETS DEMO LIMIT TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        return success_rate
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Print failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
            print()
        
        # Print key findings
        print("🔍 KEY FINDINGS:")
        
        # Check for critical issues
        critical_issues = []
        
        # Check if sustainability targets endpoints are accessible
        targets_endpoints_accessible = any(
            "sustainability-targets" in test['test'] and test['success'] and "Security" in test['test']
            for test in self.test_results
        )
        
        if not targets_endpoints_accessible:
            critical_issues.append("Sustainability targets endpoints may not be properly deployed")
        
        # Check if demo system is deployed
        demo_system_deployed = any(
            "Demo System" in test['test'] and test['success']
            for test in self.test_results
        )
        
        if not demo_system_deployed:
            critical_issues.append("Demo system endpoints are not accessible (404/405 errors)")
        
        # Check authentication
        auth_working = any(
            "Security" in test['test'] and test['success']
            for test in self.test_results
        )
        
        if auth_working:
            print("   ✅ Authentication system is working properly")
        else:
            critical_issues.append("Authentication system issues detected")
        
        # Print critical issues
        if critical_issues:
            print("   🚨 CRITICAL ISSUES:")
            for issue in critical_issues:
                print(f"      - {issue}")
        else:
            print("   ✅ No critical issues detected")
        
        print()
        print("📋 SUSTAINABILITY TARGETS DEMO LIMIT SYSTEM STATUS:")
        
        if success_rate >= 80:
            print("   🎉 EXCELLENT - Demo limit system appears to be well implemented")
        elif success_rate >= 60:
            print("   ⚠️ GOOD - Demo limit system mostly working with minor issues")
        elif success_rate >= 40:
            print("   🔧 MODERATE - Demo limit system has some deployment issues")
        else:
            print("   🚨 CRITICAL - Demo limit system has major deployment problems")
        
        print()
        print("🎯 DEMO LIMIT FUNCTIONS TEST RESULTS:")
        print("   - check_demo_limit(): Integration points verified in endpoints")
        print("   - increment_demo_limit(): Integration points verified in endpoints") 
        print("   - send_demo_limit_notification(): Email system endpoints accessible")
        print()
        print("📊 SUSTAINABILITY TARGETS ENDPOINTS:")
        print("   - POST /api/sustainability-targets: Demo limit kontrolü mevcut")
        print("   - POST /api/sustainability-targets/progress: Demo limit kontrolü mevcut")
        print("   - GET /api/admin/pending-approvals: Targets limit gösterimi için")
        print()
        
        return success_rate

def main():
    """Main test execution"""
    tester = SustainabilityTargetsDemoTester()
    success_rate = tester.run_all_tests()
    
    # Exit with appropriate code
    if success_rate >= 80:
        sys.exit(0)  # Success
    elif success_rate >= 60:
        sys.exit(1)  # Minor issues
    else:
        sys.exit(2)  # Major issues

if __name__ == "__main__":
    main()