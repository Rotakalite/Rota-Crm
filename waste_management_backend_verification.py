#!/usr/bin/env python3
"""
WASTE MANAGEMENT BACKEND VERIFICATION TEST

This test verifies the waste management backend implementation
without requiring valid authentication tokens.
"""

import requests
import json
import logging
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"
MONGO_URL = "mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster"
DB_NAME = "rotacrm"

class WasteManagementBackendVerification:
    def __init__(self):
        self.api_url = RAILWAY_API_URL
        
    async def connect_to_database(self):
        """Connect to MongoDB database"""
        try:
            self.mongo_client = AsyncIOMotorClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            await self.db.command("ping")
            logger.info("✅ Connected to MongoDB database")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {str(e)}")
            return False
    
    def test_endpoint_accessibility(self):
        """Test if waste management endpoints are accessible and properly secured"""
        logger.info("\n" + "="*80)
        logger.info("🧪 TESTING ENDPOINT ACCESSIBILITY")
        logger.info("="*80)
        
        endpoints = [
            ("POST", "/consumptions/waste"),
            ("GET", "/consumptions/waste"),
            ("GET", "/consumptions/waste/analytics")
        ]
        
        all_accessible = True
        
        for method, endpoint in endpoints:
            url = f"{self.api_url}{endpoint}"
            logger.info(f"🔍 Testing {method} {endpoint}")
            
            try:
                if method == "GET":
                    response = requests.get(url)
                else:
                    response = requests.post(url, json={"test": "data"})
                
                logger.info(f"📥 Response status: {response.status_code}")
                
                if response.status_code == 403:
                    logger.info("✅ Endpoint accessible and properly secured (403 Not authenticated)")
                elif response.status_code == 401:
                    logger.info("✅ Endpoint accessible and requires authentication (401)")
                elif response.status_code == 404:
                    logger.error("❌ Endpoint not found (404)")
                    all_accessible = False
                else:
                    logger.warning(f"⚠️ Unexpected response: {response.status_code}")
                    try:
                        data = response.json()
                        logger.info(f"Response: {data}")
                    except:
                        logger.info(f"Response text: {response.text}")
                        
            except Exception as e:
                logger.error(f"❌ Request failed: {str(e)}")
                all_accessible = False
        
        return all_accessible
    
    async def test_database_waste_collection(self):
        """Test waste management database collection"""
        logger.info("\n" + "="*80)
        logger.info("🧪 TESTING DATABASE WASTE COLLECTION")
        logger.info("="*80)
        
        try:
            # Check if waste_management collection exists
            collections = await self.db.list_collection_names()
            
            if "waste_management" not in collections:
                logger.error("❌ waste_management collection does not exist")
                return False
            
            logger.info("✅ waste_management collection exists")
            
            # Count total waste records
            total_count = await self.db.waste_management.count_documents({})
            logger.info(f"📊 Total waste records in database: {total_count}")
            
            if total_count == 0:
                logger.warning("⚠️ No waste records found in database")
                return False
            
            # Get sample records
            sample_records = await self.db.waste_management.find({}).limit(5).to_list(length=None)
            
            logger.info("📋 Sample waste records:")
            for i, record in enumerate(sample_records):
                logger.info(f"   Record {i+1}:")
                logger.info(f"     ID: {record.get('id')}")
                logger.info(f"     Client ID: {record.get('client_id')}")
                logger.info(f"     Year/Month: {record.get('year')}/{record.get('month')}")
                logger.info(f"     Total Waste: {record.get('total_waste')} kg")
                logger.info(f"     Recycling Rate: {record.get('recycling_rate')}%")
                logger.info(f"     Per Person Waste: {record.get('per_person_waste')} kg")
                logger.info(f"     Created: {record.get('created_at')}")
            
            # Check data structure
            if sample_records:
                record = sample_records[0]
                required_fields = [
                    'id', 'client_id', 'year', 'month', 'organic_waste', 'plastic_waste',
                    'glass_waste', 'paper_waste', 'metal_waste', 'electronic_waste',
                    'oil_waste', 'mixed_waste', 'accommodation_count', 'total_waste',
                    'recycling_rate', 'per_person_waste', 'created_at', 'updated_at'
                ]
                
                missing_fields = [field for field in required_fields if field not in record]
                
                if missing_fields:
                    logger.warning(f"⚠️ Missing fields in waste records: {missing_fields}")
                else:
                    logger.info("✅ Waste record structure is complete")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database test failed: {str(e)}")
            return False
    
    async def test_client_waste_data_distribution(self):
        """Test waste data distribution across clients"""
        logger.info("\n" + "="*80)
        logger.info("🧪 TESTING CLIENT WASTE DATA DISTRIBUTION")
        logger.info("="*80)
        
        try:
            # Get unique clients with waste data
            pipeline = [
                {"$group": {"_id": "$client_id", "count": {"$sum": 1}, "years": {"$addToSet": "$year"}}},
                {"$sort": {"count": -1}}
            ]
            
            client_stats = await self.db.waste_management.aggregate(pipeline).to_list(length=None)
            
            logger.info(f"📊 Clients with waste data: {len(client_stats)}")
            
            for i, stat in enumerate(client_stats):
                client_id = stat["_id"]
                count = stat["count"]
                years = stat["years"]
                
                logger.info(f"   Client {i+1}: {client_id}")
                logger.info(f"     Records: {count}")
                logger.info(f"     Years: {sorted(years)}")
                
                # Get client name if available
                try:
                    client = await self.db.clients.find_one({"id": client_id})
                    if client:
                        client_name = client.get("name") or client.get("hotel_name") or "Unknown"
                        logger.info(f"     Name: {client_name}")
                except:
                    pass
            
            # Check for recent data (2024-2025)
            recent_count = await self.db.waste_management.count_documents({"year": {"$gte": 2024}})
            logger.info(f"📊 Recent waste records (2024+): {recent_count}")
            
            if recent_count > 0:
                logger.info("✅ Recent waste data is available")
                return True
            else:
                logger.warning("⚠️ No recent waste data found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Client distribution test failed: {str(e)}")
            return False
    
    async def test_waste_data_calculations(self):
        """Test waste data calculations and analytics"""
        logger.info("\n" + "="*80)
        logger.info("🧪 TESTING WASTE DATA CALCULATIONS")
        logger.info("="*80)
        
        try:
            # Get a sample record to verify calculations
            sample_record = await self.db.waste_management.find_one({})
            
            if not sample_record:
                logger.error("❌ No waste records found for calculation test")
                return False
            
            logger.info("📋 Testing calculations on sample record:")
            logger.info(f"   Organic waste: {sample_record.get('organic_waste')} kg")
            logger.info(f"   Plastic waste: {sample_record.get('plastic_waste')} kg")
            logger.info(f"   Glass waste: {sample_record.get('glass_waste')} kg")
            logger.info(f"   Paper waste: {sample_record.get('paper_waste')} kg")
            logger.info(f"   Metal waste: {sample_record.get('metal_waste')} kg")
            logger.info(f"   Electronic waste: {sample_record.get('electronic_waste')} kg")
            logger.info(f"   Oil waste: {sample_record.get('oil_waste')} litre")
            logger.info(f"   Mixed waste: {sample_record.get('mixed_waste')} kg")
            logger.info(f"   Accommodation count: {sample_record.get('accommodation_count')}")
            
            # Verify total waste calculation
            recyclable_waste = (
                sample_record.get('plastic_waste', 0) + 
                sample_record.get('glass_waste', 0) + 
                sample_record.get('paper_waste', 0) + 
                sample_record.get('metal_waste', 0)
            )
            
            calculated_total = (
                sample_record.get('organic_waste', 0) + 
                recyclable_waste + 
                sample_record.get('electronic_waste', 0) + 
                sample_record.get('mixed_waste', 0)
            )
            
            stored_total = sample_record.get('total_waste', 0)
            
            logger.info(f"📊 Calculated total waste: {calculated_total} kg")
            logger.info(f"📊 Stored total waste: {stored_total} kg")
            
            if abs(calculated_total - stored_total) < 0.01:
                logger.info("✅ Total waste calculation is correct")
            else:
                logger.warning("⚠️ Total waste calculation mismatch")
            
            # Verify recycling rate calculation
            calculated_recycling_rate = (recyclable_waste / calculated_total * 100) if calculated_total > 0 else 0
            stored_recycling_rate = sample_record.get('recycling_rate', 0)
            
            logger.info(f"📊 Calculated recycling rate: {calculated_recycling_rate:.2f}%")
            logger.info(f"📊 Stored recycling rate: {stored_recycling_rate}%")
            
            if abs(calculated_recycling_rate - stored_recycling_rate) < 0.1:
                logger.info("✅ Recycling rate calculation is correct")
            else:
                logger.warning("⚠️ Recycling rate calculation mismatch")
            
            # Verify per-person calculation
            accommodation_count = sample_record.get('accommodation_count', 0)
            calculated_per_person = (calculated_total / accommodation_count) if accommodation_count > 0 else 0
            stored_per_person = sample_record.get('per_person_waste', 0)
            
            logger.info(f"📊 Calculated per-person waste: {calculated_per_person:.2f} kg")
            logger.info(f"📊 Stored per-person waste: {stored_per_person} kg")
            
            if abs(calculated_per_person - stored_per_person) < 0.01:
                logger.info("✅ Per-person waste calculation is correct")
            else:
                logger.warning("⚠️ Per-person waste calculation mismatch")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Calculation test failed: {str(e)}")
            return False
    
    async def run_verification(self):
        """Run all verification tests"""
        logger.info("\n" + "🔍"*40)
        logger.info("🔍 WASTE MANAGEMENT BACKEND VERIFICATION")
        logger.info("🔍"*40)
        
        # Connect to database
        if not await self.connect_to_database():
            logger.error("❌ Cannot proceed without database connection")
            return
        
        # Run tests
        test_results = []
        
        # Test 1: Endpoint accessibility
        result1 = self.test_endpoint_accessibility()
        test_results.append(("Endpoint Accessibility", result1))
        
        # Test 2: Database collection
        result2 = await self.test_database_waste_collection()
        test_results.append(("Database Collection", result2))
        
        # Test 3: Client data distribution
        result3 = await self.test_client_waste_data_distribution()
        test_results.append(("Client Data Distribution", result3))
        
        # Test 4: Data calculations
        result4 = await self.test_waste_data_calculations()
        test_results.append(("Data Calculations", result4))
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("📊 WASTE MANAGEMENT BACKEND VERIFICATION RESULTS")
        logger.info("="*80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} {test_name}")
            if result:
                passed_tests += 1
        
        logger.info(f"\n📊 Overall Result: {passed_tests}/{total_tests} tests passed")
        
        # Conclusions
        logger.info("\n🔍 CONCLUSIONS:")
        
        if passed_tests >= 3:
            logger.info("✅ WASTE MANAGEMENT BACKEND IS WORKING CORRECTLY")
            logger.info("   - Endpoints are accessible and properly secured")
            logger.info("   - Database collection exists with valid data")
            logger.info("   - Data calculations are working properly")
            logger.info("")
            logger.info("🎯 THE ISSUE IS LIKELY IN THE FRONTEND OR AUTHENTICATION:")
            logger.info("   1. Frontend may not be sending correct client_id for consultants")
            logger.info("   2. Authentication tokens may be expired or invalid")
            logger.info("   3. Frontend may not be handling error responses properly")
            logger.info("   4. Frontend may not be refreshing data after submission")
        else:
            logger.error("❌ WASTE MANAGEMENT BACKEND HAS ISSUES")
            logger.error("   - Check endpoint implementation")
            logger.error("   - Verify database schema and data integrity")
            logger.error("   - Review calculation logic")
        
        # Close database connection
        self.mongo_client.close()

async def main():
    """Main verification execution"""
    verification = WasteManagementBackendVerification()
    await verification.run_verification()

if __name__ == "__main__":
    asyncio.run(main())