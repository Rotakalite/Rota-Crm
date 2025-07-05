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
BACKEND_URL = "https://be473f49-c085-4355-8cf7-95fc4e8bf06a.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

# Test JWT tokens
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
INVALID_TOKEN = "invalid.token.format"

class TestSupplierManagementEndpoints(unittest.TestCase):
    """Test class for supplier management endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = API_URL
        logger.info(f"Using API URL: {self.api_url}")
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
        
        # Test data for supplier creation
        self.test_supplier_data = {
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
    
    def test_supplier_categories_list(self):
        """Test GET /api/suppliers/categories/list endpoint"""
        logger.info("\n=== Testing GET /api/suppliers/categories/list endpoint ===")
        
        url = f"{self.api_url}/suppliers/categories/list"
        
        # Test without authentication (should work)
        try:
            response = requests.get(url)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain categories
            data = response.json()
            self.assertIn("categories", data)
            self.assertIsInstance(data["categories"], list)
            self.assertTrue(len(data["categories"]) > 0)
            
            # Log the categories found
            logger.info(f"Found {len(data['categories'])} supplier categories")
            logger.info(f"Categories: {data['categories']}")
            
            logger.info("✅ GET /api/suppliers/categories/list test passed")
        except Exception as e:
            logger.error(f"❌ Error testing supplier categories endpoint: {str(e)}")
            raise
    
    def test_supplier_certifications_list(self):
        """Test GET /api/suppliers/certifications/list endpoint"""
        logger.info("\n=== Testing GET /api/suppliers/certifications/list endpoint ===")
        
        url = f"{self.api_url}/suppliers/certifications/list"
        
        # Test without authentication (should work)
        try:
            response = requests.get(url)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain certifications
            data = response.json()
            self.assertIn("certifications", data)
            self.assertIsInstance(data["certifications"], list)
            self.assertTrue(len(data["certifications"]) > 0)
            
            # Log the certifications found
            logger.info(f"Found {len(data['certifications'])} supplier certifications")
            logger.info(f"Certifications: {data['certifications']}")
            
            logger.info("✅ GET /api/suppliers/certifications/list test passed")
        except Exception as e:
            logger.error(f"❌ Error testing supplier certifications endpoint: {str(e)}")
            raise
    
    def test_authenticated_endpoints(self):
        """Test authenticated supplier endpoints"""
        logger.info("\n=== Testing authenticated supplier endpoints ===")
        
        # Test endpoints
        endpoints = [
            {"method": "POST", "url": f"{self.api_url}/suppliers", "data": self.test_supplier_data},
            {"method": "GET", "url": f"{self.api_url}/suppliers"},
            {"method": "GET", "url": f"{self.api_url}/suppliers/analytics/dashboard"}
        ]
        
        for endpoint in endpoints:
            method = endpoint["method"]
            url = endpoint["url"]
            data = endpoint.get("data")
            
            logger.info(f"\nTesting {method} {url}")
            
            # Test with invalid token
            try:
                if method == "GET":
                    response = requests.get(url, headers=self.headers_invalid)
                else:  # POST
                    response = requests.post(url, headers=self.headers_invalid, json=data)
                
                logger.info(f"Invalid token response status code: {response.status_code}")
                
                # Should get 401 Unauthorized
                self.assertEqual(response.status_code, 401)
                logger.info(f"✅ {method} {url} with invalid token correctly returns 401")
            except Exception as e:
                logger.error(f"❌ Error testing {method} {url} with invalid token: {str(e)}")
                raise
            
            # Test with no token
            try:
                if method == "GET":
                    response = requests.get(url)
                else:  # POST
                    response = requests.post(url, json=data)
                
                logger.info(f"No token response status code: {response.status_code}")
                
                # Should get 403 Forbidden
                self.assertEqual(response.status_code, 403)
                logger.info(f"✅ {method} {url} with no token correctly returns 403")
            except Exception as e:
                logger.error(f"❌ Error testing {method} {url} with no token: {str(e)}")
                raise

if __name__ == "__main__":
    unittest.main()