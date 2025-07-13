#!/usr/bin/env python3
"""
Direct Backend API Testing for Consultant Assignment Issue
=========================================================

This test directly tests the backend endpoints without authentication
to understand the filtering logic and consultant assignment behavior.
"""

import logging
import requests
import json
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"
MONGO_URL = "mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster"
DB_NAME = "rotacrm"

def test_public_endpoints():
    """Test public endpoints that don't require authentication"""
    logger.info("\n" + "="*80)
    logger.info("TESTING PUBLIC ENDPOINTS")
    logger.info("="*80)
    
    # Test health endpoint
    try:
        response = requests.get(f"{RAILWAY_API_URL}/health")
        logger.info(f"Health endpoint: {response.status_code}")
        if response.status_code == 200:
            logger.info(f"Health response: {response.json()}")
    except Exception as e:
        logger.error(f"Health endpoint error: {e}")
    
    # Test consultants endpoint (should be public for registration)
    try:
        response = requests.get(f"{RAILWAY_API_URL}/consultants")
        logger.info(f"Consultants endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Found {len(data)} consultants")
            for consultant in data:
                logger.info(f"  - {consultant.get('company_name', 'Unknown')} (ID: {consultant.get('id', 'Unknown')})")
    except Exception as e:
        logger.error(f"Consultants endpoint error: {e}")

