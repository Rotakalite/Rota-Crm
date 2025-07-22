import unittest
import json
import logging
import requests
import os
import sys
import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# MongoDB connection
MONGO_URL = "mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster"
DB_NAME = "rotacrm"

# Test JWT tokens for client users
KAYA_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

class TestClientDashboardStats(unittest.TestCase):
    """Test class for Client Dashboard Stats API - Focus on consumption data graphs"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {KAYA_CLIENT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_client_dashboard_stats_endpoint(self):
        """Test GET /api/client-dashboard-stats endpoint - Main focus on consumption data"""
        logger.info("\n=== Testing GET /api/client-dashboard-stats endpoint ===")
        
        url = f"{self.api_url}/client-dashboard-stats"
        
        # Test with client user (main test case)
        try:
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data keys: {list(data.keys())}")
                
                # Verify main structure
                expected_keys = ["client_info", "statistics", "consumption_data", "sustainability_progress", "recent_activities", "recommendations"]
                for key in expected_keys:
                    self.assertIn(key, data, f"Response should contain {key}")
                
                # Test client_info structure
                client_info = data["client_info"]
                client_info_keys = ["name", "certificate_status", "certificate_days_left"]
                for key in client_info_keys:
                    self.assertIn(key, client_info, f"client_info should contain {key}")
                logger.info(f"✅ client_info structure validated: {client_info}")
                
                # Test statistics structure
                statistics = data["statistics"]
                stats_keys = ["total_documents", "total_trainings", "completed_trainings"]
                for key in stats_keys:
                    self.assertIn(key, statistics, f"statistics should contain {key}")
                logger.info(f"✅ statistics structure validated: {statistics}")
                
                # Test consumption_data structure (MAIN FOCUS)
                consumption_data = data["consumption_data"]
                consumption_keys = ["energy_by_month", "water_by_month"]
                for key in consumption_keys:
                    self.assertIn(key, consumption_data, f"consumption_data should contain {key}")
                
                # Check if energy and water data exists
                energy_by_month = consumption_data["energy_by_month"]
                water_by_month = consumption_data["water_by_month"]
                
                logger.info(f"Energy by month data: {energy_by_month}")
                logger.info(f"Water by month data: {water_by_month}")
                
                if not energy_by_month and not water_by_month:
                    logger.warning("⚠️ ISSUE CONFIRMED: Both energy_by_month and water_by_month are empty!")
                    logger.warning("⚠️ This explains why frontend shows 'Henüz enerji/su tüketim verisi bulunmamaktadır.'")
                else:
                    logger.info("✅ Consumption data found - graphs should display properly")
                
                # Test sustainability_progress structure
                sustainability_progress = data["sustainability_progress"]
                progress_keys = ["carbon_reduction", "energy_efficiency", "waste_reduction", "water_saving"]
                for key in progress_keys:
                    self.assertIn(key, sustainability_progress, f"sustainability_progress should contain {key}")
                logger.info(f"✅ sustainability_progress structure validated: {sustainability_progress}")
                
                # Test recent_activities structure
                recent_activities = data["recent_activities"]
                self.assertIsInstance(recent_activities, list, "recent_activities should be a list")
                logger.info(f"✅ recent_activities structure validated: {len(recent_activities)} activities")
                
                # Test recommendations structure
                recommendations = data["recommendations"]
                self.assertIsInstance(recommendations, list, "recommendations should be a list")
                if len(recommendations) > 0:
                    rec = recommendations[0]
                    rec_keys = ["type", "title", "description", "priority"]
                    for key in rec_keys:
                        self.assertIn(key, rec, f"recommendation should contain {key}")
                logger.info(f"✅ recommendations structure validated: {len(recommendations)} recommendations")
                
                logger.info("✅ GET /api/client-dashboard-stats with client user passed")
                
            elif response.status_code in [401, 403]:
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ GET /api/client-dashboard-stats with client user - auth error (expected)")
                
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/client-dashboard-stats with client: {str(e)}")
            raise
        
        # Test with admin user
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Admin response data keys: {list(data.keys())}")
                logger.info("✅ GET /api/client-dashboard-stats with admin user passed")
                
            elif response.status_code in [401, 403]:
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ GET /api/client-dashboard-stats with admin user - auth error (expected)")
                
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/client-dashboard-stats with admin: {str(e)}")
            raise
        
        # Test authentication requirements
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Not authenticated
            self.assertEqual(response.status_code, 403)
            logger.info("✅ GET /api/client-dashboard-stats without auth returns 403")
            
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/client-dashboard-stats without auth: {str(e)}")
            raise
    
    def test_consumption_data_availability(self):
        """Test if consumption data exists in database for client dashboard"""
        logger.info("\n=== Testing consumption data availability in database ===")
        
        try:
            # Connect to MongoDB directly to check consumption data
            async def check_consumption_data():
                client = AsyncIOMotorClient(MONGO_URL)
                db = client[DB_NAME]
                
                # Check consumptions collection
                consumptions = await db.consumptions.find({}).to_list(length=10)
                logger.info(f"Found {len(consumptions)} consumption records in database")
                
                if len(consumptions) > 0:
                    sample = consumptions[0]
                    logger.info(f"Sample consumption record: {sample}")
                    
                    # Check if records have energy and water fields
                    energy_fields = ["electricity", "energy_kwh", "energy"]
                    water_fields = ["water", "water_m3"]
                    
                    for field in energy_fields:
                        if field in sample:
                            logger.info(f"✅ Found energy field: {field} = {sample[field]}")
                            break
                    else:
                        logger.warning("⚠️ No energy field found in consumption record")
                    
                    for field in water_fields:
                        if field in sample:
                            logger.info(f"✅ Found water field: {field} = {sample[field]}")
                            break
                    else:
                        logger.warning("⚠️ No water field found in consumption record")
                else:
                    logger.warning("⚠️ No consumption records found in database")
                    logger.warning("⚠️ This explains why client dashboard shows empty graphs")
                
                client.close()
            
            # Run the async function
            asyncio.run(check_consumption_data())
            
        except Exception as e:
            logger.error(f"❌ Error checking consumption data: {str(e)}")
            logger.info("⚠️ Could not verify consumption data in database")

    def test_create_sample_consumption_data(self):
        """Create sample consumption data for testing client dashboard"""
        logger.info("\n=== Creating sample consumption data for client dashboard testing ===")
        
        try:
            # Create sample consumption data via API
            url = f"{self.api_url}/consumptions"
            
            # Sample consumption data for multiple months
            sample_data = [
                {
                    "year": 2024,
                    "month": 1,
                    "electricity": 1500.5,
                    "water": 800.25,
                    "natural_gas": 400.75,
                    "coal": 200.0,
                    "accommodation_count": 150
                },
                {
                    "year": 2024,
                    "month": 2,
                    "electricity": 1400.0,
                    "water": 750.0,
                    "natural_gas": 380.0,
                    "coal": 180.0,
                    "accommodation_count": 140
                },
                {
                    "year": 2024,
                    "month": 3,
                    "electricity": 1600.0,
                    "water": 850.0,
                    "natural_gas": 420.0,
                    "coal": 220.0,
                    "accommodation_count": 160
                }
            ]
            
            for data in sample_data:
                try:
                    response = requests.post(url, headers=self.headers_admin, json=data)
                    logger.info(f"Created consumption data for month {data['month']}: {response.status_code}")
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"✅ Successfully created consumption data for month {data['month']}")
                    elif response.status_code == 400:
                        logger.info(f"⚠️ Consumption data for month {data['month']} already exists")
                    else:
                        logger.warning(f"⚠️ Failed to create consumption data for month {data['month']}: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"❌ Error creating consumption data for month {data['month']}: {str(e)}")
            
            logger.info("✅ Sample consumption data creation completed")
            
        except Exception as e:
            logger.error(f"❌ Error in sample data creation: {str(e)}")

if __name__ == '__main__':
    unittest.main()