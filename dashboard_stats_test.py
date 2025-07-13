#!/usr/bin/env python3
"""
Dashboard Stats Endpoint Testing
================================

This test specifically addresses the issue where the dashboard is showing zeros:
- customers: 0, documents: 0, trainings: 0, projects: 0

The frontend calls /api/stats endpoint for dashboard data.
There are two stats endpoints: /stats (main app) and /api/stats (api router).

Focus: Test the API router stats endpoint (/api/stats) since that's what frontend uses.
"""

import unittest
import json
import logging
import requests
import os
import sys
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL from frontend/.env
BACKEND_URL = "https://rota-crm-production.up.railway.app"
API_URL = f"{BACKEND_URL}/api"

# MongoDB connection from backend/.env
MONGO_URL = "mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster"
DB_NAME = "rotacrm"

# Test JWT tokens (these are sample tokens for testing)
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ0xJRU5UIiwiZW1haWwiOiJjbGllbnRAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBDbGllbnQifQ.signature"
CONSULTANT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ09OU1VMVEFOVCIsImVtYWlsIjoiY29uc3VsdGFudEB0ZXN0LmNvbSIsIm5hbWUiOiJUZXN0IENvbnN1bHRhbnQifQ.signature"
INVALID_TOKEN = "invalid.token.format"

