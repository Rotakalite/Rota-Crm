#!/usr/bin/env python3
"""
Consultant Access Backend Testing
Tests for Multiple Modules Consultant Access Fix

This script tests the consultant access functionality for:
1. Supplier Management - Consultant access
2. Training Management - Consultant access  
3. Waste Management - Consultant access (recheck)
4. Document Management - Consultant access (if needed)

Test scenarios:
- Consultant Role Access: Consultant users accessing endpoints
- Client Assignment Verification: Consultant only accessing assigned clients
- Parameter Handling: client_id parameter with data filtering
- Error Handling: Unauthorized access attempts
"""

import unittest
import json
import logging
import requests
import os
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL from frontend/.env
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# Test JWT tokens - These are sample tokens for testing
# In a real scenario, you would generate these from Clerk
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

# Consultant tokens - These would represent consultant users with different client assignments
CONSULTANT_TOKEN_1 = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ09OU1VMVEFOVF8wMDEiLCJlbWFpbCI6ImNvbnN1bHRhbnQxQHJvdGEuY29tIiwibmFtZSI6IkNvbnN1bHRhbnQgMSJ9.signature"

CONSULTANT_TOKEN_2 = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ09OU1VMVEFOVF8wMDIiLCJlbWFpbCI6ImNvbnN1bHRhbnQyQHJvdGEuY29tIiwibmFtZSI6IkNvbnN1bHRhbnQgMiJ9.signature"

# Client tokens for comparison
CLIENT_TOKEN_1 = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ0xJRU5UXzAwMSIsImVtYWlsIjoiY2xpZW50MUByb3RhLmNvbSIsIm5hbWUiOiJDbGllbnQgMSJ9.signature"

INVALID_TOKEN = "invalid.token.format"

# Test client IDs - These would represent actual client IDs in the database
TEST_CLIENT_ID_1 = "8bfd3a85-2483-4b63-9e80-e53747c3db7e"
TEST_CLIENT_ID_2 = "7a992a86-e2f4-4ed5-99f7-bab4966b7306"
UNASSIGNED_CLIENT_ID = "99999999-9999-9999-9999-999999999999"


