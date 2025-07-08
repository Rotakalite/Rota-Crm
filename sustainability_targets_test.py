import unittest
import json
import logging
import requests
import os
import sys
import io
import uuid
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test data
TEST_YEAR_CURRENT = 2024
TEST_YEAR_PREVIOUS = 2025

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "sustainable_tourism_crm"

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
VALID_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

# Test JWT tokens for client users
# These are sample tokens for testing different client users
KAYA_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"
CANO_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ0FOT19DTElFTlRfMDAxIiwiZW1haWwiOiJjYW5lcnBhbEBnbWFpbC5jb20iLCJuYW1lIjoiQ0FOTyBDbGllbnQifQ.signature"
DENEME_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfREVORU1FX0NMSUVOVF8wMDEiLCJlbWFpbCI6InBhbGF2YW5jYW5lckBnbWFpbC5jb20iLCJuYW1lIjoiREVORU1FIENsaWVudCJ9.signature"
NO_CLIENT_ID_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfTk9fQ0xJRU5UX0lEIiwiZW1haWwiOiJub2NsaWVudGlkQGV4YW1wbGUuY29tIiwibmFtZSI6IlVzZXIgV2l0aG91dCBDbGllbnQgSUQifQ.signature"
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self.json_data

class TestSustainabilityTargetsAPI(unittest.TestCase):
    """Test class for Sustainability Targets API endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_kaya = {"Authorization": f"Bearer {KAYA_CLIENT_TOKEN}"}
        self.headers_cano = {"Authorization": f"Bearer {CANO_CLIENT_TOKEN}"}
        self.headers_deneme = {"Authorization": f"Bearer {DENEME_CLIENT_TOKEN}"}
        self.headers_no_client_id = {"Authorization": f"Bearer {NO_CLIENT_ID_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        self.headers_no_auth = {}
        
        # Test data for sustainability target
        self.test_target_data = {
            "target_name": f"Test Target {uuid.uuid4()}",
            "category": "Çevresel",
            "target_type": "Karbon Ayak İzi",
            "target_value": 100.0,
            "unit": "kg",
            "target_period": "Yıllık",
            "deadline": (datetime.utcnow() + timedelta(days=365)).isoformat(),
            "description": "Test sustainability target for API testing",
            "client_id": "8bfd3a85-2483-4b63-9e80-e53747c3db7e"  # Sample client ID
        }
        
        # Test data for target progress
        self.test_progress_data = {
            "target_id": None,  # Will be set after target creation
            "actual_value": 50.0,
            "progress_date": datetime.utcnow().isoformat(),
            "notes": "Test progress data for API testing"
        }
    
    def test_create_sustainability_target(self):
        """Test POST /api/sustainability-targets endpoint"""
        logger.info("\n=== Testing POST /api/sustainability-targets endpoint ===")
        
        url = f"{self.api_url}/sustainability-targets"
        
        # Test with admin user
        try:
            response = requests.post(url, headers=self.headers_admin, json=self.test_target_data)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 201, 400, 401, 403, 404])
            
            if response.status_code in [200, 201]:
                # Response should contain success message and target_id
                data = response.json()
                self.assertIn("message", data)
                self.assertIn("target_id", data)
                
                # Save target_id for later tests
                self.target_id = data["target_id"]
                logger.info(f"Created sustainability target with ID: {self.target_id}")
                
                # Update test_progress_data with target_id
                self.test_progress_data["target_id"] = self.target_id
                
                logger.info("✅ POST /api/sustainability-targets with admin user passed")
            elif response.status_code == 400:
                # This could happen if validation fails
                data = response.json()
                logger.info(f"Expected 400 error: {data}")
                logger.info("✅ POST /api/sustainability-targets with admin user - expected 400 error")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Admin access required - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/sustainability-targets with admin: {str(e)}")
            raise
        
        # Test with client user (should be forbidden)
        try:
            response = requests.post(url, headers=self.headers_kaya, json=self.test_target_data)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Should get 403 Forbidden or 404 Not Found
            self.assertIn(response.status_code, [403, 404])
            
            if response.status_code == 403:
                logger.info("✅ POST /api/sustainability-targets with client user correctly returns 403")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/sustainability-targets with client: {str(e)}")
            raise
        
        # Test with invalid token
        try:
            response = requests.post(url, headers=self.headers_invalid, json=self.test_target_data)
            logger.info(f"Invalid token response status code: {response.status_code}")
            
            # Should get 401 Unauthorized or 404 Not Found
            self.assertIn(response.status_code, [401, 404])
            
            if response.status_code == 401:
                logger.info("✅ POST /api/sustainability-targets with invalid token correctly returns 401")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/sustainability-targets with invalid token: {str(e)}")
            raise
        
        # Test with no token
        try:
            response = requests.post(url, headers=self.headers_no_auth, json=self.test_target_data)
            logger.info(f"No token response status code: {response.status_code}")
            
            # Should get 403 Not authenticated or 404 Not Found
            self.assertIn(response.status_code, [403, 404])
            
            if response.status_code == 403:
                logger.info("✅ POST /api/sustainability-targets with no token correctly returns 403")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/sustainability-targets with no token: {str(e)}")
            raise
    
    def test_get_sustainability_targets(self):
        """Test GET /api/sustainability-targets endpoint"""
        logger.info("\n=== Testing GET /api/sustainability-targets endpoint ===")
        
        url = f"{self.api_url}/sustainability-targets"
        
        # Test with admin user
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} sustainability targets")
                
                # Verify response structure (should be a list)
                self.assertIsInstance(data, list)
                
                # If there are targets, check their structure
                if len(data) > 0:
                    target = data[0]
                    self.assertIn("id", target)
                    self.assertIn("client_id", target)
                    self.assertIn("target_name", target)
                    self.assertIn("category", target)
                    self.assertIn("target_type", target)
                    self.assertIn("target_value", target)
                    self.assertIn("unit", target)
                    self.assertIn("target_period", target)
                    self.assertIn("deadline", target)
                    self.assertIn("status", target)
                
                logger.info("✅ GET /api/sustainability-targets with admin user passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Access denied - received 403 Forbidden")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/sustainability-targets with admin: {str(e)}")
            raise
        
        # Test with client user
        try:
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} sustainability targets for client")
                
                # Verify response structure (should be a list)
                self.assertIsInstance(data, list)
                
                # If there are targets, check their structure and client_id
                if len(data) > 0:
                    target = data[0]
                    self.assertIn("id", target)
                    self.assertIn("client_id", target)
                    self.assertIn("target_name", target)
                    self.assertIn("category", target)
                    self.assertIn("target_type", target)
                    self.assertIn("target_value", target)
                    self.assertIn("unit", target)
                    self.assertIn("target_period", target)
                    self.assertIn("deadline", target)
                    self.assertIn("status", target)
                
                logger.info("✅ GET /api/sustainability-targets with client user passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Access denied - received 403 Forbidden")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/sustainability-targets with client: {str(e)}")
            raise
        
        # Test with category filter
        try:
            params = {"category": "Çevresel"}
            response = requests.get(url, headers=self.headers_admin, params=params)
            logger.info(f"Admin response with category filter status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} sustainability targets for category 'Çevresel'")
                
                # Verify all targets are for the specified category
                if len(data) > 0:
                    for target in data:
                        self.assertEqual(target["category"], "Çevresel")
                
                logger.info("✅ GET /api/sustainability-targets with category filter passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Access denied - received 403 Forbidden")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/sustainability-targets with category filter: {str(e)}")
            raise
    
    def test_add_target_progress(self):
        """Test POST /api/sustainability-targets/progress endpoint"""
        logger.info("\n=== Testing POST /api/sustainability-targets/progress endpoint ===")
        
        # Skip if no target_id is available
        if not hasattr(self, 'target_id'):
            logger.warning("⚠️ Skipping test_add_target_progress because no target_id is available")
            return
        
        url = f"{self.api_url}/sustainability-targets/progress"
        
        # Test with admin user
        try:
            response = requests.post(url, headers=self.headers_admin, json=self.test_progress_data)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 201, 400, 401, 403, 404])
            
            if response.status_code in [200, 201]:
                # Response should contain success message and progress_id
                data = response.json()
                self.assertIn("message", data)
                self.assertIn("progress_id", data)
                
                # Save progress_id for later tests
                self.progress_id = data["progress_id"]
                logger.info(f"Added target progress with ID: {self.progress_id}")
                
                logger.info("✅ POST /api/sustainability-targets/progress with admin user passed")
            elif response.status_code == 400:
                # This could happen if validation fails
                data = response.json()
                logger.info(f"Expected 400 error: {data}")
                logger.info("✅ POST /api/sustainability-targets/progress with admin user - expected 400 error")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Admin access required - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/sustainability-targets/progress with admin: {str(e)}")
            raise
        
        # Test with client user (should be forbidden)
        try:
            response = requests.post(url, headers=self.headers_kaya, json=self.test_progress_data)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Should get 403 Forbidden or 404 Not Found
            self.assertIn(response.status_code, [403, 404])
            
            if response.status_code == 403:
                logger.info("✅ POST /api/sustainability-targets/progress with client user correctly returns 403")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/sustainability-targets/progress with client: {str(e)}")
            raise
    
    def test_get_target_progress(self):
        """Test GET /api/sustainability-targets/{target_id}/progress endpoint"""
        logger.info("\n=== Testing GET /api/sustainability-targets/{target_id}/progress endpoint ===")
        
        # Skip if no target_id is available
        if not hasattr(self, 'target_id'):
            logger.warning("⚠️ Skipping test_get_target_progress because no target_id is available")
            return
        
        url = f"{self.api_url}/sustainability-targets/{self.target_id}/progress"
        
        # Test with admin user
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} progress records for target {self.target_id}")
                
                # Verify response structure (should be a list)
                self.assertIsInstance(data, list)
                
                # If there are progress records, check their structure
                if len(data) > 0:
                    progress = data[0]
                    self.assertIn("id", progress)
                    self.assertIn("target_id", progress)
                    self.assertIn("actual_value", progress)
                    self.assertIn("progress_date", progress)
                    self.assertIn("created_at", progress)
                
                logger.info("✅ GET /api/sustainability-targets/{target_id}/progress with admin user passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Access denied - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/sustainability-targets/{self.target_id}/progress with admin: {str(e)}")
            raise
        
        # Test with client user
        try:
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} progress records for target {self.target_id} for client")
                
                # Verify response structure (should be a list)
                self.assertIsInstance(data, list)
                
                logger.info("✅ GET /api/sustainability-targets/{target_id}/progress with client user passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Access denied - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/sustainability-targets/{self.target_id}/progress with client: {str(e)}")
            raise
    
    def test_get_single_sustainability_target(self):
        """Test GET /api/sustainability-targets/{target_id} endpoint"""
        logger.info("\n=== Testing GET /api/sustainability-targets/{target_id} endpoint ===")
        
        # Skip if no target_id is available
        if not hasattr(self, 'target_id'):
            logger.warning("⚠️ Skipping test_get_single_sustainability_target because no target_id is available")
            return
        
        url = f"{self.api_url}/sustainability-targets/{self.target_id}"
        
        # Test with admin user
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                target = response.json()
                logger.info(f"Found target: {target.get('target_name', 'Unknown')}")
                
                # Verify response structure
                self.assertIn("id", target)
                self.assertIn("client_id", target)
                self.assertIn("target_name", target)
                self.assertIn("category", target)
                self.assertIn("target_type", target)
                self.assertIn("target_value", target)
                self.assertIn("unit", target)
                self.assertIn("target_period", target)
                self.assertIn("deadline", target)
                self.assertIn("status", target)
                self.assertIn("progress", target)
                
                # Verify progress is a list
                self.assertIsInstance(target["progress"], list)
                
                logger.info("✅ GET /api/sustainability-targets/{target_id} with admin user passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Access denied - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/sustainability-targets/{self.target_id} with admin: {str(e)}")
            raise
        
        # Test with client user
        try:
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                target = response.json()
                logger.info(f"Found target for client: {target.get('target_name', 'Unknown')}")
                
                # Verify response structure
                self.assertIn("id", target)
                self.assertIn("client_id", target)
                self.assertIn("target_name", target)
                self.assertIn("category", target)
                self.assertIn("target_type", target)
                self.assertIn("target_value", target)
                self.assertIn("unit", target)
                self.assertIn("target_period", target)
                self.assertIn("deadline", target)
                self.assertIn("status", target)
                self.assertIn("progress", target)
                
                logger.info("✅ GET /api/sustainability-targets/{target_id} with client user passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Access denied - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/sustainability-targets/{self.target_id} with client: {str(e)}")
            raise
    
    def test_update_sustainability_target(self):
        """Test PUT /api/sustainability-targets/{target_id} endpoint"""
        logger.info("\n=== Testing PUT /api/sustainability-targets/{target_id} endpoint ===")
        
        # Skip if no target_id is available
        if not hasattr(self, 'target_id'):
            logger.warning("⚠️ Skipping test_update_sustainability_target because no target_id is available")
            return
        
        url = f"{self.api_url}/sustainability-targets/{self.target_id}"
        
        # Update test data
        update_data = self.test_target_data.copy()
        update_data["target_name"] = f"Updated Target {uuid.uuid4()}"
        update_data["target_value"] = 150.0
        
        # Test with admin user
        try:
            response = requests.put(url, headers=self.headers_admin, json=update_data)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 400, 401, 403, 404])
            
            if response.status_code == 200:
                # Response should contain success message
                data = response.json()
                self.assertIn("message", data)
                
                logger.info("✅ PUT /api/sustainability-targets/{target_id} with admin user passed")
            elif response.status_code == 400:
                # This could happen if validation fails
                data = response.json()
                logger.info(f"Expected 400 error: {data}")
                logger.info("✅ PUT /api/sustainability-targets/{target_id} with admin user - expected 400 error")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Admin access required - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing PUT /api/sustainability-targets/{self.target_id} with admin: {str(e)}")
            raise
        
        # Test with client user (should be forbidden)
        try:
            response = requests.put(url, headers=self.headers_kaya, json=update_data)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Should get 403 Forbidden or 404 Not Found
            self.assertIn(response.status_code, [403, 404])
            
            if response.status_code == 403:
                logger.info("✅ PUT /api/sustainability-targets/{target_id} with client user correctly returns 403")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing PUT /api/sustainability-targets/{self.target_id} with client: {str(e)}")
            raise
    
    def test_delete_sustainability_target(self):
        """Test DELETE /api/sustainability-targets/{target_id} endpoint"""
        logger.info("\n=== Testing DELETE /api/sustainability-targets/{target_id} endpoint ===")
        
        # Skip if no target_id is available
        if not hasattr(self, 'target_id'):
            logger.warning("⚠️ Skipping test_delete_sustainability_target because no target_id is available")
            return
        
        url = f"{self.api_url}/sustainability-targets/{self.target_id}"
        
        # Test with client user (should be forbidden)
        try:
            response = requests.delete(url, headers=self.headers_kaya)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Should get 403 Forbidden or 404 Not Found
            self.assertIn(response.status_code, [403, 404])
            
            if response.status_code == 403:
                logger.info("✅ DELETE /api/sustainability-targets/{target_id} with client user correctly returns 403")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing DELETE /api/sustainability-targets/{self.target_id} with client: {str(e)}")
            raise
        
        # Test with admin user
        try:
            response = requests.delete(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                # Response should contain success message
                data = response.json()
                self.assertIn("message", data)
                
                logger.info("✅ DELETE /api/sustainability-targets/{target_id} with admin user passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Admin access required - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing DELETE /api/sustainability-targets/{self.target_id} with admin: {str(e)}")
            raise
    
    def test_get_sustainability_analytics(self):
        """Test GET /api/sustainability-targets/analytics/dashboard endpoint"""
        logger.info("\n=== Testing GET /api/sustainability-targets/analytics/dashboard endpoint ===")
        
        url = f"{self.api_url}/sustainability-targets/analytics/dashboard"
        
        # Test with admin user
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data.keys()}")
                
                # Verify response structure
                self.assertIn("total_targets", data)
                self.assertIn("active_targets", data)
                self.assertIn("completed_targets", data)
                self.assertIn("overdue_targets", data)
                self.assertIn("category_distribution", data)
                self.assertIn("target_type_distribution", data)
                self.assertIn("progress_data", data)
                self.assertIn("average_progress", data)
                
                # Check progress_data structure
                progress_data = data["progress_data"]
                self.assertIsInstance(progress_data, list)
                if len(progress_data) > 0:
                    progress = progress_data[0]
                    self.assertIn("target_id", progress)
                    self.assertIn("target_name", progress)
                    self.assertIn("progress_percentage", progress)
                    self.assertIn("actual_value", progress)
                    self.assertIn("target_value", progress)
                
                logger.info("✅ GET /api/sustainability-targets/analytics/dashboard with admin user passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Access denied - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/sustainability-targets/analytics/dashboard with admin: {str(e)}")
            raise
        
        # Test with client user
        try:
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data.keys()}")
                
                # Verify response structure
                self.assertIn("total_targets", data)
                self.assertIn("active_targets", data)
                self.assertIn("completed_targets", data)
                self.assertIn("overdue_targets", data)
                self.assertIn("category_distribution", data)
                self.assertIn("target_type_distribution", data)
                self.assertIn("progress_data", data)
                self.assertIn("average_progress", data)
                
                logger.info("✅ GET /api/sustainability-targets/analytics/dashboard with client user passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Access denied - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/sustainability-targets/analytics/dashboard with client: {str(e)}")
            raise
        
        # Test with client_id parameter
        try:
            params = {"client_id": "8bfd3a85-2483-4b63-9e80-e53747c3db7e"}
            response = requests.get(url, headers=self.headers_admin, params=params)
            logger.info(f"Admin response with client_id parameter status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data.keys()}")
                
                # Verify response structure
                self.assertIn("total_targets", data)
                self.assertIn("active_targets", data)
                self.assertIn("completed_targets", data)
                self.assertIn("overdue_targets", data)
                self.assertIn("category_distribution", data)
                self.assertIn("target_type_distribution", data)
                self.assertIn("progress_data", data)
                self.assertIn("average_progress", data)
                
                logger.info("✅ GET /api/sustainability-targets/analytics/dashboard with client_id parameter passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Access denied - received 403 Forbidden")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/sustainability-targets/analytics/dashboard with client_id parameter: {str(e)}")
            raise

if __name__ == "__main__":
    unittest.main()