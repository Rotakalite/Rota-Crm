import unittest
import json
import logging
import requests
import os
import sys
import io
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from frontend/.env
BACKEND_URL = "https://eeb7db6e-db39-4d4e-be1b-fe2f8cdcb81a.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

# Test JWT tokens
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
INVALID_TOKEN = "invalid.token.format"

def run_supplier_tests():
    """Run comprehensive tests for supplier management endpoints"""
    logger.info("Starting comprehensive supplier management API tests...")
    
    # Test public endpoints
    test_public_endpoints()
    
    # Test authenticated endpoints
    test_authenticated_endpoints()
    
    logger.info("All supplier management tests completed!")

def test_public_endpoints():
    """Test public supplier endpoints that don't require authentication"""
    logger.info("\n=== Testing public supplier endpoints ===")
    
    # Test categories endpoint
    url = f"{API_URL}/suppliers/categories/list"
    logger.info(f"Testing GET {url}")
    
    try:
        response = requests.get(url)
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Found {len(data['categories'])} supplier categories")
            logger.info(f"Categories: {data['categories']}")
            logger.info("✅ GET /api/suppliers/categories/list test passed")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing supplier categories endpoint: {str(e)}")
    
    # Test certifications endpoint
    url = f"{API_URL}/suppliers/certifications/list"
    logger.info(f"Testing GET {url}")
    
    try:
        response = requests.get(url)
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Found {len(data['certifications'])} supplier certifications")
            logger.info(f"Certifications: {data['certifications']}")
            logger.info("✅ GET /api/suppliers/certifications/list test passed")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing supplier certifications endpoint: {str(e)}")

