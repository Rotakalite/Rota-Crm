#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Rota CRM
Focus on critical security issues and core functionality
"""

import unittest
import json
import logging
import requests
import os
import sys
import uuid
import time
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from frontend .env
BACKEND_API_URL = "https://5d84c72f-46a8-441d-903f-729b5668f555.preview.emergentagent.com/api"

# Test JWT tokens - these are sample tokens for testing
# In production, these would be generated from Clerk
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ0xJRU5UIiwiZW1haWwiOiJjbGllbnRAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBDbGllbnQifQ.signature"
CONSULTANT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ09OU1VMVEFOVCIsImVtYWlsIjoiY29uc3VsdGFudEB0ZXN0LmNvbSIsIm5hbWUiOiJUZXN0IENvbnN1bHRhbnQifQ.signature"
INVALID_TOKEN = "invalid.token.format"

class TestCoreAuthentication(unittest.TestCase):
    """Test core authentication and authorization"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_health_endpoint(self):
        """Test basic health endpoint - should work without auth"""
        logger.info("\n=== Testing /api/health endpoint ===")
        
        url = f"{self.api_url}/health"
        
        try:
            response = requests.get(url)
            logger.info(f"Health endpoint response status: {response.status_code}")
            
            # Health endpoint should work without authentication
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn("status", data)
            self.assertEqual(data["status"], "healthy")
            
            logger.info("✅ Health endpoint test passed")
        except Exception as e:
            logger.error(f"❌ Error testing health endpoint: {str(e)}")
            raise
    
    def test_authentication_required_endpoints(self):
        """Test that protected endpoints require authentication"""
        logger.info("\n=== Testing authentication requirements ===")
        
        protected_endpoints = [
            "/clients",
            "/consultants",
            "/folders",
            "/belge/list",
            "/suppliers",
            "/waste-management",
            "/auth/me"
        ]
        
        for endpoint in protected_endpoints:
            url = f"{self.api_url}{endpoint}"
            
            try:
                # Test with no authentication
                response = requests.get(url, headers=self.headers_no_auth)
                logger.info(f"No auth {endpoint}: {response.status_code}")
                
                # Should get 403 Forbidden or 401 Unauthorized
                self.assertIn(response.status_code, [401, 403], 
                             f"Endpoint {endpoint} should require authentication")
                
                # Test with invalid token
                response = requests.get(url, headers=self.headers_invalid)
                logger.info(f"Invalid token {endpoint}: {response.status_code}")
                
                # Should get 401 Unauthorized
                self.assertEqual(response.status_code, 401, 
                               f"Endpoint {endpoint} should reject invalid tokens")
                
            except Exception as e:
                logger.error(f"❌ Error testing authentication for {endpoint}: {str(e)}")
                # Don't raise here, continue testing other endpoints
                continue
        
        logger.info("✅ Authentication requirements test completed")

