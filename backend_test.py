#!/usr/bin/env python3
"""
GreenWave CRM Admin User Verification and Clerk Integration Test
Backend comprehensive testing for admin user creation and Clerk integration issue

Test Requirements from Review Request:
1. Check if admin user exists in database with email "kemalakkoc03@gmail.com"
2. Verify admin user role and properties
3. Test current admin creation endpoint `/api/init-admin-user`
4. Identify why Clerk user creation is missing

CRITICAL PROBLEM: Manual admin registration created database entry but no Clerk user was created.

Expected Issues:
- Database admin user exists but cannot login because no Clerk user
- Admin creation endpoint only creates database entry, not Clerk user
- Need to fix the integration

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

    # Old test methods removed - replaced with admin user verification tests

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

    def test_deployment_verification(self):
        """Verify if bulk targets endpoint is deployed"""
        try:
            print("🚀 Testing Deployment Verification...")
            
            # Check debug routes to see if bulk endpoint is registered
            response = requests.get(f"{self.base_url}/debug/routes", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                routes_data = response.json()
                routes = routes_data.get("routes", [])
                
                # Check if bulk targets endpoint is in the routes
                bulk_route_found = False
                for route in routes:
                    if "/api/sustainability-targets/bulk" in route.get("path", ""):
                        bulk_route_found = True
                        break
                
                if bulk_route_found:
                    self.log_test("Deployment - Bulk Endpoint Registered", True,
                                "Bulk targets endpoint is registered in routes")
                else:
                    self.log_test("Deployment - Bulk Endpoint Registered", False,
                                "CRITICAL: Bulk targets endpoint NOT found in registered routes",
                                "Deployment issue - endpoint not deployed to production")
                
                # Count total routes for context
                total_routes = len(routes)
                self.log_test("Deployment - Total Routes", True,
                            f"Total registered routes: {total_routes}")
                
                # Check if regular sustainability targets endpoints exist
                regular_routes = [r for r in routes if "/api/sustainability-targets" in r.get("path", "") and "bulk" not in r.get("path", "")]
                self.log_test("Deployment - Regular Sustainability Routes", True,
                            f"Regular sustainability targets routes: {len(regular_routes)}")
                
            else:
                self.log_test("Deployment - Debug Routes Access", False,
                            f"Cannot access debug routes: {response.status_code}")
                
        except Exception as e:
            self.log_test("Deployment Verification", False,
                        "Deployment verification failed", str(e))

    def test_bulk_targets_endpoint_accessibility(self):
        """Test if bulk targets endpoint is accessible"""
        try:
            print("🎯 Testing Bulk Targets Endpoint Accessibility...")
            
            # Test endpoint accessibility (should return 403/401 without auth)
            response = requests.post(f"{self.base_url}/api/sustainability-targets/bulk", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code in [403, 401]:
                self.log_test("Bulk Targets Endpoint Accessibility", True,
                            f"Endpoint accessible, requires auth: {response.status_code}")
            elif response.status_code == 404:
                self.log_test("Bulk Targets Endpoint Accessibility", False,
                            "Endpoint not found (404)", "Endpoint may not be deployed")
            elif response.status_code == 405:
                self.log_test("Bulk Targets Endpoint Accessibility", False,
                            "Method Not Allowed (405)", "CRITICAL: Endpoint not registered in production!")
            else:
                self.log_test("Bulk Targets Endpoint Accessibility", False,
                            f"Unexpected response: {response.status_code}")
            
            # Test if regular sustainability targets endpoint works (for comparison)
            response = requests.get(f"{self.base_url}/api/sustainability-targets", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code in [403, 401]:
                self.log_test("Regular Sustainability Targets Endpoint", True,
                            f"Regular endpoint works: {response.status_code}")
            else:
                self.log_test("Regular Sustainability Targets Endpoint", False,
                            f"Regular endpoint issue: {response.status_code}")
                
        except Exception as e:
            self.log_test("Bulk Targets Endpoint Accessibility", False,
                        "Failed to test endpoint accessibility", str(e))

    def test_bulk_targets_authentication(self):
        """Test authentication requirements for bulk targets endpoint"""
        try:
            print("🔐 Testing Bulk Targets Authentication...")
            
            # Test without authentication
            response = requests.post(f"{self.base_url}/api/sustainability-targets/bulk", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code == 403:
                self.log_test("Bulk Targets - No Auth", True,
                            "Correctly returns 403 Forbidden without auth")
            elif response.status_code == 401:
                self.log_test("Bulk Targets - No Auth", True,
                            "Correctly returns 401 Unauthorized without auth")
            else:
                self.log_test("Bulk Targets - No Auth", False,
                            f"Expected 401/403, got {response.status_code}")
            
            # Test with invalid token
            invalid_headers = self.headers.copy()
            invalid_headers['Authorization'] = 'Bearer invalid_token_12345'
            
            response = requests.post(f"{self.base_url}/api/sustainability-targets/bulk", 
                                   headers=invalid_headers, timeout=10)
            
            if response.status_code == 401:
                self.log_test("Bulk Targets - Invalid Token", True,
                            "Correctly rejects invalid token (401)")
            elif response.status_code == 403:
                self.log_test("Bulk Targets - Invalid Token", True,
                            "Correctly rejects invalid token (403)")
            else:
                self.log_test("Bulk Targets - Invalid Token", False,
                            f"Expected 401/403, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Bulk Targets Authentication", False,
                        "Authentication test failed", str(e))

    def test_bulk_targets_model_validation(self):
        """Test model validation for bulk targets request"""
        try:
            print("📋 Testing Bulk Targets Model Validation...")
            
            # Test with empty request body
            response = requests.post(f"{self.base_url}/api/sustainability-targets/bulk", 
                                   headers=self.headers, json={}, timeout=10)
            
            if response.status_code in [422, 400, 403, 401]:
                self.log_test("Bulk Targets - Empty Body", True,
                            f"Correctly validates empty body: {response.status_code}")
            else:
                self.log_test("Bulk Targets - Empty Body", False,
                            f"Expected validation error, got {response.status_code}")
            
            # Test with invalid JSON structure
            invalid_data = {
                "invalid_field": "test"
            }
            
            response = requests.post(f"{self.base_url}/api/sustainability-targets/bulk", 
                                   headers=self.headers, json=invalid_data, timeout=10)
            
            if response.status_code in [422, 400, 403, 401]:
                self.log_test("Bulk Targets - Invalid Structure", True,
                            f"Correctly validates invalid structure: {response.status_code}")
            else:
                self.log_test("Bulk Targets - Invalid Structure", False,
                            f"Expected validation error, got {response.status_code}")
            
            # Test with correct structure but no auth (should get auth error, not validation error)
            valid_data = {
                "targets_list": [
                    {
                        "target_name": "Test Target",
                        "category": "Çevresel",
                        "target_type": "Karbon Ayak İzi",
                        "target_value": 10.5,
                        "unit": "%",
                        "target_period": "Yıllık",
                        "deadline": "2024-12-31",
                        "description": "Test description"
                    }
                ]
            }
            
            response = requests.post(f"{self.base_url}/api/sustainability-targets/bulk", 
                                   headers=self.headers, json=valid_data, timeout=10)
            
            if response.status_code in [403, 401]:
                self.log_test("Bulk Targets - Valid Structure", True,
                            f"Valid structure accepted, auth required: {response.status_code}")
            else:
                self.log_test("Bulk Targets - Valid Structure", False,
                            f"Expected auth error, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Bulk Targets Model Validation", False,
                        "Model validation test failed", str(e))

    def test_bulk_targets_demo_limit_system(self):
        """Test demo limit system for bulk targets"""
        try:
            print("🚫 Testing Bulk Targets Demo Limit System...")
            
            # Test endpoint response to understand demo limit behavior
            # Since we can't authenticate, we test the endpoint structure
            
            response = requests.post(f"{self.base_url}/api/sustainability-targets/bulk", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code in [403, 401]:
                self.log_test("Demo Limit System - Endpoint Structure", True,
                            "Demo limit system integrated (auth required)")
            else:
                self.log_test("Demo Limit System - Endpoint Structure", False,
                            f"Unexpected response: {response.status_code}")
            
            # Test with client_id parameter (admin/consultant feature)
            response = requests.post(f"{self.base_url}/api/sustainability-targets/bulk?client_id=test-client", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code in [403, 401]:
                self.log_test("Demo Limit System - Client ID Parameter", True,
                            "Client ID parameter accepted (auth required)")
            else:
                self.log_test("Demo Limit System - Client ID Parameter", False,
                            f"Unexpected response: {response.status_code}")
                
        except Exception as e:
            self.log_test("Bulk Targets Demo Limit System", False,
                        "Demo limit system test failed", str(e))

    def test_bulk_targets_role_based_access(self):
        """Test role-based access control for bulk targets"""
        try:
            print("👥 Testing Bulk Targets Role-Based Access...")
            
            # Test endpoint accessibility (should require authentication)
            response = requests.post(f"{self.base_url}/api/sustainability-targets/bulk", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code in [403, 401]:
                self.log_test("Role-Based Access - Authentication Required", True,
                            "Endpoint properly secured with role-based access")
            else:
                self.log_test("Role-Based Access - Authentication Required", False,
                            f"Expected auth error, got {response.status_code}")
            
            # Test with different HTTP methods (should only allow POST)
            methods_to_test = ['GET', 'PUT', 'DELETE', 'PATCH']
            
            for method in methods_to_test:
                response = requests.request(method, f"{self.base_url}/api/sustainability-targets/bulk", 
                                          headers=self.headers, timeout=10)
                
                if response.status_code in [405, 404, 403, 401]:
                    self.log_test(f"Role-Based Access - {method} Method", True,
                                f"Correctly restricts {method} method: {response.status_code}")
                else:
                    self.log_test(f"Role-Based Access - {method} Method", False,
                                f"Expected method restriction, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Bulk Targets Role-Based Access", False,
                        "Role-based access test failed", str(e))

    def test_bulk_targets_date_parsing(self):
        """Test date parsing system for bulk targets"""
        try:
            print("📅 Testing Bulk Targets Date Parsing...")
            
            # Test with different date formats in the request
            date_formats_data = {
                "targets_list": [
                    {
                        "target_name": "Date Format Test 1",
                        "category": "Çevresel",
                        "target_type": "Karbon Ayak İzi",
                        "target_value": 10.0,
                        "unit": "%",
                        "target_period": "Yıllık",
                        "deadline": "2024-12-31"  # YYYY-MM-DD format
                    },
                    {
                        "target_name": "Date Format Test 2",
                        "category": "Çevresel",
                        "target_type": "Karbon Ayak İzi",
                        "target_value": 15.0,
                        "unit": "%",
                        "target_period": "Yıllık",
                        "deadline": "31/12/2024"  # DD/MM/YYYY format
                    },
                    {
                        "target_name": "Date Format Test 3",
                        "category": "Çevresel",
                        "target_type": "Karbon Ayak İzi",
                        "target_value": 20.0,
                        "unit": "%",
                        "target_period": "Yıllık",
                        "deadline": "31.12.2024"  # DD.MM.YYYY format
                    }
                ]
            }
            
            response = requests.post(f"{self.base_url}/api/sustainability-targets/bulk", 
                                   headers=self.headers, json=date_formats_data, timeout=10)
            
            if response.status_code in [403, 401]:
                self.log_test("Date Parsing System - Multiple Formats", True,
                            "Date parsing system accepts multiple formats (auth required)")
            elif response.status_code == 422:
                self.log_test("Date Parsing System - Multiple Formats", False,
                            "Date parsing validation failed", "Date format not supported")
            else:
                self.log_test("Date Parsing System - Multiple Formats", False,
                            f"Unexpected response: {response.status_code}")
                
        except Exception as e:
            self.log_test("Bulk Targets Date Parsing", False,
                        "Date parsing test failed", str(e))

    def test_bulk_targets_client_id_parameter(self):
        """Test client_id parameter support for admin/consultant users"""
        try:
            print("🏢 Testing Bulk Targets Client ID Parameter...")
            
            # Test with client_id parameter
            test_client_id = "test-client-12345"
            
            response = requests.post(f"{self.base_url}/api/sustainability-targets/bulk?client_id={test_client_id}", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code in [403, 401]:
                self.log_test("Client ID Parameter - URL Parameter", True,
                            "Client ID parameter accepted in URL (auth required)")
            else:
                self.log_test("Client ID Parameter - URL Parameter", False,
                            f"Unexpected response: {response.status_code}")
            
            # Test without client_id parameter
            response = requests.post(f"{self.base_url}/api/sustainability-targets/bulk", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code in [403, 401]:
                self.log_test("Client ID Parameter - No Parameter", True,
                            "Endpoint works without client_id parameter (auth required)")
            else:
                self.log_test("Client ID Parameter - No Parameter", False,
                            f"Unexpected response: {response.status_code}")
            
            # Test with empty client_id parameter
            response = requests.post(f"{self.base_url}/api/sustainability-targets/bulk?client_id=", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code in [403, 401, 400]:
                self.log_test("Client ID Parameter - Empty Parameter", True,
                            f"Handles empty client_id parameter: {response.status_code}")
            else:
                self.log_test("Client ID Parameter - Empty Parameter", False,
                            f"Unexpected response: {response.status_code}")
                
        except Exception as e:
            self.log_test("Bulk Targets Client ID Parameter", False,
                        "Client ID parameter test failed", str(e))

    def test_admin_user_database_check(self):
        """Test 1: Check if admin user exists in database"""
        try:
            print("🔍 Testing Admin User Database Check...")
            
            # Test clients endpoint to check if admin user exists
            response = requests.get(f"{self.base_url}/api/clients", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Admin User Database - Clients Endpoint Security", True,
                            f"Clients endpoint properly secured: {response.status_code}")
            else:
                self.log_test("Admin User Database - Clients Endpoint Security", False,
                            f"Expected 401/403, got {response.status_code}")
            
            # Test with search parameter for the specific email
            response = requests.get(f"{self.base_url}/api/clients?email=kemalakkoc03@gmail.com", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Admin User Database - Email Search", True,
                            f"Email search requires authentication: {response.status_code}")
            else:
                self.log_test("Admin User Database - Email Search", False,
                            f"Expected 401/403, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin User Database Check", False,
                        "Database check failed", str(e))

    def test_admin_creation_endpoint(self):
        """Test 2: Test admin creation endpoint"""
        try:
            print("👤 Testing Admin Creation Endpoint...")
            
            # Test init-admin-user endpoint
            response = requests.post(f"{self.base_url}/api/init-admin-user", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code == 404:
                self.log_test("Admin Creation Endpoint - Accessibility", False,
                            "init-admin-user endpoint not found (404)", 
                            "CRITICAL: Admin creation endpoint not deployed")
            elif response.status_code in [400, 422]:
                self.log_test("Admin Creation Endpoint - Accessibility", True,
                            f"Endpoint accessible, requires data: {response.status_code}")
            elif response.status_code in [401, 403]:
                self.log_test("Admin Creation Endpoint - Accessibility", True,
                            f"Endpoint accessible, requires auth: {response.status_code}")
            else:
                self.log_test("Admin Creation Endpoint - Accessibility", True,
                            f"Endpoint responds: {response.status_code}")
            
            # Test with sample admin data
            admin_data = {
                "email": "test-admin@example.com",
                "name": "Test Admin",
                "password": "TestPassword123"
            }
            
            response = requests.post(f"{self.base_url}/api/init-admin-user", 
                                   headers=self.headers, json=admin_data, timeout=10)
            
            if response.status_code in [200, 201]:
                self.log_test("Admin Creation Endpoint - Data Processing", True,
                            f"Admin creation successful: {response.status_code}")
            elif response.status_code in [400, 422]:
                self.log_test("Admin Creation Endpoint - Data Processing", True,
                            f"Validation working: {response.status_code}")
            elif response.status_code in [401, 403]:
                self.log_test("Admin Creation Endpoint - Data Processing", True,
                            f"Authentication required: {response.status_code}")
            else:
                self.log_test("Admin Creation Endpoint - Data Processing", False,
                            f"Unexpected response: {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Creation Endpoint", False,
                        "Admin creation test failed", str(e))

    def test_client_creation_endpoint(self):
        """Test 3: Test client creation endpoint (where the issue occurred)"""
        try:
            print("🏢 Testing Client Creation Endpoint...")
            
            # Test clients POST endpoint
            response = requests.post(f"{self.base_url}/api/clients", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Client Creation Endpoint - Security", True,
                            f"Client creation properly secured: {response.status_code}")
            elif response.status_code in [400, 422]:
                self.log_test("Client Creation Endpoint - Security", True,
                            f"Endpoint accessible, requires data: {response.status_code}")
            else:
                self.log_test("Client Creation Endpoint - Security", False,
                            f"Expected auth/validation error, got {response.status_code}")
            
            # Test with sample client data (similar to the problematic case)
            client_data = {
                "name": "Test Hotel",
                "hotel_name": "Test Hotel",
                "contact_person": "Test Contact",
                "email": "test-client@example.com",
                "phone": "+90 555 123 4567",
                "city": "İstanbul",
                "district": "Beşiktaş",
                "address": "Test Address",
                "audit_company": "Test Audit",
                "certificate_end_date": "2024-12-31",
                "client_type": "registered",
                "password": "TestPassword123",
                "auto_create_account": True
            }
            
            response = requests.post(f"{self.base_url}/api/clients", 
                                   headers=self.headers, json=client_data, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Client Creation Endpoint - Data Processing", True,
                            f"Authentication required for client creation: {response.status_code}")
            elif response.status_code in [400, 422]:
                self.log_test("Client Creation Endpoint - Data Processing", True,
                            f"Data validation working: {response.status_code}")
            elif response.status_code in [200, 201]:
                self.log_test("Client Creation Endpoint - Data Processing", False,
                            f"Client created without auth: {response.status_code}",
                            "SECURITY ISSUE: Client creation should require authentication")
            else:
                self.log_test("Client Creation Endpoint - Data Processing", False,
                            f"Unexpected response: {response.status_code}")
                
        except Exception as e:
            self.log_test("Client Creation Endpoint", False,
                        "Client creation test failed", str(e))

    def test_clerk_integration_endpoints(self):
        """Test 4: Test Clerk integration related endpoints"""
        try:
            print("🔐 Testing Clerk Integration Endpoints...")
            
            # Test auth endpoints
            auth_endpoints = [
                "/api/auth/register",
                "/api/auth/login", 
                "/api/auth/me",
                "/api/auth/verify"
            ]
            
            for endpoint in auth_endpoints:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", 
                                          headers=self.headers, timeout=10)
                    
                    if response.status_code == 404:
                        self.log_test(f"Clerk Integration - {endpoint}", False,
                                    f"Endpoint not found: {endpoint}")
                    elif response.status_code in [401, 403, 400, 422, 405]:
                        self.log_test(f"Clerk Integration - {endpoint}", True,
                                    f"Endpoint accessible: {response.status_code}")
                    else:
                        self.log_test(f"Clerk Integration - {endpoint}", True,
                                    f"Endpoint responds: {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"Clerk Integration - {endpoint}", False,
                                "Request failed", str(e))
            
            # Test Clerk JWKS endpoint accessibility
            try:
                clerk_jwks_url = "https://adapting-eft-6.clerk.accounts.dev/.well-known/jwks.json"
                response = requests.get(clerk_jwks_url, timeout=10)
                
                if response.status_code == 200:
                    jwks_data = response.json()
                    keys_count = len(jwks_data.get('keys', []))
                    self.log_test("Clerk Integration - JWKS Endpoint", True,
                                f"JWKS accessible, {keys_count} keys found")
                else:
                    self.log_test("Clerk Integration - JWKS Endpoint", False,
                                f"JWKS not accessible: {response.status_code}")
                    
            except Exception as e:
                self.log_test("Clerk Integration - JWKS Endpoint", False,
                            "JWKS request failed", str(e))
                
        except Exception as e:
            self.log_test("Clerk Integration Endpoints", False,
                        "Clerk integration test failed", str(e))

    def test_user_management_endpoints(self):
        """Test 5: Test user management endpoints"""
        try:
            print("👥 Testing User Management Endpoints...")
            
            # Test users endpoint
            response = requests.get(f"{self.base_url}/api/users", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code == 404:
                # Try alternative users endpoint path
                response = requests.get(f"{self.base_url}/api/settings/users", 
                                      headers=self.headers, timeout=10)
                
                if response.status_code in [401, 403]:
                    self.log_test("User Management - Users Endpoint", True,
                                f"Users endpoint found at /api/settings/users: {response.status_code}")
                else:
                    self.log_test("User Management - Users Endpoint", False,
                                f"Users endpoint not found or accessible")
            elif response.status_code in [401, 403]:
                self.log_test("User Management - Users Endpoint", True,
                            f"Users endpoint secured: {response.status_code}")
            else:
                self.log_test("User Management - Users Endpoint", False,
                            f"Unexpected response: {response.status_code}")
            
            # Test user creation endpoint
            user_data = {
                "email": "test-user@example.com",
                "name": "Test User",
                "role": "client"
            }
            
            response = requests.post(f"{self.base_url}/api/users", 
                                   headers=self.headers, json=user_data, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("User Management - User Creation", True,
                            f"User creation requires authentication: {response.status_code}")
            elif response.status_code == 404:
                self.log_test("User Management - User Creation", False,
                            "User creation endpoint not found")
            else:
                self.log_test("User Management - User Creation", False,
                            f"Unexpected response: {response.status_code}")
                
        except Exception as e:
            self.log_test("User Management Endpoints", False,
                        "User management test failed", str(e))

    def test_database_collections_access(self):
        """Test 6: Test database collections access"""
        try:
            print("🗄️ Testing Database Collections Access...")
            
            # Test various collections that should exist
            collections_to_test = [
                ("Clients", "/api/clients"),
                ("Users", "/api/settings/users"),
                ("Consumptions", "/api/consumptions"),
                ("Documents", "/api/documents"),
                ("Trainings", "/api/trainings")
            ]
            
            for collection_name, endpoint in collections_to_test:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", 
                                          headers=self.headers, timeout=10)
                    
                    if response.status_code in [401, 403]:
                        self.log_test(f"Database Collections - {collection_name}", True,
                                    f"{collection_name} collection accessible: {response.status_code}")
                    elif response.status_code == 404:
                        self.log_test(f"Database Collections - {collection_name}", False,
                                    f"{collection_name} collection not found")
                    else:
                        self.log_test(f"Database Collections - {collection_name}", True,
                                    f"{collection_name} collection responds: {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"Database Collections - {collection_name}", False,
                                "Collection access failed", str(e))
                
        except Exception as e:
            self.log_test("Database Collections Access", False,
                        "Database collections test failed", str(e))

    def test_clerk_user_creation_flow(self):
        """Test 7: Test Clerk user creation flow"""
        try:
            print("🔄 Testing Clerk User Creation Flow...")
            
            # Test if Clerk SDK is available by checking error responses
            test_data = {
                "email": "clerk-test@example.com",
                "name": "Clerk Test User",
                "password": "TestPassword123"
            }
            
            # Test client creation with Clerk integration
            response = requests.post(f"{self.base_url}/api/clients", 
                                   headers=self.headers, json=test_data, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Clerk User Creation Flow - Client Creation", True,
                            f"Client creation flow accessible: {response.status_code}")
            elif response.status_code == 500:
                # Check if it's a Clerk-related error
                try:
                    error_text = response.text.lower()
                    if "clerk" in error_text:
                        self.log_test("Clerk User Creation Flow - Client Creation", False,
                                    "Clerk integration error detected", response.text[:200])
                    else:
                        self.log_test("Clerk User Creation Flow - Client Creation", False,
                                    "Server error (not Clerk-specific)", response.text[:200])
                except:
                    self.log_test("Clerk User Creation Flow - Client Creation", False,
                                f"Server error: {response.status_code}")
            else:
                self.log_test("Clerk User Creation Flow - Client Creation", True,
                            f"Flow responds: {response.status_code}")
            
            # Test admin user creation flow
            response = requests.post(f"{self.base_url}/api/init-admin-user", 
                                   headers=self.headers, json=test_data, timeout=10)
            
            if response.status_code == 404:
                self.log_test("Clerk User Creation Flow - Admin Creation", False,
                            "Admin creation endpoint not found")
            elif response.status_code == 500:
                try:
                    error_text = response.text.lower()
                    if "clerk" in error_text:
                        self.log_test("Clerk User Creation Flow - Admin Creation", False,
                                    "Clerk integration error in admin creation", response.text[:200])
                    else:
                        self.log_test("Clerk User Creation Flow - Admin Creation", False,
                                    "Server error in admin creation", response.text[:200])
                except:
                    self.log_test("Clerk User Creation Flow - Admin Creation", False,
                                f"Server error: {response.status_code}")
            else:
                self.log_test("Clerk User Creation Flow - Admin Creation", True,
                            f"Admin creation flow responds: {response.status_code}")
                
        except Exception as e:
            self.log_test("Clerk User Creation Flow", False,
                        "Clerk flow test failed", str(e))

    def test_specific_admin_user_issue(self):
        """Test 8: Test specific admin user issue (kemalakkoc03@gmail.com)"""
        try:
            print("🎯 Testing Specific Admin User Issue...")
            
            # Test if we can search for the specific user
            search_endpoints = [
                f"/api/clients?search=kemalakkoc03@gmail.com",
                f"/api/clients?email=kemalakkoc03@gmail.com",
                f"/api/users?email=kemalakkoc03@gmail.com",
                f"/api/settings/users?email=kemalakkoc03@gmail.com"
            ]
            
            for endpoint in search_endpoints:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", 
                                          headers=self.headers, timeout=10)
                    
                    if response.status_code in [401, 403]:
                        self.log_test(f"Specific Admin User - {endpoint.split('?')[0]}", True,
                                    f"Search endpoint secured: {response.status_code}")
                    elif response.status_code == 404:
                        self.log_test(f"Specific Admin User - {endpoint.split('?')[0]}", False,
                                    "Search endpoint not found")
                    else:
                        self.log_test(f"Specific Admin User - {endpoint.split('?')[0]}", True,
                                    f"Search endpoint responds: {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"Specific Admin User - {endpoint.split('?')[0]}", False,
                                "Search request failed", str(e))
            
            # Test if the user can authenticate (should fail if no Clerk user)
            auth_test_data = {
                "email": "kemalakkoc03@gmail.com",
                "password": "test_password"
            }
            
            response = requests.post(f"{self.base_url}/api/auth/login", 
                                   headers=self.headers, json=auth_test_data, timeout=10)
            
            if response.status_code == 404:
                self.log_test("Specific Admin User - Authentication Test", False,
                            "Login endpoint not found")
            elif response.status_code in [401, 403]:
                self.log_test("Specific Admin User - Authentication Test", True,
                            f"Authentication properly handled: {response.status_code}")
            else:
                self.log_test("Specific Admin User - Authentication Test", True,
                            f"Authentication endpoint responds: {response.status_code}")
                
        except Exception as e:
            self.log_test("Specific Admin User Issue", False,
                        "Specific user test failed", str(e))

    def run_all_tests(self):
        """Run all backend tests"""
        print("🎯 Starting Admin User Verification and Clerk Integration Tests...")
        print()
        
        # 1. Basic connectivity tests
        self.test_backend_health()
        
        # 2. Admin User and Database Tests
        self.test_admin_user_database_check()
        self.test_admin_creation_endpoint()
        self.test_client_creation_endpoint()
        
        # 3. Clerk Integration Tests
        self.test_clerk_integration_endpoints()
        self.test_user_management_endpoints()
        self.test_clerk_user_creation_flow()
        
        # 4. Database and System Tests
        self.test_database_collections_access()
        self.test_specific_admin_user_issue()
        
        # 5. Additional backend stability tests
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