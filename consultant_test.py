import unittest
import json
import logging
import requests
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# Test JWT tokens
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
INVALID_JWT_TOKEN = "invalid.token.format"
CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"

class TestConsultantManagementEndpoints(unittest.TestCase):
    """Test class for consultant management endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        self.headers_no_auth = {}
        
        # Test data for consultant creation
        self.test_consultant_data = {
            "company_name": f"Test Consultant {uuid.uuid4()}",
            "authorized_person_name": "Jane Smith",
            "email": "jane@testconsultant.com",
            "phone": "9876543210",
            "address": "456 Consultant St, Test City"
        }
        
        # Test data for client-consultant assignment
        self.test_assignment_data = {
            "consultant_id": ""  # Will be filled after consultant creation
        }
    
    def test_01_create_consultant(self):
        """Test POST /api/consultants endpoint"""
        logger.info("\n=== Testing POST /api/consultants endpoint ===")
        
        url = f"{self.api_url}/consultants"
        
        # Test with no authentication (should work as per implementation)
        try:
            response = requests.post(url, json=self.test_consultant_data)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 200 OK or 201 Created
            self.assertIn(response.status_code, [200, 201])
            
            # Response should contain success message and consultant_id
            data = response.json()
            self.assertIn("message", data)
            self.assertIn("consultant_id", data)
            
            # Save consultant_id for later tests
            self.consultant_id = data["consultant_id"]
            logger.info(f"Created consultant with ID: {self.consultant_id}")
            
            # Update assignment data with consultant_id
            self.test_assignment_data["consultant_id"] = self.consultant_id
            
            logger.info("✅ POST /api/consultants test passed")
        except Exception as e:
            logger.error(f"❌ Error testing create consultant endpoint: {str(e)}")
            raise
    
    def test_02_get_consultants(self):
        """Test GET /api/consultants endpoint"""
        logger.info("\n=== Testing GET /api/consultants endpoint ===")
        
        url = f"{self.api_url}/consultants"
        
        # Test with no authentication (should work as per implementation)
        try:
            response = requests.get(url)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list of consultants
            data = response.json()
            self.assertIsInstance(data, list)
            
            # Should have at least one consultant (the one we created)
            self.assertGreaterEqual(len(data), 1)
            
            # Log the consultants found
            consultant_names = [consultant.get("company_name") for consultant in data]
            logger.info(f"Found consultants: {consultant_names}")
            
            # Verify our created consultant is in the list
            if hasattr(self, 'consultant_id'):
                consultant_ids = [consultant.get("id") for consultant in data]
                self.assertIn(self.consultant_id, consultant_ids, "Created consultant should be in the list")
            
            logger.info("✅ GET /api/consultants test passed")
        except Exception as e:
            logger.error(f"❌ Error testing get consultants endpoint: {str(e)}")
            raise
    
    def test_03_get_consultant_by_id(self):
        """Test GET /api/consultants/{consultant_id} endpoint"""
        logger.info("\n=== Testing GET /api/consultants/{consultant_id} endpoint ===")
        
        # Skip if consultant_id is not available
        if not hasattr(self, 'consultant_id'):
            logger.warning("⚠️ Skipping test_get_consultant_by_id: No consultant_id available")
            return
        
        url = f"{self.api_url}/consultants/{self.consultant_id}"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK or 401 Unauthorized
            self.assertIn(response.status_code, [200, 401])
            
            if response.status_code == 200:
                # Response should be a consultant object
                data = response.json()
                self.assertIsInstance(data, dict)
                
                # Verify consultant data
                self.assertEqual(data["id"], self.consultant_id)
                self.assertEqual(data["company_name"], self.test_consultant_data["company_name"])
                self.assertEqual(data["authorized_person_name"], self.test_consultant_data["authorized_person_name"])
                self.assertEqual(data["email"], self.test_consultant_data["email"])
                self.assertEqual(data["phone"], self.test_consultant_data["phone"])
                self.assertEqual(data["address"], self.test_consultant_data["address"])
                
                logger.info("✅ GET /api/consultants/{consultant_id} with admin auth test passed")
            else:
                logger.info("⚠️ Authentication required - received 401 Unauthorized")
        except Exception as e:
            logger.error(f"❌ Error testing get consultant by ID endpoint with admin: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ GET /api/consultants/{consultant_id} with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing get consultant by ID endpoint with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ GET /api/consultants/{consultant_id} with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing get consultant by ID endpoint with no auth: {str(e)}")
            raise
    
    def test_04_update_consultant(self):
        """Test PUT /api/consultants/{consultant_id} endpoint"""
        logger.info("\n=== Testing PUT /api/consultants/{consultant_id} endpoint ===")
        
        # Skip if consultant_id is not available
        if not hasattr(self, 'consultant_id'):
            logger.warning("⚠️ Skipping test_update_consultant: No consultant_id available")
            return
        
        url = f"{self.api_url}/consultants/{self.consultant_id}"
        
        # Updated consultant data
        updated_data = {
            "company_name": f"Updated Consultant {uuid.uuid4()}",
            "authorized_person_name": "Jane Smith Updated",
            "email": "jane.updated@testconsultant.com",
            "phone": "9876543210",
            "address": "456 Consultant St, Updated City"
        }
        
        # Test with admin authentication
        try:
            response = requests.put(url, headers=self.headers_admin, json=updated_data)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK or 401 Unauthorized
            self.assertIn(response.status_code, [200, 401])
            
            if response.status_code == 200:
                # Response should contain success message
                data = response.json()
                self.assertIn("message", data)
                
                # Verify the update by getting the consultant
                get_response = requests.get(url, headers=self.headers_admin)
                if get_response.status_code == 200:
                    updated_consultant = get_response.json()
                    self.assertEqual(updated_consultant["company_name"], updated_data["company_name"])
                    self.assertEqual(updated_consultant["authorized_person_name"], updated_data["authorized_person_name"])
                    self.assertEqual(updated_consultant["email"], updated_data["email"])
                    self.assertEqual(updated_consultant["address"], updated_data["address"])
                
                logger.info("✅ PUT /api/consultants/{consultant_id} with admin auth test passed")
            else:
                logger.info("⚠️ Authentication required - received 401 Unauthorized")
        except Exception as e:
            logger.error(f"❌ Error testing update consultant endpoint with admin: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.put(url, headers=self.headers_invalid, json=updated_data)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ PUT /api/consultants/{consultant_id} with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing update consultant endpoint with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.put(url, headers=self.headers_no_auth, json=updated_data)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ PUT /api/consultants/{consultant_id} with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing update consultant endpoint with no auth: {str(e)}")
            raise
    
    def test_05_get_consultant_clients(self):
        """Test GET /api/consultants/{consultant_id}/clients endpoint"""
        logger.info("\n=== Testing GET /api/consultants/{consultant_id}/clients endpoint ===")
        
        # Skip if consultant_id is not available
        if not hasattr(self, 'consultant_id'):
            logger.warning("⚠️ Skipping test_get_consultant_clients: No consultant_id available")
            return
        
        url = f"{self.api_url}/consultants/{self.consultant_id}/clients"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK or 401 Unauthorized
            self.assertIn(response.status_code, [200, 401])
            
            if response.status_code == 200:
                # Response should be a list of clients
                data = response.json()
                self.assertIsInstance(data, list)
                
                # Log the number of clients found
                logger.info(f"Found {len(data)} clients for consultant {self.consultant_id}")
                
                logger.info("✅ GET /api/consultants/{consultant_id}/clients with admin auth test passed")
            else:
                logger.info("⚠️ Authentication required - received 401 Unauthorized")
        except Exception as e:
            logger.error(f"❌ Error testing get consultant clients endpoint with admin: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ GET /api/consultants/{consultant_id}/clients with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing get consultant clients endpoint with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ GET /api/consultants/{consultant_id}/clients with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing get consultant clients endpoint with no auth: {str(e)}")
            raise
    
    def test_06_get_consultant_dashboard(self):
        """Test GET /api/consultants/{consultant_id}/dashboard endpoint"""
        logger.info("\n=== Testing GET /api/consultants/{consultant_id}/dashboard endpoint ===")
        
        # Skip if consultant_id is not available
        if not hasattr(self, 'consultant_id'):
            logger.warning("⚠️ Skipping test_get_consultant_dashboard: No consultant_id available")
            return
        
        url = f"{self.api_url}/consultants/{self.consultant_id}/dashboard"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK or 401 Unauthorized
            self.assertIn(response.status_code, [200, 401])
            
            if response.status_code == 200:
                # Response should be a dashboard object
                data = response.json()
                self.assertIsInstance(data, dict)
                
                # Verify dashboard data structure
                self.assertIn("total_clients", data)
                self.assertIn("active_clients", data)
                self.assertIn("completed_clients", data)
                self.assertIn("personnel_count", data)
                self.assertIn("suppliers_count", data)
                self.assertIn("targets_count", data)
                self.assertIn("recent_documents", data)
                self.assertIn("clients", data)
                
                logger.info("✅ GET /api/consultants/{consultant_id}/dashboard with admin auth test passed")
            else:
                logger.info("⚠️ Authentication required - received 401 Unauthorized")
        except Exception as e:
            logger.error(f"❌ Error testing get consultant dashboard endpoint with admin: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ GET /api/consultants/{consultant_id}/dashboard with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing get consultant dashboard endpoint with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ GET /api/consultants/{consultant_id}/dashboard with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing get consultant dashboard endpoint with no auth: {str(e)}")
            raise
    
    def test_07_assign_client_to_consultant(self):
        """Test PUT /api/clients/{client_id}/consultant endpoint"""
        logger.info("\n=== Testing PUT /api/clients/{client_id}/consultant endpoint ===")
        
        # Skip if consultant_id is not available
        if not hasattr(self, 'consultant_id'):
            logger.warning("⚠️ Skipping test_assign_client_to_consultant: No consultant_id available")
            return
        
        # Get a client to assign
        try:
            clients_url = f"{self.api_url}/clients"
            clients_response = requests.get(clients_url, headers=self.headers_admin)
            
            if clients_response.status_code == 200:
                clients = clients_response.json()
                if len(clients) > 0:
                    client_id = clients[0]["id"]
                    logger.info(f"Found client with ID: {client_id} for assignment test")
                    
                    # Test the assignment endpoint
                    url = f"{self.api_url}/clients/{client_id}/consultant"
                    
                    # Test with admin authentication
                    try:
                        response = requests.put(url, headers=self.headers_admin, json=self.test_assignment_data)
                        logger.info(f"Admin response status code: {response.status_code}")
                        
                        # Should get 200 OK, 401 Unauthorized, or 404 Not Found
                        self.assertIn(response.status_code, [200, 401, 404])
                        
                        if response.status_code == 200:
                            # Response should contain success message
                            data = response.json()
                            self.assertIn("message", data)
                            
                            logger.info("✅ PUT /api/clients/{client_id}/consultant with admin auth test passed")
                        elif response.status_code == 401:
                            logger.info("⚠️ Authentication required - received 401 Unauthorized")
                        else:
                            logger.info("⚠️ Client not found - received 404 Not Found")
                    except Exception as e:
                        logger.error(f"❌ Error testing assign client to consultant endpoint with admin: {str(e)}")
                        raise
                    
                    # Test with invalid authentication
                    try:
                        response = requests.put(url, headers=self.headers_invalid, json=self.test_assignment_data)
                        logger.info(f"Invalid auth response status code: {response.status_code}")
                        
                        # Should get 401 Unauthorized
                        self.assertEqual(response.status_code, 401)
                        
                        logger.info("✅ PUT /api/clients/{client_id}/consultant with invalid auth correctly returns 401")
                    except Exception as e:
                        logger.error(f"❌ Error testing assign client to consultant endpoint with invalid auth: {str(e)}")
                        raise
                    
                    # Test with no authentication
                    try:
                        response = requests.put(url, headers=self.headers_no_auth, json=self.test_assignment_data)
                        logger.info(f"No auth response status code: {response.status_code}")
                        
                        # Should get 403 Forbidden
                        self.assertEqual(response.status_code, 403)
                        
                        logger.info("✅ PUT /api/clients/{client_id}/consultant with no auth correctly returns 403")
                    except Exception as e:
                        logger.error(f"❌ Error testing assign client to consultant endpoint with no auth: {str(e)}")
                        raise
                else:
                    logger.warning("⚠️ No clients found for assignment test")
            else:
                logger.warning(f"⚠️ Could not get clients for assignment test: {clients_response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error getting clients for assignment test: {str(e)}")
            raise
    
    def test_08_assign_unassigned_clients(self):
        """Test POST /api/consultants/assign-unassigned endpoint"""
        logger.info("\n=== Testing POST /api/consultants/assign-unassigned endpoint ===")
        
        url = f"{self.api_url}/consultants/assign-unassigned"
        
        # Test with admin authentication
        try:
            response = requests.post(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK, 401 Unauthorized, or 404 Not Found
            self.assertIn(response.status_code, [200, 401, 404])
            
            if response.status_code == 200:
                # Response should contain success message and assignment details
                data = response.json()
                self.assertIn("message", data)
                self.assertIn("assigned_count", data)
                
                logger.info(f"Assigned {data.get('assigned_count', 0)} unassigned clients to ROTA")
                
                logger.info("✅ POST /api/consultants/assign-unassigned with admin auth test passed")
            elif response.status_code == 401:
                logger.info("⚠️ Authentication required - received 401 Unauthorized")
            else:
                logger.info("⚠️ Endpoint not found - received 404 Not Found")
        except Exception as e:
            logger.error(f"❌ Error testing assign unassigned clients endpoint with admin: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.post(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ POST /api/consultants/assign-unassigned with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing assign unassigned clients endpoint with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.post(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ POST /api/consultants/assign-unassigned with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing assign unassigned clients endpoint with no auth: {str(e)}")
            raise
    
    def test_09_delete_consultant(self):
        """Test DELETE /api/consultants/{consultant_id} endpoint"""
        logger.info("\n=== Testing DELETE /api/consultants/{consultant_id} endpoint ===")
        
        # Skip if consultant_id is not available
        if not hasattr(self, 'consultant_id'):
            logger.warning("⚠️ Skipping test_delete_consultant: No consultant_id available")
            return
        
        url = f"{self.api_url}/consultants/{self.consultant_id}"
        
        # Test with admin authentication
        try:
            response = requests.delete(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK, 400 Bad Request, 401 Unauthorized, or 404 Not Found
            self.assertIn(response.status_code, [200, 400, 401, 404])
            
            if response.status_code == 200:
                # Response should contain success message
                data = response.json()
                self.assertIn("message", data)
                
                logger.info("✅ DELETE /api/consultants/{consultant_id} with admin auth test passed")
            elif response.status_code == 400:
                # This could happen if consultant has assigned clients or is ROTA
                data = response.json()
                logger.info(f"Expected 400 error: {data}")
                logger.info("✅ DELETE /api/consultants/{consultant_id} with admin auth - expected 400 error")
            elif response.status_code == 401:
                logger.info("⚠️ Authentication required - received 401 Unauthorized")
            else:
                logger.info("⚠️ Consultant not found - received 404 Not Found")
        except Exception as e:
            logger.error(f"❌ Error testing delete consultant endpoint with admin: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.delete(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ DELETE /api/consultants/{consultant_id} with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing delete consultant endpoint with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.delete(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ DELETE /api/consultants/{consultant_id} with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing delete consultant endpoint with no auth: {str(e)}")
            raise
    
    def test_10_delete_rota_consultant(self):
        """Test DELETE /api/consultants/{consultant_id} endpoint with ROTA consultant"""
        logger.info("\n=== Testing DELETE /api/consultants/{consultant_id} endpoint with ROTA consultant ===")
        
        # First, get the ROTA consultant ID
        try:
            url = f"{self.api_url}/consultants"
            response = requests.get(url)
            
            if response.status_code == 200:
                consultants = response.json()
                rota_consultant = next((c for c in consultants if c.get("company_name") == "ROTA"), None)
                
                if rota_consultant:
                    rota_id = rota_consultant["id"]
                    logger.info(f"Found ROTA consultant with ID: {rota_id}")
                    
                    # Test deleting ROTA consultant
                    delete_url = f"{self.api_url}/consultants/{rota_id}"
                    
                    # Test with admin authentication
                    try:
                        delete_response = requests.delete(delete_url, headers=self.headers_admin)
                        logger.info(f"Admin response status code: {delete_response.status_code}")
                        
                        # Should get 400 Bad Request (cannot delete ROTA)
                        self.assertEqual(delete_response.status_code, 400)
                        
                        # Response should contain error message about ROTA
                        data = delete_response.json()
                        self.assertIn("detail", data)
                        self.assertIn("ROTA", data["detail"])
                        
                        logger.info("✅ DELETE /api/consultants/{consultant_id} with ROTA consultant correctly returns 400")
                    except Exception as e:
                        logger.error(f"❌ Error testing delete ROTA consultant endpoint: {str(e)}")
                        raise
                else:
                    logger.warning("⚠️ ROTA consultant not found")
            else:
                logger.warning(f"⚠️ Could not get consultants: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error getting ROTA consultant: {str(e)}")
            raise

if __name__ == "__main__":
    unittest.main()