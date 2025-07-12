#!/usr/bin/env python3
"""
URGENT WASTE MANAGEMENT DATA SUBMISSION DEBUG TESTING

This test specifically addresses the user-reported issue:
"Kullanıcı atık verisi giriyor ama tabloya gelmiyor ve grafik oluşmuyor"
(User enters waste data but it doesn't appear in the table and no graph is created)

Test Scenarios:
1. POST /api/consumptions/waste endpoint test - check if data is being saved
2. GET /api/consumptions/waste endpoint test - check if data can be retrieved  
3. Database verification - check if waste data exists in MongoDB
4. Consultant client_id requirement - verify consultant can submit with client_id

Suspected Issues:
- Frontend not sending client_id for consultant users
- Backend not saving data properly
- Database connection issues
- Consultant access logic problems
"""

import requests
import json
import logging
import uuid
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"
MONGO_URL = "mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster"
DB_NAME = "rotacrm"

# Test tokens (these are sample tokens - in real scenario they would be valid Clerk tokens)
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ0xJRU5UIiwiZW1haWwiOiJjbGllbnRAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBDbGllbnQifQ.signature"
CONSULTANT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ09OU1VMVEFOVCIsImVtYWlsIjoiY29uc3VsdGFudEB0ZXN0LmNvbSIsIm5hbWUiOiJUZXN0IENvbnN1bHRhbnQifQ.signature"
INVALID_TOKEN = "invalid.token.format"

