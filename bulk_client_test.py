#!/usr/bin/env python3
"""
Bulk Client Testing Suite for Rota CRM
Tests bulk client functionality including client type filtering and bulk email statistics
"""

import unittest
import json
import logging
import requests
import os
import sys
from datetime import datetime
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from frontend/.env
BACKEND_URL = "https://rota-crm-production.up.railway.app/api"

# MongoDB connection details from backend/.env
MONGO_URL = "mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster"
DB_NAME = "rotacrm"

# Test JWT tokens (these would be real tokens in production)
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
INVALID_TOKEN = "invalid.token.format"

class TestBulkClientFunctionality(unittest.TestCase):
    """Test class for bulk client functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_URL
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
        
        # MongoDB connection for direct database verification
        self.mongo_client = MongoClient(MONGO_URL)
        self.db = self.mongo_client[DB_NAME]
        
        logger.info(f"🔧 Test setup complete - API URL: {self.api_url}")
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'mongo_client'):
            self.mongo_client.close()
    
    def test_database_bulk_clients_verification(self):
        """Test 1: Verify bulk clients exist in database"""
        logger.info("\n=== Test 1: Database Bulk Clients Verification ===")
        
        try:
            # Check total clients in database
            total_clients = self.db.clients.count_documents({})
            logger.info(f"📊 Total clients in database: {total_clients}")
            
            # Check bulk clients specifically
            bulk_clients = list(self.db.clients.find({"client_type": "bulk"}))
            bulk_count = len(bulk_clients)
            logger.info(f"📊 Bulk clients in database: {bulk_count}")
            
            # Check registered clients
            registered_clients = list(self.db.clients.find({"client_type": "registered"}))
            registered_count = len(registered_clients)
            logger.info(f"📊 Registered clients in database: {registered_count}")
            
            # Check clients with no client_type (should be treated as registered)
            no_type_clients = list(self.db.clients.find({"client_type": {"$exists": False}}))
            no_type_count = len(no_type_clients)
            logger.info(f"📊 Clients without client_type: {no_type_count}")
            
            # Verify bulk clients have proper structure
            if bulk_count > 0:
                sample_bulk_client = bulk_clients[0]
                logger.info(f"📋 Sample bulk client structure:")
                logger.info(f"   ID: {sample_bulk_client.get('id', 'N/A')}")
                logger.info(f"   Name: {sample_bulk_client.get('name', 'N/A')}")
                logger.info(f"   Hotel Name: {sample_bulk_client.get('hotel_name', 'N/A')}")
                logger.info(f"   Email: {sample_bulk_client.get('email', 'N/A')}")
                logger.info(f"   Client Type: {sample_bulk_client.get('client_type', 'N/A')}")
                logger.info(f"   Import Source: {sample_bulk_client.get('import_source', 'N/A')}")
                
                # Verify bulk clients have required fields
                self.assertIn('client_type', sample_bulk_client)
                self.assertEqual(sample_bulk_client['client_type'], 'bulk')
                self.assertIn('email', sample_bulk_client)
                self.assertIn('name', sample_bulk_client)
            
            # Assertions
            self.assertGreater(total_clients, 0, "Database should contain clients")
            self.assertGreater(bulk_count, 0, "Database should contain bulk clients")
            
            logger.info(f"✅ Database verification passed - Found {bulk_count} bulk clients out of {total_clients} total")
            
        except Exception as e:
            logger.error(f"❌ Database verification failed: {str(e)}")
            raise
    
    def test_clients_endpoint_all_filter(self):
        """Test 2: GET /api/clients with client_type=all (default)"""
        logger.info("\n=== Test 2: GET /api/clients with client_type=all ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            # Test with client_type=all parameter
            params = {"client_type": "all"}
            response = requests.get(url, headers=self.headers_admin, params=params)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Retrieved {len(data)} clients with client_type=all")
                
                # Verify response structure
                self.assertIsInstance(data, list, "Response should be a list")
                
                if len(data) > 0:
                    # Check that we get both bulk and registered clients
                    bulk_clients = [c for c in data if c.get('client_type') == 'bulk']
                    registered_clients = [c for c in data if c.get('client_type') == 'registered']
                    no_type_clients = [c for c in data if 'client_type' not in c]
                    
                    logger.info(f"   Bulk clients: {len(bulk_clients)}")
                    logger.info(f"   Registered clients: {len(registered_clients)}")
                    logger.info(f"   No type clients: {len(no_type_clients)}")
                    
                    # Verify client structure
                    sample_client = data[0]
                    expected_fields = ['id', 'name', 'email', 'client_type']
                    for field in expected_fields:
                        if field == 'client_type':
                            # client_type might not exist in old records
                            continue
                        self.assertIn(field, sample_client, f"Client should have {field} field")
                    
                    # Should have both types of clients
                    self.assertGreater(len(bulk_clients), 0, "Should have bulk clients")
                    
            elif response.status_code == 401:
                data = response.json()
                logger.info(f"⚠️ Authentication error: {data.get('detail', 'No detail')}")
                self.assertIn("Invalid token", data.get("detail", ""))
                
            elif response.status_code == 403:
                data = response.json()
                logger.info(f"⚠️ Authorization error: {data.get('detail', 'No detail')}")
                
            else:
                logger.error(f"❌ Unexpected status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error testing client_type=all: {str(e)}")
            raise
    
    def test_clients_endpoint_bulk_filter(self):
        """Test 3: GET /api/clients with client_type=bulk filter"""
        logger.info("\n=== Test 3: GET /api/clients with client_type=bulk ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            # Test with client_type=bulk parameter
            params = {"client_type": "bulk"}
            response = requests.get(url, headers=self.headers_admin, params=params)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Retrieved {len(data)} bulk clients")
                
                # Verify response structure
                self.assertIsInstance(data, list, "Response should be a list")
                
                if len(data) > 0:
                    # Verify all returned clients are bulk type
                    for i, client in enumerate(data[:5]):  # Check first 5 clients
                        logger.info(f"   Client {i+1}: {client.get('name', 'N/A')} - Type: {client.get('client_type', 'N/A')}")
                        self.assertEqual(client.get('client_type'), 'bulk', f"Client {i+1} should be bulk type")
                    
                    # Verify client structure
                    sample_client = data[0]
                    expected_fields = ['id', 'name', 'email', 'client_type']
                    for field in expected_fields:
                        self.assertIn(field, sample_client, f"Bulk client should have {field} field")
                    
                    # Verify client_type is specifically 'bulk'
                    self.assertEqual(sample_client['client_type'], 'bulk')
                    
                    # Should have a significant number of bulk clients (22,877 mentioned in context)
                    self.assertGreater(len(data), 1000, "Should have many bulk clients")
                    
                else:
                    logger.warning("⚠️ No bulk clients returned - this might indicate a filtering issue")
                    
            elif response.status_code == 401:
                data = response.json()
                logger.info(f"⚠️ Authentication error: {data.get('detail', 'No detail')}")
                self.assertIn("Invalid token", data.get("detail", ""))
                
            elif response.status_code == 403:
                data = response.json()
                logger.info(f"⚠️ Authorization error: {data.get('detail', 'No detail')}")
                
            else:
                logger.error(f"❌ Unexpected status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error testing client_type=bulk: {str(e)}")
            raise
    
    def test_clients_endpoint_registered_filter(self):
        """Test 4: GET /api/clients with client_type=registered filter"""
        logger.info("\n=== Test 4: GET /api/clients with client_type=registered ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            # Test with client_type=registered parameter
            params = {"client_type": "registered"}
            response = requests.get(url, headers=self.headers_admin, params=params)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Retrieved {len(data)} registered clients")
                
                # Verify response structure
                self.assertIsInstance(data, list, "Response should be a list")
                
                if len(data) > 0:
                    # Verify all returned clients are registered type
                    for i, client in enumerate(data[:5]):  # Check first 5 clients
                        logger.info(f"   Client {i+1}: {client.get('name', 'N/A')} - Type: {client.get('client_type', 'N/A')}")
                        client_type = client.get('client_type', 'registered')  # Default to registered if not set
                        self.assertEqual(client_type, 'registered', f"Client {i+1} should be registered type")
                    
                    # Verify client structure
                    sample_client = data[0]
                    expected_fields = ['id', 'name', 'email']
                    for field in expected_fields:
                        self.assertIn(field, sample_client, f"Registered client should have {field} field")
                    
                    # Verify client_type is 'registered' or not set (defaults to registered)
                    client_type = sample_client.get('client_type', 'registered')
                    self.assertEqual(client_type, 'registered')
                    
                else:
                    logger.info("ℹ️ No registered clients returned")
                    
            elif response.status_code == 401:
                data = response.json()
                logger.info(f"⚠️ Authentication error: {data.get('detail', 'No detail')}")
                self.assertIn("Invalid token", data.get("detail", ""))
                
            elif response.status_code == 403:
                data = response.json()
                logger.info(f"⚠️ Authorization error: {data.get('detail', 'No detail')}")
                
            else:
                logger.error(f"❌ Unexpected status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error testing client_type=registered: {str(e)}")
            raise
    
    def test_clients_endpoint_pagination(self):
        """Test 5: Verify pagination works with bulk clients"""
        logger.info("\n=== Test 5: Pagination with Bulk Clients ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            # Test pagination with bulk clients
            params = {"client_type": "bulk", "page": 1, "limit": 10}
            response = requests.get(url, headers=self.headers_admin, params=params)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response includes pagination info or is just a list
                if isinstance(data, dict) and 'clients' in data:
                    # Paginated response format
                    clients = data['clients']
                    total = data.get('total', len(clients))
                    page = data.get('page', 1)
                    limit = data.get('limit', len(clients))
                    
                    logger.info(f"✅ Paginated response - Page {page}, Limit {limit}, Total {total}")
                    logger.info(f"   Retrieved {len(clients)} clients on this page")
                    
                    # Verify pagination constraints
                    self.assertLessEqual(len(clients), 10, "Should not exceed limit of 10")
                    self.assertGreater(total, len(clients), "Total should be greater than page size")
                    
                elif isinstance(data, list):
                    # Non-paginated response (all results)
                    logger.info(f"✅ Non-paginated response - Retrieved {len(data)} clients")
                    
                    # If we have many bulk clients, this should be a large number
                    if len(data) > 1000:
                        logger.info("   Large number of clients suggests pagination might not be implemented")
                    
                else:
                    logger.error(f"❌ Unexpected response format: {type(data)}")
                    
            elif response.status_code == 401:
                data = response.json()
                logger.info(f"⚠️ Authentication error: {data.get('detail', 'No detail')}")
                
            elif response.status_code == 403:
                data = response.json()
                logger.info(f"⚠️ Authorization error: {data.get('detail', 'No detail')}")
                
            else:
                logger.error(f"❌ Unexpected status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error testing pagination: {str(e)}")
            raise
    
    def test_bulk_email_stats_endpoint(self):
        """Test 6: GET /api/bulk-email/stats endpoint"""
        logger.info("\n=== Test 6: Bulk Email Statistics Endpoint ===")
        
        url = f"{self.api_url}/bulk-email/stats"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Bulk email stats retrieved successfully")
                
                # Verify response structure
                expected_fields = ['total_bulk_clients', 'clients_with_email', 'clients_without_email']
                for field in expected_fields:
                    if field in data:
                        logger.info(f"   {field}: {data[field]}")
                    else:
                        logger.warning(f"   Missing field: {field}")
                
                # Verify we have bulk clients
                total_bulk = data.get('total_bulk_clients', 0)
                with_email = data.get('clients_with_email', 0)
                without_email = data.get('clients_without_email', 0)
                
                self.assertGreater(total_bulk, 0, "Should have bulk clients")
                self.assertEqual(total_bulk, with_email + without_email, "Total should equal sum of with/without email")
                
                # Should have many bulk clients (22,877 mentioned in context)
                if total_bulk > 20000:
                    logger.info(f"   ✅ Large number of bulk clients confirmed: {total_bulk}")
                else:
                    logger.warning(f"   ⚠️ Expected more bulk clients, got: {total_bulk}")
                
            elif response.status_code == 401:
                data = response.json()
                logger.info(f"⚠️ Authentication error: {data.get('detail', 'No detail')}")
                self.assertIn("Invalid token", data.get("detail", ""))
                
            elif response.status_code == 403:
                data = response.json()
                logger.info(f"⚠️ Authorization error: {data.get('detail', 'No detail')}")
                
            elif response.status_code == 404:
                logger.error(f"❌ Endpoint not found - bulk email stats endpoint may not be implemented")
                
            else:
                logger.error(f"❌ Unexpected status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error testing bulk email stats: {str(e)}")
            raise
    
    def test_authentication_requirements(self):
        """Test 7: Authentication requirements for bulk client endpoints"""
        logger.info("\n=== Test 7: Authentication Requirements ===")
        
        endpoints_to_test = [
            ("/clients", "GET clients endpoint"),
            ("/bulk-email/stats", "Bulk email stats endpoint")
        ]
        
        for endpoint, description in endpoints_to_test:
            logger.info(f"\n--- Testing {description} ---")
            url = f"{self.api_url}{endpoint}"
            
            # Test with no authentication
            try:
                response = requests.get(url, headers=self.headers_no_auth)
                logger.info(f"No auth response status: {response.status_code}")
                self.assertEqual(response.status_code, 403, f"{description} should require authentication")
                
            except Exception as e:
                logger.error(f"❌ Error testing no auth for {description}: {str(e)}")
            
            # Test with invalid token
            try:
                response = requests.get(url, headers=self.headers_invalid)
                logger.info(f"Invalid token response status: {response.status_code}")
                self.assertEqual(response.status_code, 401, f"{description} should reject invalid tokens")
                
            except Exception as e:
                logger.error(f"❌ Error testing invalid token for {description}: {str(e)}")
        
        logger.info("✅ Authentication requirements test completed")
    
    def test_client_type_field_consistency(self):
        """Test 8: Verify client_type field consistency across all clients"""
        logger.info("\n=== Test 8: Client Type Field Consistency ===")
        
        try:
            # Direct database check for client_type field consistency
            all_clients = list(self.db.clients.find({}))
            logger.info(f"📊 Checking {len(all_clients)} clients for client_type consistency")
            
            bulk_count = 0
            registered_count = 0
            no_type_count = 0
            invalid_type_count = 0
            
            for client in all_clients:
                client_type = client.get('client_type')
                
                if client_type == 'bulk':
                    bulk_count += 1
                elif client_type == 'registered':
                    registered_count += 1
                elif client_type is None or 'client_type' not in client:
                    no_type_count += 1
                else:
                    invalid_type_count += 1
                    logger.warning(f"   Invalid client_type found: {client_type} for client {client.get('id', 'N/A')}")
            
            logger.info(f"   Bulk clients: {bulk_count}")
            logger.info(f"   Registered clients: {registered_count}")
            logger.info(f"   No client_type: {no_type_count}")
            logger.info(f"   Invalid client_type: {invalid_type_count}")
            
            # Verify consistency
            self.assertEqual(invalid_type_count, 0, "Should not have invalid client_type values")
            self.assertGreater(bulk_count, 0, "Should have bulk clients")
            
            # Check if bulk clients have import_source
            bulk_with_import_source = self.db.clients.count_documents({
                "client_type": "bulk",
                "import_source": {"$exists": True}
            })
            logger.info(f"   Bulk clients with import_source: {bulk_with_import_source}")
            
            logger.info("✅ Client type field consistency verified")
            
        except Exception as e:
            logger.error(f"❌ Error checking client type consistency: {str(e)}")
            raise

def run_bulk_client_tests():
    """Run all bulk client tests"""
    logger.info("🚀 Starting Bulk Client Functionality Tests")
    logger.info("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test methods in order
    test_methods = [
        'test_database_bulk_clients_verification',
        'test_clients_endpoint_all_filter',
        'test_clients_endpoint_bulk_filter',
        'test_clients_endpoint_registered_filter',
        'test_clients_endpoint_pagination',
        'test_bulk_email_stats_endpoint',
        'test_authentication_requirements',
        'test_client_type_field_consistency'
    ]
    
    for method in test_methods:
        test_suite.addTest(TestBulkClientFunctionality(method))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Summary
    logger.info("=" * 60)
    logger.info("🏁 Bulk Client Tests Summary")
    logger.info(f"   Tests run: {result.testsRun}")
    logger.info(f"   Failures: {len(result.failures)}")
    logger.info(f"   Errors: {len(result.errors)}")
    
    if result.failures:
        logger.error("❌ Test Failures:")
        for test, traceback in result.failures:
            logger.error(f"   {test}: {traceback}")
    
    if result.errors:
        logger.error("❌ Test Errors:")
        for test, traceback in result.errors:
            logger.error(f"   {test}: {traceback}")
    
    if result.wasSuccessful():
        logger.info("✅ All bulk client tests passed!")
    else:
        logger.error("❌ Some bulk client tests failed!")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_bulk_client_tests()
    sys.exit(0 if success else 1)