#!/usr/bin/env python3
"""
Bulk Clients API Testing Script
===============================

This script specifically tests the bulk clients API endpoint to debug why bulk clients 
are not showing in the frontend list despite being imported successfully.

Test Objectives:
1. Test `/api/clients?client_type=bulk` endpoint specifically 
2. Verify that bulk clients are returned correctly with pagination
3. Check the exact response format and structure
4. Test with different pagination parameters (page=1, limit=50)
5. Verify that the response includes proper pagination metadata

Context:
- User performed bulk import and got 1 client imported (CANER OTEL | ISPARTA)
- Frontend BulkOperations component shows empty list despite database having 1 bulk client
- Need to verify if the API is returning the bulk client correctly
"""

import requests
import json
import logging
import sys
from datetime import datetime
from pymongo import MongoClient
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = "https://rota-crm-production.up.railway.app"
API_URL = f"{BACKEND_URL}/api"

# MongoDB connection (from backend/.env)
MONGO_URL = "mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster"
DB_NAME = "rotacrm"

# Test tokens (these would normally be generated from Clerk)
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
INVALID_TOKEN = "invalid.token.format"

def print_separator(title):
    """Print a formatted separator with title"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def print_subsection(title):
    """Print a formatted subsection"""
    print(f"\n--- {title} ---")

def test_database_bulk_clients():
    """Test 1: Direct database verification of bulk clients"""
    print_separator("TEST 1: DATABASE VERIFICATION - BULK CLIENTS")
    
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Count total clients
        total_clients = db.clients.count_documents({})
        logger.info(f"📊 Total clients in database: {total_clients}")
        
        # Count bulk clients specifically
        bulk_clients_count = db.clients.count_documents({"client_type": "bulk"})
        logger.info(f"📊 Bulk clients in database: {bulk_clients_count}")
        
        # Count registered clients
        registered_clients_count = db.clients.count_documents({"client_type": "registered"})
        logger.info(f"📊 Registered clients in database: {registered_clients_count}")
        
        # Get bulk clients details
        bulk_clients = list(db.clients.find({"client_type": "bulk"}))
        
        if bulk_clients:
            print_subsection("BULK CLIENTS FOUND IN DATABASE")
            for i, client in enumerate(bulk_clients, 1):
                logger.info(f"Bulk Client {i}:")
                logger.info(f"  ID: {client.get('id', 'N/A')}")
                logger.info(f"  Name: {client.get('name', 'N/A')}")
                logger.info(f"  Hotel Name: {client.get('hotel_name', 'N/A')}")
                logger.info(f"  Contact Person: {client.get('contact_person', 'N/A')}")
                logger.info(f"  Email: {client.get('email', 'N/A')}")
                logger.info(f"  City: {client.get('city', 'N/A')}")
                logger.info(f"  Client Type: {client.get('client_type', 'N/A')}")
                logger.info(f"  Import Source: {client.get('import_source', 'N/A')}")
                logger.info(f"  Created At: {client.get('created_at', 'N/A')}")
                print()
        else:
            logger.warning("⚠️ NO BULK CLIENTS FOUND IN DATABASE!")
        
        # Check for the specific client mentioned (CANER OTEL | ISPARTA)
        caner_client = db.clients.find_one({
            "$or": [
                {"name": {"$regex": "CANER", "$options": "i"}},
                {"hotel_name": {"$regex": "CANER", "$options": "i"}},
                {"contact_person": {"$regex": "CANER", "$options": "i"}},
                {"city": {"$regex": "ISPARTA", "$options": "i"}}
            ]
        })
        
        if caner_client:
            print_subsection("CANER OTEL CLIENT FOUND")
            logger.info(f"Found CANER client:")
            logger.info(f"  ID: {caner_client.get('id', 'N/A')}")
            logger.info(f"  Name: {caner_client.get('name', 'N/A')}")
            logger.info(f"  Hotel Name: {caner_client.get('hotel_name', 'N/A')}")
            logger.info(f"  Contact Person: {caner_client.get('contact_person', 'N/A')}")
            logger.info(f"  City: {caner_client.get('city', 'N/A')}")
            logger.info(f"  Client Type: {caner_client.get('client_type', 'N/A')}")
            logger.info(f"  Import Source: {caner_client.get('import_source', 'N/A')}")
        else:
            logger.warning("⚠️ CANER OTEL CLIENT NOT FOUND!")
        
        client.close()
        
        return {
            "total_clients": total_clients,
            "bulk_clients_count": bulk_clients_count,
            "registered_clients_count": registered_clients_count,
            "bulk_clients": bulk_clients,
            "caner_client": caner_client
        }
        
    except Exception as e:
        logger.error(f"❌ Database verification failed: {str(e)}")
        return None

def test_bulk_clients_api_basic():
    """Test 2: Basic bulk clients API endpoint test"""
    print_separator("TEST 2: BASIC BULK CLIENTS API ENDPOINT")
    
    url = f"{API_URL}/clients"
    params = {"client_type": "bulk"}
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    try:
        logger.info(f"🔍 Testing URL: {url}")
        logger.info(f"🔍 Parameters: {params}")
        logger.info(f"🔍 Headers: Authorization Bearer [TOKEN]")
        
        response = requests.get(url, params=params, headers=headers)
        
        logger.info(f"📡 Response Status Code: {response.status_code}")
        logger.info(f"📡 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                logger.info(f"✅ SUCCESS: API returned {len(data) if isinstance(data, list) else 'non-list'} items")
                
                if isinstance(data, list):
                    logger.info(f"📊 Response is a list with {len(data)} items")
                    
                    if len(data) > 0:
                        print_subsection("BULK CLIENTS FROM API")
                        for i, client in enumerate(data, 1):
                            logger.info(f"API Client {i}:")
                            logger.info(f"  ID: {client.get('id', 'N/A')}")
                            logger.info(f"  Name: {client.get('name', 'N/A')}")
                            logger.info(f"  Hotel Name: {client.get('hotel_name', 'N/A')}")
                            logger.info(f"  Contact Person: {client.get('contact_person', 'N/A')}")
                            logger.info(f"  Email: {client.get('email', 'N/A')}")
                            logger.info(f"  Client Type: {client.get('client_type', 'N/A')}")
                            print()
                    else:
                        logger.warning("⚠️ API RETURNED EMPTY LIST!")
                        
                elif isinstance(data, dict):
                    logger.info(f"📊 Response is a dict with keys: {list(data.keys())}")
                    logger.info(f"📊 Full response: {json.dumps(data, indent=2)}")
                else:
                    logger.warning(f"⚠️ Unexpected response type: {type(data)}")
                    logger.info(f"📊 Response content: {data}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse JSON response: {str(e)}")
                logger.info(f"📊 Raw response: {response.text[:500]}...")
                
        elif response.status_code == 401:
            logger.warning("⚠️ AUTHENTICATION FAILED (401)")
            try:
                error_data = response.json()
                logger.info(f"Error details: {error_data}")
            except:
                logger.info(f"Raw error response: {response.text}")
                
        elif response.status_code == 403:
            logger.warning("⚠️ ACCESS FORBIDDEN (403)")
            try:
                error_data = response.json()
                logger.info(f"Error details: {error_data}")
            except:
                logger.info(f"Raw error response: {response.text}")
                
        else:
            logger.error(f"❌ UNEXPECTED STATUS CODE: {response.status_code}")
            logger.info(f"Response text: {response.text[:500]}...")
            
        return response
        
    except Exception as e:
        logger.error(f"❌ API test failed: {str(e)}")
        return None

def test_bulk_clients_api_with_pagination():
    """Test 3: Bulk clients API with pagination parameters"""
    print_separator("TEST 3: BULK CLIENTS API WITH PAGINATION")
    
    url = f"{API_URL}/clients"
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Test different pagination scenarios
    test_cases = [
        {"client_type": "bulk", "page": 1, "limit": 50},
        {"client_type": "bulk", "page": 1, "limit": 10},
        {"client_type": "bulk", "page": 2, "limit": 10},
        {"client_type": "bulk"},  # No pagination params
    ]
    
    for i, params in enumerate(test_cases, 1):
        print_subsection(f"PAGINATION TEST {i}: {params}")
        
        try:
            response = requests.get(url, params=params, headers=headers)
            logger.info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if isinstance(data, dict):
                        # Check if it's a paginated response
                        if "clients" in data:
                            clients = data["clients"]
                            pagination = data.get("pagination", {})
                            logger.info(f"✅ Paginated response: {len(clients)} clients")
                            logger.info(f"📊 Pagination info: {pagination}")
                            
                            # Log client details
                            for j, client in enumerate(clients, 1):
                                logger.info(f"  Client {j}: {client.get('name', 'N/A')} - {client.get('client_type', 'N/A')}")
                                
                        else:
                            logger.info(f"📊 Dict response keys: {list(data.keys())}")
                            
                    elif isinstance(data, list):
                        logger.info(f"✅ List response: {len(data)} clients")
                        
                        # Log client details
                        for j, client in enumerate(data, 1):
                            logger.info(f"  Client {j}: {client.get('name', 'N/A')} - {client.get('client_type', 'N/A')}")
                            
                    else:
                        logger.warning(f"⚠️ Unexpected response type: {type(data)}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error: {str(e)}")
                    
            else:
                logger.warning(f"⚠️ Non-200 status: {response.status_code}")
                try:
                    error_data = response.json()
                    logger.info(f"Error: {error_data}")
                except:
                    logger.info(f"Raw error: {response.text[:200]}...")
                    
        except Exception as e:
            logger.error(f"❌ Pagination test {i} failed: {str(e)}")

def test_all_clients_vs_bulk_clients():
    """Test 4: Compare all clients vs bulk clients response"""
    print_separator("TEST 4: ALL CLIENTS VS BULK CLIENTS COMPARISON")
    
    url = f"{API_URL}/clients"
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Test all clients
    print_subsection("ALL CLIENTS REQUEST")
    try:
        response_all = requests.get(url, headers=headers)
        logger.info(f"All clients status: {response_all.status_code}")
        
        if response_all.status_code == 200:
            all_clients = response_all.json()
            if isinstance(all_clients, list):
                logger.info(f"✅ All clients: {len(all_clients)} total")
                
                # Count by client_type
                bulk_count = sum(1 for c in all_clients if c.get('client_type') == 'bulk')
                registered_count = sum(1 for c in all_clients if c.get('client_type') == 'registered')
                other_count = len(all_clients) - bulk_count - registered_count
                
                logger.info(f"  - Bulk clients: {bulk_count}")
                logger.info(f"  - Registered clients: {registered_count}")
                logger.info(f"  - Other/Unknown: {other_count}")
                
                # Show some bulk clients if they exist
                bulk_clients_in_all = [c for c in all_clients if c.get('client_type') == 'bulk']
                if bulk_clients_in_all:
                    logger.info("Bulk clients found in all clients:")
                    for client in bulk_clients_in_all[:5]:  # Show first 5
                        logger.info(f"  - {client.get('name', 'N/A')} ({client.get('client_type', 'N/A')})")
                        
            else:
                logger.info(f"All clients response type: {type(all_clients)}")
                
    except Exception as e:
        logger.error(f"❌ All clients test failed: {str(e)}")
    
    # Test bulk clients specifically
    print_subsection("BULK CLIENTS ONLY REQUEST")
    try:
        params = {"client_type": "bulk"}
        response_bulk = requests.get(url, params=params, headers=headers)
        logger.info(f"Bulk clients status: {response_bulk.status_code}")
        
        if response_bulk.status_code == 200:
            bulk_clients = response_bulk.json()
            if isinstance(bulk_clients, list):
                logger.info(f"✅ Bulk clients only: {len(bulk_clients)} total")
                
                if bulk_clients:
                    logger.info("Bulk clients from filtered request:")
                    for client in bulk_clients:
                        logger.info(f"  - {client.get('name', 'N/A')} ({client.get('client_type', 'N/A')})")
                else:
                    logger.warning("⚠️ BULK CLIENTS FILTER RETURNED EMPTY LIST!")
                    
            else:
                logger.info(f"Bulk clients response type: {type(bulk_clients)}")
                
    except Exception as e:
        logger.error(f"❌ Bulk clients test failed: {str(e)}")

def test_authentication_scenarios():
    """Test 5: Different authentication scenarios"""
    print_separator("TEST 5: AUTHENTICATION SCENARIOS")
    
    url = f"{API_URL}/clients"
    params = {"client_type": "bulk"}
    
    test_scenarios = [
        ("Valid Admin Token", {"Authorization": f"Bearer {ADMIN_TOKEN}"}),
        ("Invalid Token", {"Authorization": f"Bearer {INVALID_TOKEN}"}),
        ("No Authorization", {}),
        ("Malformed Header", {"Authorization": "InvalidFormat"}),
    ]
    
    for scenario_name, headers in test_scenarios:
        print_subsection(f"AUTH TEST: {scenario_name}")
        
        try:
            response = requests.get(url, params=params, headers=headers)
            logger.info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        logger.info(f"✅ Success: {len(data)} bulk clients returned")
                    else:
                        logger.info(f"✅ Success: Response type {type(data)}")
                except:
                    logger.info("✅ Success: Non-JSON response")
                    
            elif response.status_code in [401, 403]:
                try:
                    error_data = response.json()
                    logger.info(f"⚠️ Expected auth error: {error_data.get('detail', 'No detail')}")
                except:
                    logger.info(f"⚠️ Expected auth error: {response.text[:100]}...")
                    
            else:
                logger.warning(f"⚠️ Unexpected status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Auth test failed: {str(e)}")

def test_response_format_analysis():
    """Test 6: Detailed response format analysis"""
    print_separator("TEST 6: RESPONSE FORMAT ANALYSIS")
    
    url = f"{API_URL}/clients"
    params = {"client_type": "bulk", "page": 1, "limit": 50}
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        logger.info(f"Content-Length: {response.headers.get('content-length', 'N/A')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                print_subsection("RESPONSE STRUCTURE ANALYSIS")
                logger.info(f"Response type: {type(data)}")
                
                if isinstance(data, dict):
                    logger.info(f"Dict keys: {list(data.keys())}")
                    
                    # Check for pagination structure
                    if "clients" in data and "pagination" in data:
                        logger.info("✅ PAGINATED RESPONSE FORMAT DETECTED")
                        clients = data["clients"]
                        pagination = data["pagination"]
                        
                        logger.info(f"Clients array length: {len(clients)}")
                        logger.info(f"Pagination info: {json.dumps(pagination, indent=2)}")
                        
                        if clients:
                            print_subsection("SAMPLE CLIENT STRUCTURE")
                            sample_client = clients[0]
                            logger.info("Sample client fields:")
                            for key, value in sample_client.items():
                                logger.info(f"  {key}: {type(value).__name__} = {value}")
                                
                    else:
                        logger.info("📊 Non-paginated dict response")
                        logger.info(f"Full response: {json.dumps(data, indent=2, default=str)}")
                        
                elif isinstance(data, list):
                    logger.info("✅ SIMPLE LIST RESPONSE FORMAT DETECTED")
                    logger.info(f"List length: {len(data)}")
                    
                    if data:
                        print_subsection("SAMPLE CLIENT STRUCTURE")
                        sample_client = data[0]
                        logger.info("Sample client fields:")
                        for key, value in sample_client.items():
                            logger.info(f"  {key}: {type(value).__name__} = {value}")
                            
                else:
                    logger.warning(f"⚠️ Unexpected response type: {type(data)}")
                    logger.info(f"Response content: {str(data)[:500]}...")
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON decode failed: {str(e)}")
                logger.info(f"Raw response (first 500 chars): {response.text[:500]}")
                
        else:
            logger.warning(f"⚠️ Non-200 response")
            logger.info(f"Response text: {response.text[:300]}...")
            
    except Exception as e:
        logger.error(f"❌ Response format analysis failed: {str(e)}")

def main():
    """Main test execution"""
    print_separator("BULK CLIENTS API DEBUGGING TEST SUITE")
    logger.info("🚀 Starting comprehensive bulk clients API testing...")
    logger.info(f"🔗 Backend URL: {BACKEND_URL}")
    logger.info(f"🔗 API URL: {API_URL}")
    logger.info(f"📅 Test started at: {datetime.now()}")
    
    # Run all tests
    try:
        # Test 1: Database verification
        db_results = test_database_bulk_clients()
        
        # Test 2: Basic API test
        api_response = test_bulk_clients_api_basic()
        
        # Test 3: Pagination tests
        test_bulk_clients_api_with_pagination()
        
        # Test 4: Compare all vs bulk clients
        test_all_clients_vs_bulk_clients()
        
        # Test 5: Authentication scenarios
        test_authentication_scenarios()
        
        # Test 6: Response format analysis
        test_response_format_analysis()
        
        # Summary
        print_separator("TEST SUMMARY")
        
        if db_results:
            logger.info(f"📊 Database Summary:")
            logger.info(f"  - Total clients: {db_results['total_clients']}")
            logger.info(f"  - Bulk clients: {db_results['bulk_clients_count']}")
            logger.info(f"  - Registered clients: {db_results['registered_clients_count']}")
            logger.info(f"  - CANER client found: {'Yes' if db_results['caner_client'] else 'No'}")
        
        if api_response:
            logger.info(f"📡 API Summary:")
            logger.info(f"  - API Status: {api_response.status_code}")
            logger.info(f"  - API accessible: {'Yes' if api_response.status_code in [200, 401, 403] else 'No'}")
        
        logger.info("🏁 Test suite completed!")
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()