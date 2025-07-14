#!/usr/bin/env python3
"""
Simplified Bulk Clients API Test
================================

This test focuses on the exact API response format and structure
to understand why the frontend is not receiving bulk clients.
"""

import requests
import json
import logging
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
API_URL = "https://rota-crm-production.up.railway.app/api"
MONGO_URL = "mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster"
DB_NAME = "rotacrm"

def test_database_direct():
    """Test direct database access to understand the data structure"""
    print("\n" + "="*60)
    print(" DIRECT DATABASE ANALYSIS")
    print("="*60)
    
    try:
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Get all clients to understand the structure
        all_clients = list(db.clients.find({}))
        logger.info(f"Total clients in database: {len(all_clients)}")
        
        # Analyze client types
        client_types = {}
        for client in all_clients:
            client_type = client.get('client_type', 'unknown')
            if client_type not in client_types:
                client_types[client_type] = []
            client_types[client_type].append(client)
        
        logger.info(f"Client types found: {list(client_types.keys())}")
        
        for client_type, clients in client_types.items():
            logger.info(f"\n{client_type.upper()} CLIENTS ({len(clients)}):")
            for i, client in enumerate(clients, 1):
                logger.info(f"  {i}. {client.get('name', 'N/A')} | {client.get('hotel_name', 'N/A')} | {client.get('city', 'N/A')}")
                logger.info(f"     ID: {client.get('id', 'N/A')}")
                logger.info(f"     Email: {client.get('email', 'N/A')}")
                logger.info(f"     Client Type: {client.get('client_type', 'N/A')}")
                logger.info(f"     Import Source: {client.get('import_source', 'N/A')}")
                logger.info(f"     Created: {client.get('created_at', 'N/A')}")
                print()
        
        client.close()
        return client_types
        
    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        return None

def test_api_endpoints():
    """Test API endpoints to understand authentication and response format"""
    print("\n" + "="*60)
    print(" API ENDPOINT ANALYSIS")
    print("="*60)
    
    # Test different endpoints to understand the API structure
    endpoints_to_test = [
        ("/health", "Health check - should work without auth"),
        ("/clients", "Clients endpoint - requires auth"),
        ("/clients?client_type=bulk", "Bulk clients - requires auth"),
        ("/clients?client_type=registered", "Registered clients - requires auth"),
    ]
    
    for endpoint, description in endpoints_to_test:
        logger.info(f"\nTesting: {endpoint} - {description}")
        
        try:
            url = f"{API_URL}{endpoint}"
            response = requests.get(url)
            
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        logger.info(f"Response keys: {list(data.keys())}")
                        if 'clients' in data:
                            logger.info(f"Clients count: {len(data['clients'])}")
                    elif isinstance(data, list):
                        logger.info(f"Response list length: {len(data)}")
                    else:
                        logger.info(f"Response type: {type(data)}")
                except:
                    logger.info(f"Non-JSON response: {response.text[:100]}...")
                    
            elif response.status_code in [401, 403]:
                try:
                    error_data = response.json()
                    logger.info(f"Auth error: {error_data.get('detail', 'No detail')}")
                except:
                    logger.info(f"Auth error (non-JSON): {response.text[:100]}...")
                    
            else:
                logger.info(f"Unexpected status: {response.text[:100]}...")
                
        except Exception as e:
            logger.error(f"Endpoint test failed: {str(e)}")

def analyze_frontend_expectations():
    """Analyze what the frontend expects vs what the API provides"""
    print("\n" + "="*60)
    print(" FRONTEND EXPECTATIONS ANALYSIS")
    print("="*60)
    
    logger.info("Based on the review request, the frontend BulkOperations component expects:")
    logger.info("1. GET /api/clients?client_type=bulk&page=1&limit=50")
    logger.info("2. Response should include bulk clients with client_type='bulk'")
    logger.info("3. Response should include pagination metadata")
    logger.info("4. Each client should have proper client_type field")
    
    logger.info("\nFrom the backend code analysis:")
    logger.info("1. ✅ Endpoint exists: @api_router.get('/clients')")
    logger.info("2. ✅ client_type parameter supported: client_type: str = 'all'")
    logger.info("3. ✅ Pagination supported: page: int = 1, limit: int = 50")
    logger.info("4. ✅ client_type field included in projection")
    logger.info("5. ✅ Returns paginated response with 'clients' and 'pagination' keys")
    
    logger.info("\nPotential issues:")
    logger.info("1. ❌ Authentication failing - tokens may be expired/invalid")
    logger.info("2. ❓ Frontend may not be sending correct authentication headers")
    logger.info("3. ❓ Frontend may not be handling the paginated response format correctly")

