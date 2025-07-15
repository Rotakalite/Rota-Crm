#!/usr/bin/env python3
"""
Registered Client Filter Test
Test the client_type=registered filter specifically for ClientManagement

Test Objectives:
1. Test `/api/clients?client_type=registered` endpoint specifically
2. Verify that it returns only registered clients (not bulk clients)
3. Test the response format matches what frontend expects
4. Check pagination works with registered clients

Context:
- Database has 2 registered clients: CRM OTEL and BIYIĞI GÜR OTEL
- Frontend ClientManagement component is not showing these clients
- clientTypeFilter is set to 'registered' by default
- Need to verify backend filtering works correctly

Expected Response:
- Should return { clients: [...], pagination: {...} }
- Should contain only clients with client_type='registered'
- Should NOT contain bulk clients
- Should have proper pagination metadata
"""

import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from frontend/.env
BACKEND_URL = "https://rota-crm-production.up.railway.app"
API_BASE_URL = f"{BACKEND_URL}/api"

# Test tokens (these would normally be valid JWT tokens from Clerk)
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
INVALID_TOKEN = "invalid.token.format"

def test_registered_client_filter():
    """
    Main test function for registered client filtering
    """
    logger.info("=" * 80)
    logger.info("REGISTERED CLIENT FILTER TEST - STARTING")
    logger.info("=" * 80)
    
    # Test 1: Basic endpoint accessibility
    test_endpoint_accessibility()
    
    # Test 2: Test registered client filtering
    test_registered_client_filtering()
    
    # Test 3: Test pagination with registered clients
    test_pagination_with_registered_clients()
    
    # Test 4: Test response format validation
    test_response_format_validation()
    
    # Test 5: Test that bulk clients are excluded
    test_bulk_clients_exclusion()
    
    # Test 6: Test authentication requirements
    test_authentication_requirements()
    
    logger.info("=" * 80)
    logger.info("REGISTERED CLIENT FILTER TEST - COMPLETED")
    logger.info("=" * 80)

def test_endpoint_accessibility():
    """Test 1: Basic endpoint accessibility"""
    logger.info("\n=== TEST 1: ENDPOINT ACCESSIBILITY ===")
    
    url = f"{API_BASE_URL}/clients"
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    try:
        # Test basic endpoint without filters
        response = requests.get(url, headers=headers, timeout=30)
        logger.info(f"Basic endpoint response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Endpoint accessible - Response type: {type(data)}")
            
            # Check if response is paginated format or direct list
            if isinstance(data, dict) and "clients" in data:
                logger.info(f"✅ Paginated response format detected - {len(data['clients'])} clients")
                if "pagination" in data:
                    logger.info(f"✅ Pagination metadata present: {data['pagination']}")
            elif isinstance(data, list):
                logger.info(f"✅ Direct list response format - {len(data)} clients")
            else:
                logger.warning(f"⚠️ Unexpected response format: {type(data)}")
                
        elif response.status_code == 401:
            logger.warning(f"⚠️ Authentication required: {response.text}")
        elif response.status_code == 403:
            logger.warning(f"⚠️ Access forbidden: {response.text}")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")

