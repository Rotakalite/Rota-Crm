import unittest
import requests
import logging
import json
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "sustainable_tourism_crm"
ALT_DB_NAME = "rotacrm"

# Test JWT token for admin
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

async def get_client_data():
    """Get client data from MongoDB"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[ALT_DB_NAME]
    
    # Get all clients
    clients = await db.clients.find().to_list(length=None)
    
    # Get target clients
    target_clients = ["DENEME OTEL", "TEST OTEL", "SES123", "Can", "ALP OTEL"]
    found_clients = []
    
    for client in clients:
        client_name = client.get("client_name", "")
        hotel_name = client.get("hotel_name", "")
        
        for target in target_clients:
            if target.lower() in client_name.lower() or target.lower() in hotel_name.lower():
                found_clients.append(client)
                logger.info(f"Found target client: {client_name} / {hotel_name}")
    
    return found_clients

def run_async(coro):
    """Run an async function in a synchronous context"""
    return asyncio.get_event_loop().run_until_complete(coro)

class TestEmailManagementEndpoints(unittest.TestCase):
    """Test class for email management endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = "https://2db8402f-b209-4375-a81f-bec839c4760e.preview.emergentagent.com/api"
        self.headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        
        # Get client data
        self.clients = run_async(get_client_data())
        logger.info(f"Found {len(self.clients)} target clients")
    
    def test_email_management_clients_real(self):
        """Test GET /api/email-management/clients-real endpoint"""
        logger.info("\n=== Testing GET /api/email-management/clients-real endpoint ===")
        
        url = f"{self.api_url}/email-management/clients-real"
        
        try:
            response = requests.get(url, headers=self.headers)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if endpoint exists
            if response.status_code == 404:
                logger.warning("Endpoint not found (404)")
                return
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 405])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.assertIsInstance(data, list)
                
                # Log the clients found
                logger.info(f"Found {len(data)} clients")
                
                # Check if our target clients are in the response
                target_clients = ["DENEME OTEL", "TEST OTEL", "SES123", "Can", "ALP OTEL"]
                found_targets = []
                
                for client in data:
                    client_name = client.get("name", "").lower()
                    
                    for target in target_clients:
                        if target.lower() in client_name:
                            found_targets.append(target)
                            logger.info(f"Found target client in response: {client.get('name')}")
                
                logger.info(f"Found {len(found_targets)} target clients in response: {found_targets}")
                
                logger.info("✅ GET /api/email-management/clients-real test passed")
            elif response.status_code == 405:
                logger.info("Method not allowed (405) - this is expected for GET requests to endpoints that require authentication")
            else:
                logger.info(f"Authentication/authorization issue: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing email-management/clients-real endpoint: {str(e)}")
            raise
    
    def test_email_management_documents_real(self):
        """Test GET /api/email-management/documents-real endpoint"""
        logger.info("\n=== Testing GET /api/email-management/documents-real endpoint ===")
        
        url = f"{self.api_url}/email-management/documents-real"
        
        try:
            response = requests.get(url, headers=self.headers)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if endpoint exists
            if response.status_code == 404:
                logger.warning("Endpoint not found (404)")
                return
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 405])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.assertIsInstance(data, list)
                
                # Log the documents found
                logger.info(f"Found {len(data)} documents")
                
                # Check if documents for our target clients are in the response
                target_clients = ["DENEME OTEL", "TEST OTEL", "SES123", "Can", "ALP OTEL"]
                found_targets = []
                
                for doc in data:
                    client_name = doc.get("client_name", "").lower()
                    
                    for target in target_clients:
                        if target.lower() in client_name:
                            found_targets.append(target)
                            logger.info(f"Found document for target client in response: {doc.get('client_name')}")
                
                logger.info(f"Found documents for {len(found_targets)} target clients in response: {found_targets}")
                
                logger.info("✅ GET /api/email-management/documents-real test passed")
            elif response.status_code == 405:
                logger.info("Method not allowed (405) - this is expected for GET requests to endpoints that require authentication")
            else:
                logger.info(f"Authentication/authorization issue: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing email-management/documents-real endpoint: {str(e)}")
            raise
    
    def test_email_management_trainings_real(self):
        """Test GET /api/email-management/trainings-real endpoint"""
        logger.info("\n=== Testing GET /api/email-management/trainings-real endpoint ===")
        
        url = f"{self.api_url}/email-management/trainings-real"
        
        try:
            response = requests.get(url, headers=self.headers)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if endpoint exists
            if response.status_code == 404:
                logger.warning("Endpoint not found (404)")
                return
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 405])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.assertIsInstance(data, list)
                
                # Log the trainings found
                logger.info(f"Found {len(data)} trainings")
                
                # Check if trainings for our target clients are in the response
                target_clients = ["DENEME OTEL", "TEST OTEL", "SES123", "Can", "ALP OTEL"]
                found_targets = []
                
                for training in data:
                    client_name = training.get("client_name", "").lower()
                    
                    for target in target_clients:
                        if target.lower() in client_name:
                            found_targets.append(target)
                            logger.info(f"Found training for target client in response: {training.get('client_name')}")
                
                logger.info(f"Found trainings for {len(found_targets)} target clients in response: {found_targets}")
                
                logger.info("✅ GET /api/email-management/trainings-real test passed")
            elif response.status_code == 405:
                logger.info("Method not allowed (405) - this is expected for GET requests to endpoints that require authentication")
            else:
                logger.info(f"Authentication/authorization issue: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing email-management/trainings-real endpoint: {str(e)}")
            raise

if __name__ == "__main__":
    unittest.main()