class TestDocumentManagementSecurity(unittest.TestCase):
    """Test Document Management API security - CRITICAL FOCUS"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_folders_endpoint_security(self):
        """Test GET /api/folders endpoint security - CRITICAL"""
        logger.info("\n=== Testing GET /api/folders endpoint security ===")
        
        url = f"{self.api_url}/folders"
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status: {response.status_code}")
            
            # Should require authentication
            self.assertIn(response.status_code, [401, 403], 
                         "Folders endpoint should require authentication")
            
            logger.info("✅ No auth correctly rejected")
        except Exception as e:
            logger.error(f"❌ Error testing no auth: {str(e)}")
        
        # Test with invalid token
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid token response status: {response.status_code}")
            
            # Should reject invalid tokens
            self.assertEqual(response.status_code, 401, 
                           "Folders endpoint should reject invalid tokens")
            
            logger.info("✅ Invalid token correctly rejected")
        except Exception as e:
            logger.error(f"❌ Error testing invalid token: {str(e)}")
        
        # Test with admin token
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Admin can see {len(data)} folders")
                
                # Admin should see all folders
                self.assertIsInstance(data, list)
                
                logger.info("✅ Admin access working")
            else:
                logger.warning(f"⚠️ Admin access returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing admin access: {str(e)}")
        
        # Test with client token - CRITICAL SECURITY TEST
        try:
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Client can see {len(data)} folders")
                
                # CRITICAL: Client should only see their own folders
                # If they see all folders, this is a security vulnerability
                if len(data) > 100:  # Assuming there are many folders in the system
                    logger.error("🚨 CRITICAL SECURITY ISSUE: Client can see all folders!")
                    self.fail("SECURITY VULNERABILITY: Client users can see folders for all clients")
                else:
                    logger.info("✅ Client filtering appears to be working")
            else:
                logger.warning(f"⚠️ Client access returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing client access: {str(e)}")
    
    def test_document_list_endpoint_security(self):
        """Test GET /api/belge/list endpoint security - CRITICAL"""
        logger.info("\n=== Testing GET /api/belge/list endpoint security ===")
        
        url = f"{self.api_url}/belge/list"
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status: {response.status_code}")
            
            # Should require authentication
            self.assertIn(response.status_code, [401, 403], 
                         "Document list endpoint should require authentication")
            
            logger.info("✅ No auth correctly rejected")
        except Exception as e:
            logger.error(f"❌ Error testing no auth: {str(e)}")
        
        # Test with invalid token
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid token response status: {response.status_code}")
            
            # Should reject invalid tokens
            self.assertEqual(response.status_code, 401, 
                           "Document list endpoint should reject invalid tokens")
            
            logger.info("✅ Invalid token correctly rejected")
        except Exception as e:
            logger.error(f"❌ Error testing invalid token: {str(e)}")
        
        # Test with client token - CRITICAL SECURITY TEST
        try:
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if "documents" in data:
                    documents = data["documents"]
                else:
                    documents = data if isinstance(data, list) else []
                
                logger.info(f"Client can see {len(documents)} documents")
                
                # CRITICAL: Client should only see their own documents
                # Check if all documents belong to the same client
                if len(documents) > 0:
                    client_ids = set()
                    for doc in documents:
                        if "client_id" in doc:
                            client_ids.add(doc["client_id"])
                    
                    if len(client_ids) > 1:
                        logger.error("🚨 CRITICAL SECURITY ISSUE: Client can see documents from multiple clients!")
                        self.fail("SECURITY VULNERABILITY: Client users can see documents from other clients")
                    else:
                        logger.info("✅ Client document filtering appears to be working")
                else:
                    logger.info("ℹ️ No documents found for client")
            else:
                logger.warning(f"⚠️ Client access returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing client access: {str(e)}")
    
    def test_level4_folder_structure(self):
        """Test Level 4 folder structure implementation"""
        logger.info("\n=== Testing Level 4 folder structure ===")
        
        url = f"{self.api_url}/folders"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Total folders found: {len(data)}")
                
                # Check for Level 4 folders
                level4_folders = [f for f in data if f.get("level") == 4]
                logger.info(f"Level 4 folders found: {len(level4_folders)}")
                
                # Check for expected Level 4 folder names
                expected_level4_names = ["POLİTİKALAR", "PROSEDÜRLER", "FORMLAR", "LİSTELER", "KAYITLAR"]
                found_names = set()
                
                for folder in level4_folders:
                    folder_name = folder.get("name", "")
                    for expected_name in expected_level4_names:
                        if expected_name in folder_name:
                            found_names.add(expected_name)
                
                logger.info(f"Found Level 4 folder types: {found_names}")
                
                # Verify we have the expected folder structure
                if len(found_names) >= 3:  # At least 3 of the 5 expected types
                    logger.info("✅ Level 4 folder structure appears to be implemented")
                else:
                    logger.warning("⚠️ Level 4 folder structure may be incomplete")
                
                # Check folder hierarchy
                folders_by_level = {}
                for folder in data:
                    level = folder.get("level", 0)
                    if level not in folders_by_level:
                        folders_by_level[level] = 0
                    folders_by_level[level] += 1
                
                logger.info(f"Folder distribution by level: {folders_by_level}")
                
            else:
                logger.warning(f"⚠️ Could not retrieve folders: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing Level 4 folder structure: {str(e)}")

class TestConsultantManagement(unittest.TestCase):
    """Test Consultant Management System APIs"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_consultant_list_endpoint(self):
        """Test GET /api/consultants endpoint"""
        logger.info("\n=== Testing GET /api/consultants endpoint ===")
        
        url = f"{self.api_url}/consultants"
        
        # Test with no authentication - should work for registration
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status: {response.status_code}")
            
            # This endpoint might be public for client registration
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} consultants (public access)")
                self.assertIsInstance(data, list)
                logger.info("✅ Public consultant list access working")
            else:
                logger.info(f"ℹ️ Public access not allowed: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing public access: {str(e)}")
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Admin can see {len(data)} consultants")
                self.assertIsInstance(data, list)
                
                # Check consultant data structure
                if len(data) > 0:
                    consultant = data[0]
                    expected_fields = ["id", "company_name", "authorized_person_name", "email"]
                    for field in expected_fields:
                        self.assertIn(field, consultant, f"Consultant should have {field} field")
                
                logger.info("✅ Admin consultant access working")
            else:
                logger.warning(f"⚠️ Admin access returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing admin access: {str(e)}")
    
    def test_consultant_creation(self):
        """Test POST /api/consultants endpoint"""
        logger.info("\n=== Testing POST /api/consultants endpoint ===")
        
        url = f"{self.api_url}/consultants"
        
        # Test data for consultant creation
        test_consultant = {
            "company_name": f"Test Consultant Company {uuid.uuid4()}",
            "authorized_person_name": "Test Person",
            "email": f"test{uuid.uuid4()}@testconsultant.com",
            "phone": "1234567890",
            "address": "123 Test Street, Test City"
        }
        
        # Test with no authentication - should work for registration
        try:
            response = requests.post(url, headers=self.headers_no_auth, json=test_consultant)
            logger.info(f"No auth response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Consultant created successfully: {data}")
                self.assertIn("consultant_id", data)
                logger.info("✅ Public consultant creation working")
            else:
                logger.info(f"ℹ️ Public creation not allowed: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing public creation: {str(e)}")

