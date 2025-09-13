#!/usr/bin/env python3
"""
CRITICAL AUTHENTICATION BUG - Focused Test
Testing the specific admin client creation and Clerk integration issue

CRITICAL ISSUE:
- Admin creates client → NO database user created
- Admin creates client → NO Clerk user created  
- Users cannot login

This test will simulate the exact admin workflow to identify the bug.
"""

import requests
import json
import time
import sys
from datetime import datetime

class CriticalAuthBugTester:
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
            'User-Agent': 'Critical-Auth-Bug-Tester/1.0'
        }
        
        print(f"🚨 CRITICAL AUTHENTICATION BUG TESTER")
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

    def test_clerk_configuration(self):
        """Test 1: Check Clerk configuration"""
        try:
            print("🔐 Testing Clerk Configuration...")
            
            # Test JWKS endpoint
            clerk_jwks_url = "https://adapting-eft-6.clerk.accounts.dev/.well-known/jwks.json"
            response = requests.get(clerk_jwks_url, timeout=10)
            
            if response.status_code == 200:
                jwks_data = response.json()
                keys_count = len(jwks_data.get('keys', []))
                self.log_test("Clerk Configuration - JWKS Endpoint", True,
                            f"JWKS accessible, {keys_count} keys found")
            else:
                self.log_test("Clerk Configuration - JWKS Endpoint", False,
                            f"JWKS not accessible: {response.status_code}")
            
            # Test if backend can access Clerk
            response = requests.get(f"{self.base_url}/api/health", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                self.log_test("Clerk Configuration - Backend Health", True,
                            f"Backend healthy: {health_data.get('status', 'unknown')}")
            else:
                self.log_test("Clerk Configuration - Backend Health", False,
                            f"Backend not healthy: {response.status_code}")
                
        except Exception as e:
            self.log_test("Clerk Configuration", False,
                        "Clerk configuration test failed", str(e))

    def test_admin_client_creation_flow(self):
        """Test 2: Test the exact admin client creation flow"""
        try:
            print("🏢 Testing Admin Client Creation Flow...")
            
            # Step 1: Test client creation endpoint accessibility
            response = requests.post(f"{self.base_url}/api/clients", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Admin Client Creation Flow - Endpoint Security", True,
                            f"Endpoint properly secured: {response.status_code}")
            else:
                self.log_test("Admin Client Creation Flow - Endpoint Security", False,
                            f"Security issue: {response.status_code}")
            
            # Step 2: Test with realistic client data (the exact scenario from the bug report)
            realistic_client_data = {
                "name": "Kritik Test Oteli",
                "hotel_name": "Kritik Test Oteli", 
                "contact_person": "Kemal Akkoç",
                "email": "kritik-test@example.com",
                "phone": "+90 555 123 4567",
                "city": "İstanbul",
                "district": "Beşiktaş", 
                "address": "Test Mahallesi Test Sokak No:123",
                "audit_company": "Test Denetim Firması",
                "certificate_end_date": "2024-12-31",
                "client_type": "registered",
                "password": "KritikTest123!",  # Admin-defined password
                "auto_create_account": True    # Should trigger Clerk user creation
            }
            
            response = requests.post(f"{self.base_url}/api/clients", 
                                   headers=self.headers, json=realistic_client_data, timeout=15)
            
            if response.status_code in [401, 403]:
                self.log_test("Admin Client Creation Flow - Authentication Check", True,
                            f"Authentication required: {response.status_code}")
            elif response.status_code == 500:
                # This could be the Clerk integration error
                try:
                    error_text = response.text
                    if "clerk" in error_text.lower():
                        self.log_test("Admin Client Creation Flow - Clerk Integration Error", False,
                                    "CRITICAL: Clerk integration failing", error_text[:500])
                    else:
                        self.log_test("Admin Client Creation Flow - Server Error", False,
                                    "Server error during client creation", error_text[:500])
                except:
                    self.log_test("Admin Client Creation Flow - Server Error", False,
                                f"Server error: {response.status_code}")
            else:
                self.log_test("Admin Client Creation Flow - Unexpected Response", False,
                            f"Unexpected response: {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Client Creation Flow", False,
                        "Admin client creation flow test failed", str(e))

    def test_team_member_creation_flow(self):
        """Test 3: Test the exact team member creation flow"""
        try:
            print("👥 Testing Team Member Creation Flow...")
            
            # Use a realistic client ID for testing
            test_client_id = "test-client-12345"
            
            # Step 1: Test team member creation endpoint accessibility
            response = requests.post(f"{self.base_url}/api/clients/{test_client_id}/team/add", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Team Member Creation Flow - Endpoint Security", True,
                            f"Endpoint properly secured: {response.status_code}")
            elif response.status_code == 404:
                self.log_test("Team Member Creation Flow - Client Validation", True,
                            f"Proper client validation: {response.status_code}")
            else:
                self.log_test("Team Member Creation Flow - Endpoint Security", False,
                            f"Security issue: {response.status_code}")
            
            # Step 2: Test with realistic team member data
            realistic_team_data = {
                "name": "Fatma Demir",
                "email": "fatma.demir@kritiktest.com",
                "role": "Sürdürülebilirlik Uzmanı",
                "department": "Çevre Yönetimi",
                "phone": "+90 555 987 6543",
                "position": "Uzman"
            }
            
            response = requests.post(f"{self.base_url}/api/clients/{test_client_id}/team/add", 
                                   headers=self.headers, json=realistic_team_data, timeout=15)
            
            if response.status_code in [401, 403]:
                self.log_test("Team Member Creation Flow - Authentication Check", True,
                            f"Authentication required: {response.status_code}")
            elif response.status_code == 404:
                self.log_test("Team Member Creation Flow - Client Not Found", True,
                            f"Proper client validation: {response.status_code}")
            elif response.status_code == 500:
                # This could be the Clerk integration error
                try:
                    error_text = response.text
                    if "clerk" in error_text.lower():
                        self.log_test("Team Member Creation Flow - Clerk Integration Error", False,
                                    "CRITICAL: Clerk integration failing", error_text[:500])
                    else:
                        self.log_test("Team Member Creation Flow - Server Error", False,
                                    "Server error during team member creation", error_text[:500])
                except:
                    self.log_test("Team Member Creation Flow - Server Error", False,
                                f"Server error: {response.status_code}")
            else:
                self.log_test("Team Member Creation Flow - Unexpected Response", False,
                            f"Unexpected response: {response.status_code}")
                
        except Exception as e:
            self.log_test("Team Member Creation Flow", False,
                        "Team member creation flow test failed", str(e))

    def test_database_user_creation_endpoints(self):
        """Test 4: Test database user creation endpoints"""
        try:
            print("🗄️ Testing Database User Creation Endpoints...")
            
            # Test users endpoint
            response = requests.get(f"{self.base_url}/api/settings/users", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Database User Creation - Users Endpoint", True,
                            f"Users endpoint secured: {response.status_code}")
            elif response.status_code == 404:
                self.log_test("Database User Creation - Users Endpoint Missing", False,
                            "CRITICAL: Users endpoint not found!")
            else:
                self.log_test("Database User Creation - Users Endpoint", True,
                            f"Users endpoint responds: {response.status_code}")
            
            # Test user creation
            test_user_data = {
                "email": "test-user-creation@example.com",
                "name": "Test User Creation",
                "role": "client",
                "clerk_user_id": "test_clerk_id_12345"
            }
            
            response = requests.post(f"{self.base_url}/api/settings/users", 
                                   headers=self.headers, json=test_user_data, timeout=15)
            
            if response.status_code in [401, 403]:
                self.log_test("Database User Creation - User Creation Security", True,
                            f"User creation secured: {response.status_code}")
            elif response.status_code == 404:
                self.log_test("Database User Creation - User Creation Missing", False,
                            "CRITICAL: User creation endpoint not found!")
            elif response.status_code == 500:
                try:
                    error_text = response.text
                    self.log_test("Database User Creation - Server Error", False,
                                "Server error during user creation", error_text[:500])
                except:
                    self.log_test("Database User Creation - Server Error", False,
                                f"Server error: {response.status_code}")
            else:
                self.log_test("Database User Creation - Unexpected Response", False,
                            f"Unexpected response: {response.status_code}")
                
        except Exception as e:
            self.log_test("Database User Creation Endpoints", False,
                        "Database user creation test failed", str(e))

    def test_clerk_user_creation_simulation(self):
        """Test 5: Simulate Clerk user creation issue"""
        try:
            print("🔄 Testing Clerk User Creation Simulation...")
            
            # Test if there's a specific Clerk user creation endpoint
            clerk_endpoints = [
                "/api/auth/create-user",
                "/api/clerk/create-user", 
                "/api/admin/create-user",
                "/api/users/create"
            ]
            
            for endpoint in clerk_endpoints:
                try:
                    response = requests.post(f"{self.base_url}{endpoint}", 
                                           headers=self.headers, timeout=10)
                    
                    if response.status_code == 404:
                        self.log_test(f"Clerk User Creation - {endpoint}", False,
                                    f"Endpoint not found: {endpoint}")
                    elif response.status_code in [401, 403]:
                        self.log_test(f"Clerk User Creation - {endpoint}", True,
                                    f"Endpoint secured: {response.status_code}")
                    else:
                        self.log_test(f"Clerk User Creation - {endpoint}", True,
                                    f"Endpoint responds: {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"Clerk User Creation - {endpoint}", False,
                                "Request failed", str(e))
            
            # Test if there's a repair endpoint for Clerk integration
            response = requests.post(f"{self.base_url}/api/repair-admin-clerk", 
                                   headers=self.headers, timeout=15)
            
            if response.status_code == 500:
                try:
                    error_text = response.text
                    self.log_test("Clerk User Creation - Repair Endpoint Error", False,
                                "CRITICAL: Clerk repair endpoint failing", error_text[:500])
                except:
                    self.log_test("Clerk User Creation - Repair Endpoint Error", False,
                                f"Clerk repair endpoint error: {response.status_code}")
            elif response.status_code == 404:
                self.log_test("Clerk User Creation - Repair Endpoint Missing", False,
                            "Clerk repair endpoint not found")
            else:
                self.log_test("Clerk User Creation - Repair Endpoint", True,
                            f"Clerk repair endpoint responds: {response.status_code}")
                
        except Exception as e:
            self.log_test("Clerk User Creation Simulation", False,
                        "Clerk user creation simulation failed", str(e))

    def test_authentication_endpoints(self):
        """Test 6: Test authentication endpoints"""
        try:
            print("🔐 Testing Authentication Endpoints...")
            
            # Test login endpoint
            response = requests.post(f"{self.base_url}/api/auth/login", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code == 404:
                self.log_test("Authentication Endpoints - Login Missing", False,
                            "CRITICAL: Login endpoint not found!")
            elif response.status_code in [400, 422]:
                self.log_test("Authentication Endpoints - Login", True,
                            f"Login endpoint accessible: {response.status_code}")
            else:
                self.log_test("Authentication Endpoints - Login", True,
                            f"Login endpoint responds: {response.status_code}")
            
            # Test register endpoint
            response = requests.post(f"{self.base_url}/api/auth/register", 
                                   headers=self.headers, timeout=10)
            
            if response.status_code == 404:
                self.log_test("Authentication Endpoints - Register Missing", False,
                            "Register endpoint not found")
            elif response.status_code in [400, 422, 405]:
                self.log_test("Authentication Endpoints - Register", True,
                            f"Register endpoint accessible: {response.status_code}")
            else:
                self.log_test("Authentication Endpoints - Register", True,
                            f"Register endpoint responds: {response.status_code}")
            
            # Test me endpoint
            response = requests.get(f"{self.base_url}/api/auth/me", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Authentication Endpoints - Me", True,
                            f"Me endpoint secured: {response.status_code}")
            else:
                self.log_test("Authentication Endpoints - Me", False,
                            f"Me endpoint security issue: {response.status_code}")
                
        except Exception as e:
            self.log_test("Authentication Endpoints", False,
                        "Authentication endpoints test failed", str(e))

    def run_critical_tests(self):
        """Run all critical authentication bug tests"""
        print("🚨 Starting CRITICAL Authentication Bug Analysis...")
        print()
        
        # Run focused tests
        self.test_clerk_configuration()
        self.test_admin_client_creation_flow()
        self.test_team_member_creation_flow()
        self.test_database_user_creation_endpoints()
        self.test_clerk_user_creation_simulation()
        self.test_authentication_endpoints()
        
        # Print summary
        self.print_summary()
        
        return self.test_results

    def print_summary(self):
        """Print test summary with critical analysis"""
        print()
        print("=" * 80)
        print("🚨 CRITICAL AUTHENTICATION BUG ANALYSIS")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📈 Total: {self.total_tests}")
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        print()
        
        # Critical issues analysis
        critical_issues = []
        for result in self.test_results:
            if not result['success'] and 'CRITICAL' in result['details']:
                critical_issues.append(result)
        
        if critical_issues:
            print("🚨 CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"   • {issue['test']}")
                print(f"     {issue['details']}")
            print()
        
        # Print failed tests details
        if self.failed_tests > 0:
            print("❌ ALL FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}")
                    if result['error']:
                        print(f"     Error: {result['error']}")
            print()
        
        # Root cause analysis
        print("🔍 ROOT CAUSE ANALYSIS:")
        if any("Clerk" in result['test'] and not result['success'] for result in self.test_results):
            print("   • Clerk integration issues detected")
        if any("User Creation" in result['test'] and not result['success'] for result in self.test_results):
            print("   • Database user creation problems detected")
        if any("Authentication" in result['test'] and not result['success'] for result in self.test_results):
            print("   • Authentication endpoint issues detected")
        
        print("=" * 80)

def main():
    """Main test execution"""
    tester = CriticalAuthBugTester()
    
    try:
        results = tester.run_critical_tests()
        
        # Save results to file
        with open('/app/critical_auth_bug_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        print(f"📄 Critical test results saved to: /app/critical_auth_bug_results.json")
        
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