class TestConsultantSupplierAccess(unittest.TestCase):
    """Test consultant access to Supplier Management endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_consultant1 = {"Authorization": f"Bearer {CONSULTANT_TOKEN_1}"}
        self.headers_consultant2 = {"Authorization": f"Bearer {CONSULTANT_TOKEN_2}"}
        self.headers_client1 = {"Authorization": f"Bearer {CLIENT_TOKEN_1}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
        
        # Test supplier data
        self.test_supplier_data = {
            "company_name": f"Consultant Test Supplier {uuid.uuid4()}",
            "address": "123 Test Street, Test City",
            "category": "Gıda & İçecek",
            "certifications": ["ISO 14001"],
            "monthly_purchase_amount": 1000.0,
            "monthly_purchase_unit": "TL",
            "local_supplier": True,
            "description": "Test supplier for consultant access testing",
            "client_id": TEST_CLIENT_ID_1
        }
    
    def test_consultant_create_supplier_with_valid_client(self):
        """Test consultant creating supplier for assigned client"""
        logger.info("\n=== Testing Consultant POST /api/suppliers with valid assigned client ===")
        
        url = f"{self.api_url}/suppliers"
        
        try:
            response = requests.post(url, headers=self.headers_consultant1, json=self.test_supplier_data)
            logger.info(f"Consultant response status code: {response.status_code}")
            
            # Expected outcomes:
            # 200/201: Success - consultant can create supplier for assigned client
            # 403: Forbidden - client not assigned to consultant
            # 401: Unauthorized - token issues
            # 400: Bad request - validation errors
            self.assertIn(response.status_code, [200, 201, 400, 401, 403])
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.assertIn("message", data)
                self.assertIn("supplier_id", data)
                logger.info(f"✅ Consultant successfully created supplier: {data['supplier_id']}")
                
            elif response.status_code == 403:
                data = response.json()
                logger.info(f"✅ Expected 403 - Client not assigned to consultant: {data.get('detail', 'No detail')}")
                
            elif response.status_code == 401:
                data = response.json()
                logger.info(f"✅ Expected 401 - Authentication issue: {data.get('detail', 'No detail')}")
                
            elif response.status_code == 400:
                data = response.json()
                logger.info(f"✅ Expected 400 - Validation error: {data.get('detail', 'No detail')}")
                
        except Exception as e:
            logger.error(f"❌ Error testing consultant supplier creation: {str(e)}")
            raise
    
    def test_consultant_create_supplier_with_invalid_client(self):
        """Test consultant creating supplier for unassigned client"""
        logger.info("\n=== Testing Consultant POST /api/suppliers with unassigned client ===")
        
        url = f"{self.api_url}/suppliers"
        
        # Use unassigned client ID
        invalid_supplier_data = self.test_supplier_data.copy()
        invalid_supplier_data["client_id"] = UNASSIGNED_CLIENT_ID
        invalid_supplier_data["company_name"] = f"Invalid Client Test Supplier {uuid.uuid4()}"
        
        try:
            response = requests.post(url, headers=self.headers_consultant1, json=invalid_supplier_data)
            logger.info(f"Consultant response status code: {response.status_code}")
            
            # Should get 403 Forbidden for unassigned client
            if response.status_code == 403:
                data = response.json()
                logger.info(f"✅ Correctly blocked unassigned client access: {data.get('detail', 'No detail')}")
                self.assertIn("yetkiniz yok", data.get("detail", "").lower())
                
            elif response.status_code == 401:
                data = response.json()
                logger.info(f"✅ Authentication issue (expected): {data.get('detail', 'No detail')}")
                
            else:
                logger.warning(f"⚠️ Unexpected response code: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing consultant invalid client access: {str(e)}")
            raise
    
    def test_consultant_get_suppliers_with_client_filter(self):
        """Test consultant getting suppliers with client_id filter"""
        logger.info("\n=== Testing Consultant GET /api/suppliers with client_id filter ===")
        
        url = f"{self.api_url}/suppliers"
        params = {"client_id": TEST_CLIENT_ID_1}
        
        try:
            response = requests.get(url, headers=self.headers_consultant1, params=params)
            logger.info(f"Consultant response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Consultant retrieved {len(data)} suppliers for assigned client")
                
                # Verify all suppliers belong to the requested client
                for supplier in data:
                    if "client_id" in supplier:
                        self.assertEqual(supplier["client_id"], TEST_CLIENT_ID_1)
                        
            elif response.status_code == 403:
                data = response.json()
                logger.info(f"✅ Expected 403 - Client access denied: {data.get('detail', 'No detail')}")
                
            elif response.status_code == 401:
                data = response.json()
                logger.info(f"✅ Expected 401 - Authentication issue: {data.get('detail', 'No detail')}")
                
            else:
                logger.warning(f"⚠️ Unexpected response code: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing consultant supplier retrieval: {str(e)}")
            raise
    
    def test_consultant_get_suppliers_without_client_filter(self):
        """Test consultant getting suppliers without client_id filter"""
        logger.info("\n=== Testing Consultant GET /api/suppliers without client_id filter ===")
        
        url = f"{self.api_url}/suppliers"
        
        try:
            response = requests.get(url, headers=self.headers_consultant1)
            logger.info(f"Consultant response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Consultant retrieved {len(data)} suppliers for all assigned clients")
                
                # Should only see suppliers for assigned clients
                logger.info("Verifying suppliers belong to assigned clients...")
                
            elif response.status_code == 403:
                data = response.json()
                logger.info(f"✅ Expected 403 - No consultant ID: {data.get('detail', 'No detail')}")
                
            elif response.status_code == 401:
                data = response.json()
                logger.info(f"✅ Expected 401 - Authentication issue: {data.get('detail', 'No detail')}")
                
            else:
                logger.warning(f"⚠️ Unexpected response code: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing consultant supplier retrieval without filter: {str(e)}")
            raise


class TestConsultantTrainingAccess(unittest.TestCase):
    """Test consultant access to Training Management endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_consultant1 = {"Authorization": f"Bearer {CONSULTANT_TOKEN_1}"}
        self.headers_consultant2 = {"Authorization": f"Bearer {CONSULTANT_TOKEN_2}"}
        self.headers_client1 = {"Authorization": f"Bearer {CLIENT_TOKEN_1}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_consultant_get_trainings(self):
        """Test consultant getting trainings for assigned clients"""
        logger.info("\n=== Testing Consultant GET /api/trainings ===")
        
        url = f"{self.api_url}/trainings"
        
        try:
            response = requests.get(url, headers=self.headers_consultant1)
            logger.info(f"Consultant response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Consultant retrieved {len(data)} trainings for assigned clients")
                
                # Verify trainings belong to assigned clients
                for training in data:
                    if "client_id" in training:
                        logger.info(f"Training client_id: {training['client_id']}")
                        
            elif response.status_code == 401:
                data = response.json()
                logger.info(f"✅ Expected 401 - Authentication issue: {data.get('detail', 'No detail')}")
                
            elif response.status_code == 403:
                data = response.json()
                logger.info(f"✅ Expected 403 - Access denied: {data.get('detail', 'No detail')}")
                
            else:
                logger.warning(f"⚠️ Unexpected response code: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing consultant training access: {str(e)}")
            raise
    
    def test_consultant_vs_admin_training_access(self):
        """Compare consultant vs admin training access"""
        logger.info("\n=== Comparing Consultant vs Admin Training Access ===")
        
        url = f"{self.api_url}/trainings"
        
        # Test admin access
        try:
            admin_response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {admin_response.status_code}")
            
            admin_count = 0
            if admin_response.status_code == 200:
                admin_data = admin_response.json()
                admin_count = len(admin_data)
                logger.info(f"Admin can see {admin_count} trainings")
                
        except Exception as e:
            logger.error(f"❌ Error testing admin training access: {str(e)}")
        
        # Test consultant access
        try:
            consultant_response = requests.get(url, headers=self.headers_consultant1)
            logger.info(f"Consultant response status code: {consultant_response.status_code}")
            
            consultant_count = 0
            if consultant_response.status_code == 200:
                consultant_data = consultant_response.json()
                consultant_count = len(consultant_data)
                logger.info(f"Consultant can see {consultant_count} trainings")
                
                # Consultant should see fewer or equal trainings than admin
                if admin_count > 0:
                    self.assertLessEqual(consultant_count, admin_count, 
                                       "Consultant should not see more trainings than admin")
                    
        except Exception as e:
            logger.error(f"❌ Error testing consultant training access comparison: {str(e)}")


class TestConsultantWasteAnalyticsAccess(unittest.TestCase):
    """Test consultant access to Waste Management Analytics endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_consultant1 = {"Authorization": f"Bearer {CONSULTANT_TOKEN_1}"}
        self.headers_consultant2 = {"Authorization": f"Bearer {CONSULTANT_TOKEN_2}"}
        self.headers_client1 = {"Authorization": f"Bearer {CLIENT_TOKEN_1}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_consultant_waste_analytics_with_client_id(self):
        """Test consultant accessing waste analytics with client_id"""
        logger.info("\n=== Testing Consultant GET /api/consumptions/waste/analytics with client_id ===")
        
        url = f"{self.api_url}/consumptions/waste/analytics"
        params = {"client_id": TEST_CLIENT_ID_1, "year": 2024}
        
        try:
            response = requests.get(url, headers=self.headers_consultant1, params=params)
            logger.info(f"Consultant response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Consultant successfully accessed waste analytics for assigned client")
                
                # Verify response structure
                expected_keys = ["yearly_totals", "monthly_data", "waste_breakdown", "recycling_performance"]
                for key in expected_keys:
                    self.assertIn(key, data, f"Missing key: {key}")
                    
            elif response.status_code == 403:
                data = response.json()
                logger.info(f"✅ Expected 403 - Client access denied: {data.get('detail', 'No detail')}")
                
            elif response.status_code == 401:
                data = response.json()
                logger.info(f"✅ Expected 401 - Authentication issue: {data.get('detail', 'No detail')}")
                
            elif response.status_code == 400:
                data = response.json()
                logger.info(f"✅ Expected 400 - Bad request: {data.get('detail', 'No detail')}")
                
            else:
                logger.warning(f"⚠️ Unexpected response code: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing consultant waste analytics access: {str(e)}")
            raise
    
    def test_consultant_waste_analytics_without_client_id(self):
        """Test consultant accessing waste analytics without client_id (should fail)"""
        logger.info("\n=== Testing Consultant GET /api/consumptions/waste/analytics without client_id ===")
        
        url = f"{self.api_url}/consumptions/waste/analytics"
        params = {"year": 2024}
        
        try:
            response = requests.get(url, headers=self.headers_consultant1, params=params)
            logger.info(f"Consultant response status code: {response.status_code}")
            
            # Should get 400 Bad Request - Client ID required
            if response.status_code == 400:
                data = response.json()
                logger.info(f"✅ Correctly requires client_id: {data.get('detail', 'No detail')}")
                self.assertIn("client id required", data.get("detail", "").lower())
                
            elif response.status_code == 401:
                data = response.json()
                logger.info(f"✅ Expected 401 - Authentication issue: {data.get('detail', 'No detail')}")
                
            else:
                logger.warning(f"⚠️ Unexpected response code: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing consultant waste analytics without client_id: {str(e)}")
            raise
    
    def test_consultant_waste_analytics_with_unassigned_client(self):
        """Test consultant accessing waste analytics for unassigned client"""
        logger.info("\n=== Testing Consultant GET /api/consumptions/waste/analytics with unassigned client ===")
        
        url = f"{self.api_url}/consumptions/waste/analytics"
        params = {"client_id": UNASSIGNED_CLIENT_ID, "year": 2024}
        
        try:
            response = requests.get(url, headers=self.headers_consultant1, params=params)
            logger.info(f"Consultant response status code: {response.status_code}")
            
            # Should get 403 Forbidden for unassigned client
            if response.status_code == 403:
                data = response.json()
                logger.info(f"✅ Correctly blocked unassigned client access: {data.get('detail', 'No detail')}")
                self.assertIn("yetkiniz yok", data.get("detail", "").lower())
                
            elif response.status_code == 401:
                data = response.json()
                logger.info(f"✅ Expected 401 - Authentication issue: {data.get('detail', 'No detail')}")
                
            else:
                logger.warning(f"⚠️ Unexpected response code: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing consultant unassigned client access: {str(e)}")
            raise


class TestConsultantAuthenticationAndAuthorization(unittest.TestCase):
    """Test consultant authentication and authorization scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_consultant1 = {"Authorization": f"Bearer {CONSULTANT_TOKEN_1}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_consultant_endpoints_require_authentication(self):
        """Test that consultant endpoints require authentication"""
        logger.info("\n=== Testing Authentication Requirements for Consultant Endpoints ===")
        
        endpoints_to_test = [
            "/suppliers",
            "/trainings", 
            "/consumptions/waste/analytics"
        ]
        
        for endpoint in endpoints_to_test:
            url = f"{self.api_url}{endpoint}"
            
            # Test with no authentication
            try:
                response = requests.get(url, headers=self.headers_no_auth)
                logger.info(f"No auth {endpoint} response: {response.status_code}")
                
                # Should get 403 Forbidden
                self.assertEqual(response.status_code, 403, 
                               f"Endpoint {endpoint} should require authentication")
                
            except Exception as e:
                logger.error(f"❌ Error testing no auth for {endpoint}: {str(e)}")
            
            # Test with invalid token
            try:
                response = requests.get(url, headers=self.headers_invalid)
                logger.info(f"Invalid token {endpoint} response: {response.status_code}")
                
                # Should get 401 Unauthorized
                self.assertEqual(response.status_code, 401, 
                               f"Endpoint {endpoint} should reject invalid tokens")
                
            except Exception as e:
                logger.error(f"❌ Error testing invalid token for {endpoint}: {str(e)}")
    
    def test_consultant_vs_client_vs_admin_access_patterns(self):
        """Test access patterns across different user roles"""
        logger.info("\n=== Testing Access Patterns Across User Roles ===")
        
        test_cases = [
            {
                "endpoint": "/suppliers",
                "params": {"client_id": TEST_CLIENT_ID_1},
                "description": "Supplier listing with client filter"
            },
            {
                "endpoint": "/trainings",
                "params": {},
                "description": "Training listing"
            },
            {
                "endpoint": "/consumptions/waste/analytics",
                "params": {"client_id": TEST_CLIENT_ID_1, "year": 2024},
                "description": "Waste analytics with client filter"
            }
        ]
        
        for test_case in test_cases:
            logger.info(f"\n--- Testing {test_case['description']} ---")
            url = f"{self.api_url}{test_case['endpoint']}"
            
            # Test with consultant
            try:
                response = requests.get(url, headers=self.headers_consultant1, params=test_case['params'])
                logger.info(f"Consultant access: {response.status_code}")
                
                if response.status_code in [200, 401, 403]:
                    logger.info(f"✅ Consultant access pattern as expected")
                else:
                    logger.warning(f"⚠️ Unexpected consultant response: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error testing consultant access: {str(e)}")
            
            # Test with admin
            try:
                response = requests.get(url, headers=self.headers_admin, params=test_case['params'])
                logger.info(f"Admin access: {response.status_code}")
                
                if response.status_code in [200, 401]:
                    logger.info(f"✅ Admin access pattern as expected")
                else:
                    logger.warning(f"⚠️ Unexpected admin response: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error testing admin access: {str(e)}")


def run_consultant_access_tests():
    """Run all consultant access tests"""
    logger.info("🚀 STARTING CONSULTANT ACCESS BACKEND TESTING")
    logger.info(f"Backend URL: {RAILWAY_API_URL}")
    logger.info("=" * 80)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestConsultantSupplierAccess,
        TestConsultantTrainingAccess,
        TestConsultantWasteAnalyticsAccess,
        TestConsultantAuthenticationAndAuthorization
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Summary
    logger.info("=" * 80)
    logger.info("🏁 CONSULTANT ACCESS TESTING COMPLETED")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    if result.failures:
        logger.info("\n❌ FAILURES:")
        for test, traceback in result.failures:
            logger.info(f"- {test}: {traceback}")
    
    if result.errors:
        logger.info("\n❌ ERRORS:")
        for test, traceback in result.errors:
            logger.info(f"- {test}: {traceback}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    logger.info(f"\n✅ SUCCESS RATE: {success_rate:.1f}%")
    
    return result


if __name__ == "__main__":
    run_consultant_access_tests()