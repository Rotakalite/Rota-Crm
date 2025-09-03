#!/usr/bin/env python3
"""
🎯 REAL CLIENT CARBON FOOTPRINT TEST
Test with actual client ID from database to debug API response
"""

import asyncio
import requests
import json
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection
MONGO_URL = "mongodb+srv://rotacrm_user:Ccpp1144..@rotacrm-cluster.meezxmj.mongodb.net/rotacrm-cluster?retryWrites=true&w=majority&appName=rotacrm-cluster"
DB_NAME = "rotacrm-cluster"
BACKEND_URL = "https://rota-crm-production.up.railway.app"
API_BASE = f"{BACKEND_URL}/api"

async def get_real_client_id():
    """Get a real client ID from database"""
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Get first client
        real_client = await db.clients.find_one({})
        if real_client:
            print(f"✅ Found real client: {real_client.get('name', 'Unknown')} (ID: {real_client['id']})")
            return real_client['id']
        else:
            print("❌ No clients found in database")
            return None
            
    except Exception as e:
        print(f"❌ Error getting client: {e}")
        return None
    finally:
        client.close()

async def test_carbon_footprint_with_real_client():
    """Test carbon footprint API with real client"""
    
    # Get real client ID
    client_id = await get_real_client_id()
    if not client_id:
        return
        
    print(f"\n🎯 Testing Carbon Footprint API with real client: {client_id}")
    
    # Test carbon footprint endpoint
    params = {
        "client_id": client_id,
        "year": 2024
    }
    
    try:
        response = requests.get(f"{API_BASE}/analytics/carbon-footprint", 
                              params=params, timeout=10)
        
        print(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            # Success! Analyze the response
            data = response.json()
            print(f"✅ SUCCESS! Got API response")
            
            # Check for critical fields
            critical_fields = ["total_waste_co2", "total_hotel_co2"]
            
            print(f"\n🔍 API RESPONSE ANALYSIS:")
            print(f"  total_carbon_emissions: {data.get('total_carbon_emissions', 'NOT FOUND')}")
            print(f"  total_waste_co2: {data.get('total_waste_co2', 'NOT FOUND')}")
            print(f"  total_hotel_co2: {data.get('total_hotel_co2', 'NOT FOUND')}")
            print(f"  methodology: {data.get('methodology', 'NOT FOUND')}")
            
            # Check monthly data
            monthly_data = data.get('monthly_carbon_data', [])
            print(f"\n📊 Monthly Data ({len(monthly_data)} months):")
            
            for month_data in monthly_data:
                month_name = month_data.get('month_name', 'Unknown')
                waste_co2 = month_data.get('total_waste_co2', 'NOT FOUND')
                hotel_co2 = month_data.get('total_hotel_co2', 'NOT FOUND')
                accommodation = month_data.get('accommodation_count', 0)
                
                print(f"  {month_name}: waste_co2={waste_co2}, hotel_co2={hotel_co2}, accommodation={accommodation}")
                
            # Full response for debugging
            print(f"\n📋 FULL API RESPONSE:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
        elif response.status_code in [401, 403]:
            print(f"🔒 Authentication required: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'No detail')}")
            except:
                print(f"   Raw response: {response.text}")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ API test error: {e}")

if __name__ == "__main__":
    asyncio.run(test_carbon_footprint_with_real_client())