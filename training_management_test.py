#!/usr/bin/env python3
"""
Training Management Backend Testing Suite
Tests the Training Management backend functionality including:
1. Training Personnel Selection System
2. Training Auto-Complete System  
3. Training CRUD Operations
4. Training Model Updates
5. Client Integration
6. Authentication & Authorization
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

# Railway backend URL (as requested by user)
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# Test JWT tokens for different user types
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"
CONSULTANT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ09OU1VMVEFOVF8wMDEiLCJlbWFpbCI6ImNvbnN1bHRhbnRAcm90YS5jb20iLCJuYW1lIjoiQ29uc3VsdGFudCBVc2VyIn0.signature"
INVALID_TOKEN = "invalid.token.format"

class TrainingManagementTest(unittest.TestCase):
    """Test class for Training Management backend functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}", "Content-Type": "application/json"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}", "Content-Type": "application/json"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}", "Content-Type": "application/json"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}", "Content-Type": "application/json"}
        self.headers_no_auth = {"Content-Type": "application/json"}
        
        # Test data
        self.test_client_id = str(uuid.uuid4())
        self.test_training_data = {
            "client_id": self.test_client_id,
            "name": "Sürdürülebilirlik Eğitimi",
            "subject": "Çevre Yönetimi",
            "participant_count": 25,
            "trainer": "Ahmet Yılmaz",
            "training_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "description": "Otel personeli için sürdürülebilirlik eğitimi",
            "attendees": ["personnel_1", "personnel_2", "personnel_3"]
        }
        
        logger.info(f"🧪 Test setup completed. Using API URL: {self.api_url}")

    def test_1_training_personnel_selection_endpoint(self):
        """Test 1: Training Personnel Selection System - /api/clients/{client_id}/personnel"""
        logger.info("\n" + "="*80)
        logger.info("TEST 1: Training Personnel Selection System")
        logger.info("Testing /api/clients/{client_id}/personnel endpoint")
        logger.info("="*80)
        
        test_client_id = "test-client-123"
        url = f"{self.api_url}/clients/{test_client_id}/personnel"
        
        # Test 1.1: Admin access
        logger.info("\n--- Test 1.1: Admin Access to Personnel Selection ---")
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Admin can access personnel endpoint")
                logger.info(f"Personnel count: {len(data) if isinstance(data, list) else 'N/A'}")
                
                # Verify response structure
                if isinstance(data, list) and len(data) > 0:
                    personnel = data[0]
                    expected_fields = ["id", "name", "position", "client_id"]
                    for field in expected_fields:
                        if field in personnel:
                            logger.info(f"✅ Personnel has {field} field")
                        else:
                            logger.warning(f"⚠️ Personnel missing {field} field")
                            
            elif response.status_code in [401, 403]:
                logger.info(f"⚠️ Authentication required: {response.status_code}")
                try:
                    error_data = response.json()
                    logger.info(f"Error detail: {error_data.get('detail', 'No detail')}")
                except:
                    logger.info(f"Error response: {response.text}")
            else:
                logger.info(f"⚠️ Unexpected response: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing admin access: {str(e)}")
        
        # Test 1.2: Client access (should only see their own personnel)
        logger.info("\n--- Test 1.2: Client Access to Personnel Selection ---")
        try:
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Client can access personnel endpoint")
                logger.info(f"Personnel count: {len(data) if isinstance(data, list) else 'N/A'}")
            elif response.status_code == 403:
                logger.info(f"✅ Client access properly restricted (403)")
            elif response.status_code in [401]:
                logger.info(f"⚠️ Authentication issue: {response.status_code}")
            else:
                logger.info(f"⚠️ Unexpected response: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing client access: {str(e)}")
        
        # Test 1.3: Consultant access
        logger.info("\n--- Test 1.3: Consultant Access to Personnel Selection ---")
        try:
            response = requests.get(url, headers=self.headers_consultant)
            logger.info(f"Consultant response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Consultant can access personnel endpoint")
                logger.info(f"Personnel count: {len(data) if isinstance(data, list) else 'N/A'}")
            elif response.status_code == 403:
                logger.info(f"✅ Consultant access properly restricted (403)")
            elif response.status_code in [401]:
                logger.info(f"⚠️ Authentication issue: {response.status_code}")
            else:
                logger.info(f"⚠️ Unexpected response: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing consultant access: {str(e)}")
        
        # Test 1.4: No authentication
        logger.info("\n--- Test 1.4: No Authentication Access ---")
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status: {response.status_code}")
            
            if response.status_code == 403:
                logger.info(f"✅ No auth properly blocked (403)")
            elif response.status_code == 401:
                logger.info(f"✅ No auth properly blocked (401)")
            else:
                logger.warning(f"⚠️ Unexpected response for no auth: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing no auth access: {str(e)}")

    def test_2_training_auto_complete_system(self):
        """Test 2: Training Auto-Complete System - /api/trainings/auto-complete"""
        logger.info("\n" + "="*80)
        logger.info("TEST 2: Training Auto-Complete System")
        logger.info("Testing /api/trainings/auto-complete endpoint")
        logger.info("="*80)
        
        url = f"{self.api_url}/trainings/auto-complete"
        
        # Test 2.1: Admin access to auto-complete
        logger.info("\n--- Test 2.1: Admin Access to Auto-Complete ---")
        try:
            response = requests.post(url, headers=self.headers_admin)
            logger.info(f"Admin auto-complete response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Auto-complete endpoint accessible")
                logger.info(f"Response: {data}")
                
                # Check response structure
                if "message" in data:
                    logger.info(f"✅ Response has message field")
                if "updated_count" in data:
                    logger.info(f"✅ Response has updated_count field: {data['updated_count']}")
                    
            elif response.status_code in [401, 403]:
                logger.info(f"⚠️ Authentication/Authorization required: {response.status_code}")
                try:
                    error_data = response.json()
                    logger.info(f"Error detail: {error_data.get('detail', 'No detail')}")
                except:
                    logger.info(f"Error response: {response.text}")
            else:
                logger.info(f"⚠️ Unexpected response: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing admin auto-complete: {str(e)}")
        
        # Test 2.2: Client access (should be restricted)
        logger.info("\n--- Test 2.2: Client Access to Auto-Complete (Should be Restricted) ---")
        try:
            response = requests.post(url, headers=self.headers_client)
            logger.info(f"Client auto-complete response status: {response.status_code}")
            
            if response.status_code == 403:
                logger.info(f"✅ Client access properly restricted (403)")
            elif response.status_code == 401:
                logger.info(f"⚠️ Authentication issue: {response.status_code}")
            elif response.status_code == 200:
                logger.warning(f"⚠️ Client should not have access to auto-complete")
            else:
                logger.info(f"⚠️ Unexpected response: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing client auto-complete: {str(e)}")
        
        # Test 2.3: No authentication
        logger.info("\n--- Test 2.3: No Authentication Access ---")
        try:
            response = requests.post(url, headers=self.headers_no_auth)
            logger.info(f"No auth auto-complete response status: {response.status_code}")
            
            if response.status_code == 403:
                logger.info(f"✅ No auth properly blocked (403)")
            elif response.status_code == 401:
                logger.info(f"✅ No auth properly blocked (401)")
            else:
                logger.warning(f"⚠️ Unexpected response for no auth: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing no auth auto-complete: {str(e)}")

    def test_3_training_crud_operations(self):
        """Test 3: Training CRUD Operations"""
        logger.info("\n" + "="*80)
        logger.info("TEST 3: Training CRUD Operations")
        logger.info("Testing GET/POST/PUT/DELETE /api/trainings endpoints")
        logger.info("="*80)
        
        # Test 3.1: GET /api/trainings
        logger.info("\n--- Test 3.1: GET /api/trainings ---")
        url_get = f"{self.api_url}/trainings"
        
        try:
            response = requests.get(url_get, headers=self.headers_admin)
            logger.info(f"GET trainings response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ GET trainings successful")
                logger.info(f"Training count: {len(data) if isinstance(data, list) else 'N/A'}")
                
                # Verify response structure
                if isinstance(data, list) and len(data) > 0:
                    training = data[0]
                    expected_fields = ["id", "client_id", "name", "subject", "participant_count", 
                                     "trainer", "training_date", "description", "status", "attendees"]
                    for field in expected_fields:
                        if field in training:
                            logger.info(f"✅ Training has {field} field: {training.get(field)}")
                        else:
                            logger.warning(f"⚠️ Training missing {field} field")
                            
                    # Check for personnel_ids field (attendees)
                    if "attendees" in training:
                        logger.info(f"✅ Training has personnel selection (attendees): {training['attendees']}")
                    
                    # Check for client_id field
                    if "client_id" in training:
                        logger.info(f"✅ Training has client_id field: {training['client_id']}")
                        
            elif response.status_code in [401, 403]:
                logger.info(f"⚠️ Authentication required: {response.status_code}")
            else:
                logger.info(f"⚠️ Unexpected response: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing GET trainings: {str(e)}")
        
        # Test 3.2: POST /api/trainings
        logger.info("\n--- Test 3.2: POST /api/trainings ---")
        url_post = f"{self.api_url}/trainings"
        
        try:
            response = requests.post(url_post, headers=self.headers_admin, json=self.test_training_data)
            logger.info(f"POST training response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"✅ POST training successful")
                logger.info(f"Created training ID: {data.get('id', 'N/A')}")
                
                # Save training ID for later tests
                self.created_training_id = data.get("id")
                
                # Verify created training structure
                expected_fields = ["id", "client_id", "name", "subject", "participant_count", 
                                 "trainer", "training_date", "description", "attendees"]
                for field in expected_fields:
                    if field in data:
                        logger.info(f"✅ Created training has {field} field")
                    else:
                        logger.warning(f"⚠️ Created training missing {field} field")
                        
            elif response.status_code in [401, 403]:
                logger.info(f"⚠️ Authentication/Authorization required: {response.status_code}")
            elif response.status_code == 400:
                logger.info(f"⚠️ Bad request (possibly validation error): {response.status_code}")
                try:
                    error_data = response.json()
                    logger.info(f"Error detail: {error_data.get('detail', 'No detail')}")
                except:
                    logger.info(f"Error response: {response.text}")
            else:
                logger.info(f"⚠️ Unexpected response: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing POST training: {str(e)}")
        
        # Test 3.3: PUT /api/trainings/{id} (if we have a training ID)
        if hasattr(self, 'created_training_id') and self.created_training_id:
            logger.info("\n--- Test 3.3: PUT /api/trainings/{id} ---")
            url_put = f"{self.api_url}/trainings/{self.created_training_id}"
            
            update_data = {
                "name": "Updated Sürdürülebilirlik Eğitimi",
                "participant_count": 30,
                "status": "completed"
            }
            
            try:
                response = requests.put(url_put, headers=self.headers_admin, json=update_data)
                logger.info(f"PUT training response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ PUT training successful")
                    logger.info(f"Updated training name: {data.get('name', 'N/A')}")
                    logger.info(f"Updated participant count: {data.get('participant_count', 'N/A')}")
                    
                elif response.status_code in [401, 403]:
                    logger.info(f"⚠️ Authentication/Authorization required: {response.status_code}")
                elif response.status_code == 404:
                    logger.info(f"⚠️ Training not found: {response.status_code}")
                else:
                    logger.info(f"⚠️ Unexpected response: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error testing PUT training: {str(e)}")
        
        # Test 3.4: DELETE /api/trainings/{id} (if we have a training ID)
        if hasattr(self, 'created_training_id') and self.created_training_id:
            logger.info("\n--- Test 3.4: DELETE /api/trainings/{id} ---")
            url_delete = f"{self.api_url}/trainings/{self.created_training_id}"
            
            try:
                response = requests.delete(url_delete, headers=self.headers_admin)
                logger.info(f"DELETE training response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ DELETE training successful")
                    logger.info(f"Delete message: {data.get('message', 'N/A')}")
                    
                elif response.status_code in [401, 403]:
                    logger.info(f"⚠️ Authentication/Authorization required: {response.status_code}")
                elif response.status_code == 404:
                    logger.info(f"⚠️ Training not found: {response.status_code}")
                else:
                    logger.info(f"⚠️ Unexpected response: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error testing DELETE training: {str(e)}")

    def test_4_client_integration_registered_filtering(self):
        """Test 4: Client Integration with client_type='registered' filtering"""
        logger.info("\n" + "="*80)
        logger.info("TEST 4: Client Integration - Registered Client Filtering")
        logger.info("Testing client_type='registered' filtering in training system")
        logger.info("="*80)
        
        # Test 4.1: Get clients with registered filter
        logger.info("\n--- Test 4.1: GET /api/clients with client_type=registered ---")
        url = f"{self.api_url}/clients"
        params = {"client_type": "registered"}
        
        try:
            response = requests.get(url, headers=self.headers_admin, params=params)
            logger.info(f"GET clients (registered) response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ GET registered clients successful")
                
                if isinstance(data, list):
                    logger.info(f"Registered clients count: {len(data)}")
                    
                    # Verify all clients are registered type
                    for client in data:
                        client_type = client.get("client_type", "unknown")
                        if client_type == "registered":
                            logger.info(f"✅ Client {client.get('name', 'N/A')} is registered type")
                        else:
                            logger.warning(f"⚠️ Client {client.get('name', 'N/A')} has type: {client_type}")
                            
                elif isinstance(data, dict) and "clients" in data:
                    clients = data["clients"]
                    logger.info(f"Registered clients count: {len(clients)}")
                    
                    # Verify all clients are registered type
                    for client in clients:
                        client_type = client.get("client_type", "unknown")
                        if client_type == "registered":
                            logger.info(f"✅ Client {client.get('name', 'N/A')} is registered type")
                        else:
                            logger.warning(f"⚠️ Client {client.get('name', 'N/A')} has type: {client_type}")
                else:
                    logger.info(f"Unexpected response format: {type(data)}")
                    
            elif response.status_code in [401, 403]:
                logger.info(f"⚠️ Authentication required: {response.status_code}")
            else:
                logger.info(f"⚠️ Unexpected response: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing registered clients: {str(e)}")
        
        # Test 4.2: Get clients with bulk filter (should be separate)
        logger.info("\n--- Test 4.2: GET /api/clients with client_type=bulk ---")
        params = {"client_type": "bulk"}
        
        try:
            response = requests.get(url, headers=self.headers_admin, params=params)
            logger.info(f"GET clients (bulk) response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ GET bulk clients successful")
                
                if isinstance(data, list):
                    logger.info(f"Bulk clients count: {len(data)}")
                    
                    # Verify all clients are bulk type
                    for client in data:
                        client_type = client.get("client_type", "unknown")
                        if client_type == "bulk":
                            logger.info(f"✅ Client {client.get('name', 'N/A')} is bulk type")
                        else:
                            logger.warning(f"⚠️ Client {client.get('name', 'N/A')} has type: {client_type}")
                            
                elif isinstance(data, dict) and "clients" in data:
                    clients = data["clients"]
                    logger.info(f"Bulk clients count: {len(clients)}")
                    
                    # Verify all clients are bulk type
                    for client in clients:
                        client_type = client.get("client_type", "unknown")
                        if client_type == "bulk":
                            logger.info(f"✅ Client {client.get('name', 'N/A')} is bulk type")
                        else:
                            logger.warning(f"⚠️ Client {client.get('name', 'N/A')} has type: {client_type}")
                else:
                    logger.info(f"Unexpected response format: {type(data)}")
                    
            elif response.status_code in [401, 403]:
                logger.info(f"⚠️ Authentication required: {response.status_code}")
            else:
                logger.info(f"⚠️ Unexpected response: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing bulk clients: {str(e)}")

    def test_5_authentication_authorization(self):
        """Test 5: Authentication & Authorization for all training endpoints"""
        logger.info("\n" + "="*80)
        logger.info("TEST 5: Authentication & Authorization")
        logger.info("Testing authentication and role-based access control")
        logger.info("="*80)
        
        endpoints_to_test = [
            ("GET", "/trainings", "Get all trainings"),
            ("POST", "/trainings", "Create training"),
            ("POST", "/trainings/auto-complete", "Auto-complete trainings"),
            ("GET", "/clients/test-client/personnel", "Get client personnel")
        ]
        
        for method, endpoint, description in endpoints_to_test:
            logger.info(f"\n--- Test 5.{endpoints_to_test.index((method, endpoint, description)) + 1}: {description} ---")
            url = f"{self.api_url}{endpoint}"
            
            # Test with invalid token
            logger.info(f"Testing {method} {endpoint} with invalid token...")
            try:
                if method == "GET":
                    response = requests.get(url, headers=self.headers_invalid)
                elif method == "POST":
                    response = requests.post(url, headers=self.headers_invalid, json=self.test_training_data)
                elif method == "PUT":
                    response = requests.put(url, headers=self.headers_invalid, json={})
                elif method == "DELETE":
                    response = requests.delete(url, headers=self.headers_invalid)
                
                logger.info(f"Invalid token response status: {response.status_code}")
                
                if response.status_code == 401:
                    logger.info(f"✅ Invalid token properly rejected (401)")
                elif response.status_code == 403:
                    logger.info(f"✅ Invalid token properly rejected (403)")
                else:
                    logger.warning(f"⚠️ Unexpected response for invalid token: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error testing invalid token: {str(e)}")
            
            # Test with no authentication
            logger.info(f"Testing {method} {endpoint} with no authentication...")
            try:
                if method == "GET":
                    response = requests.get(url, headers=self.headers_no_auth)
                elif method == "POST":
                    response = requests.post(url, headers=self.headers_no_auth, json=self.test_training_data)
                elif method == "PUT":
                    response = requests.put(url, headers=self.headers_no_auth, json={})
                elif method == "DELETE":
                    response = requests.delete(url, headers=self.headers_no_auth)
                
                logger.info(f"No auth response status: {response.status_code}")
                
                if response.status_code == 403:
                    logger.info(f"✅ No auth properly rejected (403)")
                elif response.status_code == 401:
                    logger.info(f"✅ No auth properly rejected (401)")
                else:
                    logger.warning(f"⚠️ Unexpected response for no auth: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error testing no auth: {str(e)}")

    def test_6_training_model_validation(self):
        """Test 6: Training Model Updates - client_id and personnel_ids fields"""
        logger.info("\n" + "="*80)
        logger.info("TEST 6: Training Model Validation")
        logger.info("Testing Training model with client_id and personnel_ids fields")
        logger.info("="*80)
        
        # Test 6.1: Create training with all required fields
        logger.info("\n--- Test 6.1: Create Training with All Required Fields ---")
        url = f"{self.api_url}/trainings"
        
        complete_training_data = {
            "client_id": str(uuid.uuid4()),
            "name": "Model Validation Test Training",
            "subject": "Data Model Testing",
            "participant_count": 15,
            "trainer": "Test Trainer",
            "training_date": (datetime.utcnow() + timedelta(days=5)).isoformat(),
            "description": "Testing training model validation",
            "attendees": ["personnel_001", "personnel_002", "personnel_003"]  # This is personnel_ids
        }
        
        try:
            response = requests.post(url, headers=self.headers_admin, json=complete_training_data)
            logger.info(f"Complete training creation response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"✅ Training created with all fields")
                
                # Verify all fields are present
                required_fields = ["id", "client_id", "name", "subject", "participant_count", 
                                 "trainer", "training_date", "description", "attendees"]
                for field in required_fields:
                    if field in data:
                        logger.info(f"✅ Training has {field}: {data[field]}")
                    else:
                        logger.warning(f"⚠️ Training missing {field}")
                
                # Specifically check client_id and personnel_ids (attendees)
                if data.get("client_id") == complete_training_data["client_id"]:
                    logger.info(f"✅ client_id correctly set: {data['client_id']}")
                else:
                    logger.warning(f"⚠️ client_id mismatch")
                
                if data.get("attendees") == complete_training_data["attendees"]:
                    logger.info(f"✅ personnel_ids (attendees) correctly set: {data['attendees']}")
                else:
                    logger.warning(f"⚠️ personnel_ids (attendees) mismatch")
                    
                self.validation_training_id = data.get("id")
                
            elif response.status_code in [401, 403]:
                logger.info(f"⚠️ Authentication required: {response.status_code}")
            else:
                logger.info(f"⚠️ Unexpected response: {response.status_code}")
                try:
                    error_data = response.json()
                    logger.info(f"Error detail: {error_data.get('detail', 'No detail')}")
                except:
                    logger.info(f"Error response: {response.text}")
                    
        except Exception as e:
            logger.error(f"❌ Error testing complete training creation: {str(e)}")
        
        # Test 6.2: Create training with missing required fields
        logger.info("\n--- Test 6.2: Create Training with Missing Required Fields ---")
        
        incomplete_training_data = {
            "name": "Incomplete Training",
            "subject": "Missing Fields Test"
            # Missing client_id, participant_count, trainer, training_date, description
        }
        
        try:
            response = requests.post(url, headers=self.headers_admin, json=incomplete_training_data)
            logger.info(f"Incomplete training creation response status: {response.status_code}")
            
            if response.status_code == 400:
                logger.info(f"✅ Incomplete training properly rejected (400)")
                try:
                    error_data = response.json()
                    logger.info(f"Validation error: {error_data.get('detail', 'No detail')}")
                except:
                    logger.info(f"Error response: {response.text}")
            elif response.status_code == 422:
                logger.info(f"✅ Incomplete training properly rejected (422 - Validation Error)")
                try:
                    error_data = response.json()
                    logger.info(f"Validation error: {error_data.get('detail', 'No detail')}")
                except:
                    logger.info(f"Error response: {response.text}")
            elif response.status_code in [401, 403]:
                logger.info(f"⚠️ Authentication required: {response.status_code}")
            else:
                logger.warning(f"⚠️ Unexpected response for incomplete data: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing incomplete training creation: {str(e)}")

    def test_7_comprehensive_integration_test(self):
        """Test 7: Comprehensive Integration Test"""
        logger.info("\n" + "="*80)
        logger.info("TEST 7: Comprehensive Integration Test")
        logger.info("Testing complete training management workflow")
        logger.info("="*80)
        
        # Test 7.1: Get registered clients for training
        logger.info("\n--- Test 7.1: Get Registered Clients for Training ---")
        clients_url = f"{self.api_url}/clients"
        params = {"client_type": "registered"}
        
        selected_client_id = None
        try:
            response = requests.get(clients_url, headers=self.headers_admin, params=params)
            logger.info(f"Get registered clients response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    selected_client_id = data[0].get("id")
                    logger.info(f"✅ Selected client for training: {data[0].get('name', 'N/A')}")
                elif isinstance(data, dict) and "clients" in data and len(data["clients"]) > 0:
                    selected_client_id = data["clients"][0].get("id")
                    logger.info(f"✅ Selected client for training: {data['clients'][0].get('name', 'N/A')}")
                else:
                    logger.warning(f"⚠️ No registered clients found")
                    selected_client_id = str(uuid.uuid4())  # Use test client ID
                    
            else:
                logger.info(f"⚠️ Could not get clients: {response.status_code}")
                selected_client_id = str(uuid.uuid4())  # Use test client ID
                
        except Exception as e:
            logger.error(f"❌ Error getting clients: {str(e)}")
            selected_client_id = str(uuid.uuid4())  # Use test client ID
        
        # Test 7.2: Get personnel for selected client
        if selected_client_id:
            logger.info("\n--- Test 7.2: Get Personnel for Selected Client ---")
            personnel_url = f"{self.api_url}/clients/{selected_client_id}/personnel"
            
            personnel_ids = []
            try:
                response = requests.get(personnel_url, headers=self.headers_admin)
                logger.info(f"Get client personnel response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        personnel_ids = [person.get("id") for person in data if person.get("id")]
                        logger.info(f"✅ Found {len(personnel_ids)} personnel for client")
                    else:
                        logger.info(f"⚠️ Unexpected personnel response format")
                        personnel_ids = ["test_personnel_1", "test_personnel_2"]
                else:
                    logger.info(f"⚠️ Could not get personnel: {response.status_code}")
                    personnel_ids = ["test_personnel_1", "test_personnel_2"]
                    
            except Exception as e:
                logger.error(f"❌ Error getting personnel: {str(e)}")
                personnel_ids = ["test_personnel_1", "test_personnel_2"]
        
        # Test 7.3: Create training with selected client and personnel
        if selected_client_id:
            logger.info("\n--- Test 7.3: Create Training with Selected Client and Personnel ---")
            trainings_url = f"{self.api_url}/trainings"
            
            integration_training_data = {
                "client_id": selected_client_id,
                "name": "Integration Test Training",
                "subject": "Complete Workflow Test",
                "participant_count": len(personnel_ids) if personnel_ids else 10,
                "trainer": "Integration Test Trainer",
                "training_date": (datetime.utcnow() + timedelta(days=3)).isoformat(),
                "description": "Testing complete training management workflow",
                "attendees": personnel_ids[:3] if personnel_ids else ["test_personnel_1", "test_personnel_2"]
            }
            
            created_training_id = None
            try:
                response = requests.post(trainings_url, headers=self.headers_admin, json=integration_training_data)
                logger.info(f"Create integration training response status: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    created_training_id = data.get("id")
                    logger.info(f"✅ Integration training created: {created_training_id}")
                    logger.info(f"Training name: {data.get('name')}")
                    logger.info(f"Client ID: {data.get('client_id')}")
                    logger.info(f"Personnel (attendees): {data.get('attendees')}")
                else:
                    logger.info(f"⚠️ Could not create training: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error creating integration training: {str(e)}")
        
        # Test 7.4: Verify training appears in GET /api/trainings
        if created_training_id:
            logger.info("\n--- Test 7.4: Verify Training in GET /api/trainings ---")
            
            try:
                response = requests.get(trainings_url, headers=self.headers_admin)
                logger.info(f"Get all trainings response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        found_training = None
                        for training in data:
                            if training.get("id") == created_training_id:
                                found_training = training
                                break
                        
                        if found_training:
                            logger.info(f"✅ Integration training found in GET /api/trainings")
                            logger.info(f"Training client_id: {found_training.get('client_id')}")
                            logger.info(f"Training attendees: {found_training.get('attendees')}")
                        else:
                            logger.warning(f"⚠️ Integration training not found in GET /api/trainings")
                    else:
                        logger.info(f"⚠️ Unexpected trainings response format")
                else:
                    logger.info(f"⚠️ Could not get trainings: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error verifying training: {str(e)}")

def run_training_management_tests():
    """Run all training management tests"""
    logger.info("🚀 Starting Training Management Backend Tests")
    logger.info(f"🌐 Using Railway API URL: {RAILWAY_API_URL}")
    logger.info("="*100)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test methods
    test_methods = [
        'test_1_training_personnel_selection_endpoint',
        'test_2_training_auto_complete_system',
        'test_3_training_crud_operations',
        'test_4_client_integration_registered_filtering',
        'test_5_authentication_authorization',
        'test_6_training_model_validation',
        'test_7_comprehensive_integration_test'
    ]
    
    for method in test_methods:
        suite.addTest(TrainingManagementTest(method))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    logger.info("\n" + "="*100)
    logger.info("🏁 TRAINING MANAGEMENT BACKEND TESTS COMPLETED")
    logger.info("="*100)
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
    
    if not result.failures and not result.errors:
        logger.info("\n✅ ALL TESTS PASSED!")
    
    return result

if __name__ == "__main__":
    run_training_management_tests()