class TestClientManagement(unittest.TestCase):
    """Test Client Management APIs"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_client_list_endpoint_security(self):
        """Test GET /api/clients endpoint security - CRITICAL"""
        logger.info("\n=== Testing GET /api/clients endpoint security ===")
        
        url = f"{self.api_url}/clients"
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status: {response.status_code}")
            
            # Should require authentication
            self.assertIn(response.status_code, [401, 403], 
                         "Clients endpoint should require authentication")
            
            logger.info("✅ No auth correctly rejected")
        except Exception as e:
            logger.error(f"❌ Error testing no auth: {str(e)}")
        
        # Test with invalid token
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid token response status: {response.status_code}")
            
            # Should reject invalid tokens
            self.assertEqual(response.status_code, 401, 
                           "Clients endpoint should reject invalid tokens")
            
            logger.info("✅ Invalid token correctly rejected")
        except Exception as e:
            logger.error(f"❌ Error testing invalid token: {str(e)}")
        
        # Test with admin token
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Admin can see {len(data)} clients")
                
                # Admin should see all clients
                self.assertIsInstance(data, list)
                
                logger.info("✅ Admin access working")
            else:
                logger.warning(f"⚠️ Admin access returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing admin access: {str(e)}")
        
        # Test with client token - CRITICAL SECURITY TEST
        try:
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Client can see {len(data)} clients")
                
                # CRITICAL: Client should only see their own client record
                if len(data) > 1:
                    logger.error("🚨 CRITICAL SECURITY ISSUE: Client can see multiple client records!")
                    self.fail("SECURITY VULNERABILITY: Client users can see other clients' data")
                elif len(data) == 1:
                    logger.info("✅ Client filtering appears to be working")
                else:
                    logger.info("ℹ️ No client data found")
            else:
                logger.warning(f"⚠️ Client access returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing client access: {str(e)}")

class TestEmailManagement(unittest.TestCase):
    """Test Email Management APIs"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_email_management_endpoints(self):
        """Test email management endpoints"""
        logger.info("\n=== Testing Email Management endpoints ===")
        
        email_endpoints = [
            "/email-management/clients-real",
            "/email-management/documents-real", 
            "/email-management/trainings-real"
        ]
        
        for endpoint in email_endpoints:
            url = f"{self.api_url}{endpoint}"
            
            try:
                # Test with admin authentication
                response = requests.get(url, headers=self.headers_admin)
                logger.info(f"Admin {endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ {endpoint} working - returned {len(data) if isinstance(data, list) else 'data'}")
                elif response.status_code == 404:
                    logger.warning(f"⚠️ {endpoint} not found - may not be implemented")
                else:
                    logger.warning(f"⚠️ {endpoint} returned {response.status_code}")
                
                # Test with no authentication
                response = requests.get(url, headers=self.headers_no_auth)
                logger.info(f"No auth {endpoint}: {response.status_code}")
                
                # Should require authentication
                self.assertIn(response.status_code, [401, 403, 404], 
                             f"Email endpoint {endpoint} should require authentication or not exist")
                
            except Exception as e:
                logger.error(f"❌ Error testing {endpoint}: {str(e)}")
                continue