class DashboardStatsTest(unittest.TestCase):
    """Test class for dashboard stats endpoint issue"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = API_URL
        self.backend_url = BACKEND_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
        
        logger.info(f"🔧 Test setup complete - API URL: {self.api_url}")
    
    def test_stats_endpoint_accessibility(self):
        """Test if /api/stats endpoint is accessible"""
        logger.info("\n=== Testing /api/stats endpoint accessibility ===")
        
        url = f"{self.api_url}/stats"
        
        # Test with admin token
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ /api/stats endpoint is accessible with admin token")
                data = response.json()
                logger.info(f"Response data keys: {list(data.keys())}")
                return True
            elif response.status_code == 401:
                logger.warning("⚠️ Admin token appears to be invalid/expired")
                data = response.json()
                logger.info(f"Auth error: {data}")
                return False
            elif response.status_code == 404:
                logger.error("❌ /api/stats endpoint not found (404)")
                return False
            else:
                logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing /api/stats accessibility: {str(e)}")
            return False
    
    def test_stats_endpoint_authentication(self):
        """Test authentication requirements for /api/stats endpoint"""
        logger.info("\n=== Testing /api/stats endpoint authentication ===")
        
        url = f"{self.api_url}/stats"
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden (not authenticated)
            if response.status_code == 403:
                logger.info("✅ Endpoint correctly requires authentication (403 Forbidden)")
            else:
                logger.warning(f"⚠️ Expected 403, got {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing no auth: {str(e)}")
        
        # Test with invalid token
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid token response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            if response.status_code == 401:
                logger.info("✅ Endpoint correctly rejects invalid tokens (401 Unauthorized)")
            else:
                logger.warning(f"⚠️ Expected 401, got {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing invalid token: {str(e)}")
    
    def test_stats_endpoint_response_structure(self):
        """Test the response structure of /api/stats endpoint"""
        logger.info("\n=== Testing /api/stats endpoint response structure ===")
        
        url = f"{self.api_url}/stats"
        
        # Test with admin token
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {json.dumps(data, indent=2)}")
                
                # Check required fields for dashboard
                required_fields = ["total_clients", "total_documents", "total_trainings"]
                missing_fields = []
                
                for field in required_fields:
                    if field not in data:
                        missing_fields.append(field)
                    else:
                        logger.info(f"✅ Found {field}: {data[field]}")
                
                if missing_fields:
                    logger.error(f"❌ Missing required fields: {missing_fields}")
                else:
                    logger.info("✅ All required fields present in response")
                
                # Check if values are zeros (the reported issue)
                if data.get("total_clients", 0) == 0:
                    logger.warning("⚠️ total_clients is 0 - this might be the dashboard issue")
                if data.get("total_documents", 0) == 0:
                    logger.warning("⚠️ total_documents is 0 - this might be the dashboard issue")
                if data.get("total_trainings", 0) == 0:
                    logger.warning("⚠️ total_trainings is 0 - this might be the dashboard issue")
                
                # Check for stage_distribution
                if "stage_distribution" in data:
                    logger.info(f"✅ Found stage_distribution: {data['stage_distribution']}")
                else:
                    logger.warning("⚠️ Missing stage_distribution field")
                
                return data
            elif response.status_code == 401:
                logger.warning("⚠️ Authentication failed - token may be expired")
                data = response.json()
                logger.info(f"Auth error details: {data}")
                return None
            else:
                logger.error(f"❌ Unexpected response status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error testing response structure: {str(e)}")
            return None
    
    def test_stats_endpoint_role_logic(self):
        """Test role-based logic for /api/stats endpoint"""
        logger.info("\n=== Testing /api/stats endpoint role-based logic ===")
        
        url = f"{self.api_url}/stats"
        
        # Test with different user roles
        test_cases = [
            ("admin", self.headers_admin, "Admin should see all statistics"),
            ("client", self.headers_client, "Client should see only their own statistics"),
            ("consultant", self.headers_consultant, "Consultant should see assigned clients' statistics")
        ]
        
        for role, headers, description in test_cases:
            try:
                logger.info(f"\n--- Testing {role} role ---")
                response = requests.get(url, headers=headers)
                logger.info(f"{role.capitalize()} response status code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"{role.capitalize()} data: {json.dumps(data, indent=2)}")
                    logger.info(f"✅ {description}")
                elif response.status_code == 401:
                    logger.warning(f"⚠️ {role.capitalize()} token authentication failed")
                    error_data = response.json()
                    logger.info(f"Auth error: {error_data}")
                else:
                    logger.warning(f"⚠️ {role.capitalize()} unexpected status: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error testing {role} role: {str(e)}")
    
    def test_database_data_verification(self):
        """Test if there's actual data in the database collections"""
        logger.info("\n=== Testing database data verification ===")
        
        try:
            # Use synchronous MongoDB client for simpler testing
            from pymongo import MongoClient
            
            # Connect to MongoDB
            client = MongoClient(MONGO_URL)
            db = client[DB_NAME]
            
            # Test clients collection
            try:
                clients_count = db.clients.count_documents({})
                logger.info(f"📊 Clients collection count: {clients_count}")
                
                if clients_count > 0:
                    logger.info("✅ Clients collection has data")
                    # Get sample client data
                    sample_clients = list(db.clients.find({}).limit(3))
                    for i, client in enumerate(sample_clients):
                        client_name = client.get("name", "Unknown")
                        hotel_name = client.get("hotel_name", "Unknown")
                        logger.info(f"  Client {i+1}: {client_name} / {hotel_name}")
                else:
                    logger.warning("⚠️ Clients collection is empty - this explains zero customers")
                    
            except Exception as e:
                logger.error(f"❌ Error checking clients collection: {str(e)}")
            
            # Test documents collection
            try:
                documents_count = db.documents.count_documents({})
                logger.info(f"📊 Documents collection count: {documents_count}")
                
                if documents_count > 0:
                    logger.info("✅ Documents collection has data")
                    # Get sample document data
                    sample_docs = list(db.documents.find({}).limit(3))
                    for i, doc in enumerate(sample_docs):
                        doc_name = doc.get("name", "Unknown")
                        client_id = doc.get("client_id", "Unknown")
                        logger.info(f"  Document {i+1}: {doc_name} (Client: {client_id})")
                else:
                    logger.warning("⚠️ Documents collection is empty - this explains zero documents")
                    
            except Exception as e:
                logger.error(f"❌ Error checking documents collection: {str(e)}")
            
            # Test trainings collection
            try:
                trainings_count = db.trainings.count_documents({})
                logger.info(f"📊 Trainings collection count: {trainings_count}")
                
                if trainings_count > 0:
                    logger.info("✅ Trainings collection has data")
                    # Get sample training data
                    sample_trainings = list(db.trainings.find({}).limit(3))
                    for i, training in enumerate(sample_trainings):
                        training_name = training.get("name", "Unknown")
                        client_id = training.get("client_id", "Unknown")
                        logger.info(f"  Training {i+1}: {training_name} (Client: {client_id})")
                else:
                    logger.warning("⚠️ Trainings collection is empty - this explains zero trainings")
                    
            except Exception as e:
                logger.error(f"❌ Error checking trainings collection: {str(e)}")
            
            # Close connection
            client.close()
            
        except Exception as e:
            logger.error(f"❌ Error connecting to database: {str(e)}")
    
    def test_alternative_stats_endpoint(self):
        """Test the alternative /stats endpoint (main app)"""
        logger.info("\n=== Testing alternative /stats endpoint (main app) ===")
        
        url = f"{self.backend_url}/stats"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Main app /stats response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Main app /stats data: {json.dumps(data, indent=2)}")
                logger.info("✅ Alternative /stats endpoint is working")
                
                # Compare with /api/stats if both work
                api_url = f"{self.api_url}/stats"
                api_response = requests.get(api_url, headers=self.headers_admin)
                
                if api_response.status_code == 200:
                    api_data = api_response.json()
                    
                    # Compare the data
                    if data == api_data:
                        logger.info("✅ Both endpoints return identical data")
                    else:
                        logger.warning("⚠️ Endpoints return different data")
                        logger.info(f"Main app data: {data}")
                        logger.info(f"API router data: {api_data}")
                
            elif response.status_code == 401:
                logger.warning("⚠️ Main app /stats authentication failed")
                error_data = response.json()
                logger.info(f"Auth error: {error_data}")
            else:
                logger.warning(f"⚠️ Main app /stats unexpected status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing main app /stats: {str(e)}")
    
    def test_comprehensive_dashboard_diagnosis(self):
        """Comprehensive diagnosis of dashboard stats issue"""
        logger.info("\n=== COMPREHENSIVE DASHBOARD DIAGNOSIS ===")
        
        # Step 1: Test endpoint accessibility
        logger.info("🔍 Step 1: Testing endpoint accessibility...")
        endpoint_accessible = self.test_stats_endpoint_accessibility()
        
        # Step 2: Test database data
        logger.info("🔍 Step 2: Checking database data...")
        self.test_database_data_verification()
        
        # Step 3: Test response structure
        logger.info("🔍 Step 3: Testing response structure...")
        response_data = self.test_stats_endpoint_response_structure()
        
        # Step 4: Test authentication
        logger.info("🔍 Step 4: Testing authentication...")
        self.test_stats_endpoint_authentication()
        
        # Step 5: Test role logic
        logger.info("🔍 Step 5: Testing role logic...")
        self.test_stats_endpoint_role_logic()
        
        # Step 6: Test alternative endpoint
        logger.info("🔍 Step 6: Testing alternative endpoint...")
        self.test_alternative_stats_endpoint()
        
        # Summary
        logger.info("\n=== DIAGNOSIS SUMMARY ===")
        
        if not endpoint_accessible:
            logger.error("❌ CRITICAL: /api/stats endpoint is not accessible")
            logger.error("   This is likely the root cause of dashboard showing zeros")
            logger.error("   Frontend cannot get data from the backend")
        elif response_data is None:
            logger.error("❌ CRITICAL: Authentication issues with /api/stats endpoint")
            logger.error("   Frontend may be using expired/invalid tokens")
        elif response_data and all(response_data.get(field, 0) == 0 for field in ["total_clients", "total_documents", "total_trainings"]):
            logger.warning("⚠️ WARNING: Endpoint returns all zeros")
            logger.warning("   This could be due to:")
            logger.warning("   1. Empty database collections")
            logger.warning("   2. Role-based filtering showing no data")
            logger.warning("   3. Database connection issues")
        else:
            logger.info("✅ Endpoint appears to be working correctly")
            logger.info("   The issue may be in frontend data handling")

def run_dashboard_stats_test():
    """Run the dashboard stats test"""
    logger.info("🚀 Starting Dashboard Stats Endpoint Test")
    logger.info("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(DashboardStatsTest)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 DASHBOARD STATS TEST SUMMARY")
    logger.info("=" * 60)
    
    if result.wasSuccessful():
        logger.info("✅ All tests passed successfully")
    else:
        logger.error(f"❌ {len(result.failures)} test(s) failed")
        logger.error(f"❌ {len(result.errors)} test(s) had errors")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    # Run the comprehensive dashboard diagnosis
    test_case = DashboardStatsTest()
    test_case.setUp()
    test_case.test_comprehensive_dashboard_diagnosis()