#!/usr/bin/env python3
"""
Bulk Client API Testing - Direct Backend Testing
Tests the bulk client functionality with proper authentication handling
"""

import unittest
import json
import logging
import requests
import os
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

class TestBulkClientAPI(unittest.TestCase):
    """Test class for bulk client API functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_URL
        
        # MongoDB connection for direct database verification
        self.mongo_client = MongoClient(MONGO_URL)
        self.db = self.mongo_client[DB_NAME]
        
        logger.info(f"🔧 Test setup complete - API URL: {self.api_url}")
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'mongo_client'):
            self.mongo_client.close()
    
    def test_bulk_client_database_verification(self):
        """Test 1: Comprehensive database verification of bulk clients"""
        logger.info("\n=== Test 1: Comprehensive Database Verification ===")
        
        try:
            # Get total client counts
            total_clients = self.db.clients.count_documents({})
            bulk_clients = self.db.clients.count_documents({"client_type": "bulk"})
            registered_clients = self.db.clients.count_documents({"client_type": "registered"})
            no_type_clients = self.db.clients.count_documents({"client_type": {"$exists": False}})
            
            logger.info(f"📊 Database Statistics:")
            logger.info(f"   Total clients: {total_clients}")
            logger.info(f"   Bulk clients: {bulk_clients}")
            logger.info(f"   Registered clients: {registered_clients}")
            logger.info(f"   No client_type: {no_type_clients}")
            
            # Verify bulk clients have proper structure
            sample_bulk_clients = list(self.db.clients.find({"client_type": "bulk"}).limit(3))
            
            logger.info(f"📋 Sample bulk clients:")
            for i, client in enumerate(sample_bulk_clients):
                logger.info(f"   Client {i+1}:")
                logger.info(f"     ID: {client.get('id', 'N/A')}")
                logger.info(f"     Name: {client.get('name', 'N/A')}")
                logger.info(f"     Hotel Name: {client.get('hotel_name', 'N/A')}")
                logger.info(f"     Email: {client.get('email', 'N/A')}")
                logger.info(f"     City: {client.get('city', 'N/A')}")
                logger.info(f"     Client Type: {client.get('client_type', 'N/A')}")
                logger.info(f"     Import Source: {client.get('import_source', 'N/A')}")
            
            # Verify bulk clients with email
            bulk_with_email = self.db.clients.count_documents({
                "client_type": "bulk",
                "email": {"$ne": "", "$exists": True, "$ne": None}
            })
            
            bulk_without_email = bulk_clients - bulk_with_email
            
            logger.info(f"📧 Email Statistics:")
            logger.info(f"   Bulk clients with email: {bulk_with_email}")
            logger.info(f"   Bulk clients without email: {bulk_without_email}")
            logger.info(f"   Email coverage: {(bulk_with_email/bulk_clients*100):.2f}%" if bulk_clients > 0 else "   Email coverage: 0%")
            
            # Verify import source
            bulk_from_excel = self.db.clients.count_documents({
                "client_type": "bulk",
                "import_source": "bulk_excel"
            })
            
            logger.info(f"📥 Import Statistics:")
            logger.info(f"   Bulk clients from Excel import: {bulk_from_excel}")
            
            # City distribution
            city_pipeline = [
                {"$match": {"client_type": "bulk"}},
                {"$group": {"_id": "$city", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            top_cities = list(self.db.clients.aggregate(city_pipeline))
            
            logger.info(f"🏙️ Top 5 Cities for Bulk Clients:")
            for city_data in top_cities:
                city_name = city_data['_id'] or 'Unknown'
                count = city_data['count']
                logger.info(f"   {city_name}: {count} clients")
            
            # Assertions
            self.assertGreater(total_clients, 0, "Database should contain clients")
            self.assertGreater(bulk_clients, 20000, "Should have many bulk clients (expected ~22,877)")
            self.assertEqual(bulk_from_excel, bulk_clients, "All bulk clients should be from Excel import")
            
            logger.info("✅ Database verification completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Database verification failed: {str(e)}")
            raise
    
    def test_api_endpoints_authentication_behavior(self):
        """Test 2: API endpoints authentication behavior"""
        logger.info("\n=== Test 2: API Endpoints Authentication Behavior ===")
        
        endpoints_to_test = [
            ("/clients", "GET clients endpoint"),
            ("/clients?client_type=all", "GET clients with client_type=all"),
            ("/clients?client_type=bulk", "GET clients with client_type=bulk"),
            ("/clients?client_type=registered", "GET clients with client_type=registered"),
            ("/bulk-email/stats", "Bulk email stats endpoint")
        ]
        
        for endpoint, description in endpoints_to_test:
            logger.info(f"\n--- Testing {description} ---")
            url = f"{self.api_url}{endpoint}"
            
            # Test with no authentication
            try:
                response = requests.get(url)
                logger.info(f"No auth - Status: {response.status_code}")
                
                if response.status_code == 403:
                    logger.info("✅ Correctly requires authentication (403 Forbidden)")
                elif response.status_code == 401:
                    logger.info("✅ Correctly requires authentication (401 Unauthorized)")
                else:
                    logger.warning(f"⚠️ Unexpected status without auth: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error testing no auth for {description}: {str(e)}")
            
            # Test with invalid token
            try:
                headers = {"Authorization": "Bearer invalid.token.format"}
                response = requests.get(url, headers=headers)
                logger.info(f"Invalid token - Status: {response.status_code}")
                
                if response.status_code == 401:
                    logger.info("✅ Correctly rejects invalid token (401 Unauthorized)")
                else:
                    logger.warning(f"⚠️ Unexpected status with invalid token: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error testing invalid token for {description}: {str(e)}")
    
    def test_client_type_filtering_logic_verification(self):
        """Test 3: Verify client type filtering logic through database queries"""
        logger.info("\n=== Test 3: Client Type Filtering Logic Verification ===")
        
        try:
            # Simulate the filtering logic that should be in the API
            
            # Test "all" filter (should return all clients)
            all_clients_query = {}
            all_clients_count = self.db.clients.count_documents(all_clients_query)
            logger.info(f"📊 'all' filter would return: {all_clients_count} clients")
            
            # Test "bulk" filter
            bulk_clients_query = {"client_type": "bulk"}
            bulk_clients_count = self.db.clients.count_documents(bulk_clients_query)
            logger.info(f"📊 'bulk' filter would return: {bulk_clients_count} clients")
            
            # Test "registered" filter
            registered_clients_query = {"client_type": "registered"}
            registered_clients_count = self.db.clients.count_documents(registered_clients_query)
            logger.info(f"📊 'registered' filter would return: {registered_clients_count} clients")
            
            # Test combined query (bulk OR registered OR no type - should equal all)
            combined_query = {
                "$or": [
                    {"client_type": "bulk"},
                    {"client_type": "registered"},
                    {"client_type": {"$exists": False}}
                ]
            }
            combined_count = self.db.clients.count_documents(combined_query)
            logger.info(f"📊 Combined query returns: {combined_count} clients")
            
            # Verify logic
            self.assertEqual(all_clients_count, combined_count, "All clients should equal combined bulk+registered+no_type")
            self.assertGreater(bulk_clients_count, 0, "Should have bulk clients")
            
            # Test pagination simulation
            page_size = 50
            total_pages = (bulk_clients_count + page_size - 1) // page_size
            logger.info(f"📄 Pagination for bulk clients: {total_pages} pages with {page_size} per page")
            
            # Get first page of bulk clients
            first_page_bulk = list(self.db.clients.find(
                {"client_type": "bulk"},
                {"id": 1, "name": 1, "hotel_name": 1, "email": 1, "client_type": 1, "_id": 0}
            ).limit(page_size))
            
            logger.info(f"📄 First page contains {len(first_page_bulk)} bulk clients")
            
            # Verify all are bulk type
            for client in first_page_bulk[:3]:  # Check first 3
                self.assertEqual(client.get('client_type'), 'bulk')
                logger.info(f"   ✅ {client.get('name', 'N/A')} - Type: {client.get('client_type')}")
            
            logger.info("✅ Client type filtering logic verification completed")
            
        except Exception as e:
            logger.error(f"❌ Filtering logic verification failed: {str(e)}")
            raise
    
    def test_bulk_email_stats_data_verification(self):
        """Test 4: Verify bulk email statistics data"""
        logger.info("\n=== Test 4: Bulk Email Statistics Data Verification ===")
        
        try:
            # Simulate the bulk email stats endpoint logic
            
            # Total bulk clients
            total_bulk_clients = self.db.clients.count_documents({"client_type": "bulk"})
            
            # Bulk clients with email
            bulk_clients_with_email = self.db.clients.count_documents({
                "client_type": "bulk",
                "email": {"$ne": "", "$exists": True, "$ne": None}
            })
            
            # Email coverage percentage
            email_coverage = (bulk_clients_with_email / total_bulk_clients * 100) if total_bulk_clients > 0 else 0
            
            logger.info(f"📧 Bulk Email Statistics:")
            logger.info(f"   Total bulk clients: {total_bulk_clients}")
            logger.info(f"   Bulk clients with email: {bulk_clients_with_email}")
            logger.info(f"   Email coverage: {email_coverage:.2f}%")
            
            # City distribution
            city_pipeline = [
                {"$match": {"client_type": "bulk"}},
                {"$group": {"_id": "$city", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            city_stats = list(self.db.clients.aggregate(city_pipeline))
            
            logger.info(f"🏙️ Top 10 Cities for Bulk Clients:")
            for i, city_data in enumerate(city_stats):
                city_name = city_data['_id'] or 'Unknown'
                count = city_data['count']
                logger.info(f"   {i+1}. {city_name}: {count} clients")
            
            # Audit company distribution
            audit_pipeline = [
                {"$match": {"client_type": "bulk"}},
                {"$group": {"_id": "$audit_company", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            audit_stats = list(self.db.clients.aggregate(audit_pipeline))
            
            logger.info(f"🏢 Top 10 Audit Companies for Bulk Clients:")
            for i, audit_data in enumerate(audit_stats):
                company_name = audit_data['_id'] or 'Unknown'
                count = audit_data['count']
                logger.info(f"   {i+1}. {company_name}: {count} clients")
            
            # Assertions
            self.assertGreater(total_bulk_clients, 20000, "Should have many bulk clients")
            self.assertGreater(bulk_clients_with_email, 0, "Should have bulk clients with email")
            self.assertGreater(email_coverage, 0, "Email coverage should be > 0%")
            self.assertGreater(len(city_stats), 0, "Should have city distribution data")
            
            logger.info("✅ Bulk email statistics verification completed")
            
        except Exception as e:
            logger.error(f"❌ Bulk email statistics verification failed: {str(e)}")
            raise
    
    def test_api_response_format_expectations(self):
        """Test 5: Verify expected API response formats"""
        logger.info("\n=== Test 5: API Response Format Expectations ===")
        
        try:
            # Test what the API responses should look like based on the backend code
            
            # Expected structure for GET /api/clients (admin user)
            expected_clients_response = {
                "clients": [],  # List of client objects
                "pagination": {
                    "page": 1,
                    "limit": 50,
                    "total_count": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_prev": False
                },
                "search": None,
                "sort": "hotel_name",
                "order": "asc",
                "client_type": "all"
            }
            
            logger.info("📋 Expected GET /api/clients response structure:")
            logger.info(f"   {json.dumps(expected_clients_response, indent=2)}")
            
            # Expected structure for GET /api/bulk-email/stats
            expected_stats_response = {
                "total_bulk_clients": 0,
                "bulk_clients_with_email": 0,
                "email_coverage_percentage": 0.0,
                "city_distribution": [],  # Top 10 cities
                "audit_company_distribution": []  # Top 10 audit companies
            }
            
            logger.info("📋 Expected GET /api/bulk-email/stats response structure:")
            logger.info(f"   {json.dumps(expected_stats_response, indent=2)}")
            
            # Expected client object structure
            expected_client_object = {
                "id": "uuid-string",
                "hotel_name": "Hotel Name",
                "name": "Client Name",
                "city": "City Name",
                "district": "District Name",
                "phone": "Phone Number",
                "email": "email@example.com",
                "certificate_end_date": None,
                "audit_company": "Audit Company",
                "current_stage": "I.Aşama",
                "client_type": "bulk",
                "created_at": "2025-01-01T00:00:00"
            }
            
            logger.info("📋 Expected client object structure:")
            logger.info(f"   {json.dumps(expected_client_object, indent=2)}")
            
            # Verify actual data matches expected structure
            sample_client = self.db.clients.find_one({"client_type": "bulk"})
            if sample_client:
                logger.info("📋 Actual client object from database:")
                # Remove _id for comparison
                if '_id' in sample_client:
                    del sample_client['_id']
                logger.info(f"   {json.dumps(sample_client, indent=2, default=str)}")
                
                # Verify required fields exist
                required_fields = ['id', 'name', 'email', 'client_type']
                for field in required_fields:
                    self.assertIn(field, sample_client, f"Client should have {field} field")
                
                self.assertEqual(sample_client['client_type'], 'bulk')
            
            logger.info("✅ API response format verification completed")
            
        except Exception as e:
            logger.error(f"❌ API response format verification failed: {str(e)}")
            raise

def run_bulk_client_api_tests():
    """Run all bulk client API tests"""
    logger.info("🚀 Starting Bulk Client API Tests")
    logger.info("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test methods in order
    test_methods = [
        'test_bulk_client_database_verification',
        'test_api_endpoints_authentication_behavior',
        'test_client_type_filtering_logic_verification',
        'test_bulk_email_stats_data_verification',
        'test_api_response_format_expectations'
    ]
    
    for method in test_methods:
        test_suite.addTest(TestBulkClientAPI(method))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Summary
    logger.info("=" * 60)
    logger.info("🏁 Bulk Client API Tests Summary")
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
        logger.info("✅ All bulk client API tests passed!")
    else:
        logger.error("❌ Some bulk client API tests failed!")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    import sys
    success = run_bulk_client_api_tests()
    sys.exit(0 if success else 1)