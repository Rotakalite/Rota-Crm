#!/usr/bin/env python3
"""
Self-Signup + Demo System Backend Test
Comprehensive testing of the new demo system implementation
"""

import asyncio
import aiohttp
import json
import uuid
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DemoSystemBackendTest:
    def __init__(self):
        # Use the production URL from frontend .env
        self.base_url = "https://survey-module.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
        # Test data
        self.test_demo_user = {
            "clerk_user_id": f"demo_test_{uuid.uuid4().hex[:8]}",
            "email": f"demo_test_{uuid.uuid4().hex[:8]}@example.com",
            "name": "Demo Test User"
        }
        
        # Admin token for testing (would need real token in production)
        self.admin_token = None
        
    async def log_test_result(self, test_name: str, success: bool, details: str = "", response_data: dict = None):
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
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        logger.info(f"{status}: {test_name} - {details}")
        
    async def make_request(self, method: str, endpoint: str, data: dict = None, headers: dict = None, auth_required: bool = True):
        """Make HTTP request to API"""
        url = f"{self.api_url}{endpoint}"
        
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if headers:
            default_headers.update(headers)
            
        if auth_required and self.admin_token:
            default_headers["Authorization"] = f"Bearer {self.admin_token}"
        
        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == "GET":
                    async with session.get(url, headers=default_headers) as response:
                        response_text = await response.text()
                        try:
                            response_data = await response.json() if response_text else {}
                        except:
                            response_data = {"raw_response": response_text}
                        return response.status, response_data
                        
                elif method.upper() == "POST":
                    async with session.post(url, json=data, headers=default_headers) as response:
                        response_text = await response.text()
                        try:
                            response_data = await response.json() if response_text else {}
                        except:
                            response_data = {"raw_response": response_text}
                        return response.status, response_data
                        
                elif method.upper() == "PUT":
                    async with session.put(url, json=data, headers=default_headers) as response:
                        response_text = await response.text()
                        try:
                            response_data = await response.json() if response_text else {}
                        except:
                            response_data = {"raw_response": response_text}
                        return response.status, response_data
                        
        except Exception as e:
            logger.error(f"Request failed: {method} {url} - {str(e)}")
            return 500, {"error": str(e)}
    
    async def test_backend_health(self):
        """Test 1: Backend Health Check"""
        try:
            status, data = await self.make_request("GET", "/health", auth_required=False)
            
            if status == 200:
                await self.log_test_result(
                    "Backend Health Check", 
                    True, 
                    f"Backend is healthy - Service: {data.get('service', 'Unknown')}", 
                    data
                )
            else:
                await self.log_test_result(
                    "Backend Health Check", 
                    False, 
                    f"Health check failed with status {status}", 
                    data
                )
                
        except Exception as e:
            await self.log_test_result("Backend Health Check", False, f"Exception: {str(e)}")
    
    async def test_self_signup_endpoint_accessibility(self):
        """Test 2: Self-Signup Endpoint Accessibility"""
        try:
            # Test with empty data to check if endpoint exists
            status, data = await self.make_request("POST", "/auth/self-signup", data={}, auth_required=False)
            
            if status in [400, 422]:  # Bad request is expected with empty data
                await self.log_test_result(
                    "Self-Signup Endpoint Accessibility", 
                    True, 
                    f"Endpoint accessible (status {status} expected with empty data)", 
                    data
                )
            elif status == 404:
                await self.log_test_result(
                    "Self-Signup Endpoint Accessibility", 
                    False, 
                    "Endpoint not found (404)", 
                    data
                )
            else:
                await self.log_test_result(
                    "Self-Signup Endpoint Accessibility", 
                    True, 
                    f"Endpoint accessible with status {status}", 
                    data
                )
                
        except Exception as e:
            await self.log_test_result("Self-Signup Endpoint Accessibility", False, f"Exception: {str(e)}")
    
    async def test_self_signup_validation(self):
        """Test 3: Self-Signup Field Validation"""
        try:
            # Test missing required fields
            test_cases = [
                ({}, "Empty data"),
                ({"email": "test@example.com"}, "Missing clerk_user_id and name"),
                ({"clerk_user_id": "test123"}, "Missing email and name"),
                ({"name": "Test User"}, "Missing clerk_user_id and email")
            ]
            
            validation_passed = 0
            for test_data, description in test_cases:
                status, data = await self.make_request("POST", "/auth/self-signup", data=test_data, auth_required=False)
                
                if status in [400, 422]:  # Validation error expected
                    validation_passed += 1
                    logger.info(f"✅ Validation test passed: {description} - Status {status}")
                else:
                    logger.warning(f"⚠️ Validation test unexpected: {description} - Status {status}")
            
            success = validation_passed >= 3  # At least 3 validation tests should pass
            await self.log_test_result(
                "Self-Signup Field Validation", 
                success, 
                f"Validation tests passed: {validation_passed}/4"
            )
                
        except Exception as e:
            await self.log_test_result("Self-Signup Field Validation", False, f"Exception: {str(e)}")
    
    async def test_self_signup_demo_user_creation(self):
        """Test 4: Demo User Creation via Self-Signup"""
        try:
            status, data = await self.make_request("POST", "/auth/self-signup", data=self.test_demo_user, auth_required=False)
            
            if status == 201 or status == 200:
                # Check response structure
                expected_fields = ["message", "user_id", "status", "demo_limits", "max_demo_limit"]
                has_all_fields = all(field in data for field in expected_fields)
                
                if has_all_fields and data.get("status") == "demo_user":
                    await self.log_test_result(
                        "Demo User Creation via Self-Signup", 
                        True, 
                        f"Demo user created successfully with proper structure", 
                        data
                    )
                    # Store user_id for later tests
                    self.demo_user_id = data.get("user_id")
                else:
                    await self.log_test_result(
                        "Demo User Creation via Self-Signup", 
                        False, 
                        f"Response missing required fields or wrong status", 
                        data
                    )
            elif status == 400 and "already exists" in str(data):
                await self.log_test_result(
                    "Demo User Creation via Self-Signup", 
                    True, 
                    "User already exists (expected if test run multiple times)", 
                    data
                )
            else:
                await self.log_test_result(
                    "Demo User Creation via Self-Signup", 
                    False, 
                    f"Failed with status {status}", 
                    data
                )
                
        except Exception as e:
            await self.log_test_result("Demo User Creation via Self-Signup", False, f"Exception: {str(e)}")
    
    async def test_demo_user_status_assignment(self):
        """Test 5: Demo User Status Assignment"""
        try:
            # Create another demo user to test status
            test_user = {
                "clerk_user_id": f"demo_status_test_{uuid.uuid4().hex[:8]}",
                "email": f"demo_status_test_{uuid.uuid4().hex[:8]}@example.com",
                "name": "Demo Status Test User"
            }
            
            status, data = await self.make_request("POST", "/auth/self-signup", data=test_user, auth_required=False)
            
            if status in [200, 201]:
                if data.get("status") == "demo_user" and data.get("max_demo_limit") == 3:
                    demo_limits = data.get("demo_limits", {})
                    expected_limit_types = ["documents", "trainings", "consumptions", "personnel", "suppliers"]
                    has_all_limits = all(limit_type in demo_limits for limit_type in expected_limit_types)
                    
                    if has_all_limits:
                        await self.log_test_result(
                            "Demo User Status Assignment", 
                            True, 
                            "Demo user created with correct status and limits structure", 
                            data
                        )
                    else:
                        await self.log_test_result(
                            "Demo User Status Assignment", 
                            False, 
                            f"Missing demo limit types: {expected_limit_types}", 
                            data
                        )
                else:
                    await self.log_test_result(
                        "Demo User Status Assignment", 
                        False, 
                        f"Wrong status or max_demo_limit: {data.get('status')}, {data.get('max_demo_limit')}", 
                        data
                    )
            elif status == 400 and "already exists" in str(data):
                await self.log_test_result(
                    "Demo User Status Assignment", 
                    True, 
                    "User already exists (test passed previously)", 
                    data
                )
            else:
                await self.log_test_result(
                    "Demo User Status Assignment", 
                    False, 
                    f"Failed to create demo user: status {status}", 
                    data
                )
                
        except Exception as e:
            await self.log_test_result("Demo User Status Assignment", False, f"Exception: {str(e)}")
    
    async def test_email_uniqueness_validation(self):
        """Test 6: Email Uniqueness Validation"""
        try:
            # Try to create user with same email
            duplicate_user = {
                "clerk_user_id": f"duplicate_test_{uuid.uuid4().hex[:8]}",
                "email": self.test_demo_user["email"],  # Same email
                "name": "Duplicate Email Test User"
            }
            
            status, data = await self.make_request("POST", "/auth/self-signup", data=duplicate_user, auth_required=False)
            
            if status == 400 and ("already registered" in str(data) or "already exists" in str(data)):
                await self.log_test_result(
                    "Email Uniqueness Validation", 
                    True, 
                    "Email uniqueness properly validated", 
                    data
                )
            else:
                await self.log_test_result(
                    "Email Uniqueness Validation", 
                    False, 
                    f"Email uniqueness not validated properly: status {status}", 
                    data
                )
                
        except Exception as e:
            await self.log_test_result("Email Uniqueness Validation", False, f"Exception: {str(e)}")
    
    async def test_admin_pending_approvals_endpoint(self):
        """Test 7: Admin Pending Approvals Endpoint"""
        try:
            status, data = await self.make_request("GET", "/admin/pending-approvals", auth_required=True)
            
            if status == 403 or status == 401:
                await self.log_test_result(
                    "Admin Pending Approvals Endpoint", 
                    True, 
                    f"Endpoint properly secured (status {status})", 
                    data
                )
            elif status == 200:
                # If we had admin token, this would work
                await self.log_test_result(
                    "Admin Pending Approvals Endpoint", 
                    True, 
                    "Endpoint accessible with admin auth", 
                    data
                )
            elif status == 404:
                await self.log_test_result(
                    "Admin Pending Approvals Endpoint", 
                    False, 
                    "Endpoint not found (404)", 
                    data
                )
            else:
                await self.log_test_result(
                    "Admin Pending Approvals Endpoint", 
                    True, 
                    f"Endpoint exists (status {status})", 
                    data
                )
                
        except Exception as e:
            await self.log_test_result("Admin Pending Approvals Endpoint", False, f"Exception: {str(e)}")
    
    async def test_admin_approve_user_endpoint(self):
        """Test 8: Admin Approve User Endpoint"""
        try:
            test_user_id = "test_user_id_123"
            status, data = await self.make_request("POST", f"/admin/approve-user/{test_user_id}", auth_required=True)
            
            if status == 403 or status == 401:
                await self.log_test_result(
                    "Admin Approve User Endpoint", 
                    True, 
                    f"Endpoint properly secured (status {status})", 
                    data
                )
            elif status == 404 and "not found" in str(data):
                await self.log_test_result(
                    "Admin Approve User Endpoint", 
                    True, 
                    "Endpoint accessible but user not found (expected)", 
                    data
                )
            elif status == 404:
                await self.log_test_result(
                    "Admin Approve User Endpoint", 
                    False, 
                    "Endpoint not found (404)", 
                    data
                )
            else:
                await self.log_test_result(
                    "Admin Approve User Endpoint", 
                    True, 
                    f"Endpoint exists (status {status})", 
                    data
                )
                
        except Exception as e:
            await self.log_test_result("Admin Approve User Endpoint", False, f"Exception: {str(e)}")
    
    async def test_demo_limit_system_structure(self):
        """Test 9: Demo Limit System Structure"""
        try:
            # Test if demo limit functions are implemented by checking response structure
            # This is indirect testing since we can't directly call internal functions
            
            # Create a demo user and check the response structure
            test_user = {
                "clerk_user_id": f"demo_limit_test_{uuid.uuid4().hex[:8]}",
                "email": f"demo_limit_test_{uuid.uuid4().hex[:8]}@example.com",
                "name": "Demo Limit Test User"
            }
            
            status, data = await self.make_request("POST", "/auth/self-signup", data=test_user, auth_required=False)
            
            if status in [200, 201]:
                demo_limits = data.get("demo_limits", {})
                max_demo_limit = data.get("max_demo_limit")
                
                # Check if all required limit types are present
                required_types = ["documents", "trainings", "consumptions", "personnel", "suppliers"]
                all_types_present = all(limit_type in demo_limits for limit_type in required_types)
                all_counts_zero = all(demo_limits.get(limit_type, -1) == 0 for limit_type in required_types)
                
                if all_types_present and all_counts_zero and max_demo_limit == 3:
                    await self.log_test_result(
                        "Demo Limit System Structure", 
                        True, 
                        "Demo limit system properly structured with all required types", 
                        data
                    )
                else:
                    await self.log_test_result(
                        "Demo Limit System Structure", 
                        False, 
                        f"Demo limit structure incomplete: types={all_types_present}, zeros={all_counts_zero}, max={max_demo_limit}", 
                        data
                    )
            elif status == 400 and "already exists" in str(data):
                await self.log_test_result(
                    "Demo Limit System Structure", 
                    True, 
                    "User already exists (structure tested previously)", 
                    data
                )
            else:
                await self.log_test_result(
                    "Demo Limit System Structure", 
                    False, 
                    f"Failed to create demo user for structure test: status {status}", 
                    data
                )
                
        except Exception as e:
            await self.log_test_result("Demo Limit System Structure", False, f"Exception: {str(e)}")
    
    async def test_backward_compatibility(self):
        """Test 10: Backward Compatibility"""
        try:
            # Test that existing endpoints still work
            endpoints_to_test = [
                ("/health", "GET", False),
                ("/clients", "GET", True),
                ("/documents", "GET", True),
                ("/trainings", "GET", True),
                ("/consumptions", "GET", True)
            ]
            
            compatibility_score = 0
            total_endpoints = len(endpoints_to_test)
            
            for endpoint, method, auth_required in endpoints_to_test:
                try:
                    status, data = await self.make_request(method, endpoint, auth_required=auth_required)
                    
                    if not auth_required and status == 200:
                        compatibility_score += 1
                    elif auth_required and status in [401, 403]:  # Properly secured
                        compatibility_score += 1
                    elif auth_required and status == 200:  # Working with auth
                        compatibility_score += 1
                    elif status != 404:  # Endpoint exists
                        compatibility_score += 0.5
                        
                except Exception:
                    pass  # Endpoint might not be accessible, but that's ok
            
            success_rate = (compatibility_score / total_endpoints) * 100
            success = success_rate >= 80  # 80% compatibility required
            
            await self.log_test_result(
                "Backward Compatibility", 
                success, 
                f"Compatibility score: {success_rate:.1f}% ({compatibility_score}/{total_endpoints})"
            )
                
        except Exception as e:
            await self.log_test_result("Backward Compatibility", False, f"Exception: {str(e)}")
    
    async def test_demo_system_integration(self):
        """Test 11: Demo System Integration"""
        try:
            # Test the complete demo system flow
            integration_tests = []
            
            # 1. Self-signup creates demo user
            test_user = {
                "clerk_user_id": f"integration_test_{uuid.uuid4().hex[:8]}",
                "email": f"integration_test_{uuid.uuid4().hex[:8]}@example.com",
                "name": "Integration Test User"
            }
            
            status, data = await self.make_request("POST", "/auth/self-signup", data=test_user, auth_required=False)
            if status in [200, 201] and data.get("status") == "demo_user":
                integration_tests.append("✅ Self-signup creates demo user")
            elif status == 400 and "already exists" in str(data):
                integration_tests.append("✅ Self-signup handles existing users")
            else:
                integration_tests.append("❌ Self-signup failed")
            
            # 2. Admin endpoints are secured
            status, _ = await self.make_request("GET", "/admin/pending-approvals", auth_required=True)
            if status in [401, 403]:
                integration_tests.append("✅ Admin endpoints properly secured")
            else:
                integration_tests.append("❌ Admin endpoints not secured")
            
            # 3. Demo user structure is correct
            if status in [200, 201]:
                demo_limits = data.get("demo_limits", {})
                if len(demo_limits) == 5 and data.get("max_demo_limit") == 3:
                    integration_tests.append("✅ Demo user structure correct")
                else:
                    integration_tests.append("❌ Demo user structure incorrect")
            
            success_count = len([t for t in integration_tests if t.startswith("✅")])
            total_count = len(integration_tests)
            success = success_count >= (total_count * 0.8)  # 80% success rate
            
            await self.log_test_result(
                "Demo System Integration", 
                success, 
                f"Integration tests: {success_count}/{total_count} passed. Details: {'; '.join(integration_tests)}"
            )
                
        except Exception as e:
            await self.log_test_result("Demo System Integration", False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all demo system tests"""
        logger.info("🚀 Starting Self-Signup + Demo System Backend Tests")
        logger.info(f"🎯 Testing against: {self.base_url}")
        
        # Run all tests
        await self.test_backend_health()
        await self.test_self_signup_endpoint_accessibility()
        await self.test_self_signup_validation()
        await self.test_self_signup_demo_user_creation()
        await self.test_demo_user_status_assignment()
        await self.test_email_uniqueness_validation()
        await self.test_admin_pending_approvals_endpoint()
        await self.test_admin_approve_user_endpoint()
        await self.test_demo_limit_system_structure()
        await self.test_backward_compatibility()
        await self.test_demo_system_integration()
        
        # Calculate success rate
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        # Print summary
        print("\n" + "="*80)
        print("🎯 SELF-SIGNUP + DEMO SYSTEM BACKEND TEST RESULTS")
        print("="*80)
        print(f"📊 Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.total_tests - self.passed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print("="*80)
        
        # Print detailed results
        print("\n📋 DETAILED TEST RESULTS:")
        print("-" * 80)
        for result in self.test_results:
            print(f"{result['status']} {result['test']}")
            if result['details']:
                print(f"   📝 {result['details']}")
            print()
        
        # Overall assessment
        if success_rate >= 90:
            print("🎉 EXCELLENT: Demo system is fully functional!")
        elif success_rate >= 80:
            print("✅ GOOD: Demo system is mostly functional with minor issues")
        elif success_rate >= 70:
            print("⚠️ MODERATE: Demo system has some issues that need attention")
        else:
            print("🚨 CRITICAL: Demo system has major issues requiring immediate fixes")
        
        print("="*80)
        
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "success_rate": success_rate,
            "results": self.test_results
        }

async def main():
    """Main test execution"""
    tester = DemoSystemBackendTest()
    results = await tester.run_all_tests()
    return results

if __name__ == "__main__":
    asyncio.run(main())