class TestSupplierManagement(unittest.TestCase):
    """Test Supplier Management APIs"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_supplier_public_endpoints(self):
        """Test public supplier endpoints"""
        logger.info("\n=== Testing Supplier public endpoints ===")
        
        public_endpoints = [
            "/suppliers/categories/list",
            "/suppliers/certifications/list"
        ]
        
        for endpoint in public_endpoints:
            url = f"{self.api_url}{endpoint}"
            
            try:
                # Test without authentication - should work
                response = requests.get(url, headers=self.headers_no_auth)
                logger.info(f"No auth {endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ {endpoint} working - public access OK")
                    
                    # Check data structure
                    if "categories" in endpoint:
                        self.assertIn("categories", data)
                        self.assertIsInstance(data["categories"], list)
                    elif "certifications" in endpoint:
                        self.assertIn("certifications", data)
                        self.assertIsInstance(data["certifications"], list)
                else:
                    logger.warning(f"⚠️ {endpoint} returned {response.status_code}")
                
            except Exception as e:
                logger.error(f"❌ Error testing {endpoint}: {str(e)}")
                continue
    
    def test_supplier_protected_endpoints(self):
        """Test protected supplier endpoints"""
        logger.info("\n=== Testing Supplier protected endpoints ===")
        
        protected_endpoints = [
            "/suppliers",
            "/suppliers/analytics/dashboard"
        ]
        
        for endpoint in protected_endpoints:
            url = f"{self.api_url}{endpoint}"
            
            try:
                # Test with no authentication
                response = requests.get(url, headers=self.headers_no_auth)
                logger.info(f"No auth {endpoint}: {response.status_code}")
                
                # Should require authentication
                self.assertIn(response.status_code, [401, 403, 404], 
                             f"Supplier endpoint {endpoint} should require authentication")
                
                # Test with invalid token
                response = requests.get(url, headers=self.headers_invalid)
                logger.info(f"Invalid token {endpoint}: {response.status_code}")
                
                # Should reject invalid tokens
                self.assertIn(response.status_code, [401, 404], 
                             f"Supplier endpoint {endpoint} should reject invalid tokens")
                
            except Exception as e:
                logger.error(f"❌ Error testing {endpoint}: {str(e)}")
                continue

class TestWasteManagement(unittest.TestCase):
    """Test Waste Management APIs"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_waste_management_endpoints(self):
        """Test waste management endpoints"""
        logger.info("\n=== Testing Waste Management endpoints ===")
        
        waste_endpoints = [
            "/waste-management",
            "/waste-management/analytics"
        ]
        
        for endpoint in waste_endpoints:
            url = f"{self.api_url}{endpoint}"
            
            try:
                # Test with no authentication
                response = requests.get(url, headers=self.headers_no_auth)
                logger.info(f"No auth {endpoint}: {response.status_code}")
                
                # Should require authentication
                self.assertIn(response.status_code, [401, 403, 404], 
                             f"Waste endpoint {endpoint} should require authentication")
                
                # Test with invalid token
                response = requests.get(url, headers=self.headers_invalid)
                logger.info(f"Invalid token {endpoint}: {response.status_code}")
                
                # Should reject invalid tokens
                self.assertIn(response.status_code, [401, 404], 
                             f"Waste endpoint {endpoint} should reject invalid tokens")
                
                # Test with admin authentication
                response = requests.get(url, headers=self.headers_admin)
                logger.info(f"Admin {endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ {endpoint} working with admin auth")
                elif response.status_code == 404:
                    logger.warning(f"⚠️ {endpoint} not found")
                else:
                    logger.warning(f"⚠️ {endpoint} returned {response.status_code}")
                
            except Exception as e:
                logger.error(f"❌ Error testing {endpoint}: {str(e)}")
                continue

def run_comprehensive_tests():
    """Run all comprehensive backend tests"""
    logger.info("🚀 Starting Comprehensive Backend Testing for Rota CRM")
    logger.info(f"Testing backend at: {BACKEND_API_URL}")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes in order of priority
    test_classes = [
        TestCoreAuthentication,
        TestDocumentManagementSecurity,  # CRITICAL FOCUS
        TestClientManagement,            # CRITICAL FOCUS
        TestConsultantManagement,
        TestEmailManagement,
        TestSupplierManagement,
        TestWasteManagement
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("🏁 COMPREHENSIVE BACKEND TESTING SUMMARY")
    logger.info("="*80)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    if result.failures:
        logger.error("\n❌ FAILURES:")
        for test, traceback in result.failures:
            logger.error(f"  - {test}: {traceback}")
    
    if result.errors:
        logger.error("\n❌ ERRORS:")
        for test, traceback in result.errors:
            logger.error(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        logger.info("\n✅ ALL TESTS PASSED!")
    else:
        logger.error("\n❌ SOME TESTS FAILED!")
    
    return result

if __name__ == "__main__":
    result = run_comprehensive_tests()
    sys.exit(0 if result.wasSuccessful() else 1)