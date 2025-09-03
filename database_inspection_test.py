#!/usr/bin/env python3
"""
Database Collection Inspection - Find Waste Data
"""

import pymongo
from pymongo import MongoClient
import os
from dotenv import load_dotenv

def inspect_database():
    # Load environment variables
    load_dotenv('/app/backend/.env')
    
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME', 'rotacrm-cluster')
    
    print(f"🔍 Inspecting database: {db_name}")
    print("=" * 60)
    
    try:
        client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        
        # List all collections
        collections = db.list_collection_names()
        print(f"📋 Found {len(collections)} collections:")
        for i, collection in enumerate(collections, 1):
            count = db[collection].count_documents({})
            print(f"   {i}. {collection}: {count} documents")
        
        print()
        
        # Check each collection for waste-related fields
        print("🔍 Searching for waste-related data in all collections:")
        print()
        
        waste_fields = ['organic_waste', 'plastic_waste', 'glass_waste', 'paper_waste', 'metal_waste', 'total_waste']
        
        for collection_name in collections:
            collection = db[collection_name]
            
            # Sample a few documents to check structure
            sample_docs = list(collection.find().limit(3))
            
            if sample_docs:
                print(f"📁 Collection: {collection_name}")
                
                # Check if any waste fields exist
                has_waste_fields = False
                for doc in sample_docs:
                    for field in waste_fields:
                        if field in doc:
                            has_waste_fields = True
                            break
                    if has_waste_fields:
                        break
                
                if has_waste_fields:
                    print(f"   🗑️  HAS WASTE DATA!")
                    # Show sample document structure
                    sample = sample_docs[0]
                    print(f"   📋 Sample document fields: {list(sample.keys())}")
                    
                    # Show waste field values
                    for field in waste_fields:
                        if field in sample:
                            print(f"      {field}: {sample[field]}")
                else:
                    print(f"   ❌ No waste fields found")
                
                # Show sample document structure anyway
                if sample_docs:
                    sample = sample_docs[0]
                    print(f"   📋 Sample fields: {list(sample.keys())[:10]}...")  # First 10 fields
                
                print()
        
        # Specifically check for environment-related collections
        print("🌱 Environment-related collection search:")
        env_collections = [col for col in collections if 'env' in col.lower() or 'waste' in col.lower() or 'environment' in col.lower()]
        
        if env_collections:
            print(f"   Found: {env_collections}")
        else:
            print("   ❌ No environment-related collections found")
        
        print()
        
        # Check consumptions collection in detail
        if 'consumptions' in collections:
            print("📊 Detailed consumptions collection analysis:")
            consumptions = db.consumptions
            
            # Get all field names from sample documents
            sample_consumptions = list(consumptions.find().limit(5))
            all_fields = set()
            for doc in sample_consumptions:
                all_fields.update(doc.keys())
            
            print(f"   📋 All fields in consumptions: {sorted(list(all_fields))}")
            
            # Check for accommodation_count
            with_accommodation = consumptions.count_documents({"accommodation_count": {"$gt": 0}})
            print(f"   🏨 Records with accommodation_count > 0: {with_accommodation}")
            
            if sample_consumptions:
                sample = sample_consumptions[0]
                print(f"   📋 Sample consumption record:")
                for key, value in sample.items():
                    print(f"      {key}: {value}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Database inspection failed: {e}")

if __name__ == "__main__":
    inspect_database()