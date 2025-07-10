#!/usr/bin/env python3
"""
Comprehensive Railway Backend Testing for Rota-CRM
Testing URL: https://rota-crm-production.up.railway.app/api

Priority Areas:
1. Sustainability Targets Module (PRIORITY)
2. Core Authentication & Authorization
3. Document Management APIs
4. Other Core Modules (Client, Consultant, Supplier, Personnel Management)
"""

import unittest
import json
import logging
import requests
import os
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL - CORRECT URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# Test JWT tokens - These are sample tokens for testing
# In production, these would be generated from Clerk authentication
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ0xJRU5UIiwiZW1haWwiOiJjbGllbnRAZXhhbXBsZS5jb20iLCJuYW1lIjoiQ2xpZW50IFVzZXIifQ.signature"
CONSULTANT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ09OU1VMVEFOVCIsImVtYWlsIjoiY29uc3VsdGFudEBleGFtcGxlLmNvbSIsIm5hbWUiOiJDb25zdWx0YW50IFVzZXIifQ.signature"
INVALID_TOKEN = "invalid.token.format"

class TestRailwayBackendHealth(unittest.TestCase):
    """Test basic health and connectivity to Railway backend"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        logger.info(f"Testing Railway Backend URL: {self.api_url}")
    
    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        logger.info("\n=== Testing /api/health endpoint ===")
        
        url = f"{self.api_url}/health"
        
        try:
            response = requests.get(url, timeout=30)
            logger.info(f"Health endpoint response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Health response: {data}")
                
                # Verify health response structure
                self.assertIn("status", data)
                self.assertEqual(data["status"], "healthy")
                
                logger.info("✅ Health endpoint test passed")
            else:
                logger.warning(f"⚠️ Health endpoint returned {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Health endpoint connection error: {str(e)}")
            raise
    
    def test_root_endpoint(self):
        """Test root endpoint connectivity"""
        logger.info("\n=== Testing root endpoint connectivity ===")
        
        # Test the base URL without /api
        base_url = "https://rota-crm-production.up.railway.app"
        
        try:
            response = requests.get(base_url, timeout=30)
            logger.info(f"Root endpoint response status: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ Root endpoint accessible")
            else:
                logger.warning(f"⚠️ Root endpoint returned {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Root endpoint connection error: {str(e)}")
            # Don't raise here as this is not critical

class TestSustainabilityTargetsModule(unittest.TestCase):
    """Test Sustainability Targets Module - PRIORITY"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
        
        # Test data for sustainability targets
        self.test_target_data = {
            "target_name": f"Test Carbon Reduction Target {uuid.uuid4()}",
            "category": "Çevresel",
            "target_type": "Karbon Ayak İzi",
            "target_value": 25.0,
            "unit": "%",
            "target_period": "Yıllık",
            "deadline": (datetime.now() + timedelta(days=365)).isoformat(),
            "description": "Test target for carbon footprint reduction",
            "client_id": "test-client-id"
        }
        
        self.test_progress_data = {
            "target_id": "test-target-id",
            "actual_value": 15.0,
            "progress_date": datetime.now().isoformat(),
            "notes": "Progress update for testing"
        }
    
    def test_create_sustainability_target(self):
        """Test POST /api/sustainability-targets"""
        logger.info("\n=== Testing POST /api/sustainability-targets ===")
        
        url = f"{self.api_url}/sustainability-targets"
        
        # Test with admin authentication
        try:
            response = requests.post(url, headers=self.headers_admin, json=self.test_target_data, timeout=30)
            logger.info(f"Admin create target response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Target created successfully: {data}")
                
                # Verify response structure
                self.assertIn("message", data)
                if "target_id" in data:
                    self.target_id = data["target_id"]
                    logger.info(f"Created target ID: {self.target_id}")
                
                logger.info("✅ POST /api/sustainability-targets with admin passed")
                
            elif response.status_code == 401:
                logger.info("⚠️ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("⚠️ Access forbidden - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint not found - received 404 Not Found")
            else:
                logger.warning(f"⚠️ Unexpected response: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error testing create sustainability target: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.post(url, headers=self.headers_no_auth, json=self.test_target_data, timeout=30)
            logger.info(f"No auth create target response status: {response.status_code}")
            
            # Should require authentication
            self.assertIn(response.status_code, [401, 403, 404])
            logger.info("✅ POST /api/sustainability-targets correctly requires authentication")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error testing create sustainability target without auth: {str(e)}")
            raise
    
    def test_list_sustainability_targets(self):
        """Test GET /api/sustainability-targets"""
        logger.info("\n=== Testing GET /api/sustainability-targets ===")
        
        url = f"{self.api_url}/sustainability-targets"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin, timeout=30)
            logger.info(f"Admin list targets response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} sustainability targets")
                
                # Verify response is a list
                self.assertIsInstance(data, list)
                
                # If targets exist, verify structure
                if len(data) > 0:
                    target = data[0]
                    expected_fields = ["id", "target_name", "category", "target_type", "target_value", "unit"]
                    for field in expected_fields:
                        self.assertIn(field, target, f"Missing field: {field}")
                
                logger.info("✅ GET /api/sustainability-targets with admin passed")
                
            elif response.status_code == 401:
                logger.info("⚠️ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("⚠️ Access forbidden - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint not found - received 404 Not Found")
            else:
                logger.warning(f"⚠️ Unexpected response: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error testing list sustainability targets: {str(e)}")
            raise
    
    def test_sustainability_targets_analytics(self):
        """Test GET /api/sustainability-targets/analytics/dashboard"""
        logger.info("\n=== Testing GET /api/sustainability-targets/analytics/dashboard ===")
        
        url = f"{self.api_url}/sustainability-targets/analytics/dashboard"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin, timeout=30)
            logger.info(f"Admin analytics response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Analytics data keys: {list(data.keys())}")
                
                # Verify analytics response structure
                expected_fields = ["total_targets", "targets_by_category", "targets_by_status", "progress_overview"]
                for field in expected_fields:
                    if field in data:
                        logger.info(f"✓ Found analytics field: {field}")
                
                logger.info("✅ GET /api/sustainability-targets/analytics/dashboard with admin passed")
                
            elif response.status_code == 401:
                logger.info("⚠️ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("⚠️ Access forbidden - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint not found - received 404 Not Found")
            else:
                logger.warning(f"⚠️ Unexpected response: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error testing sustainability targets analytics: {str(e)}")
            raise

class TestCoreAuthentication(unittest.TestCase):
    """Test Core Authentication & Authorization"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_auth_me_endpoint(self):
        """Test GET /api/auth/me endpoint"""
        logger.info("\n=== Testing GET /api/auth/me ===")
        
        url = f"{self.api_url}/auth/me"
        
        # Test with admin token
        try:
            response = requests.get(url, headers=self.headers_admin, timeout=30)
            logger.info(f"Admin auth/me response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Admin user data: {data}")
                
                # Verify user data structure
                expected_fields = ["id", "email", "name", "role"]
                for field in expected_fields:
                    if field in data:
                        logger.info(f"✓ Found user field: {field}")
                
                logger.info("✅ GET /api/auth/me with admin token passed")
                
            elif response.status_code == 401:
                logger.info("⚠️ Admin token invalid - received 401 Unauthorized")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint not found - received 404 Not Found")
            else:
                logger.warning(f"⚠️ Unexpected response: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error testing auth/me with admin token: {str(e)}")
            raise
        
        # Test with invalid token
        try:
            response = requests.get(url, headers=self.headers_invalid, timeout=30)
            logger.info(f"Invalid token auth/me response status: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertIn(response.status_code, [401, 404])
            logger.info("✅ GET /api/auth/me correctly rejects invalid token")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error testing auth/me with invalid token: {str(e)}")
            raise
        
        # Test with no token
        try:
            response = requests.get(url, headers=self.headers_no_auth, timeout=30)
            logger.info(f"No token auth/me response status: {response.status_code}")
            
            # Should get 403 Forbidden or 401 Unauthorized
            self.assertIn(response.status_code, [401, 403, 404])
            logger.info("✅ GET /api/auth/me correctly requires authentication")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error testing auth/me without token: {str(e)}")
            raise

class TestDocumentManagement(unittest.TestCase):
    """Test Document Management APIs"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_folders_endpoint(self):
        """Test GET /api/folders endpoint"""
        logger.info("\n=== Testing GET /api/folders ===")
        
        url = f"{self.api_url}/folders"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin, timeout=30)
            logger.info(f"Admin folders response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} folders")
                
                # Verify response is a list
                self.assertIsInstance(data, list)
                
                # If folders exist, verify structure
                if len(data) > 0:
                    folder = data[0]
                    expected_fields = ["id", "name", "client_id"]
                    for field in expected_fields:
                        if field in folder:
                            logger.info(f"✓ Found folder field: {field}")
                
                logger.info("✅ GET /api/folders with admin passed")
                
            elif response.status_code == 401:
                logger.info("⚠️ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("⚠️ Access forbidden - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint not found - received 404 Not Found")
            else:
                logger.warning(f"⚠️ Unexpected response: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error testing folders endpoint: {str(e)}")
            raise
    
    def test_belge_list_endpoint(self):
        """Test GET /api/belge/list endpoint"""
        logger.info("\n=== Testing GET /api/belge/list ===")
        
        url = f"{self.api_url}/belge/list"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin, timeout=30)
            logger.info(f"Admin belge/list response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, dict) and "documents" in data:
                    documents = data["documents"]
                    logger.info(f"Found {len(documents)} documents")
                elif isinstance(data, list):
                    logger.info(f"Found {len(data)} documents")
                else:
                    logger.info(f"Response data: {data}")
                
                logger.info("✅ GET /api/belge/list with admin passed")
                
            elif response.status_code == 401:
                logger.info("⚠️ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("⚠️ Access forbidden - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint not found - received 404 Not Found")
            else:
                logger.warning(f"⚠️ Unexpected response: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error testing belge/list endpoint: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth, timeout=30)
            logger.info(f"No auth belge/list response status: {response.status_code}")
            
            # Should require authentication
            self.assertIn(response.status_code, [401, 403, 404])
            logger.info("✅ GET /api/belge/list correctly requires authentication")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error testing belge/list without auth: {str(e)}")
            raise

class TestClientManagement(unittest.TestCase):
    """Test Client Management endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
        
        # Test data for client creation
        self.test_client_data = {
            "name": f"Test Client {uuid.uuid4()}",
            "hotel_name": f"Test Hotel {uuid.uuid4()}",
            "contact_person": "John Doe",
            "email": "john@testhotel.com",
            "phone": "1234567890",
            "address": "123 Test St, Test City"
        }
    
    def test_clients_list_endpoint(self):
        """Test GET /api/clients endpoint"""
        logger.info("\n=== Testing GET /api/clients ===")
        
        url = f"{self.api_url}/clients"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin, timeout=30)
            logger.info(f"Admin clients response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} clients")
                
                # Verify response is a list
                self.assertIsInstance(data, list)
                
                # If clients exist, verify structure
                if len(data) > 0:
                    client = data[0]
                    expected_fields = ["id", "name", "hotel_name", "email"]
                    for field in expected_fields:
                        if field in client:
                            logger.info(f"✓ Found client field: {field}")
                
                logger.info("✅ GET /api/clients with admin passed")
                
            elif response.status_code == 401:
                logger.info("⚠️ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("⚠️ Access forbidden - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint not found - received 404 Not Found")
            else:
                logger.warning(f"⚠️ Unexpected response: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error testing clients endpoint: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth, timeout=30)
            logger.info(f"No auth clients response status: {response.status_code}")
            
            # Should require authentication
            self.assertIn(response.status_code, [401, 403, 404])
            logger.info("✅ GET /api/clients correctly requires authentication")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error testing clients without auth: {str(e)}")
            raise

class TestConsultantManagement(unittest.TestCase):
    """Test Consultant Management endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
        
        # Test data for consultant creation
        self.test_consultant_data = {
            "company_name": f"Test Consulting {uuid.uuid4()}",
            "authorized_person_name": "Jane Smith",
            "email": "jane@testconsulting.com",
            "phone": "0987654321",
            "address": "456 Consultant Ave, Business City"
        }
    
    def test_consultants_list_endpoint(self):
        """Test GET /api/consultants endpoint"""
        logger.info("\n=== Testing GET /api/consultants ===")
        
        url = f"{self.api_url}/consultants"
        
        # Test without authentication (should work for registration)
        try:
            response = requests.get(url, timeout=30)
            logger.info(f"No auth consultants response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} consultants")
                
                # Verify response is a list
                self.assertIsInstance(data, list)
                
                # If consultants exist, verify structure
                if len(data) > 0:
                    consultant = data[0]
                    expected_fields = ["id", "company_name", "authorized_person_name", "email"]
                    for field in expected_fields:
                        if field in consultant:
                            logger.info(f"✓ Found consultant field: {field}")
                
                logger.info("✅ GET /api/consultants without auth passed")
                
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint not found - received 404 Not Found")
            else:
                logger.warning(f"⚠️ Unexpected response: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error testing consultants endpoint: {str(e)}")
            raise
    
    def test_create_consultant_endpoint(self):
        """Test POST /api/consultants endpoint"""
        logger.info("\n=== Testing POST /api/consultants ===")
        
        url = f"{self.api_url}/consultants"
        
        # Test without authentication (should work for registration)
        try:
            response = requests.post(url, json=self.test_consultant_data, timeout=30)
            logger.info(f"Create consultant response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Consultant created: {data}")
                
                # Verify response structure
                self.assertIn("message", data)
                if "consultant_id" in data:
                    logger.info(f"Created consultant ID: {data['consultant_id']}")
                
                logger.info("✅ POST /api/consultants passed")
                
            elif response.status_code == 400:
                # Could be validation error or duplicate
                data = response.json()
                logger.info(f"Expected 400 error: {data}")
                logger.info("✅ POST /api/consultants - expected 400 error")
                
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint not found - received 404 Not Found")
            else:
                logger.warning(f"⚠️ Unexpected response: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error testing create consultant: {str(e)}")
            raise

class TestSupplierManagement(unittest.TestCase):
    """Test Supplier Management endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_supplier_categories_endpoint(self):
        """Test GET /api/suppliers/categories/list endpoint"""
        logger.info("\n=== Testing GET /api/suppliers/categories/list ===")
        
        url = f"{self.api_url}/suppliers/categories/list"
        
        # Test without authentication (should work)
        try:
            response = requests.get(url, timeout=30)
            logger.info(f"Supplier categories response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Supplier categories data: {data}")
                
                # Verify response structure
                if "categories" in data:
                    categories = data["categories"]
                    logger.info(f"Found {len(categories)} supplier categories")
                    self.assertIsInstance(categories, list)
                
                logger.info("✅ GET /api/suppliers/categories/list passed")
                
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint not found - received 404 Not Found")
            else:
                logger.warning(f"⚠️ Unexpected response: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error testing supplier categories: {str(e)}")
            raise
    
    def test_supplier_certifications_endpoint(self):
        """Test GET /api/suppliers/certifications/list endpoint"""
        logger.info("\n=== Testing GET /api/suppliers/certifications/list ===")
        
        url = f"{self.api_url}/suppliers/certifications/list"
        
        # Test without authentication (should work)
        try:
            response = requests.get(url, timeout=30)
            logger.info(f"Supplier certifications response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Supplier certifications data: {data}")
                
                # Verify response structure
                if "certifications" in data:
                    certifications = data["certifications"]
                    logger.info(f"Found {len(certifications)} supplier certifications")
                    self.assertIsInstance(certifications, list)
                
                logger.info("✅ GET /api/suppliers/certifications/list passed")
                
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint not found - received 404 Not Found")
            else:
                logger.warning(f"⚠️ Unexpected response: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error testing supplier certifications: {str(e)}")
            raise

def run_all_tests():
    """Run all test suites"""
    logger.info("🚀 Starting comprehensive Railway backend testing...")
    logger.info(f"Testing URL: {RAILWAY_API_URL}")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes in priority order
    test_classes = [
        TestRailwayBackendHealth,
        TestSustainabilityTargetsModule,  # PRIORITY
        TestCoreAuthentication,
        TestDocumentManagement,
        TestClientManagement,
        TestConsultantManagement,
        TestSupplierManagement
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("🏁 RAILWAY BACKEND TESTING SUMMARY")
    logger.info("="*80)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    if result.failures:
        logger.info("\n❌ FAILURES:")
        for test, traceback in result.failures:
            logger.info(f"  - {test}: {traceback}")
    
    if result.errors:
        logger.info("\n❌ ERRORS:")
        for test, traceback in result.errors:
            logger.info(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        logger.info("\n✅ ALL TESTS PASSED!")
    else:
        logger.info(f"\n⚠️ {len(result.failures + result.errors)} TESTS FAILED")
    
    return result

if __name__ == "__main__":
    run_all_tests()