def test_authenticated_endpoints():
    """Test authenticated supplier endpoints"""
    logger.info("\n=== Testing authenticated supplier endpoints ===")
    
    # Test data for supplier creation
    test_supplier_data = {
        "company_name": f"Test Supplier {uuid.uuid4()}",
        "contact_person": "John Doe",
        "email": "john@testsupplier.com",
        "phone": "1234567890",
        "address": "123 Test St, Test City",
        "category": "Gıda & İçecek",
        "sustainability_score": 75,
        "certifications": ["ISO 14001", "Organik Sertifika"],
        "local_supplier": True,
        "website": "https://testsupplier.com",
        "description": "A test supplier for API testing",
        "client_id": "8bfd3a85-2483-4b63-9e80-e53747c3db7e"  # Sample client ID
    }
    
    # Headers
    headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
    
    # Test POST /api/suppliers
    url = f"{API_URL}/suppliers"
    logger.info(f"Testing POST {url}")
    
    # Test with invalid token
    try:
        response = requests.post(url, headers=headers_invalid, json=test_supplier_data)
        logger.info(f"Invalid token response status code: {response.status_code}")
        
        if response.status_code == 401:
            logger.info("✅ POST /api/suppliers with invalid token correctly returns 401")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing POST /api/suppliers with invalid token: {str(e)}")
    
    # Test with no token
    try:
        response = requests.post(url, json=test_supplier_data)
        logger.info(f"No token response status code: {response.status_code}")
        
        if response.status_code == 403:
            logger.info("✅ POST /api/suppliers with no token correctly returns 403")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing POST /api/suppliers with no token: {str(e)}")
    
    # Test GET /api/suppliers
    url = f"{API_URL}/suppliers"
    logger.info(f"Testing GET {url}")
    
    # Test with invalid token
    try:
        response = requests.get(url, headers=headers_invalid)
        logger.info(f"Invalid token response status code: {response.status_code}")
        
        if response.status_code == 401:
            logger.info("✅ GET /api/suppliers with invalid token correctly returns 401")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing GET /api/suppliers with invalid token: {str(e)}")
    
    # Test with no token
    try:
        response = requests.get(url)
        logger.info(f"No token response status code: {response.status_code}")
        
        if response.status_code == 403:
            logger.info("✅ GET /api/suppliers with no token correctly returns 403")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing GET /api/suppliers with no token: {str(e)}")
    
    # Test GET /api/suppliers/analytics/dashboard
    url = f"{API_URL}/suppliers/analytics/dashboard"
    logger.info(f"Testing GET {url}")
    
    # Test with invalid token
    try:
        response = requests.get(url, headers=headers_invalid)
        logger.info(f"Invalid token response status code: {response.status_code}")
        
        if response.status_code == 401:
            logger.info("✅ GET /api/suppliers/analytics/dashboard with invalid token correctly returns 401")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing GET /api/suppliers/analytics/dashboard with invalid token: {str(e)}")
    
    # Test with no token
    try:
        response = requests.get(url)
        logger.info(f"No token response status code: {response.status_code}")
        
        if response.status_code == 403:
            logger.info("✅ GET /api/suppliers/analytics/dashboard with no token correctly returns 403")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing GET /api/suppliers/analytics/dashboard with no token: {str(e)}")
    
    # Test GET /api/suppliers/{supplier_id}
    # Use a dummy ID since we don't have a valid one
    supplier_id = "test-supplier-id"
    url = f"{API_URL}/suppliers/{supplier_id}"
    logger.info(f"Testing GET {url}")
    
    # Test with invalid token
    try:
        response = requests.get(url, headers=headers_invalid)
        logger.info(f"Invalid token response status code: {response.status_code}")
        
        if response.status_code == 401:
            logger.info("✅ GET /api/suppliers/{supplier_id} with invalid token correctly returns 401")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing GET /api/suppliers/{supplier_id} with invalid token: {str(e)}")
    
    # Test with no token
    try:
        response = requests.get(url)
        logger.info(f"No token response status code: {response.status_code}")
        
        if response.status_code == 403:
            logger.info("✅ GET /api/suppliers/{supplier_id} with no token correctly returns 403")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing GET /api/suppliers/{supplier_id} with no token: {str(e)}")
    
    # Test PUT /api/suppliers/{supplier_id}
    url = f"{API_URL}/suppliers/{supplier_id}"
    logger.info(f"Testing PUT {url}")
    
    update_data = {
        "company_name": f"Updated Supplier {uuid.uuid4()}",
        "sustainability_score": 85,
        "certifications": ["ISO 14001", "Organik Sertifika", "Fair Trade"],
        "description": "Updated description for testing"
    }
    
    # Test with invalid token
    try:
        response = requests.put(url, headers=headers_invalid, json=update_data)
        logger.info(f"Invalid token response status code: {response.status_code}")
        
        if response.status_code == 401:
            logger.info("✅ PUT /api/suppliers/{supplier_id} with invalid token correctly returns 401")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing PUT /api/suppliers/{supplier_id} with invalid token: {str(e)}")
    
    # Test with no token
    try:
        response = requests.put(url, json=update_data)
        logger.info(f"No token response status code: {response.status_code}")
        
        if response.status_code == 403:
            logger.info("✅ PUT /api/suppliers/{supplier_id} with no token correctly returns 403")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing PUT /api/suppliers/{supplier_id} with no token: {str(e)}")
    
    # Test DELETE /api/suppliers/{supplier_id}
    url = f"{API_URL}/suppliers/{supplier_id}"
    logger.info(f"Testing DELETE {url}")
    
    # Test with invalid token
    try:
        response = requests.delete(url, headers=headers_invalid)
        logger.info(f"Invalid token response status code: {response.status_code}")
        
        if response.status_code == 401:
            logger.info("✅ DELETE /api/suppliers/{supplier_id} with invalid token correctly returns 401")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing DELETE /api/suppliers/{supplier_id} with invalid token: {str(e)}")
    
    # Test with no token
    try:
        response = requests.delete(url)
        logger.info(f"No token response status code: {response.status_code}")
        
        if response.status_code == 403:
            logger.info("✅ DELETE /api/suppliers/{supplier_id} with no token correctly returns 403")
        else:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing DELETE /api/suppliers/{supplier_id} with no token: {str(e)}")

if __name__ == "__main__":
    run_supplier_tests()