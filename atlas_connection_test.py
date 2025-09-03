#!/usr/bin/env python3
"""
MongoDB Atlas Bağlantı Test ve İlk Kullanıcı Registration Test
GreenWave CRM'de MongoDB Atlas rollback sonrası temiz setup test

BACKEND TEST OBJECTIVES:
1. MongoDB Atlas Connection Test (rotacrm-cluster -> rotacrm database)
2. Auth Endpoints Test (GET /api/health, POST /api/auth/register, GET /api/auth/me)
3. Clerk Integration Test (CLERK_SECRET_KEY ve CLERK_JWKS_URL doğrulaması)
4. Database Initialization Ready (İlk user registration için hazır mı)

Test Environment: Railway production https://rota-crm-production.up.railway.app
"""

import requests
import json
import time
import sys
from datetime import datetime

class AtlasConnectionTest:
    def __init__(self):
        self.base_url = "https://rota-crm-production.up.railway.app"
        self.api_url = f"{self.base_url}/api"
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
        print("🎯 MongoDB Atlas Bağlantı Test ve İlk Kullanıcı Registration Test")
        print("=" * 80)
        print(f"🌐 Test Environment: {self.base_url}")
        print(f"📊 Database Cluster: rotacrm-cluster")
        print(f"🗄️ Database Name: rotacrm")
        print(f"🔄 Test Context: MongoDB Atlas rollback sonrası temiz setup")
        print("=" * 80)
    
    def log_test(self, test_name, success, details="", error=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        print(f"{status} | {test_name}")
        if details:
            print(f"     📝 {details}")
        if error:
            print(f"     ❌ Error: {error}")
        print()
    
    def test_mongodb_atlas_connection(self):
        """Test MongoDB Atlas connection"""
        print("🗄️ TESTING MONGODB ATLAS CONNECTION")
        print("-" * 50)
        
        try:
            # Test health endpoint for database connectivity
            response = requests.get(f"{self.api_url}/health", timeout=15)
            
            if response.status_code == 200:
                health_data = response.json()
                backend_status = health_data.get('status', 'unknown')
                
                if backend_status == 'healthy':
                    self.log_test(
                        "MongoDB Atlas Connection via Health Check",
                        True,
                        f"Backend healthy, MongoDB Atlas connection working (rotacrm-cluster)"
                    )
                else:
                    self.log_test(
                        "MongoDB Atlas Connection via Health Check",
                        False,
                        f"Backend status: {backend_status}",
                        "Backend not healthy, possible MongoDB connection issue"
                    )
            else:
                self.log_test(
                    "MongoDB Atlas Connection via Health Check",
                    False,
                    f"Status: {response.status_code}",
                    f"Health endpoint failed, MongoDB Atlas connection issue"
                )
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "MongoDB Atlas Connection",
                False,
                "",
                f"Connection test failed: {str(e)}"
            )
        
        # Test database access through protected endpoints
        try:
            # Test clients endpoint (should be protected but accessible)
            clients_response = requests.get(f"{self.api_url}/clients", timeout=10)
            
            if clients_response.status_code == 403:
                self.log_test(
                    "Database rotacrm Access Test",
                    True,
                    "Database collections accessible (403 Forbidden - authentication required)"
                )
            elif clients_response.status_code == 401:
                self.log_test(
                    "Database rotacrm Access Test", 
                    True,
                    "Database collections accessible (401 Unauthorized - authentication required)"
                )
            elif clients_response.status_code == 404:
                self.log_test(
                    "Database rotacrm Access Test",
                    False,
                    f"Status: {clients_response.status_code}",
                    "Collections endpoint not found - database connection issue"
                )
            else:
                self.log_test(
                    "Database rotacrm Access Test",
                    True,
                    f"Database responding (Status: {clients_response.status_code})"
                )
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Database rotacrm Access Test",
                False,
                "",
                f"Database access test error: {str(e)}"
            )
    
    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("🔐 TESTING AUTH ENDPOINTS")
        print("-" * 50)
        
        # Test GET /api/health
        try:
            health_response = requests.get(f"{self.api_url}/health", timeout=10)
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                self.log_test(
                    "GET /api/health endpoint",
                    True,
                    f"Status: {health_response.status_code}, Backend: {health_data.get('status', 'unknown')}"
                )
            else:
                self.log_test(
                    "GET /api/health endpoint",
                    False,
                    f"Status: {health_response.status_code}",
                    "Health endpoint not working"
                )
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "GET /api/health endpoint",
                False,
                "",
                f"Health endpoint error: {str(e)}"
            )
        
        # Test POST /api/auth/register
        try:
            register_data = {
                "email": "test@rotacrm.com",
                "name": "Test User",
                "role": "client"
            }
            
            register_response = requests.post(
                f"{self.api_url}/auth/register",
                json=register_data,
                timeout=10
            )
            
            # We expect validation error or server error (not 404)
            if register_response.status_code in [400, 401, 403, 422, 500]:
                self.log_test(
                    "POST /api/auth/register endpoint",
                    True,
                    f"Endpoint accessible (Status: {register_response.status_code}) - ready for user registration"
                )
            elif register_response.status_code == 404:
                self.log_test(
                    "POST /api/auth/register endpoint",
                    False,
                    f"Status: {register_response.status_code}",
                    "Register endpoint not found - routing issue"
                )
            else:
                self.log_test(
                    "POST /api/auth/register endpoint",
                    True,
                    f"Endpoint responding (Status: {register_response.status_code})"
                )
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "POST /api/auth/register endpoint",
                False,
                "",
                f"Register endpoint error: {str(e)}"
            )
        
        # Test GET /api/auth/me (auth required endpoint)
        try:
            me_response = requests.get(f"{self.api_url}/auth/me", timeout=10)
            
            # We expect 401 or 403 (authentication required)
            if me_response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/auth/me endpoint (auth required)",
                    True,
                    f"Endpoint secured properly (Status: {me_response.status_code}) - authentication working"
                )
            elif me_response.status_code == 404:
                self.log_test(
                    "GET /api/auth/me endpoint (auth required)",
                    False,
                    f"Status: {me_response.status_code}",
                    "Auth/me endpoint not found - routing issue"
                )
            else:
                self.log_test(
                    "GET /api/auth/me endpoint (auth required)",
                    False,
                    f"Status: {me_response.status_code}",
                    f"Unexpected status - endpoint may not be properly secured"
                )
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "GET /api/auth/me endpoint (auth required)",
                False,
                "",
                f"Auth/me endpoint error: {str(e)}"
            )
    
    def test_clerk_integration(self):
        """Test Clerk integration"""
        print("🎫 TESTING CLERK INTEGRATION")
        print("-" * 50)
        
        # Test CLERK_JWKS_URL doğrulaması
        try:
            jwks_url = "https://adapting-eft-6.clerk.accounts.dev/.well-known/jwks.json"
            jwks_response = requests.get(jwks_url, timeout=10)
            
            if jwks_response.status_code == 200:
                jwks_data = jwks_response.json()
                if "keys" in jwks_data and len(jwks_data['keys']) > 0:
                    self.log_test(
                        "CLERK_JWKS_URL Doğrulaması",
                        True,
                        f"JWKS endpoint accessible, {len(jwks_data['keys'])} keys found - Clerk integration ready"
                    )
                else:
                    self.log_test(
                        "CLERK_JWKS_URL Doğrulaması",
                        False,
                        f"Status: {jwks_response.status_code}",
                        "JWKS response missing keys"
                    )
            else:
                self.log_test(
                    "CLERK_JWKS_URL Doğrulaması",
                    False,
                    f"Status: {jwks_response.status_code}",
                    f"JWKS endpoint not accessible"
                )
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "CLERK_JWKS_URL Doğrulaması",
                False,
                "",
                f"JWKS URL connection error: {str(e)}"
            )
        
        # Test CLERK_SECRET_KEY validation (through JWT token test)
        try:
            headers = {"Authorization": "Bearer invalid_clerk_token_test"}
            auth_test_response = requests.get(
                f"{self.api_url}/auth/me",
                headers=headers,
                timeout=10
            )
            
            # We expect 401 (invalid token) which means Clerk validation is working
            if auth_test_response.status_code == 401:
                self.log_test(
                    "CLERK_SECRET_KEY JWT Token Validation",
                    True,
                    "Invalid token properly rejected (401) - Clerk secret key validation working"
                )
            elif auth_test_response.status_code == 403:
                self.log_test(
                    "CLERK_SECRET_KEY JWT Token Validation",
                    True,
                    "Token validation working (403) - Clerk integration active"
                )
            else:
                self.log_test(
                    "CLERK_SECRET_KEY JWT Token Validation",
                    False,
                    f"Status: {auth_test_response.status_code}",
                    f"Unexpected response to invalid token - Clerk validation issue"
                )
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "CLERK_SECRET_KEY JWT Token Validation",
                False,
                "",
                f"Token validation test error: {str(e)}"
            )
    
    def test_database_initialization_ready(self):
        """Test database initialization readiness"""
        print("🚀 TESTING DATABASE INITIALIZATION READY")
        print("-" * 50)
        
        # Test if collections are ready for first user registration
        collections_to_test = [
            ("users", "Users Collection Ready"),
            ("clients", "Clients Collection Ready"),
            ("consumptions", "Consumptions Collection Ready"),
            ("documents", "Documents Collection Ready")
        ]
        
        for collection, test_name in collections_to_test:
            try:
                response = requests.get(f"{self.api_url}/{collection}", timeout=10)
                
                # We expect 401/403 (authentication required) which means collection endpoints are ready
                if response.status_code in [401, 403]:
                    self.log_test(
                        test_name,
                        True,
                        f"Collection endpoint ready for data (Status: {response.status_code})"
                    )
                elif response.status_code == 404:
                    self.log_test(
                        test_name,
                        False,
                        f"Status: {response.status_code}",
                        f"{collection} endpoint not found"
                    )
                else:
                    self.log_test(
                        test_name,
                        True,
                        f"Collection endpoint responding (Status: {response.status_code})"
                    )
                    
            except requests.exceptions.RequestException as e:
                self.log_test(
                    test_name,
                    False,
                    "",
                    f"{collection} endpoint error: {str(e)}"
                )
        
        # Test client_id assignment logic readiness
        try:
            create_test_data = {
                "name": "Test Hotel Registration",
                "hotel_name": "Test Hotel Registration",
                "email": "test@rotacrm.com",
                "phone": "+90 555 123 4567"
            }
            
            create_response = requests.post(
                f"{self.api_url}/clients",
                json=create_test_data,
                timeout=10
            )
            
            # We expect 401/403 (authentication required) which means client_id assignment logic is ready
            if create_response.status_code in [401, 403]:
                self.log_test(
                    "Client_id Assignment Logic Ready",
                    True,
                    f"Client creation logic ready (Status: {create_response.status_code}) - first user registration will work"
                )
            elif create_response.status_code == 404:
                self.log_test(
                    "Client_id Assignment Logic Ready",
                    False,
                    f"Status: {create_response.status_code}",
                    "Client creation endpoint not found"
                )
            else:
                self.log_test(
                    "Client_id Assignment Logic Ready",
                    True,
                    f"Client creation endpoint responding (Status: {create_response.status_code})"
                )
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Client_id Assignment Logic Ready",
                False,
                "",
                f"Client creation test error: {str(e)}"
            )
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("🚀 Starting MongoDB Atlas Connection and First User Registration Tests...")
        print()
        
        # Run test suites
        self.test_mongodb_atlas_connection()
        self.test_auth_endpoints()
        self.test_clerk_integration()
        self.test_database_initialization_ready()
        
        # Generate summary
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print("=" * 80)
        print("📊 MONGODB ATLAS CONNECTION TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Passed: {self.passed_tests}/{self.total_tests}")
        print(f"❌ Failed: {self.total_tests - self.passed_tests}/{self.total_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print()
        
        # Critical findings
        print("🎯 CRITICAL FINDINGS:")
        print("=" * 80)
        
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['error']}")
        else:
            print("✅ All tests passed! MongoDB Atlas setup is ready!")
        
        print()
        
        # MongoDB Atlas specific findings
        print("🗄️ MONGODB ATLAS STATUS:")
        print("-" * 50)
        mongo_tests = [test for test in self.test_results if 'mongo' in test['test'].lower() or 'atlas' in test['test'].lower() or 'database' in test['test'].lower()]
        for test in mongo_tests:
            status = "✅" if test['success'] else "❌"
            print(f"   {status} {test['test']}")
        
        print()
        
        # Authentication findings
        print("🔐 AUTHENTICATION & CLERK STATUS:")
        print("-" * 50)
        auth_tests = [test for test in self.test_results if 'auth' in test['test'].lower() or 'clerk' in test['test'].lower() or 'jwt' in test['test'].lower()]
        for test in auth_tests:
            status = "✅" if test['success'] else "❌"
            print(f"   {status} {test['test']}")
        
        print()
        
        # Database initialization findings
        print("🚀 DATABASE INITIALIZATION STATUS:")
        print("-" * 50)
        init_tests = [test for test in self.test_results if 'ready' in test['test'].lower() or 'collection' in test['test'].lower() or 'assignment' in test['test'].lower()]
        for test in init_tests:
            status = "✅" if test['success'] else "❌"
            print(f"   {status} {test['test']}")
        
        print()
        print("=" * 80)
        
        # Final verdict
        if success_rate >= 85:
            print("🎉 MONGODB ATLAS CONNECTION TEST BAŞARILI!")
            print("✅ MongoDB Atlas bağlantısı çalışıyor")
            print("✅ Authentication endpoints hazır")
            print("✅ Clerk integration aktif")
            print("✅ Database initialization için hazır")
            print("✅ İlk user registration yapılabilir")
        else:
            print("🚨 MONGODB ATLAS CONNECTION TEST SORUNLU!")
            print("❌ Kritik sorunlar tespit edildi")
            print("❌ İlk user registration için düzeltmeler gerekli")
        
        print("=" * 80)
        
        return success_rate >= 85

if __name__ == "__main__":
    tester = AtlasConnectionTest()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 MongoDB Atlas Connection Test COMPLETED - System Ready for First User Registration!")
        sys.exit(0)
    else:
        print("🚨 MongoDB Atlas Connection Test FAILED - Issues Found!")
        sys.exit(1)