class WasteManagementUrgentTest:
    def __init__(self):
        self.api_url = RAILWAY_API_URL
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
        
        # Test data for waste submission
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Use realistic waste data as per the app requirements
        self.test_waste_data = {
            "year": 2025,  # Use 2025 as specified in test requirements
            "month": 1,    # January
            "organic_waste": 150.5,      # kg - realistic hotel organic waste
            "plastic_waste": 45.0,       # kg - plastic bottles, containers
            "glass_waste": 25.5,         # kg - glass bottles
            "paper_waste": 35.0,         # kg - paper, cardboard
            "metal_waste": 12.0,         # kg - cans, metal containers
            "electronic_waste": 3.0,     # kg - small electronics
            "oil_waste": 8.0,            # litre - cooking oil
            "mixed_waste": 40.0,         # kg - non-recyclable waste
            "accommodation_count": 180   # Number of guests for per-person calculation
        }
        
        # Test client ID (this should be a real client ID from the database)
        self.test_client_id = "7a992a86-e2f4-4ed5-99f7-bab4966b7306"  # From test_result.md
        
    async def connect_to_database(self):
        """Connect to MongoDB database for direct verification"""
        try:
            self.mongo_client = AsyncIOMotorClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            logger.info("✅ Connected to MongoDB database")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {str(e)}")
            return False
    
    async def verify_database_connection(self):
        """Verify database connection and check collections"""
        try:
            # Test database connection
            await self.db.command("ping")
            logger.info("✅ Database ping successful")
            
            # Check if waste_management collection exists
            collections = await self.db.list_collection_names()
            logger.info(f"📊 Available collections: {collections}")
            
            if "waste_management" in collections:
                logger.info("✅ waste_management collection exists")
                
                # Count existing waste records
                waste_count = await self.db.waste_management.count_documents({})
                logger.info(f"📊 Existing waste records in database: {waste_count}")
                
                # Show sample waste records
                sample_records = await self.db.waste_management.find({}).limit(3).to_list(length=None)
                for i, record in enumerate(sample_records):
                    logger.info(f"📋 Sample waste record {i+1}: client_id={record.get('client_id')}, year={record.get('year')}, month={record.get('month')}, total_waste={record.get('total_waste')}")
            else:
                logger.warning("⚠️ waste_management collection does not exist")
            
            return True
        except Exception as e:
            logger.error(f"❌ Database verification failed: {str(e)}")
            return False
    
    def test_post_waste_endpoint_admin(self):
        """Test POST /api/consumptions/waste with admin user"""
        logger.info("\n" + "="*80)
        logger.info("🧪 TEST 1: POST /api/consumptions/waste with ADMIN user")
        logger.info("="*80)
        
        url = f"{self.api_url}/consumptions/waste"
        
        # Admin must specify client_id
        admin_waste_data = self.test_waste_data.copy()
        admin_waste_data["client_id"] = self.test_client_id
        
        try:
            logger.info(f"📤 Sending POST request to: {url}")
            logger.info(f"📋 Request data: {json.dumps(admin_waste_data, indent=2)}")
            
            response = requests.post(url, headers=self.headers_admin, json=admin_waste_data)
            
            logger.info(f"📥 Response status code: {response.status_code}")
            logger.info(f"📥 Response headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                logger.info(f"📥 Response data: {json.dumps(response_data, indent=2)}")
            except:
                logger.info(f"📥 Response text: {response.text}")
            
            # Analyze response
            if response.status_code == 200 or response.status_code == 201:
                logger.info("✅ SUCCESS: Waste data submitted successfully by admin")
                if "id" in response_data:
                    self.created_waste_id = response_data["id"]
                    logger.info(f"💾 Created waste record ID: {self.created_waste_id}")
                return True
            elif response.status_code == 400:
                logger.warning("⚠️ BAD REQUEST: Possible duplicate record or validation error")
                logger.warning(f"Error details: {response_data.get('detail', 'No details')}")
                return False
            elif response.status_code == 401:
                logger.error("❌ AUTHENTICATION FAILED: Invalid or expired token")
                return False
            elif response.status_code == 403:
                logger.error("❌ AUTHORIZATION FAILED: Insufficient permissions")
                return False
            else:
                logger.error(f"❌ UNEXPECTED ERROR: Status code {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ REQUEST FAILED: {str(e)}")
            return False
    
    def test_post_waste_endpoint_consultant(self):
        """Test POST /api/consumptions/waste with consultant user"""
        logger.info("\n" + "="*80)
        logger.info("🧪 TEST 2: POST /api/consumptions/waste with CONSULTANT user")
        logger.info("="*80)
        
        url = f"{self.api_url}/consumptions/waste"
        
        # Consultant must specify client_id for assigned clients
        consultant_waste_data = self.test_waste_data.copy()
        consultant_waste_data["client_id"] = self.test_client_id
        consultant_waste_data["month"] = 2  # Use different month to avoid conflict
        
        try:
            logger.info(f"📤 Sending POST request to: {url}")
            logger.info(f"📋 Request data: {json.dumps(consultant_waste_data, indent=2)}")
            
            response = requests.post(url, headers=self.headers_consultant, json=consultant_waste_data)
            
            logger.info(f"📥 Response status code: {response.status_code}")
            
            try:
                response_data = response.json()
                logger.info(f"📥 Response data: {json.dumps(response_data, indent=2)}")
            except:
                logger.info(f"📥 Response text: {response.text}")
            
            # Analyze response
            if response.status_code == 200 or response.status_code == 201:
                logger.info("✅ SUCCESS: Waste data submitted successfully by consultant")
                return True
            elif response.status_code == 400:
                logger.warning("⚠️ BAD REQUEST: Possible validation error or missing client_id")
                logger.warning(f"Error details: {response_data.get('detail', 'No details')}")
                return False
            elif response.status_code == 401:
                logger.error("❌ AUTHENTICATION FAILED: Invalid or expired token")
                return False
            elif response.status_code == 403:
                logger.error("❌ AUTHORIZATION FAILED: Consultant not assigned to client or insufficient permissions")
                logger.error(f"Error details: {response_data.get('detail', 'No details')}")
                return False
            else:
                logger.error(f"❌ UNEXPECTED ERROR: Status code {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ REQUEST FAILED: {str(e)}")
            return False
    
    def test_post_waste_endpoint_client(self):
        """Test POST /api/consumptions/waste with client user"""
        logger.info("\n" + "="*80)
        logger.info("🧪 TEST 3: POST /api/consumptions/waste with CLIENT user")
        logger.info("="*80)
        
        url = f"{self.api_url}/consumptions/waste"
        
        # Client should not specify client_id (uses their own)
        client_waste_data = self.test_waste_data.copy()
        client_waste_data["month"] = 3  # Use different month to avoid conflict
        # Remove client_id for client users
        client_waste_data.pop("client_id", None)
        
        try:
            logger.info(f"📤 Sending POST request to: {url}")
            logger.info(f"📋 Request data: {json.dumps(client_waste_data, indent=2)}")
            
            response = requests.post(url, headers=self.headers_client, json=client_waste_data)
            
            logger.info(f"📥 Response status code: {response.status_code}")
            
            try:
                response_data = response.json()
                logger.info(f"📥 Response data: {json.dumps(response_data, indent=2)}")
            except:
                logger.info(f"📥 Response text: {response.text}")
            
            # Analyze response
            if response.status_code == 200 or response.status_code == 201:
                logger.info("✅ SUCCESS: Waste data submitted successfully by client")
                return True
            elif response.status_code == 400:
                logger.warning("⚠️ BAD REQUEST: Client not properly linked or validation error")
                logger.warning(f"Error details: {response_data.get('detail', 'No details')}")
                return False
            elif response.status_code == 401:
                logger.error("❌ AUTHENTICATION FAILED: Invalid or expired token")
                return False
            elif response.status_code == 403:
                logger.error("❌ AUTHORIZATION FAILED: Client not assigned or insufficient permissions")
                return False
            else:
                logger.error(f"❌ UNEXPECTED ERROR: Status code {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ REQUEST FAILED: {str(e)}")
            return False
    
    def test_get_waste_endpoint(self):
        """Test GET /api/consumptions/waste endpoint"""
        logger.info("\n" + "="*80)
        logger.info("🧪 TEST 4: GET /api/consumptions/waste - Data Retrieval Test")
        logger.info("="*80)
        
        url = f"{self.api_url}/consumptions/waste"
        
        # Test with admin user
        try:
            logger.info(f"📤 Sending GET request to: {url} (Admin user)")
            
            response = requests.get(url, headers=self.headers_admin)
            
            logger.info(f"📥 Response status code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    logger.info(f"📊 Found {len(response_data)} waste records")
                    
                    if len(response_data) > 0:
                        logger.info("✅ SUCCESS: Waste data can be retrieved")
                        
                        # Show sample records
                        for i, record in enumerate(response_data[:3]):
                            logger.info(f"📋 Record {i+1}: client_id={record.get('client_id')}, year={record.get('year')}, month={record.get('month')}, total_waste={record.get('total_waste')}")
                        
                        return True
                    else:
                        logger.warning("⚠️ NO DATA: No waste records found in database")
                        return False
                        
                except Exception as e:
                    logger.error(f"❌ JSON PARSE ERROR: {str(e)}")
                    logger.info(f"📥 Response text: {response.text}")
                    return False
            else:
                try:
                    response_data = response.json()
                    logger.error(f"❌ GET REQUEST FAILED: {response_data.get('detail', 'No details')}")
                except:
                    logger.error(f"❌ GET REQUEST FAILED: Status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ REQUEST FAILED: {str(e)}")
            return False
    
    def test_get_waste_analytics_endpoint(self):
        """Test GET /api/consumptions/waste/analytics endpoint"""
        logger.info("\n" + "="*80)
        logger.info("🧪 TEST 5: GET /api/consumptions/waste/analytics - Graph Data Test")
        logger.info("="*80)
        
        url = f"{self.api_url}/consumptions/waste/analytics"
        
        # Test with admin user and client_id parameter
        try:
            params = {"client_id": self.test_client_id, "year": 2025}
            logger.info(f"📤 Sending GET request to: {url} with params: {params}")
            
            response = requests.get(url, headers=self.headers_admin, params=params)
            
            logger.info(f"📥 Response status code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    logger.info(f"📊 Analytics data structure: {list(response_data.keys())}")
                    
                    # Check required analytics fields
                    required_fields = ["yearly_totals", "monthly_data", "waste_breakdown", "recycling_performance"]
                    missing_fields = [field for field in required_fields if field not in response_data]
                    
                    if not missing_fields:
                        logger.info("✅ SUCCESS: Analytics data structure is complete")
                        
                        # Check data content
                        yearly_totals = response_data.get("yearly_totals", {})
                        monthly_data = response_data.get("monthly_data", [])
                        waste_breakdown = response_data.get("waste_breakdown", {})
                        recycling_performance = response_data.get("recycling_performance", {})
                        
                        logger.info(f"📊 Yearly totals: {yearly_totals}")
                        logger.info(f"📊 Monthly data count: {len(monthly_data)}")
                        logger.info(f"📊 Waste breakdown: {waste_breakdown}")
                        logger.info(f"📊 Recycling performance: {recycling_performance}")
                        
                        if monthly_data:
                            logger.info("✅ SUCCESS: Graph data is available")
                            return True
                        else:
                            logger.warning("⚠️ NO GRAPH DATA: Monthly data is empty")
                            return False
                    else:
                        logger.error(f"❌ INCOMPLETE DATA: Missing fields: {missing_fields}")
                        return False
                        
                except Exception as e:
                    logger.error(f"❌ JSON PARSE ERROR: {str(e)}")
                    logger.info(f"📥 Response text: {response.text}")
                    return False
            else:
                try:
                    response_data = response.json()
                    logger.error(f"❌ ANALYTICS REQUEST FAILED: {response_data.get('detail', 'No details')}")
                except:
                    logger.error(f"❌ ANALYTICS REQUEST FAILED: Status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ REQUEST FAILED: {str(e)}")
            return False
    
    async def test_database_direct_verification(self):
        """Test 6: Direct database verification"""
        logger.info("\n" + "="*80)
        logger.info("🧪 TEST 6: Direct Database Verification")
        logger.info("="*80)
        
        try:
            # Check if our test data was actually saved
            filter_query = {
                "client_id": self.test_client_id,
                "year": 2025
            }
            
            logger.info(f"🔍 Searching for waste records with filter: {filter_query}")
            
            records = await self.db.waste_management.find(filter_query).to_list(length=None)
            
            logger.info(f"📊 Found {len(records)} waste records for test client")
            
            if records:
                logger.info("✅ SUCCESS: Waste data exists in database")
                
                for i, record in enumerate(records):
                    logger.info(f"📋 Record {i+1}: ID={record.get('id')}, month={record.get('month')}, total_waste={record.get('total_waste')}, created_at={record.get('created_at')}")
                
                return True
            else:
                logger.warning("⚠️ NO DATA: No waste records found in database for test client")
                
                # Check if there are any waste records at all
                all_records = await self.db.waste_management.find({}).limit(5).to_list(length=None)
                logger.info(f"📊 Total waste records in database: {len(all_records)}")
                
                if all_records:
                    logger.info("📋 Sample records from database:")
                    for i, record in enumerate(all_records):
                        logger.info(f"   Record {i+1}: client_id={record.get('client_id')}, year={record.get('year')}, month={record.get('month')}")
                
                return False
                
        except Exception as e:
            logger.error(f"❌ DATABASE VERIFICATION FAILED: {str(e)}")
            return False
    
    def test_authentication_and_authorization(self):
        """Test 7: Authentication and authorization scenarios"""
        logger.info("\n" + "="*80)
        logger.info("🧪 TEST 7: Authentication & Authorization")
        logger.info("="*80)
        
        url = f"{self.api_url}/consumptions/waste"
        
        # Test with invalid token
        logger.info("🔐 Testing with invalid token...")
        try:
            response = requests.post(url, headers=self.headers_invalid, json=self.test_waste_data)
            logger.info(f"📥 Invalid token response: {response.status_code}")
            
            if response.status_code == 401:
                logger.info("✅ SUCCESS: Invalid token correctly rejected")
            else:
                logger.warning(f"⚠️ UNEXPECTED: Expected 401, got {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Invalid token test failed: {str(e)}")
        
        # Test with no token
        logger.info("🔐 Testing with no authentication...")
        try:
            response = requests.post(url, headers=self.headers_no_auth, json=self.test_waste_data)
            logger.info(f"📥 No auth response: {response.status_code}")
            
            if response.status_code == 403:
                logger.info("✅ SUCCESS: No authentication correctly rejected")
            else:
                logger.warning(f"⚠️ UNEXPECTED: Expected 403, got {response.status_code}")
        except Exception as e:
            logger.error(f"❌ No auth test failed: {str(e)}")
        
        return True
    
    async def run_all_tests(self):
        """Run all waste management tests"""
        logger.info("\n" + "🚨"*40)
        logger.info("🚨 URGENT WASTE MANAGEMENT DATA SUBMISSION DEBUG TESTING")
        logger.info("🚨 Issue: User enters waste data but it doesn't appear in table/graph")
        logger.info("🚨"*40)
        
        # Connect to database
        if not await self.connect_to_database():
            logger.error("❌ Cannot proceed without database connection")
            return
        
        # Verify database
        if not await self.verify_database_connection():
            logger.error("❌ Database verification failed")
            return
        
        # Run tests
        test_results = []
        
        # Test 1: Admin POST
        result1 = self.test_post_waste_endpoint_admin()
        test_results.append(("Admin POST", result1))
        
        # Test 2: Consultant POST
        result2 = self.test_post_waste_endpoint_consultant()
        test_results.append(("Consultant POST", result2))
        
        # Test 3: Client POST
        result3 = self.test_post_waste_endpoint_client()
        test_results.append(("Client POST", result3))
        
        # Test 4: GET data retrieval
        result4 = self.test_get_waste_endpoint()
        test_results.append(("GET Data Retrieval", result4))
        
        # Test 5: Analytics/Graph data
        result5 = self.test_get_waste_analytics_endpoint()
        test_results.append(("Analytics/Graph Data", result5))
        
        # Test 6: Database verification
        result6 = await self.test_database_direct_verification()
        test_results.append(("Database Verification", result6))
        
        # Test 7: Authentication
        result7 = self.test_authentication_and_authorization()
        test_results.append(("Authentication", result7))
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("📊 WASTE MANAGEMENT TEST RESULTS SUMMARY")
        logger.info("="*80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} {test_name}")
            if result:
                passed_tests += 1
        
        logger.info(f"\n📊 Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED: Waste management system is working correctly")
        else:
            logger.error("🚨 SOME TESTS FAILED: Issues found in waste management system")
            
            # Provide diagnostic information
            logger.info("\n🔍 DIAGNOSTIC INFORMATION:")
            
            if not test_results[0][1]:  # Admin POST failed
                logger.error("❌ Admin cannot submit waste data - check authentication and permissions")
            
            if not test_results[1][1]:  # Consultant POST failed
                logger.error("❌ Consultant cannot submit waste data - check client assignment and permissions")
            
            if not test_results[2][1]:  # Client POST failed
                logger.error("❌ Client cannot submit waste data - check client linking and permissions")
            
            if not test_results[3][1]:  # GET failed
                logger.error("❌ Cannot retrieve waste data - check database connection and data existence")
            
            if not test_results[4][1]:  # Analytics failed
                logger.error("❌ Cannot get analytics/graph data - check data processing and calculations")
            
            if not test_results[5][1]:  # Database verification failed
                logger.error("❌ Data not found in database - check data persistence and storage")
        
        # Close database connection
        self.mongo_client.close()

async def main():
    """Main test execution"""
    test = WasteManagementUrgentTest()
    await test.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())