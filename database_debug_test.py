#!/usr/bin/env python3
"""
🎯 DATABASE DEBUG TEST - WASTE & HOTEL DATA ANALYSIS
Direct database query to check for waste records and accommodation data

CRITICAL DEBUG QUESTIONS:
❓ consumption.waste_data field database'de var mı?
❓ consumption.hotel_data field database'de var mı?
❓ Bu fields'lar dolu mu yoksa her zaman empty array mı?
❓ Waste collection'da gerçek data var mı?
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import json

# MongoDB connection
MONGO_URL = "mongodb+srv://rotacrm_user:Ccpp1144..@rotacrm-cluster.meezxmj.mongodb.net/rotacrm-cluster?retryWrites=true&w=majority&appName=rotacrm-cluster"
DB_NAME = "rotacrm-cluster"

class DatabaseDebugger:
    def __init__(self):
        self.client = None
        self.db = None
        self.results = []
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(MONGO_URL)
            self.db = self.client[DB_NAME]
            # Test connection
            await self.client.admin.command('ping')
            print("✅ Connected to MongoDB Atlas")
            return True
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
            
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            
    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} - {test_name}"
        if details:
            result += f" | {details}"
        self.results.append(result)
        print(result)
        
    async def analyze_collections(self):
        """Analyze available collections"""
        try:
            collections = await self.db.list_collection_names()
            print(f"\n📊 Available Collections ({len(collections)}):")
            for collection in sorted(collections):
                count = await self.db[collection].count_documents({})
                print(f"  - {collection}: {count} documents")
                
            # Check for waste-related collections
            waste_collections = [col for col in collections if 'waste' in col.lower()]
            if waste_collections:
                self.log_result("Waste Collections Found", True, f"Collections: {waste_collections}")
            else:
                self.log_result("Waste Collections Found", False, "No waste-related collections found")
                
        except Exception as e:
            self.log_result("Collections Analysis", False, f"Error: {e}")
            
    async def analyze_consumption_schema(self):
        """Analyze consumption collection schema"""
        try:
            # Get sample consumption documents
            sample_docs = await self.db.consumptions.find().limit(5).to_list(length=5)
            
            if not sample_docs:
                self.log_result("Consumption Documents", False, "No consumption documents found")
                return
                
            self.log_result("Consumption Documents", True, f"Found {len(sample_docs)} sample documents")
            
            # Analyze schema
            all_fields = set()
            waste_data_found = False
            hotel_data_found = False
            accommodation_count_found = False
            
            for doc in sample_docs:
                all_fields.update(doc.keys())
                if 'waste_data' in doc:
                    waste_data_found = True
                if 'hotel_data' in doc:
                    hotel_data_found = True
                if 'accommodation_count' in doc:
                    accommodation_count_found = True
                    
            print(f"\n📋 Consumption Schema Fields ({len(all_fields)}):")
            for field in sorted(all_fields):
                print(f"  - {field}")
                
            self.log_result("waste_data Field", waste_data_found, "Found in consumption documents" if waste_data_found else "Not found in consumption documents")
            self.log_result("hotel_data Field", hotel_data_found, "Found in consumption documents" if hotel_data_found else "Not found in consumption documents")
            self.log_result("accommodation_count Field", accommodation_count_found, "Found in consumption documents" if accommodation_count_found else "Not found in consumption documents")
            
        except Exception as e:
            self.log_result("Consumption Schema Analysis", False, f"Error: {e}")
            
    async def analyze_waste_data(self):
        """Analyze waste data in database"""
        try:
            # Check waste collection
            waste_count = await self.db.waste.count_documents({})
            self.log_result("Waste Collection", waste_count > 0, f"Found {waste_count} waste documents")
            
            if waste_count > 0:
                # Get sample waste documents
                sample_waste = await self.db.waste.find().limit(3).to_list(length=3)
                print(f"\n🗑️ Sample Waste Documents:")
                for i, doc in enumerate(sample_waste, 1):
                    print(f"  Document {i}:")
                    print(f"    client_id: {doc.get('client_id', 'N/A')}")
                    print(f"    year: {doc.get('year', 'N/A')}")
                    print(f"    month: {doc.get('month', 'N/A')}")
                    print(f"    organic_waste: {doc.get('organic_waste', 0)}")
                    print(f"    plastic_waste: {doc.get('plastic_waste', 0)}")
                    print(f"    total_waste: {doc.get('total_waste', 0)}")
                    
            # Check environment collection (alternative waste storage)
            env_count = await self.db.environment.count_documents({})
            self.log_result("Environment Collection", env_count > 0, f"Found {env_count} environment documents")
            
        except Exception as e:
            self.log_result("Waste Data Analysis", False, f"Error: {e}")
            
    async def analyze_accommodation_data(self):
        """Analyze accommodation data in consumption records"""
        try:
            # Find consumption records with accommodation_count > 0
            accommodation_query = {"accommodation_count": {"$gt": 0}}
            accommodation_count = await self.db.consumptions.count_documents(accommodation_query)
            
            self.log_result("Accommodation Data", accommodation_count > 0, f"Found {accommodation_count} records with accommodation_count > 0")
            
            if accommodation_count > 0:
                # Get sample accommodation data
                sample_accommodation = await self.db.consumptions.find(accommodation_query).limit(5).to_list(length=5)
                
                print(f"\n🏨 Sample Accommodation Data:")
                total_accommodation = 0
                for i, doc in enumerate(sample_accommodation, 1):
                    acc_count = doc.get('accommodation_count', 0)
                    total_accommodation += acc_count
                    print(f"  Record {i}:")
                    print(f"    client_id: {doc.get('client_id', 'N/A')}")
                    print(f"    year: {doc.get('year', 'N/A')}")
                    print(f"    month: {doc.get('month', 'N/A')}")
                    print(f"    accommodation_count: {acc_count}")
                    
                avg_accommodation = total_accommodation / len(sample_accommodation)
                self.log_result("Accommodation Count Analysis", True, f"Average accommodation_count: {avg_accommodation:.1f}")
                
        except Exception as e:
            self.log_result("Accommodation Data Analysis", False, f"Error: {e}")
            
    async def analyze_specific_client(self, client_id="94927a77-edc3-45ec-8329-795feae35771"):
        """Analyze specific client data"""
        try:
            print(f"\n🎯 Analyzing Client: {client_id}")
            
            # Check client exists
            client = await self.db.clients.find_one({"id": client_id})
            if not client:
                self.log_result("Test Client Exists", False, f"Client {client_id} not found")
                return
                
            self.log_result("Test Client Exists", True, f"Client: {client.get('name', 'Unknown')}")
            
            # Check consumption data for this client
            consumption_query = {"client_id": client_id}
            consumption_count = await self.db.consumptions.count_documents(consumption_query)
            self.log_result("Client Consumption Data", consumption_count > 0, f"Found {consumption_count} consumption records")
            
            # Check waste data for this client
            waste_query = {"client_id": client_id}
            waste_count = await self.db.waste.count_documents(waste_query)
            self.log_result("Client Waste Data", waste_count > 0, f"Found {waste_count} waste records")
            
            # Check accommodation data for this client
            accommodation_query = {"client_id": client_id, "accommodation_count": {"$gt": 0}}
            accommodation_count = await self.db.consumptions.count_documents(accommodation_query)
            self.log_result("Client Accommodation Data", accommodation_count > 0, f"Found {accommodation_count} records with accommodation > 0")
            
            # Get sample data for 2024
            sample_consumption = await self.db.consumptions.find({"client_id": client_id, "year": 2024}).limit(3).to_list(length=3)
            if sample_consumption:
                print(f"\n📊 Sample 2024 Consumption Data for {client_id}:")
                for i, doc in enumerate(sample_consumption, 1):
                    print(f"  Month {doc.get('month', 'N/A')}:")
                    print(f"    electricity: {doc.get('electricity', 0)}")
                    print(f"    water: {doc.get('water', 0)}")
                    print(f"    accommodation_count: {doc.get('accommodation_count', 0)}")
                    print(f"    waste_data: {doc.get('waste_data', 'Not found')}")
                    print(f"    hotel_data: {doc.get('hotel_data', 'Not found')}")
                    
        except Exception as e:
            self.log_result("Specific Client Analysis", False, f"Error: {e}")
            
    async def check_carbon_calculation_data_flow(self):
        """Check data flow for carbon calculation"""
        try:
            print(f"\n🔍 CARBON CALCULATION DATA FLOW ANALYSIS")
            
            # 1. Check if consumptions have waste_data field populated
            consumptions_with_waste = await self.db.consumptions.count_documents({"waste_data": {"$exists": True, "$ne": []}})
            self.log_result("Consumptions with waste_data", consumptions_with_waste > 0, f"Found {consumptions_with_waste} consumption records with waste_data")
            
            # 2. Check if consumptions have hotel_data field populated
            consumptions_with_hotel = await self.db.consumptions.count_documents({"hotel_data": {"$exists": True, "$ne": []}})
            self.log_result("Consumptions with hotel_data", consumptions_with_hotel > 0, f"Found {consumptions_with_hotel} consumption records with hotel_data")
            
            # 3. Check waste collection for matching data
            waste_with_data = await self.db.waste.count_documents({"$or": [
                {"organic_waste": {"$gt": 0}},
                {"plastic_waste": {"$gt": 0}},
                {"glass_waste": {"$gt": 0}},
                {"paper_waste": {"$gt": 0}},
                {"metal_waste": {"$gt": 0}}
            ]})
            self.log_result("Waste Records with Data", waste_with_data > 0, f"Found {waste_with_data} waste records with actual waste amounts")
            
            # 4. Check accommodation data distribution
            accommodation_stats = await self.db.consumptions.aggregate([
                {"$match": {"accommodation_count": {"$gt": 0}}},
                {"$group": {
                    "_id": None,
                    "total_records": {"$sum": 1},
                    "avg_accommodation": {"$avg": "$accommodation_count"},
                    "max_accommodation": {"$max": "$accommodation_count"},
                    "min_accommodation": {"$min": "$accommodation_count"}
                }}
            ]).to_list(length=1)
            
            if accommodation_stats:
                stats = accommodation_stats[0]
                self.log_result("Accommodation Statistics", True, 
                              f"Records: {stats['total_records']}, Avg: {stats['avg_accommodation']:.1f}, Max: {stats['max_accommodation']}, Min: {stats['min_accommodation']}")
            else:
                self.log_result("Accommodation Statistics", False, "No accommodation data found")
                
        except Exception as e:
            self.log_result("Carbon Calculation Data Flow", False, f"Error: {e}")
            
    async def run_all_tests(self):
        """Run all database debug tests"""
        print("🎯 STARTING DATABASE DEBUG TEST - WASTE & HOTEL DATA")
        print("="*80)
        print("🚨 CRITICAL DEBUG: Why are Atık CO2 and Konaklama CO2 showing 0.000?")
        print("="*80)
        
        if not await self.connect():
            return
            
        try:
            await self.analyze_collections()
            await self.analyze_consumption_schema()
            await self.analyze_waste_data()
            await self.analyze_accommodation_data()
            await self.analyze_specific_client()
            await self.check_carbon_calculation_data_flow()
            
        finally:
            await self.close()
            
        # Print summary
        print("\n" + "="*80)
        print("🎯 DATABASE DEBUG TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if "✅ PASS" in r])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print("="*80)
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.results:
            print(f"  {result}")
            
        print("\n🔍 CRITICAL FINDINGS:")
        print("="*80)
        print("Based on database analysis, the root cause of 0.000 CO2 values should be identified.")
        print("Check if waste_data and hotel_data fields are properly populated in consumption records.")
        print("Verify if waste collection has actual data that matches consumption records by client_id, year, month.")
        print("="*80)

async def main():
    """Main execution"""
    debugger = DatabaseDebugger()
    await debugger.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())