#!/usr/bin/env python3
"""
Public Stats Endpoint Testing
Test the new /api/stats-public endpoint for dashboard
"""

import requests
import json
import logging
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from frontend .env
BACKEND_URL = "https://rota-crm-production.up.railway.app"
API_URL = f"{BACKEND_URL}/api"

# MongoDB connection from backend .env
MONGO_URL = "mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster"
DB_NAME = "rotacrm"

class PublicStatsTest:
    def __init__(self):
        self.api_url = API_URL
        self.mongo_url = MONGO_URL
        self.db_name = DB_NAME
        self.client = None
        self.db = None
        
    async def connect_to_database(self):
        """Connect to MongoDB database"""
        try:
            self.client = AsyncIOMotorClient(self.mongo_url)
            self.db = self.client[self.db_name]
            logger.info(f"✅ Connected to MongoDB: {self.db_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {str(e)}")
            return False
    
    async def get_database_counts(self):
        """Get actual counts from database"""
        try:
            # Get actual counts from database
            total_clients = await self.db.clients.count_documents({})
            total_documents = await self.db.documents.count_documents({})
            total_trainings = await self.db.trainings.count_documents({})
            
            # Get stage distribution
            stage_1_clients = await self.db.clients.count_documents({"current_stage": "I.Aşama"})
            stage_2_clients = await self.db.clients.count_documents({"current_stage": "II.Aşama"})
            stage_3_clients = await self.db.clients.count_documents({"current_stage": "III.Aşama"})
            
            logger.info(f"📊 DATABASE COUNTS:")
            logger.info(f"   Total Clients: {total_clients}")
            logger.info(f"   Total Documents: {total_documents}")
            logger.info(f"   Total Trainings: {total_trainings}")
            logger.info(f"   Stage 1 Clients: {stage_1_clients}")
            logger.info(f"   Stage 2 Clients: {stage_2_clients}")
            logger.info(f"   Stage 3 Clients: {stage_3_clients}")
            
            return {
                "total_clients": total_clients,
                "total_documents": total_documents,
                "total_trainings": total_trainings,
                "stage_distribution": {
                    "stage_1": stage_1_clients,
                    "stage_2": stage_2_clients,
                    "stage_3": stage_3_clients
                }
            }
        except Exception as e:
            logger.error(f"❌ Error getting database counts: {str(e)}")
            return None
    
    async def get_sample_data(self):
        """Get sample data from database for verification"""
        try:
            # Get sample clients
            clients = await self.db.clients.find({}).limit(5).to_list(length=5)
            logger.info(f"📋 SAMPLE CLIENTS:")
            for i, client in enumerate(clients, 1):
                logger.info(f"   {i}. {client.get('name', 'Unknown')} - Stage: {client.get('current_stage', 'Unknown')}")
            
            # Get sample documents
            documents = await self.db.documents.find({}).limit(3).to_list(length=3)
            logger.info(f"📄 SAMPLE DOCUMENTS:")
            for i, doc in enumerate(documents, 1):
                logger.info(f"   {i}. {doc.get('name', 'Unknown')} - Client: {doc.get('client_id', 'Unknown')}")
            
            # Get sample trainings
            trainings = await self.db.trainings.find({}).limit(3).to_list(length=3)
            logger.info(f"🎓 SAMPLE TRAININGS:")
            for i, training in enumerate(trainings, 1):
                logger.info(f"   {i}. {training.get('name', 'Unknown')} - Client: {training.get('client_id', 'Unknown')}")
                
        except Exception as e:
            logger.error(f"❌ Error getting sample data: {str(e)}")
    
    def test_public_stats_endpoint(self):
        """Test the public stats endpoint"""
        logger.info("🧪 TESTING PUBLIC STATS ENDPOINT")
        logger.info("=" * 50)
        
        try:
            # Test endpoint without authentication
            url = f"{self.api_url}/stats-public"
            logger.info(f"📡 Testing URL: {url}")
            
            response = requests.get(url, timeout=30)
            
            logger.info(f"📊 Response Status: {response.status_code}")
            logger.info(f"📊 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ SUCCESS: Public stats endpoint working!")
                logger.info(f"📊 RESPONSE DATA:")
                logger.info(json.dumps(data, indent=2))
                
                # Verify response structure
                required_fields = ["total_clients", "total_documents", "total_trainings", "stage_distribution"]
                missing_fields = []
                
                for field in required_fields:
                    if field not in data:
                        missing_fields.append(field)
                
                if missing_fields:
                    logger.error(f"❌ Missing required fields: {missing_fields}")
                    return False, data
                
                # Verify stage_distribution structure
                stage_dist = data.get("stage_distribution", {})
                required_stages = ["stage_1", "stage_2", "stage_3"]
                missing_stages = []
                
                for stage in required_stages:
                    if stage not in stage_dist:
                        missing_stages.append(stage)
                
                if missing_stages:
                    logger.error(f"❌ Missing stage distribution fields: {missing_stages}")
                    return False, data
                
                logger.info(f"✅ Response structure is correct!")
                return True, data
                
            else:
                logger.error(f"❌ FAILED: Status {response.status_code}")
                logger.error(f"❌ Response: {response.text}")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ ERROR testing public stats endpoint: {str(e)}")
            return False, None
    
    def test_endpoint_accessibility(self):
        """Test that endpoint is accessible without authentication"""
        logger.info("🔓 TESTING ENDPOINT ACCESSIBILITY (NO AUTH)")
        logger.info("=" * 50)
        
        try:
            url = f"{self.api_url}/stats-public"
            
            # Test without any headers
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"✅ SUCCESS: Endpoint accessible without authentication")
                return True
            elif response.status_code == 401:
                logger.error(f"❌ FAILED: Endpoint requires authentication (401)")
                return False
            elif response.status_code == 403:
                logger.error(f"❌ FAILED: Endpoint forbidden (403)")
                return False
            else:
                logger.error(f"❌ FAILED: Unexpected status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ ERROR testing accessibility: {str(e)}")
            return False
    
    async def compare_api_vs_database(self):
        """Compare API response with actual database data"""
        logger.info("🔍 COMPARING API RESPONSE VS DATABASE DATA")
        logger.info("=" * 50)
        
        try:
            # Get data from API
            success, api_data = self.test_public_stats_endpoint()
            if not success or not api_data:
                logger.error("❌ Could not get API data for comparison")
                return False
            
            # Get data from database
            db_data = await self.get_database_counts()
            if not db_data:
                logger.error("❌ Could not get database data for comparison")
                return False
            
            # Compare the data
            logger.info("📊 COMPARISON RESULTS:")
            
            # Compare total counts
            fields_to_compare = ["total_clients", "total_documents", "total_trainings"]
            all_match = True
            
            for field in fields_to_compare:
                api_value = api_data.get(field, 0)
                db_value = db_data.get(field, 0)
                
                if api_value == db_value:
                    logger.info(f"   ✅ {field}: API={api_value}, DB={db_value} - MATCH")
                else:
                    logger.error(f"   ❌ {field}: API={api_value}, DB={db_value} - MISMATCH")
                    all_match = False
            
            # Compare stage distribution
            api_stages = api_data.get("stage_distribution", {})
            db_stages = db_data.get("stage_distribution", {})
            
            stage_fields = ["stage_1", "stage_2", "stage_3"]
            for stage in stage_fields:
                api_value = api_stages.get(stage, 0)
                db_value = db_stages.get(stage, 0)
                
                if api_value == db_value:
                    logger.info(f"   ✅ {stage}: API={api_value}, DB={db_value} - MATCH")
                else:
                    logger.error(f"   ❌ {stage}: API={api_value}, DB={db_value} - MISMATCH")
                    all_match = False
            
            if all_match:
                logger.info("✅ ALL DATA MATCHES: API returns real database data!")
                return True
            else:
                logger.error("❌ DATA MISMATCH: API does not return accurate database data")
                return False
                
        except Exception as e:
            logger.error(f"❌ ERROR comparing API vs database: {str(e)}")
            return False
    
    async def run_comprehensive_test(self):
        """Run comprehensive test of public stats endpoint"""
        logger.info("🚀 STARTING COMPREHENSIVE PUBLIC STATS ENDPOINT TEST")
        logger.info("=" * 60)
        
        # Connect to database
        if not await self.connect_to_database():
            logger.error("❌ Cannot connect to database, aborting tests")
            return False
        
        try:
            # Test 1: Database verification
            logger.info("\n📊 STEP 1: DATABASE DATA VERIFICATION")
            db_data = await self.get_database_counts()
            if not db_data:
                logger.error("❌ Cannot get database data")
                return False
            
            # Test 2: Sample data
            logger.info("\n📋 STEP 2: SAMPLE DATA VERIFICATION")
            await self.get_sample_data()
            
            # Test 3: Endpoint accessibility
            logger.info("\n🔓 STEP 3: ENDPOINT ACCESSIBILITY TEST")
            if not self.test_endpoint_accessibility():
                logger.error("❌ Endpoint accessibility test failed")
                return False
            
            # Test 4: API response structure
            logger.info("\n🧪 STEP 4: API RESPONSE STRUCTURE TEST")
            success, api_data = self.test_public_stats_endpoint()
            if not success:
                logger.error("❌ API response test failed")
                return False
            
            # Test 5: Data accuracy comparison
            logger.info("\n🔍 STEP 5: DATA ACCURACY COMPARISON")
            if not await self.compare_api_vs_database():
                logger.error("❌ Data accuracy test failed")
                return False
            
            # Final summary
            logger.info("\n" + "=" * 60)
            logger.info("🎉 ALL TESTS PASSED!")
            logger.info("✅ Public stats endpoint is working correctly")
            logger.info("✅ Returns real data from database")
            logger.info("✅ Response structure matches frontend expectations")
            logger.info("✅ No authentication required")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ ERROR in comprehensive test: {str(e)}")
            return False
        finally:
            if self.client:
                self.client.close()

async def main():
    """Main test function"""
    test = PublicStatsTest()
    success = await test.run_comprehensive_test()
    
    if success:
        print("\n🎉 PUBLIC STATS ENDPOINT TEST: PASSED")
        return 0
    else:
        print("\n❌ PUBLIC STATS ENDPOINT TEST: FAILED")
        return 1

if __name__ == "__main__":
    import sys
    result = asyncio.run(main())
    sys.exit(result)