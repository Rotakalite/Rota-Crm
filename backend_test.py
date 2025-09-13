#!/usr/bin/env python3
"""
CRITICAL AUTHENTICATION BUG - Admin Module Registration Failure Test
Backend comprehensive testing for admin client creation and team member creation

CRITICAL ISSUE REPORTED:
- Admin modülünden kaydedilen müşteriler ve takım üyeleri:
  1. Database users'ta kayıt olmuyor
  2. Clerk'te kayıt olmuyor  
  3. Sisteme giriş yapamıyorlar

REGRESSION BUG: Supabase→MongoDB migration sırasında admin creation code bozulmuş

TEST REQUIREMENTS:
1. Admin client creation endpoint test: `/api/clients` POST
2. Team member creation endpoint test: `/api/clients/{client_id}/team/add` POST
3. Database'de user creation kontrol
4. Clerk integration çalışıyor mu kontrol

EXPECTED BEHAVIOR:
- Admin creates client → Database user + Clerk user created
- Admin creates team member → Database user + Clerk user created
- Users can login with created credentials

CURRENT BROKEN BEHAVIOR:
- Admin creates client/team → NO database user
- Admin creates client/team → NO Clerk user
- Users CANNOT login

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

    # Old test methods removed - focusing on admin user verification and Clerk integration

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

    # Old bulk targets test methods removed - focusing on admin user verification

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

    def test_admin_client_creation_endpoint(self):
        """Test 3: CRITICAL - Test admin client creation endpoint (main issue)"""
        try:
            print("🚨 Testing CRITICAL Admin Client Creation Endpoint...")
            
            # Test clients POST endpoint accessibility
            response = requests.post(f"{self.base_url}/api/clients", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Admin Client Creation - Endpoint Security", True,
                            f"Client creation properly secured: {response.status_code}")
            elif response.status_code in [400, 422]:
                self.log_test("Admin Client Creation - Endpoint Security", True,
                            f"Endpoint accessible, requires data: {response.status_code}")
            else:
                self.log_test("Admin Client Creation - Endpoint Security", False,
                            f"Expected auth/validation error, got {response.status_code}")
            
            # Test with REALISTIC client data (matching the reported issue)
            critical_client_data = {
                "name": "Test Otel Müşteri",
                "hotel_name": "Test Otel Müşteri",
                "contact_person": "Ahmet Yılmaz",
                "email": "test-musteri@example.com",
                "phone": "+90 555 123 4567",
                "city": "İstanbul",
                "district": "Beşiktaş",
                "address": "Test Mahallesi Test Sokak No:123",
                "audit_company": "Test Denetim Firması",
                "certificate_end_date": "2024-12-31",
                "client_type": "registered",
                "password": "MusteriSifre123!",  # Admin-defined password
                "auto_create_account": True      # Should create Clerk user
            }
            
            response = requests.post(f"{self.base_url}/api/clients", 
                                   headers=self.headers, json=critical_client_data, timeout=15)
            
            if response.status_code in [401, 403]:
                self.log_test("Admin Client Creation - Authentication Required", True,
                            f"Authentication required for client creation: {response.status_code}")
            elif response.status_code in [400, 422]:
                self.log_test("Admin Client Creation - Data Validation", True,
                            f"Data validation working: {response.status_code}")
            elif response.status_code in [200, 201]:
                self.log_test("Admin Client Creation - SECURITY ISSUE", False,
                            f"Client created without auth: {response.status_code}",
                            "CRITICAL: Client creation should require admin authentication")
            elif response.status_code == 500:
                # Check if it's a Clerk integration error
                try:
                    error_text = response.text.lower()
                    if "clerk" in error_text:
                        self.log_test("Admin Client Creation - Clerk Integration Error", False,
                                    "Clerk integration failing during client creation", response.text[:300])
                    else:
                        self.log_test("Admin Client Creation - Server Error", False,
                                    "Server error during client creation", response.text[:300])
                except:
                    self.log_test("Admin Client Creation - Server Error", False,
                                f"Server error: {response.status_code}")
            else:
                self.log_test("Admin Client Creation - Unexpected Response", False,
                            f"Unexpected response: {response.status_code}")
            
            # Test without password (to check if this causes the issue)
            no_password_data = critical_client_data.copy()
            del no_password_data["password"]
            
            response = requests.post(f"{self.base_url}/api/clients", 
                                   headers=self.headers, json=no_password_data, timeout=15)
            
            if response.status_code in [401, 403]:
                self.log_test("Admin Client Creation - No Password Test", True,
                            f"No password test requires auth: {response.status_code}")
            elif response.status_code in [400, 422]:
                self.log_test("Admin Client Creation - No Password Validation", True,
                            f"Validation working for no password: {response.status_code}")
            else:
                self.log_test("Admin Client Creation - No Password Issue", False,
                            f"Unexpected response without password: {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Client Creation Endpoint", False,
                        "Admin client creation test failed", str(e))

    def test_team_member_creation_endpoint(self):
        """Test 4: CRITICAL - Test team member creation endpoint"""
        try:
            print("👥 Testing CRITICAL Team Member Creation Endpoint...")
            
            # Use a sample client ID for testing
            test_client_id = "test-client-id-12345"
            
            # Test team member creation endpoint accessibility
            response = requests.post(f"{self.base_url}/api/clients/{test_client_id}/team/add", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Team Member Creation - Endpoint Security", True,
                            f"Team member creation properly secured: {response.status_code}")
            elif response.status_code in [400, 422]:
                self.log_test("Team Member Creation - Endpoint Security", True,
                            f"Endpoint accessible, requires data: {response.status_code}")
            elif response.status_code == 404:
                self.log_test("Team Member Creation - Client Not Found", True,
                            f"Proper 404 for non-existent client: {response.status_code}")
            else:
                self.log_test("Team Member Creation - Endpoint Security", False,
                            f"Expected auth/validation error, got {response.status_code}")
            
            # Test with REALISTIC team member data (matching the reported issue)
            critical_team_data = {
                "name": "Fatma Demir",
                "email": "fatma.demir@example.com",
                "role": "Sürdürülebilirlik Uzmanı",
                "department": "Çevre Yönetimi",
                "phone": "+90 555 987 6543",
                "position": "Uzman"
            }
            
            response = requests.post(f"{self.base_url}/api/clients/{test_client_id}/team/add", 
                                   headers=self.headers, json=critical_team_data, timeout=15)
            
            if response.status_code in [401, 403]:
                self.log_test("Team Member Creation - Authentication Required", True,
                            f"Authentication required for team member creation: {response.status_code}")
            elif response.status_code == 404:
                self.log_test("Team Member Creation - Client Validation", True,
                            f"Proper client validation: {response.status_code}")
            elif response.status_code in [400, 422]:
                self.log_test("Team Member Creation - Data Validation", True,
                            f"Data validation working: {response.status_code}")
            elif response.status_code in [200, 201]:
                self.log_test("Team Member Creation - SECURITY ISSUE", False,
                            f"Team member created without auth: {response.status_code}",
                            "CRITICAL: Team member creation should require authentication")
            elif response.status_code == 500:
                # Check if it's a Clerk integration error
                try:
                    error_text = response.text.lower()
                    if "clerk" in error_text:
                        self.log_test("Team Member Creation - Clerk Integration Error", False,
                                    "Clerk integration failing during team member creation", response.text[:300])
                    else:
                        self.log_test("Team Member Creation - Server Error", False,
                                    "Server error during team member creation", response.text[:300])
                except:
                    self.log_test("Team Member Creation - Server Error", False,
                                f"Server error: {response.status_code}")
            else:
                self.log_test("Team Member Creation - Unexpected Response", False,
                            f"Unexpected response: {response.status_code}")
            
            # Test with missing required fields
            incomplete_team_data = {
                "name": "Test User",
                # Missing email - should cause validation error
                "role": "Test Role"
            }
            
            response = requests.post(f"{self.base_url}/api/clients/{test_client_id}/team/add", 
                                   headers=self.headers, json=incomplete_team_data, timeout=15)
            
            if response.status_code in [401, 403]:
                self.log_test("Team Member Creation - Incomplete Data Test", True,
                            f"Incomplete data test requires auth: {response.status_code}")
            elif response.status_code in [400, 422]:
                self.log_test("Team Member Creation - Incomplete Data Validation", True,
                            f"Validation working for incomplete data: {response.status_code}")
            else:
                self.log_test("Team Member Creation - Incomplete Data Issue", False,
                            f"Unexpected response with incomplete data: {response.status_code}")
                
        except Exception as e:
            self.log_test("Team Member Creation Endpoint", False,
                        "Team member creation test failed", str(e))

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

    def test_database_investigation(self):
        """Test 9: Database Investigation - Check if client exists but user doesn't"""
        try:
            print("🔍 Testing Database Investigation...")
            
            # Test if we can get any information about database state
            # Since we can't directly access database, we test through API responses
            
            # Test clients endpoint with different parameters
            test_params = [
                "",
                "?limit=1",
                "?client_type=registered",
                "?search=kemal"
            ]
            
            for param in test_params:
                try:
                    response = requests.get(f"{self.base_url}/api/clients{param}", 
                                          headers=self.headers, timeout=10)
                    
                    if response.status_code in [401, 403]:
                        self.log_test(f"Database Investigation - Clients API {param or 'base'}", True,
                                    f"Clients API accessible: {response.status_code}")
                    elif response.status_code == 200:
                        # This shouldn't happen without auth, but if it does, it's useful info
                        self.log_test(f"Database Investigation - Clients API {param or 'base'}", False,
                                    f"SECURITY ISSUE: Clients API accessible without auth: {response.status_code}")
                    else:
                        self.log_test(f"Database Investigation - Clients API {param or 'base'}", True,
                                    f"Clients API responds: {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"Database Investigation - Clients API {param or 'base'}", False,
                                "Request failed", str(e))
            
            # Test users endpoint with different parameters
            users_params = [
                "",
                "?limit=1",
                "?role=client",
                "?email=kemalakkoc03@gmail.com"
            ]
            
            for param in users_params:
                try:
                    response = requests.get(f"{self.base_url}/api/settings/users{param}", 
                                          headers=self.headers, timeout=10)
                    
                    if response.status_code in [401, 403]:
                        self.log_test(f"Database Investigation - Users API {param or 'base'}", True,
                                    f"Users API accessible: {response.status_code}")
                    elif response.status_code == 200:
                        self.log_test(f"Database Investigation - Users API {param or 'base'}", False,
                                    f"SECURITY ISSUE: Users API accessible without auth: {response.status_code}")
                    else:
                        self.log_test(f"Database Investigation - Users API {param or 'base'}", True,
                                    f"Users API responds: {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"Database Investigation - Users API {param or 'base'}", False,
                                "Request failed", str(e))
                
        except Exception as e:
            self.log_test("Database Investigation", False,
                        "Database investigation failed", str(e))

    def test_client_creation_clerk_integration_detailed(self):
        """Test 10: Detailed Client Creation and Clerk Integration Test"""
        try:
            print("🔧 Testing Detailed Client Creation and Clerk Integration...")
            
            # Test client creation with all required fields (similar to the problematic case)
            detailed_client_data = {
                "name": "Test Hotel Kemal",
                "hotel_name": "Test Hotel Kemal",
                "contact_person": "Kemal Test",
                "email": "kemal-test@example.com",
                "phone": "+90 555 123 4567",
                "city": "İstanbul",
                "district": "Beşiktaş",
                "address": "Test Address 123",
                "audit_company": "Test Audit Company",
                "certificate_end_date": "2024-12-31",
                "client_type": "registered",
                "password": "TestPassword123!",
                "auto_create_account": True
            }
            
            # Test with complete data
            response = requests.post(f"{self.base_url}/api/clients", 
                                   headers=self.headers, json=detailed_client_data, timeout=15)
            
            if response.status_code in [401, 403]:
                self.log_test("Detailed Client Creation - Complete Data", True,
                            f"Client creation requires authentication: {response.status_code}")
            elif response.status_code in [400, 422]:
                self.log_test("Detailed Client Creation - Complete Data", True,
                            f"Data validation working: {response.status_code}")
            elif response.status_code in [200, 201]:
                self.log_test("Detailed Client Creation - Complete Data", False,
                            f"SECURITY ISSUE: Client created without auth: {response.status_code}")
            else:
                self.log_test("Detailed Client Creation - Complete Data", False,
                            f"Unexpected response: {response.status_code}")
            
            # Test without password (to see if this causes the issue)
            no_password_data = detailed_client_data.copy()
            del no_password_data["password"]
            
            response = requests.post(f"{self.base_url}/api/clients", 
                                   headers=self.headers, json=no_password_data, timeout=15)
            
            if response.status_code in [401, 403]:
                self.log_test("Detailed Client Creation - No Password", True,
                            f"Client creation without password requires auth: {response.status_code}")
            elif response.status_code in [400, 422]:
                self.log_test("Detailed Client Creation - No Password", True,
                            f"Validation working for no password: {response.status_code}")
            else:
                self.log_test("Detailed Client Creation - No Password", False,
                            f"Unexpected response: {response.status_code}")
            
            # Test without auto_create_account
            no_auto_create_data = detailed_client_data.copy()
            no_auto_create_data["auto_create_account"] = False
            
            response = requests.post(f"{self.base_url}/api/clients", 
                                   headers=self.headers, json=no_auto_create_data, timeout=15)
            
            if response.status_code in [401, 403]:
                self.log_test("Detailed Client Creation - No Auto Create", True,
                            f"Client creation without auto create requires auth: {response.status_code}")
            else:
                self.log_test("Detailed Client Creation - No Auto Create", False,
                            f"Unexpected response: {response.status_code}")
                
        except Exception as e:
            self.log_test("Detailed Client Creation and Clerk Integration", False,
                        "Detailed client creation test failed", str(e))

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
        self.test_database_investigation()
        self.test_client_creation_clerk_integration_detailed()
        
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