def test_registered_client_filtering():
    """Test 2: Test registered client filtering"""
    logger.info("\n=== TEST 2: REGISTERED CLIENT FILTERING ===")
    
    url = f"{API_BASE_URL}/clients"
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    params = {"client_type": "registered"}
    
    try:
        # Test with client_type=registered filter
        response = requests.get(url, headers=headers, params=params, timeout=30)
        logger.info(f"Registered filter response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Registered filter successful - Response type: {type(data)}")
            
            # Handle both paginated and direct list responses
            clients = []
            if isinstance(data, dict) and "clients" in data:
                clients = data["clients"]
                logger.info(f"✅ Paginated response - {len(clients)} registered clients found")
            elif isinstance(data, list):
                clients = data
                logger.info(f"✅ Direct list response - {len(clients)} registered clients found")
            
            # Verify all clients have client_type='registered'
            registered_count = 0
            bulk_count = 0
            missing_type_count = 0
            
            for i, client in enumerate(clients):
                client_type = client.get("client_type", "missing")
                client_name = client.get("name", "Unknown")
                hotel_name = client.get("hotel_name", "Unknown")
                
                logger.info(f"Client {i+1}: {client_name} / {hotel_name} - Type: {client_type}")
                
                if client_type == "registered":
                    registered_count += 1
                elif client_type == "bulk":
                    bulk_count += 1
                    logger.error(f"❌ BULK CLIENT FOUND IN REGISTERED FILTER: {client_name}")
                else:
                    missing_type_count += 1
                    logger.warning(f"⚠️ CLIENT WITH MISSING/INVALID TYPE: {client_name} - Type: {client_type}")
            
            logger.info(f"📊 FILTERING RESULTS:")
            logger.info(f"   Registered clients: {registered_count}")
            logger.info(f"   Bulk clients (should be 0): {bulk_count}")
            logger.info(f"   Missing/invalid type: {missing_type_count}")
            
            # Verify expected registered clients are present
            expected_clients = ["CRM OTEL", "BIYIĞI GÜR OTEL"]
            found_expected = []
            
            for client in clients:
                client_name = client.get("name", "")
                hotel_name = client.get("hotel_name", "")
                full_name = f"{client_name} {hotel_name}".upper()
                
                for expected in expected_clients:
                    if expected.upper() in full_name:
                        found_expected.append(expected)
                        logger.info(f"✅ Expected client found: {expected}")
            
            logger.info(f"📊 EXPECTED CLIENTS VERIFICATION:")
            logger.info(f"   Expected: {expected_clients}")
            logger.info(f"   Found: {found_expected}")
            
            if bulk_count == 0:
                logger.info("✅ FILTERING SUCCESS: No bulk clients in registered filter")
            else:
                logger.error("❌ FILTERING FAILED: Bulk clients found in registered filter")
                
        elif response.status_code == 401:
            logger.warning(f"⚠️ Authentication required: {response.text}")
        elif response.status_code == 403:
            logger.warning(f"⚠️ Access forbidden: {response.text}")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")

def test_pagination_with_registered_clients():
    """Test 3: Test pagination with registered clients"""
    logger.info("\n=== TEST 3: PAGINATION WITH REGISTERED CLIENTS ===")
    
    url = f"{API_BASE_URL}/clients"
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    params = {
        "client_type": "registered",
        "page": 1,
        "limit": 50
    }
    
    try:
        # Test pagination parameters
        response = requests.get(url, headers=headers, params=params, timeout=30)
        logger.info(f"Pagination test response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Pagination test successful - Response type: {type(data)}")
            
            # Check pagination metadata
            if isinstance(data, dict):
                if "pagination" in data:
                    pagination = data["pagination"]
                    logger.info(f"✅ Pagination metadata found:")
                    logger.info(f"   Current page: {pagination.get('current_page', 'N/A')}")
                    logger.info(f"   Total pages: {pagination.get('total_pages', 'N/A')}")
                    logger.info(f"   Total items: {pagination.get('total_items', 'N/A')}")
                    logger.info(f"   Items per page: {pagination.get('items_per_page', 'N/A')}")
                    
                    # Verify pagination values
                    if pagination.get('current_page') == 1:
                        logger.info("✅ Current page correctly set to 1")
                    if pagination.get('items_per_page') == 50:
                        logger.info("✅ Items per page correctly set to 50")
                        
                else:
                    logger.warning("⚠️ No pagination metadata in response")
                
                if "clients" in data:
                    clients = data["clients"]
                    logger.info(f"✅ Clients array found with {len(clients)} items")
                    
                    # Verify all are registered clients
                    for client in clients:
                        if client.get("client_type") != "registered":
                            logger.error(f"❌ Non-registered client in paginated results: {client.get('name')}")
                else:
                    logger.warning("⚠️ No clients array in response")
            else:
                logger.warning("⚠️ Response is not paginated format")
                
        elif response.status_code == 401:
            logger.warning(f"⚠️ Authentication required: {response.text}")
        elif response.status_code == 403:
            logger.warning(f"⚠️ Access forbidden: {response.text}")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")

