#!/usr/bin/env python3
"""
ROTA CRM Railway Backend Comprehensive Test
Testing Railway Backend URL: https://rota-crm-production.up.railway.app/api

This script tests all the specific endpoints mentioned in the review request:
1. DANIŞMAN YÖNETİMİ (Consultant Management)
2. EMAIL YÖNETİMİ - DOKÜMAN SORUNU (Email Management - Document Issue)
3. EĞİTİM YÖNETİMİ (Training Management)
4. CLIENT YÖNETİMİ (Client Management)
5. AUTHENTICATION TEST
"""

import requests
import json
import logging
import uuid
from datetime import datetime
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/railway_backend_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Railway Backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# Test tokens (these are sample tokens - in real scenario they would be generated from Clerk)
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ0xJRU5UIiwiZW1haWwiOiJjbGllbnRAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBDbGllbnQifQ.signature"
INVALID_TOKEN = "invalid.token.format"

class RailwayBackendTester:
    def __init__(self):
        self.api_url = RAILWAY_API_URL
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
        
        # Test results storage
        self.test_results = {
            "consultant_management": {},
            "email_management": {},
            "training_management": {},
            "client_management": {},
            "authentication": {},
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "critical_issues": [],
                "working_endpoints": [],
                "broken_endpoints": []
            }
        }
        
        # Test client IDs for filtering tests
        self.test_client_ids = []
    
    def log_test_result(self, category, test_name, status, details, is_critical=False):
        """Log test result and update summary"""
        self.test_results[category][test_name] = {
            "status": status,
            "details": details,
            "is_critical": is_critical
        }
        
        self.test_results["summary"]["total_tests"] += 1
        if status == "PASS":
            self.test_results["summary"]["passed_tests"] += 1
            if "endpoint" in details:
                self.test_results["summary"]["working_endpoints"].append(details["endpoint"])
        else:
            self.test_results["summary"]["failed_tests"] += 1
            if is_critical:
                self.test_results["summary"]["critical_issues"].append(f"{category}: {test_name}")
            if "endpoint" in details:
                self.test_results["summary"]["broken_endpoints"].append(details["endpoint"])
    
    def test_endpoint(self, method, endpoint, headers=None, data=None, params=None, expected_status=None):
        """Generic endpoint testing method"""
        url = f"{self.api_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers or {}, params=params or {})
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers or {}, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers or {}, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers or {})
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "response_size": len(response.text),
                "accessible": True
            }
            
            # Try to parse JSON response
            try:
                result["response_data"] = response.json()
            except:
                result["response_data"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
            
            # Check if status code matches expected
            if expected_status:
                if isinstance(expected_status, list):
                    result["status_match"] = response.status_code in expected_status
                else:
                    result["status_match"] = response.status_code == expected_status
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                "endpoint": endpoint,
                "method": method,
                "error": str(e),
                "accessible": False
            }
    
    def test_consultant_management(self):
        """Test DANIŞMAN YÖNETİMİ endpoints"""
        logger.info("\n" + "="*60)
        logger.info("1. DANIŞMAN YÖNETİMİ TESTİ (CONSULTANT MANAGEMENT)")
        logger.info("="*60)
        
        # Test GET /api/consultants (list all consultants)
        logger.info("\n--- Testing GET /api/consultants (list all consultants) ---")
        result = self.test_endpoint("GET", "/consultants", expected_status=[200, 401, 403])
        
        if result["accessible"]:
            if result["status_code"] == 200:
                consultants = result.get("response_data", [])
                logger.info(f"✅ GET /api/consultants - SUCCESS: Found {len(consultants)} consultants")
                logger.info(f"   Consultants: {[c.get('company_name', 'Unknown') for c in consultants[:5]]}")
                self.log_test_result("consultant_management", "list_consultants", "PASS", result)
            else:
                logger.info(f"⚠️ GET /api/consultants - AUTH REQUIRED: Status {result['status_code']}")
                self.log_test_result("consultant_management", "list_consultants", "AUTH_REQUIRED", result)
        else:
            logger.error(f"❌ GET /api/consultants - FAILED: {result.get('error')}")
            self.log_test_result("consultant_management", "list_consultants", "FAIL", result, is_critical=True)
        
        # Test POST /api/consultants (create new consultant)
        logger.info("\n--- Testing POST /api/consultants (create new consultant) ---")
        consultant_data = {
            "company_name": f"Test Danışmanlık {uuid.uuid4().hex[:8]}",
            "authorized_person_name": "Test Yetkili",
            "email": f"test{uuid.uuid4().hex[:8]}@testdanismanlik.com",
            "phone": "0532 123 45 67",
            "address": "Test Adres, İstanbul"
        }
        
        result = self.test_endpoint("POST", "/consultants", data=consultant_data, expected_status=[200, 201, 400, 401, 403])
        
        if result["accessible"]:
            if result["status_code"] in [200, 201]:
                logger.info(f"✅ POST /api/consultants - SUCCESS: Created consultant")
                logger.info(f"   Response: {result.get('response_data', {})}")
                self.log_test_result("consultant_management", "create_consultant", "PASS", result)
            elif result["status_code"] == 400:
                logger.info(f"⚠️ POST /api/consultants - VALIDATION ERROR: {result.get('response_data', {})}")
                self.log_test_result("consultant_management", "create_consultant", "VALIDATION_ERROR", result)
            else:
                logger.info(f"⚠️ POST /api/consultants - AUTH REQUIRED: Status {result['status_code']}")
                self.log_test_result("consultant_management", "create_consultant", "AUTH_REQUIRED", result)
        else:
            logger.error(f"❌ POST /api/consultants - FAILED: {result.get('error')}")
            self.log_test_result("consultant_management", "create_consultant", "FAIL", result, is_critical=True)
        
        # Test GET /api/consultants/{id} (single consultant details) - with admin auth
        logger.info("\n--- Testing GET /api/consultants/{id} (single consultant details) ---")
        # First get a consultant ID from the list
        consultants_result = self.test_endpoint("GET", "/consultants")
        if consultants_result["accessible"] and consultants_result["status_code"] == 200:
            consultants = consultants_result.get("response_data", [])
            if consultants:
                consultant_id = consultants[0].get("id")
                if consultant_id:
                    result = self.test_endpoint("GET", f"/consultants/{consultant_id}", 
                                              headers=self.headers_admin, expected_status=[200, 401, 403, 404])
                    
                    if result["accessible"]:
                        if result["status_code"] == 200:
                            logger.info(f"✅ GET /api/consultants/{consultant_id} - SUCCESS")
                            logger.info(f"   Consultant: {result.get('response_data', {}).get('company_name', 'Unknown')}")
                            self.log_test_result("consultant_management", "get_consultant_details", "PASS", result)
                        else:
                            logger.info(f"⚠️ GET /api/consultants/{consultant_id} - Status {result['status_code']}")
                            self.log_test_result("consultant_management", "get_consultant_details", "AUTH_REQUIRED", result)
                    else:
                        logger.error(f"❌ GET /api/consultants/{consultant_id} - FAILED: {result.get('error')}")
                        self.log_test_result("consultant_management", "get_consultant_details", "FAIL", result, is_critical=True)
                else:
                    logger.warning("⚠️ No consultant ID found in consultant list")
                    self.log_test_result("consultant_management", "get_consultant_details", "SKIP", {"reason": "No consultant ID"})
            else:
                logger.warning("⚠️ No consultants found to test individual consultant endpoint")
                self.log_test_result("consultant_management", "get_consultant_details", "SKIP", {"reason": "No consultants"})
        else:
            logger.warning("⚠️ Could not get consultant list to test individual consultant endpoint")
            self.log_test_result("consultant_management", "get_consultant_details", "SKIP", {"reason": "List failed"})
    
    def test_email_management(self):
        """Test EMAIL YÖNETİMİ - DOKÜMAN SORUNU endpoints"""
        logger.info("\n" + "="*60)
        logger.info("2. EMAIL YÖNETİMİ - DOKÜMAN SORUNU TESTİ")
        logger.info("="*60)
        
        # Test GET /api/belge/list (list documents)
        logger.info("\n--- Testing GET /api/belge/list (list documents) ---")
        result = self.test_endpoint("GET", "/belge/list", headers=self.headers_admin, expected_status=[200, 401, 403])
        
        if result["accessible"]:
            if result["status_code"] == 200:
                response_data = result.get("response_data", {})
                if isinstance(response_data, dict) and "documents" in response_data:
                    documents = response_data["documents"]
                    logger.info(f"✅ GET /api/belge/list - SUCCESS: Found {len(documents)} documents")
                    if documents:
                        logger.info(f"   Sample document: {documents[0].get('document_name', 'Unknown')}")
                        # Store client IDs for filtering tests
                        self.test_client_ids = list(set([doc.get('client_id') for doc in documents if doc.get('client_id')]))
                        logger.info(f"   Found client IDs: {self.test_client_ids[:3]}...")
                elif isinstance(response_data, list):
                    logger.info(f"✅ GET /api/belge/list - SUCCESS: Found {len(response_data)} documents")
                    if response_data:
                        logger.info(f"   Sample document: {response_data[0].get('document_name', 'Unknown')}")
                        self.test_client_ids = list(set([doc.get('client_id') for doc in response_data if doc.get('client_id')]))
                else:
                    logger.info(f"✅ GET /api/belge/list - SUCCESS: Response format: {type(response_data)}")
                
                self.log_test_result("email_management", "list_documents", "PASS", result)
            else:
                logger.info(f"⚠️ GET /api/belge/list - AUTH REQUIRED: Status {result['status_code']}")
                self.log_test_result("email_management", "list_documents", "AUTH_REQUIRED", result)
        else:
            logger.error(f"❌ GET /api/belge/list - FAILED: {result.get('error')}")
            self.log_test_result("email_management", "list_documents", "FAIL", result, is_critical=True)
        
        # Test GET /api/belge/list?client_id={test_client_id} (client filtering)
        logger.info("\n--- Testing GET /api/belge/list?client_id={test_client_id} (client filtering) ---")
        if self.test_client_ids:
            test_client_id = self.test_client_ids[0]
            result = self.test_endpoint("GET", "/belge/list", headers=self.headers_admin, 
                                      params={"client_id": test_client_id}, expected_status=[200, 401, 403])
            
            if result["accessible"]:
                if result["status_code"] == 200:
                    response_data = result.get("response_data", {})
                    if isinstance(response_data, dict) and "documents" in response_data:
                        filtered_docs = response_data["documents"]
                    elif isinstance(response_data, list):
                        filtered_docs = response_data
                    else:
                        filtered_docs = []
                    
                    logger.info(f"✅ GET /api/belge/list?client_id={test_client_id} - SUCCESS: Found {len(filtered_docs)} documents")
                    
                    # Check if filtering actually works
                    if filtered_docs:
                        all_same_client = all(doc.get('client_id') == test_client_id for doc in filtered_docs)
                        if all_same_client:
                            logger.info(f"   ✅ FILTERING WORKS: All documents belong to client {test_client_id}")
                            self.log_test_result("email_management", "client_filtering", "PASS", result)
                        else:
                            logger.warning(f"   ⚠️ FILTERING ISSUE: Some documents don't belong to client {test_client_id}")
                            self.log_test_result("email_management", "client_filtering", "FILTERING_ISSUE", result, is_critical=True)
                    else:
                        logger.info(f"   ℹ️ No documents found for client {test_client_id}")
                        self.log_test_result("email_management", "client_filtering", "NO_DATA", result)
                else:
                    logger.info(f"⚠️ GET /api/belge/list with client_id - AUTH REQUIRED: Status {result['status_code']}")
                    self.log_test_result("email_management", "client_filtering", "AUTH_REQUIRED", result)
            else:
                logger.error(f"❌ GET /api/belge/list with client_id - FAILED: {result.get('error')}")
                self.log_test_result("email_management", "client_filtering", "FAIL", result, is_critical=True)
        else:
            logger.warning("⚠️ No client IDs available for filtering test")
            self.log_test_result("email_management", "client_filtering", "SKIP", {"reason": "No client IDs"})
        
        # Test POST /api/belge/upload (document upload endpoint exists?)
        logger.info("\n--- Testing POST /api/belge/upload (document upload endpoint) ---")
        # We'll test if the endpoint exists by sending a request without file data
        result = self.test_endpoint("POST", "/belge/upload", headers=self.headers_admin, 
                                  expected_status=[400, 401, 403, 422, 405])
        
        if result["accessible"]:
            if result["status_code"] in [400, 422]:
                logger.info(f"✅ POST /api/belge/upload - ENDPOINT EXISTS: Status {result['status_code']} (validation error expected)")
                logger.info(f"   Response: {result.get('response_data', {})}")
                self.log_test_result("email_management", "upload_endpoint_exists", "PASS", result)
            elif result["status_code"] in [401, 403]:
                logger.info(f"✅ POST /api/belge/upload - ENDPOINT EXISTS: Status {result['status_code']} (auth required)")
                self.log_test_result("email_management", "upload_endpoint_exists", "AUTH_REQUIRED", result)
            elif result["status_code"] == 405:
                logger.warning(f"⚠️ POST /api/belge/upload - METHOD NOT ALLOWED: Status {result['status_code']}")
                self.log_test_result("email_management", "upload_endpoint_exists", "METHOD_NOT_ALLOWED", result)
            else:
                logger.info(f"ℹ️ POST /api/belge/upload - Status {result['status_code']}")
                self.log_test_result("email_management", "upload_endpoint_exists", "UNKNOWN", result)
        else:
            logger.error(f"❌ POST /api/belge/upload - FAILED: {result.get('error')}")
            self.log_test_result("email_management", "upload_endpoint_exists", "FAIL", result, is_critical=True)
        
        # Test MongoDB document data retrieval by checking if we get actual data
        logger.info("\n--- Testing MongoDB Document Data Retrieval ---")
        # This is tested through the /api/belge/list endpoint
        list_result = self.test_endpoint("GET", "/belge/list", headers=self.headers_admin)
        
        if list_result["accessible"] and list_result["status_code"] == 200:
            response_data = list_result.get("response_data", {})
            if isinstance(response_data, dict) and "documents" in response_data:
                documents = response_data["documents"]
            elif isinstance(response_data, list):
                documents = response_data
            else:
                documents = []
            
            if documents:
                # Check if documents have proper MongoDB structure
                sample_doc = documents[0]
                required_fields = ["id", "client_id", "document_name", "created_at"]
                has_required_fields = all(field in sample_doc for field in required_fields)
                
                if has_required_fields:
                    logger.info(f"✅ MongoDB Data Retrieval - SUCCESS: Documents have proper structure")
                    logger.info(f"   Sample document fields: {list(sample_doc.keys())}")
                    self.log_test_result("email_management", "mongodb_data_retrieval", "PASS", 
                                       {"documents_count": len(documents), "sample_fields": list(sample_doc.keys())})
                else:
                    logger.warning(f"⚠️ MongoDB Data Retrieval - INCOMPLETE: Missing required fields")
                    logger.info(f"   Sample document fields: {list(sample_doc.keys())}")
                    self.log_test_result("email_management", "mongodb_data_retrieval", "INCOMPLETE", 
                                       {"documents_count": len(documents), "sample_fields": list(sample_doc.keys())})
            else:
                logger.info(f"ℹ️ MongoDB Data Retrieval - NO DATA: No documents found")
                self.log_test_result("email_management", "mongodb_data_retrieval", "NO_DATA", {"documents_count": 0})
        else:
            logger.error(f"❌ MongoDB Data Retrieval - FAILED: Could not retrieve document list")
            self.log_test_result("email_management", "mongodb_data_retrieval", "FAIL", list_result, is_critical=True)
    
    def test_training_management(self):
        """Test EĞİTİM YÖNETİMİ endpoints"""
        logger.info("\n" + "="*60)
        logger.info("3. EĞİTİM YÖNETİMİ TESTİ (TRAINING MANAGEMENT)")
        logger.info("="*60)
        
        # Test GET /api/trainings (list trainings)
        logger.info("\n--- Testing GET /api/trainings (list trainings) ---")
        result = self.test_endpoint("GET", "/trainings", headers=self.headers_admin, expected_status=[200, 401, 403, 404])
        
        if result["accessible"]:
            if result["status_code"] == 200:
                trainings = result.get("response_data", [])
                logger.info(f"✅ GET /api/trainings - SUCCESS: Found {len(trainings)} trainings")
                if trainings:
                    logger.info(f"   Sample training: {trainings[0].get('name', 'Unknown')}")
                    # Store client IDs for filtering tests
                    training_client_ids = list(set([t.get('client_id') for t in trainings if t.get('client_id')]))
                    logger.info(f"   Training client IDs: {training_client_ids[:3]}...")
                self.log_test_result("training_management", "list_trainings", "PASS", result)
            elif result["status_code"] == 404:
                logger.warning(f"⚠️ GET /api/trainings - NOT FOUND: Endpoint may not be implemented")
                self.log_test_result("training_management", "list_trainings", "NOT_IMPLEMENTED", result)
            else:
                logger.info(f"⚠️ GET /api/trainings - AUTH REQUIRED: Status {result['status_code']}")
                self.log_test_result("training_management", "list_trainings", "AUTH_REQUIRED", result)
        else:
            logger.error(f"❌ GET /api/trainings - FAILED: {result.get('error')}")
            self.log_test_result("training_management", "list_trainings", "FAIL", result, is_critical=True)
        
        # Test GET /api/trainings?client_id={test_client_id} (client filtering)
        logger.info("\n--- Testing GET /api/trainings?client_id={test_client_id} (client filtering) ---")
        if self.test_client_ids:
            test_client_id = self.test_client_ids[0]
            result = self.test_endpoint("GET", "/trainings", headers=self.headers_admin, 
                                      params={"client_id": test_client_id}, expected_status=[200, 401, 403, 404])
            
            if result["accessible"]:
                if result["status_code"] == 200:
                    filtered_trainings = result.get("response_data", [])
                    logger.info(f"✅ GET /api/trainings?client_id={test_client_id} - SUCCESS: Found {len(filtered_trainings)} trainings")
                    
                    # Check if filtering actually works
                    if filtered_trainings:
                        all_same_client = all(t.get('client_id') == test_client_id for t in filtered_trainings)
                        if all_same_client:
                            logger.info(f"   ✅ FILTERING WORKS: All trainings belong to client {test_client_id}")
                            self.log_test_result("training_management", "client_filtering", "PASS", result)
                        else:
                            logger.warning(f"   ⚠️ FILTERING ISSUE: Some trainings don't belong to client {test_client_id}")
                            self.log_test_result("training_management", "client_filtering", "FILTERING_ISSUE", result, is_critical=True)
                    else:
                        logger.info(f"   ℹ️ No trainings found for client {test_client_id}")
                        self.log_test_result("training_management", "client_filtering", "NO_DATA", result)
                elif result["status_code"] == 404:
                    logger.warning(f"⚠️ GET /api/trainings with client_id - NOT FOUND: Endpoint may not be implemented")
                    self.log_test_result("training_management", "client_filtering", "NOT_IMPLEMENTED", result)
                else:
                    logger.info(f"⚠️ GET /api/trainings with client_id - AUTH REQUIRED: Status {result['status_code']}")
                    self.log_test_result("training_management", "client_filtering", "AUTH_REQUIRED", result)
            else:
                logger.error(f"❌ GET /api/trainings with client_id - FAILED: {result.get('error')}")
                self.log_test_result("training_management", "client_filtering", "FAIL", result, is_critical=True)
        else:
            logger.warning("⚠️ No client IDs available for training filtering test")
            self.log_test_result("training_management", "client_filtering", "SKIP", {"reason": "No client IDs"})
    
    def test_client_management(self):
        """Test CLIENT YÖNETİMİ endpoints"""
        logger.info("\n" + "="*60)
        logger.info("4. CLIENT YÖNETİMİ TESTİ (CLIENT MANAGEMENT)")
        logger.info("="*60)
        
        # Test GET /api/clients (client list)
        logger.info("\n--- Testing GET /api/clients (client list) ---")
        result = self.test_endpoint("GET", "/clients", headers=self.headers_admin, expected_status=[200, 401, 403])
        
        if result["accessible"]:
            if result["status_code"] == 200:
                clients = result.get("response_data", [])
                logger.info(f"✅ GET /api/clients - SUCCESS: Found {len(clients)} clients")
                if clients:
                    logger.info(f"   Sample client: {clients[0].get('name', 'Unknown')} - {clients[0].get('hotel_name', 'Unknown')}")
                    
                    # Validate Client IDs
                    logger.info("\n--- Validating Client IDs ---")
                    valid_ids = 0
                    invalid_ids = 0
                    
                    for client in clients[:5]:  # Check first 5 clients
                        client_id = client.get('id')
                        if client_id:
                            # Check if it's a valid UUID format
                            try:
                                uuid.UUID(client_id)
                                valid_ids += 1
                            except ValueError:
                                invalid_ids += 1
                                logger.warning(f"   ⚠️ Invalid UUID format: {client_id}")
                        else:
                            invalid_ids += 1
                            logger.warning(f"   ⚠️ Missing client ID for client: {client.get('name', 'Unknown')}")
                    
                    logger.info(f"   Client ID Validation: {valid_ids} valid, {invalid_ids} invalid")
                    
                    if invalid_ids == 0:
                        logger.info(f"   ✅ ALL CLIENT IDs ARE VALID")
                        self.log_test_result("client_management", "client_id_validation", "PASS", 
                                           {"valid_ids": valid_ids, "invalid_ids": invalid_ids})
                    else:
                        logger.warning(f"   ⚠️ SOME CLIENT IDs ARE INVALID")
                        self.log_test_result("client_management", "client_id_validation", "PARTIAL", 
                                           {"valid_ids": valid_ids, "invalid_ids": invalid_ids})
                
                self.log_test_result("client_management", "list_clients", "PASS", result)
            else:
                logger.info(f"⚠️ GET /api/clients - AUTH REQUIRED: Status {result['status_code']}")
                self.log_test_result("client_management", "list_clients", "AUTH_REQUIRED", result)
        else:
            logger.error(f"❌ GET /api/clients - FAILED: {result.get('error')}")
            self.log_test_result("client_management", "list_clients", "FAIL", result, is_critical=True)
    
    def test_authentication(self):
        """Test AUTHENTICATION scenarios"""
        logger.info("\n" + "="*60)
        logger.info("5. AUTHENTICATION TESTİ")
        logger.info("="*60)
        
        # Test endpoints that should work without authentication (NO AUTH)
        logger.info("\n--- Testing NO AUTH Endpoints ---")
        no_auth_endpoints = [
            ("/health", "GET"),
            ("/consultants", "GET"),
            ("/suppliers/categories/list", "GET"),
            ("/suppliers/certifications/list", "GET")
        ]
        
        no_auth_working = []
        no_auth_broken = []
        
        for endpoint, method in no_auth_endpoints:
            result = self.test_endpoint(method, endpoint, expected_status=[200, 404])
            
            if result["accessible"]:
                if result["status_code"] == 200:
                    logger.info(f"✅ {method} {endpoint} - NO AUTH WORKS")
                    no_auth_working.append(f"{method} {endpoint}")
                elif result["status_code"] == 404:
                    logger.warning(f"⚠️ {method} {endpoint} - NOT FOUND (may not be implemented)")
                    no_auth_broken.append(f"{method} {endpoint} (404)")
                else:
                    logger.warning(f"⚠️ {method} {endpoint} - Unexpected status: {result['status_code']}")
                    no_auth_broken.append(f"{method} {endpoint} ({result['status_code']})")
            else:
                logger.error(f"❌ {method} {endpoint} - FAILED: {result.get('error')}")
                no_auth_broken.append(f"{method} {endpoint} (error)")
        
        self.log_test_result("authentication", "no_auth_endpoints", "PASS" if no_auth_working else "FAIL", 
                           {"working": no_auth_working, "broken": no_auth_broken})
        
        # Test endpoints that should require authentication
        logger.info("\n--- Testing AUTH REQUIRED Endpoints ---")
        auth_required_endpoints = [
            ("/belge/list", "GET"),
            ("/clients", "GET"),
            ("/auth/me", "GET"),
            ("/sustainability-targets", "GET")
        ]
        
        auth_working = []
        auth_broken = []
        
        for endpoint, method in auth_required_endpoints:
            # Test without auth - should get 403 or 401
            result_no_auth = self.test_endpoint(method, endpoint, expected_status=[401, 403, 404])
            
            # Test with invalid auth - should get 401
            result_invalid_auth = self.test_endpoint(method, endpoint, headers=self.headers_invalid, expected_status=[401, 404])
            
            if result_no_auth["accessible"] and result_invalid_auth["accessible"]:
                if result_no_auth["status_code"] in [401, 403] and result_invalid_auth["status_code"] in [401, 404]:
                    logger.info(f"✅ {method} {endpoint} - AUTH REQUIRED WORKS (no auth: {result_no_auth['status_code']}, invalid: {result_invalid_auth['status_code']})")
                    auth_working.append(f"{method} {endpoint}")
                elif result_no_auth["status_code"] == 404:
                    logger.warning(f"⚠️ {method} {endpoint} - NOT FOUND (may not be implemented)")
                    auth_broken.append(f"{method} {endpoint} (404)")
                else:
                    logger.warning(f"⚠️ {method} {endpoint} - AUTH NOT ENFORCED (no auth: {result_no_auth['status_code']}, invalid: {result_invalid_auth['status_code']})")
                    auth_broken.append(f"{method} {endpoint} (not enforced)")
            else:
                logger.error(f"❌ {method} {endpoint} - FAILED to test auth")
                auth_broken.append(f"{method} {endpoint} (error)")
        
        self.log_test_result("authentication", "auth_required_endpoints", "PASS" if auth_working else "FAIL", 
                           {"working": auth_working, "broken": auth_broken})
        
        # Test JWT token validation with /api/auth/me
        logger.info("\n--- Testing JWT Token Validation ---")
        result = self.test_endpoint("GET", "/auth/me", headers=self.headers_admin, expected_status=[200, 401, 404])
        
        if result["accessible"]:
            if result["status_code"] == 200:
                user_data = result.get("response_data", {})
                logger.info(f"✅ JWT Token Validation - SUCCESS")
                logger.info(f"   User: {user_data.get('name', 'Unknown')} ({user_data.get('email', 'Unknown')})")
                logger.info(f"   Role: {user_data.get('role', 'Unknown')}")
                self.log_test_result("authentication", "jwt_validation", "PASS", result)
            elif result["status_code"] == 401:
                logger.warning(f"⚠️ JWT Token Validation - TOKEN INVALID/EXPIRED")
                self.log_test_result("authentication", "jwt_validation", "TOKEN_INVALID", result)
            elif result["status_code"] == 404:
                logger.warning(f"⚠️ JWT Token Validation - ENDPOINT NOT FOUND")
                self.log_test_result("authentication", "jwt_validation", "NOT_IMPLEMENTED", result)
            else:
                logger.warning(f"⚠️ JWT Token Validation - Unexpected status: {result['status_code']}")
                self.log_test_result("authentication", "jwt_validation", "UNKNOWN", result)
        else:
            logger.error(f"❌ JWT Token Validation - FAILED: {result.get('error')}")
            self.log_test_result("authentication", "jwt_validation", "FAIL", result, is_critical=True)
    
    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*80)
        logger.info("ROTA CRM RAILWAY BACKEND TEST RAPORU")
        logger.info("="*80)
        
        summary = self.test_results["summary"]
        
        logger.info(f"\n📊 GENEL ÖZET:")
        logger.info(f"   Toplam Test: {summary['total_tests']}")
        logger.info(f"   Başarılı: {summary['passed_tests']}")
        logger.info(f"   Başarısız: {summary['failed_tests']}")
        logger.info(f"   Başarı Oranı: {(summary['passed_tests']/summary['total_tests']*100):.1f}%" if summary['total_tests'] > 0 else "   Başarı Oranı: 0%")
        
        if summary['critical_issues']:
            logger.info(f"\n🚨 KRİTİK SORUNLAR ({len(summary['critical_issues'])}):")
            for issue in summary['critical_issues']:
                logger.info(f"   ❌ {issue}")
        
        if summary['working_endpoints']:
            logger.info(f"\n✅ ÇALIŞAN ENDPOINT'LER ({len(summary['working_endpoints'])}):")
            for endpoint in summary['working_endpoints']:
                logger.info(f"   ✅ {endpoint}")
        
        if summary['broken_endpoints']:
            logger.info(f"\n❌ ÇALIŞMAYAN ENDPOINT'LER ({len(summary['broken_endpoints'])}):")
            for endpoint in summary['broken_endpoints']:
                logger.info(f"   ❌ {endpoint}")
        
        # Detailed results by category
        categories = [
            ("consultant_management", "1. DANIŞMAN YÖNETİMİ"),
            ("email_management", "2. EMAIL YÖNETİMİ"),
            ("training_management", "3. EĞİTİM YÖNETİMİ"),
            ("client_management", "4. CLIENT YÖNETİMİ"),
            ("authentication", "5. AUTHENTICATION")
        ]
        
        for category_key, category_name in categories:
            category_results = self.test_results[category_key]
            if category_results:
                logger.info(f"\n📋 {category_name} DETAYLARI:")
                for test_name, test_result in category_results.items():
                    status_icon = "✅" if test_result["status"] == "PASS" else "❌" if test_result["status"] == "FAIL" else "⚠️"
                    logger.info(f"   {status_icon} {test_name}: {test_result['status']}")
                    if test_result.get("is_critical"):
                        logger.info(f"      🚨 KRİTİK SORUN")
        
        # Save detailed results to file
        try:
            with open('/app/railway_backend_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"\n💾 Detaylı test sonuçları kaydedildi: /app/railway_backend_test_results.json")
        except Exception as e:
            logger.error(f"❌ Test sonuçları kaydedilemedi: {str(e)}")
        
        return self.test_results
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        logger.info("🚀 ROTA CRM Railway Backend Comprehensive Test Starting...")
        logger.info(f"🎯 Target URL: {self.api_url}")
        logger.info(f"⏰ Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Run all test categories
            self.test_consultant_management()
            self.test_email_management()
            self.test_training_management()
            self.test_client_management()
            self.test_authentication()
            
            # Generate final report
            results = self.generate_report()
            
            logger.info("\n🎉 Test tamamlandı!")
            return results
            
        except Exception as e:
            logger.error(f"❌ Test sırasında hata oluştu: {str(e)}")
            raise

def main():
    """Main function to run the tests"""
    tester = RailwayBackendTester()
    results = tester.run_all_tests()
    
    # Return exit code based on critical issues
    if results["summary"]["critical_issues"]:
        logger.error(f"❌ Test failed with {len(results['summary']['critical_issues'])} critical issues")
        return 1
    else:
        logger.info("✅ Test completed successfully")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)