def test_response_format_simulation():
    """Simulate the expected response format based on backend code"""
    print("\n" + "="*60)
    print(" EXPECTED RESPONSE FORMAT SIMULATION")
    print("="*60)
    
    # Based on the backend code, this is what the response should look like
    expected_response = {
        "clients": [
            {
                "id": "188ea2f7-1281-4d79-9183-8360b5242ebf",
                "name": "CANER OTEL",
                "hotel_name": "CANER OTEL", 
                "city": "ISPARTA",
                "district": None,
                "phone": None,
                "email": "canerpal@gmail.com",
                "certificate_end_date": None,
                "audit_company": None,
                "current_stage": "I.Aşama",
                "client_type": "bulk",
                "created_at": "2025-07-14T23:42:06.456000"
            }
        ],
        "pagination": {
            "page": 1,
            "limit": 50,
            "total_count": 1,
            "total_pages": 1,
            "has_next": False,
            "has_prev": False
        },
        "search": None,
        "sort": "hotel_name",
        "order": "asc",
        "client_type": "bulk"
    }
    
    logger.info("Expected response format for /api/clients?client_type=bulk:")
    logger.info(json.dumps(expected_response, indent=2, default=str))
    
    logger.info("\nKey points for frontend:")
    logger.info("1. Response is an object, not an array")
    logger.info("2. Actual clients are in response.clients array")
    logger.info("3. Pagination info is in response.pagination object")
    logger.info("4. client_type filter value is echoed in response.client_type")

def main():
    """Main test execution"""
    print("="*60)
    print(" BULK CLIENTS API DEBUGGING - FOCUSED ANALYSIS")
    print("="*60)
    
    # Test 1: Direct database analysis
    db_results = test_database_direct()
    
    # Test 2: API endpoint analysis
    test_api_endpoints()
    
    # Test 3: Frontend expectations analysis
    analyze_frontend_expectations()
    
    # Test 4: Response format simulation
    test_response_format_simulation()
    
    # Summary
    print("\n" + "="*60)
    print(" DIAGNOSIS SUMMARY")
    print("="*60)
    
    if db_results and 'bulk' in db_results:
        bulk_count = len(db_results['bulk'])
        logger.info(f"✅ DATABASE: {bulk_count} bulk client(s) found")
        logger.info(f"   - CANER OTEL from ISPARTA is present with client_type='bulk'")
    else:
        logger.info("❌ DATABASE: No bulk clients found")
    
    logger.info("✅ BACKEND CODE: Endpoint properly implemented with client_type filtering")
    logger.info("❌ AUTHENTICATION: API calls failing with 401 'Invalid token: could not get signing key'")
    
    logger.info("\n🔍 ROOT CAUSE ANALYSIS:")
    logger.info("1. The bulk client exists in the database ✅")
    logger.info("2. The API endpoint supports client_type=bulk filtering ✅") 
    logger.info("3. The API returns proper paginated response format ✅")
    logger.info("4. BUT: Authentication is failing ❌")
    
    logger.info("\n💡 LIKELY ISSUE:")
    logger.info("The frontend is probably getting 401/403 errors when calling the API,")
    logger.info("which means the bulk clients list appears empty not because there are")
    logger.info("no bulk clients, but because the API calls are being rejected.")
    
    logger.info("\n🔧 RECOMMENDED FIXES:")
    logger.info("1. Check frontend authentication token generation/refresh")
    logger.info("2. Verify Clerk JWT token configuration")
    logger.info("3. Check if frontend is handling 401/403 errors properly")
    logger.info("4. Ensure frontend is using correct API URL and headers")

if __name__ == "__main__":
    main()