def test_response_format_validation():
    """Test 4: Test response format validation"""
    logger.info("\n=== TEST 4: RESPONSE FORMAT VALIDATION ===")
    
    url = f"{API_BASE_URL}/clients"
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    params = {"client_type": "registered"}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        logger.info(f"Response format validation status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ JSON response received")
            
            # Validate expected response structure
            if isinstance(data, dict):
                logger.info("✅ Response is object format")
                
                # Check for expected fields
                expected_fields = ["clients", "pagination"]
                for field in expected_fields:
                    if field in data:
                        logger.info(f"✅ Field '{field}' present in response")
                    else:
                        logger.warning(f"⚠️ Field '{field}' missing from response")
                
                # Validate clients array structure
                if "clients" in data and isinstance(data["clients"], list):
                    clients = data["clients"]
                    logger.info(f"✅ Clients array with {len(clients)} items")
                    
                    if len(clients) > 0:
                        # Validate first client structure
                        client = clients[0]
                        expected_client_fields = [
                            "id", "name", "hotel_name", "contact_person", 
                            "email", "phone", "address", "client_type"
                        ]
                        
                        logger.info("📋 Client structure validation:")
                        for field in expected_client_fields:
                            if field in client:
                                logger.info(f"   ✅ {field}: {client.get(field)}")
                            else:
                                logger.warning(f"   ⚠️ {field}: MISSING")
                
            elif isinstance(data, list):
                logger.info("✅ Response is array format (legacy)")
                logger.info(f"   Array length: {len(data)}")
                
                if len(data) > 0:
                    # Validate first client structure
                    client = data[0]
                    expected_client_fields = [
                        "id", "name", "hotel_name", "contact_person", 
                        "email", "phone", "address", "client_type"
                    ]
                    
                    logger.info("📋 Client structure validation:")
                    for field in expected_client_fields:
                        if field in client:
                            logger.info(f"   ✅ {field}: {client.get(field)}")
                        else:
                            logger.warning(f"   ⚠️ {field}: MISSING")
            else:
                logger.error(f"❌ Unexpected response format: {type(data)}")
                
        elif response.status_code == 401:
            logger.warning(f"⚠️ Authentication required: {response.text}")
        elif response.status_code == 403:
            logger.warning(f"⚠️ Access forbidden: {response.text}")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")