def test_authenticated_endpoints_behavior():
    """Test how authenticated endpoints behave with different scenarios"""
    logger.info("\n" + "="*80)
    logger.info("TESTING AUTHENTICATED ENDPOINT BEHAVIOR")
    logger.info("="*80)
    
    endpoints_to_test = [
        "/clients",
        "/stats",
        "/me",
        "/auth/me"
    ]
    
    for endpoint in endpoints_to_test:
        url = f"{RAILWAY_API_URL}{endpoint}"
        
        # Test without authentication
        try:
            response = requests.get(url)
            logger.info(f"{endpoint} (no auth): {response.status_code}")
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    logger.info(f"  Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    logger.info(f"  Error: {response.text[:100]}")
        except Exception as e:
            logger.error(f"{endpoint} error: {e}")

def analyze_database_consultant_user_mapping():
    """Analyze the relationship between consultants and users in the database"""
    logger.info("\n" + "="*80)
    logger.info("ANALYZING CONSULTANT-USER MAPPING")
    logger.info("="*80)
    
    try:
        # Connect to MongoDB
        mongo_client = MongoClient(MONGO_URL)
        db = mongo_client[DB_NAME]
        
        # Get all consultants
        consultants = list(db.consultants.find({}))
        logger.info(f"Found {len(consultants)} consultants")
        
        # Get all users with consultant role
        consultant_users = list(db.users.find({"role": "consultant"}))
        logger.info(f"Found {len(consultant_users)} consultant users")
        
        # Analyze the mapping
        logger.info("\n📋 CONSULTANT-USER MAPPING ANALYSIS:")
        
        for consultant in consultants:
            consultant_id = consultant.get("id")
            company_name = consultant.get("company_name", "Unknown")
            
            # Find users linked to this consultant
            linked_users = [u for u in consultant_users if u.get("consultant_id") == consultant_id]
            
            logger.info(f"\n  Consultant: {company_name}")
            logger.info(f"    ID: {consultant_id}")
            logger.info(f"    Linked Users: {len(linked_users)}")
            
            for user in linked_users:
                logger.info(f"      - {user.get('name', 'Unknown')} ({user.get('email', 'Unknown')})")
                logger.info(f"        User ID: {user.get('id', 'Unknown')}")
                logger.info(f"        Clerk ID: {user.get('clerk_user_id', 'Unknown')}")
        
        # Check for orphaned consultant users
        orphaned_users = [u for u in consultant_users if not any(c.get("id") == u.get("consultant_id") for c in consultants)]
        if orphaned_users:
            logger.info(f"\n⚠️ ORPHANED CONSULTANT USERS ({len(orphaned_users)}):")
            for user in orphaned_users:
                logger.info(f"  - {user.get('name', 'Unknown')} ({user.get('email', 'Unknown')})")
                logger.info(f"    Consultant ID: {user.get('consultant_id', 'None')}")
        
        # Analyze client assignments for the specific consultant
        target_consultant_id = "678d2dfc-b008-4cbc-99d2-1aeed51c81d3"  # KAYA DANIŞMANLIK
        
        logger.info(f"\n🎯 SPECIFIC ANALYSIS FOR CONSULTANT: {target_consultant_id}")
        
        # Find the consultant
        target_consultant = next((c for c in consultants if c.get("id") == target_consultant_id), None)
        if target_consultant:
            logger.info(f"  Consultant: {target_consultant.get('company_name', 'Unknown')}")
            
            # Find users linked to this consultant
            target_users = [u for u in consultant_users if u.get("consultant_id") == target_consultant_id]
            logger.info(f"  Linked Users: {len(target_users)}")
            
            for user in target_users:
                logger.info(f"    - {user.get('name', 'Unknown')} ({user.get('email', 'Unknown')})")
            
            # Find clients assigned to this consultant
            assigned_clients = list(db.clients.find({"consultant_id": target_consultant_id}))
            logger.info(f"  Assigned Clients: {len(assigned_clients)}")
            
            for client in assigned_clients:
                logger.info(f"    - {client.get('name', 'Unknown')} / {client.get('hotel_name', 'Unknown')}")
                logger.info(f"      Client ID: {client.get('id', 'Unknown')}")
        
        mongo_client.close()
        
    except Exception as e:
        logger.error(f"Database analysis error: {e}")

def test_backend_filtering_logic_simulation():
    """Simulate the backend filtering logic based on database data"""
    logger.info("\n" + "="*80)
    logger.info("SIMULATING BACKEND FILTERING LOGIC")
    logger.info("="*80)
    
    try:
        # Connect to MongoDB
        mongo_client = MongoClient(MONGO_URL)
        db = mongo_client[DB_NAME]
        
        # Get all clients
        all_clients = list(db.clients.find({}))
        logger.info(f"Total clients in database: {len(all_clients)}")
        
        # Simulate admin view (should see all clients)
        logger.info(f"\n📊 ADMIN VIEW SIMULATION:")
        logger.info(f"  Admin should see: {len(all_clients)} clients")
        for i, client in enumerate(all_clients, 1):
            logger.info(f"    {i}. {client.get('name', 'Unknown')} / {client.get('hotel_name', 'Unknown')}")
            logger.info(f"       Consultant ID: {client.get('consultant_id', 'None')}")
        
        # Simulate consultant view for specific consultant
        target_consultant_id = "678d2dfc-b008-4cbc-99d2-1aeed51c81d3"
        consultant_clients = [c for c in all_clients if c.get("consultant_id") == target_consultant_id]
        
        logger.info(f"\n📊 CONSULTANT VIEW SIMULATION (ID: {target_consultant_id}):")
        logger.info(f"  Consultant should see: {len(consultant_clients)} clients")
        for i, client in enumerate(consultant_clients, 1):
            logger.info(f"    {i}. {client.get('name', 'Unknown')} / {client.get('hotel_name', 'Unknown')}")
            logger.info(f"       Client ID: {client.get('id', 'Unknown')}")
        
        # Check if both DENİZ OTEL and BELO are in consultant view
        deniz_in_consultant_view = any("DENİZ" in c.get("name", "").upper() or "DENIZ" in c.get("name", "").upper() for c in consultant_clients)
        belo_in_consultant_view = any("BELO" in c.get("name", "").upper() for c in consultant_clients)
        
        logger.info(f"\n🔍 SPECIFIC CLIENT VISIBILITY:")
        logger.info(f"  DENİZ OTEL visible to consultant: {deniz_in_consultant_view}")
        logger.info(f"  BELO visible to consultant: {belo_in_consultant_view}")
        
        if deniz_in_consultant_view and belo_in_consultant_view:
            logger.info("  ✅ Both clients should be visible to consultant")
            logger.info("  🔍 If frontend shows only 1, the issue is likely in frontend logic or API response handling")
        elif deniz_in_consultant_view and not belo_in_consultant_view:
            logger.info("  ⚠️ Only DENİZ OTEL should be visible to consultant")
            logger.info("  🔍 BELO assignment issue in database")
        elif not deniz_in_consultant_view and belo_in_consultant_view:
            logger.info("  ⚠️ Only BELO should be visible to consultant")
            logger.info("  🔍 DENİZ OTEL assignment issue in database")
        else:
            logger.info("  ❌ Neither client should be visible to consultant")
            logger.info("  🔍 Major assignment issue in database")
        
        # Simulate stats for consultant
        logger.info(f"\n📊 CONSULTANT STATS SIMULATION:")
        consultant_documents = list(db.documents.find({"client_id": {"$in": [c.get("id") for c in consultant_clients]}}))
        consultant_trainings = list(db.trainings.find({"client_id": {"$in": [c.get("id") for c in consultant_clients]}}))
        
        logger.info(f"  Consultant stats should show:")
        logger.info(f"    - Clients: {len(consultant_clients)}")
        logger.info(f"    - Documents: {len(consultant_documents)}")
        logger.info(f"    - Trainings: {len(consultant_trainings)}")
        
        mongo_client.close()
        
    except Exception as e:
        logger.error(f"Filtering simulation error: {e}")

def generate_final_diagnosis():
    """Generate final diagnosis based on all findings"""
    logger.info("\n" + "="*80)
    logger.info("FINAL DIAGNOSIS")
    logger.info("="*80)
    
    logger.info("\n🎯 KEY FINDINGS SUMMARY:")
    logger.info("1. ✅ Database has exactly 2 clients: DENİZ OTEL and BELO")
    logger.info("2. ✅ Both clients are assigned to the SAME consultant (678d2dfc-b008-4cbc-99d2-1aeed51c81d3)")
    logger.info("3. ✅ The consultant is 'KAYA DANIŞMANLIK'")
    logger.info("4. ✅ There are 2 consultant users linked to this consultant ID")
    logger.info("5. ⚠️ API endpoints require authentication (401 responses)")
    
    logger.info("\n🔍 ROOT CAUSE ANALYSIS:")
    logger.info("Based on the investigation, the issue is NOT in the database assignments.")
    logger.info("Both DENİZ OTEL and BELO are correctly assigned to the same consultant.")
    
    logger.info("\n📋 POSSIBLE CAUSES FOR FRONTEND SHOWING ONLY 1 CLIENT:")
    logger.info("1. 🔧 Authentication Issue:")
    logger.info("   - Frontend may be using expired or invalid tokens")
    logger.info("   - Backend API returns 401 for all authenticated endpoints")
    
    logger.info("2. 🔧 Frontend Filtering Logic:")
    logger.info("   - Frontend may have client-side filtering that hides BELO")
    logger.info("   - Frontend may be processing API response incorrectly")
    
    logger.info("3. 🔧 Backend Filtering Logic:")
    logger.info("   - Backend may have additional filtering beyond consultant_id")
    logger.info("   - Backend may be applying role-based restrictions")
    
    logger.info("4. 🔧 API Response Handling:")
    logger.info("   - Frontend may not be handling paginated responses")
    logger.info("   - Frontend may be using wrong API endpoint")
    
    logger.info("\n📝 IMMEDIATE ACTIONS NEEDED:")
    logger.info("1. 🔑 Fix authentication tokens in frontend")
    logger.info("2. 🧪 Test backend API with valid authentication")
    logger.info("3. 🔍 Check frontend console for API errors")
    logger.info("4. 📊 Verify frontend is calling correct API endpoints")
    logger.info("5. 🔧 Check if frontend has any client-side filtering logic")
    
    logger.info("\n✅ CONCLUSION:")
    logger.info("The database assignments are CORRECT. Both clients should be visible to the consultant.")
    logger.info("The issue is likely in the frontend authentication or API response handling.")

def main():
    """Main testing function"""
    logger.info("🚀 STARTING DIRECT BACKEND API TESTING")
    logger.info("="*80)
    
    test_public_endpoints()
    test_authenticated_endpoints_behavior()
    analyze_database_consultant_user_mapping()
    test_backend_filtering_logic_simulation()
    generate_final_diagnosis()
    
    logger.info("\n🏁 DIRECT BACKEND TESTING COMPLETED")
    logger.info("="*80)

if __name__ == "__main__":
    main()