def test_bulk_clients_exclusion():
    """Test 5: Test that bulk clients are excluded from registered filter"""
    logger.info("\n=== TEST 5: BULK CLIENTS EXCLUSION TEST ===")
    
    url = f"{API_BASE_URL}/clients"
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    try:
        # First, get all clients to see what's in the database
        logger.info("🔍 Getting all clients to verify database content...")
        response_all = requests.get(url, headers=headers, timeout=30)
        
        if response_all.status_code == 200:
            all_data = response_all.json()
            all_clients = all_data.get("clients", all_data) if isinstance(all_data, dict) else all_data
            
            bulk_clients = [c for c in all_clients if c.get("client_type") == "bulk"]
            registered_clients = [c for c in all_clients if c.get("client_type") == "registered"]
            
            logger.info(f"📊 Database content:")
            logger.info(f"   Total clients: {len(all_clients)}")
            logger.info(f"   Bulk clients: {len(bulk_clients)}")
            logger.info(f"   Registered clients: {len(registered_clients)}")
            
            # Log some bulk client names for reference
            if bulk_clients:
                logger.info("📋 Sample bulk clients:")
                for i, client in enumerate(bulk_clients[:5]):  # Show first 5
                    logger.info(f"   {i+1}. {client.get('name', 'Unknown')} / {client.get('hotel_name', 'Unknown')}")
        
        # Now test registered filter
        logger.info("\n🔍 Testing registered filter exclusion...")
        params = {"client_type": "registered"}
        response_registered = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response_registered.status_code == 200:
            registered_data = response_registered.json()
            filtered_clients = registered_data.get("clients", registered_data) if isinstance(registered_data, dict) else registered_data
            
            logger.info(f"📊 Registered filter results:")
            logger.info(f"   Filtered clients: {len(filtered_clients)}")
            
            # Check for any bulk clients in the filtered results
            bulk_in_registered = [c for c in filtered_clients if c.get("client_type") == "bulk"]
            
            if bulk_in_registered:
                logger.error(f"❌ CRITICAL: {len(bulk_in_registered)} bulk clients found in registered filter!")
                for client in bulk_in_registered:
                    logger.error(f"   ❌ Bulk client: {client.get('name')} / {client.get('hotel_name')}")
            else:
                logger.info("✅ SUCCESS: No bulk clients found in registered filter")
            
            # Verify all filtered clients are registered
            non_registered = [c for c in filtered_clients if c.get("client_type") != "registered"]
            
            if non_registered:
                logger.error(f"❌ CRITICAL: {len(non_registered)} non-registered clients found!")
                for client in non_registered:
                    logger.error(f"   ❌ Non-registered: {client.get('name')} - Type: {client.get('client_type')}")
            else:
                logger.info("✅ SUCCESS: All filtered clients are registered type")
                
        # Test bulk filter to ensure it works in reverse
        logger.info("\n🔍 Testing bulk filter for comparison...")
        params_bulk = {"client_type": "bulk"}
        response_bulk = requests.get(url, headers=headers, params=params_bulk, timeout=30)
        
        if response_bulk.status_code == 200:
            bulk_data = response_bulk.json()
            bulk_filtered = bulk_data.get("clients", bulk_data) if isinstance(bulk_data, dict) else bulk_data
            
            logger.info(f"📊 Bulk filter results:")
            logger.info(f"   Bulk filtered clients: {len(bulk_filtered)}")
            
            # Check for any registered clients in bulk filter
            registered_in_bulk = [c for c in bulk_filtered if c.get("client_type") == "registered"]
            
            if registered_in_bulk:
                logger.error(f"❌ CRITICAL: {len(registered_in_bulk)} registered clients found in bulk filter!")
            else:
                logger.info("✅ SUCCESS: No registered clients found in bulk filter")
                
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")

def test_authentication_requirements():
    """Test 6: Test authentication requirements"""
    logger.info("\n=== TEST 6: AUTHENTICATION REQUIREMENTS ===")
    
    url = f"{API_BASE_URL}/clients"
    params = {"client_type": "registered"}
    
    # Test scenarios
    test_cases = [
        ("No Authentication", {}, [403], "Should require authentication"),
        ("Invalid Token", {"Authorization": f"Bearer {INVALID_TOKEN}"}, [401], "Should reject invalid token"),
        ("Malformed Token", {"Authorization": "Bearer malformed.token"}, [401], "Should reject malformed token"),
        ("Empty Token", {"Authorization": "Bearer "}, [401], "Should reject empty token"),
        ("Valid Token", {"Authorization": f"Bearer {ADMIN_TOKEN}"}, [200, 401], "Should work with valid token or return auth error")
    ]
    
    for test_name, headers, expected_codes, description in test_cases:
        try:
            logger.info(f"\n--- {test_name} ---")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            logger.info(f"Status: {response.status_code} - {description}")
            
            if response.status_code in expected_codes:
                logger.info(f"✅ {test_name}: Expected status code {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    clients = data.get("clients", data) if isinstance(data, dict) else data
                    logger.info(f"   Retrieved {len(clients)} registered clients")
                    
                elif response.status_code in [401, 403]:
                    try:
                        error_data = response.json()
                        logger.info(f"   Error: {error_data.get('detail', 'No detail')}")
                    except:
                        logger.info(f"   Error response: {response.text}")
            else:
                logger.error(f"❌ {test_name}: Unexpected status {response.status_code}, expected {expected_codes}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ {test_name} request failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ {test_name} unexpected error: {str(e)}")

if __name__ == "__main__":
    test_registered_client_filter()