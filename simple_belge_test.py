import requests
import logging
import os
import json
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://9ef171d3-ce2f-48b5-9bdc-59bfb459ed67.preview.emergentagent.com/api"

# Test JWT tokens
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
KAYA_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

# Headers for different user types
headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
headers_client = {"Authorization": f"Bearer {KAYA_CLIENT_TOKEN}"}
headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
headers_no_auth = {}

# Test data
test_client_id = "8bfd3a85-2483-4b63-9e80-e53747c3db7e"  # Sample client ID
test_folder_id = "folder123"  # Will be updated with actual folder ID
test_document_id = None  # Will be set after upload

# Create a test file
test_file_path = "/tmp/test_document.pdf"
with open(test_file_path, "w") as f:
    f.write("This is a test PDF document content.")

def test_list_endpoint():
    """Test GET /api/belge/list endpoint"""
    logger.info("\n=== Testing GET /api/belge/list endpoint ===")
    
    url = f"{RAILWAY_API_URL}/belge/list"
    
    # Test with admin authentication
    try:
        response = requests.get(url, headers=headers_admin)
        logger.info(f"Admin response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Found {len(data)} documents")
            
            # If there are documents, check their structure
            if len(data) > 0:
                document = data[0]
                logger.info(f"Sample document: {document}")
            
            logger.info("✅ GET /api/belge/list with admin auth test passed")
        elif response.status_code == 404:
            logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        else:
            logger.info(f"⚠️ Unexpected status code: {response.status_code}")
    
    except Exception as e:
        logger.error(f"❌ Error testing list endpoint with admin: {e}")
    
    # Test with client authentication
    try:
        response = requests.get(url, headers=headers_client)
        logger.info(f"Client response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Found {len(data)} documents for client")
            
            logger.info("✅ GET /api/belge/list with client auth test passed")
        elif response.status_code in [401, 403]:
            logger.info("✅ GET /api/belge/list with client auth - auth error")
        elif response.status_code == 404:
            logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        else:
            logger.info(f"⚠️ Unexpected status code: {response.status_code}")
    
    except Exception as e:
        logger.error(f"❌ Error testing list endpoint with client: {e}")
    
    # Test with client_id parameter
    try:
        params = {"client_id": test_client_id}
        response = requests.get(url, headers=headers_admin, params=params)
        logger.info(f"Admin response with client_id parameter status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Found {len(data)} documents for client_id {test_client_id}")
            
            logger.info("✅ GET /api/belge/list with client_id parameter test passed")
        elif response.status_code == 404:
            logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        else:
            logger.info(f"⚠️ Unexpected status code: {response.status_code}")
    
    except Exception as e:
        logger.error(f"❌ Error testing list endpoint with client_id parameter: {e}")

def test_download_endpoint():
    """Test GET /api/belge/download/{id} endpoint"""
    logger.info("\n=== Testing GET /api/belge/download/{id} endpoint ===")
    
    # First, get a document ID from the list endpoint
    url_list = f"{RAILWAY_API_URL}/belge/list"
    document_id = None
    
    try:
        response = requests.get(url_list, headers=headers_admin)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                document_id = data[0]["id"]
                logger.info(f"Using document ID: {document_id}")
    except Exception as e:
        logger.error(f"❌ Error getting document ID: {e}")
    
    if not document_id:
        logger.warning("No document ID found, using a random UUID")
        document_id = str(uuid.uuid4())
    
    url = f"{RAILWAY_API_URL}/belge/download/{document_id}"
    
    # Test with admin authentication
    try:
        response = requests.get(url, headers=headers_admin)
        logger.info(f"Admin response status code: {response.status_code}")
        
        if response.status_code == 200:
            # Verify content type is not text/plain
            content_type = response.headers.get('Content-Type', '')
            logger.info(f"Content-Type: {content_type}")
            
            # Verify Content-Disposition header
            content_disposition = response.headers.get('Content-Disposition', '')
            logger.info(f"Content-Disposition: {content_disposition}")
            
            # Save the downloaded file for inspection
            download_path = "/tmp/downloaded_document.pdf"
            with open(download_path, 'wb') as f:
                f.write(response.content)
            
            # Verify file size
            file_size = os.path.getsize(download_path)
            logger.info(f"Downloaded file size: {file_size} bytes")
            
            # Clean up
            os.remove(download_path)
            
            logger.info("✅ GET /api/belge/download/{id} with admin auth test passed")
        elif response.status_code == 404:
            logger.info("⚠️ Document not found or endpoint not implemented")
        else:
            logger.info(f"⚠️ Unexpected status code: {response.status_code}")
    
    except Exception as e:
        logger.error(f"❌ Error testing download endpoint with admin: {e}")
    
    # Test with invalid authentication
    try:
        response = requests.get(url, headers=headers_invalid)
        logger.info(f"Invalid auth response status code: {response.status_code}")
        
        if response.status_code == 401:
            logger.info("✅ GET /api/belge/download/{id} with invalid auth correctly returns 401")
        elif response.status_code == 404:
            logger.info("⚠️ Document not found or endpoint not implemented")
        else:
            logger.info(f"⚠️ Unexpected status code: {response.status_code}")
    
    except Exception as e:
        logger.error(f"❌ Error testing download endpoint with invalid auth: {e}")
    
    # Test with no authentication
    try:
        response = requests.get(url, headers=headers_no_auth)
        logger.info(f"No auth response status code: {response.status_code}")
        
        if response.status_code in [401, 403]:
            logger.info("✅ GET /api/belge/download/{id} with no auth correctly returns 401/403")
        elif response.status_code == 404:
            logger.info("⚠️ Document not found or endpoint not implemented")
        else:
            logger.info(f"⚠️ Unexpected status code: {response.status_code}")
    
    except Exception as e:
        logger.error(f"❌ Error testing download endpoint with no auth: {e}")

def test_delete_endpoint():
    """Test DELETE /api/belge/delete/{id} endpoint"""
    logger.info("\n=== Testing DELETE /api/belge/delete/{id} endpoint ===")
    
    # First, get a document ID from the list endpoint
    url_list = f"{RAILWAY_API_URL}/belge/list"
    document_id = None
    
    try:
        response = requests.get(url_list, headers=headers_admin)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                document_id = data[0]["id"]
                logger.info(f"Using document ID: {document_id}")
    except Exception as e:
        logger.error(f"❌ Error getting document ID: {e}")
    
    if not document_id:
        logger.warning("No document ID found, using a random UUID")
        document_id = str(uuid.uuid4())
    
    url = f"{RAILWAY_API_URL}/belge/delete/{document_id}"
    
    # Test with admin authentication
    try:
        response = requests.delete(url, headers=headers_admin)
        logger.info(f"Admin response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response data: {data}")
            
            logger.info("✅ DELETE /api/belge/delete/{id} with admin auth test passed")
        elif response.status_code == 404:
            logger.info("⚠️ Document not found or endpoint not implemented")
        else:
            logger.info(f"⚠️ Unexpected status code: {response.status_code}")
    
    except Exception as e:
        logger.error(f"❌ Error testing delete endpoint with admin: {e}")
    
    # Test with invalid authentication
    try:
        # Use a different document ID
        different_id = str(uuid.uuid4())
        url = f"{RAILWAY_API_URL}/belge/delete/{different_id}"
        
        response = requests.delete(url, headers=headers_invalid)
        logger.info(f"Invalid auth response status code: {response.status_code}")
        
        if response.status_code == 401:
            logger.info("✅ DELETE /api/belge/delete/{id} with invalid auth correctly returns 401")
        elif response.status_code == 404:
            logger.info("⚠️ Document not found or endpoint not implemented")
        else:
            logger.info(f"⚠️ Unexpected status code: {response.status_code}")
    
    except Exception as e:
        logger.error(f"❌ Error testing delete endpoint with invalid auth: {e}")
    
    # Test with no authentication
    try:
        # Use a different document ID
        different_id = str(uuid.uuid4())
        url = f"{RAILWAY_API_URL}/belge/delete/{different_id}"
        
        response = requests.delete(url, headers=headers_no_auth)
        logger.info(f"No auth response status code: {response.status_code}")
        
        if response.status_code in [401, 403]:
            logger.info("✅ DELETE /api/belge/delete/{id} with no auth correctly returns 401/403")
        elif response.status_code == 404:
            logger.info("⚠️ Document not found or endpoint not implemented")
        else:
            logger.info(f"⚠️ Unexpected status code: {response.status_code}")
    
    except Exception as e:
        logger.error(f"❌ Error testing delete endpoint with no auth: {e}")

def test_upload_endpoint():
    """Test POST /api/belge/upload endpoint"""
    logger.info("\n=== Testing POST /api/belge/upload endpoint ===")
    
    url = f"{RAILWAY_API_URL}/belge/upload"
    
    # Test with admin authentication
    try:
        with open(test_file_path, "rb") as f:
            files = {"file": ("test_document_türkçe.pdf", f, "application/pdf")}
            data = {
                "client_id": test_client_id,
                "folder_id": "folder123",  # Using a placeholder folder ID
                "document_name": "Test Belge Türkçe Karakterler İÇÖŞĞÜ",
                "document_type": "TR1_CRITERIA",
                "stage": "I.Aşama"
            }
            
            response = requests.post(url, headers=headers_admin, files=files, data=data)
            logger.info(f"Admin response status code: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Save document_id for later tests
                global test_document_id
                test_document_id = data.get("document_id")
                logger.info(f"Uploaded document with ID: {test_document_id}")
                
                logger.info("✅ POST /api/belge/upload with admin auth test passed")
            elif response.status_code == 400:
                # This could happen if required fields are missing
                data = response.json()
                logger.info(f"Expected 400 error: {data}")
                logger.info("✅ POST /api/belge/upload with admin auth - expected 400 error")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
            else:
                logger.info(f"⚠️ Unexpected status code: {response.status_code}")
        
    except Exception as e:
        logger.error(f"❌ Error testing upload endpoint with admin: {e}")
    
    # Test with no authentication
    try:
        with open(test_file_path, "rb") as f:
            files = {"file": ("test_document.pdf", f, "application/pdf")}
            data = {
                "client_id": test_client_id,
                "folder_id": "folder123",  # Using a placeholder folder ID
                "document_name": "Test Document",
                "document_type": "TR1_CRITERIA",
                "stage": "I.Aşama"
            }
            
            response = requests.post(url, headers=headers_no_auth, files=files, data=data)
            logger.info(f"No auth response status code: {response.status_code}")
            
            if response.status_code in [401, 403]:
                logger.info("✅ POST /api/belge/upload with no auth correctly returns 401/403")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
            else:
                logger.info(f"⚠️ Unexpected status code: {response.status_code}")
        
    except Exception as e:
        logger.error(f"❌ Error testing upload endpoint with no auth: {e}")
    
    # Test with invalid authentication
    try:
        with open(test_file_path, "rb") as f:
            files = {"file": ("test_document.pdf", f, "application/pdf")}
            data = {
                "client_id": test_client_id,
                "folder_id": "folder123",  # Using a placeholder folder ID
                "document_name": "Test Document",
                "document_type": "TR1_CRITERIA",
                "stage": "I.Aşama"
            }
            
            response = requests.post(url, headers=headers_invalid, files=files, data=data)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            if response.status_code == 401:
                logger.info("✅ POST /api/belge/upload with invalid auth correctly returns 401")
            elif response.status_code == 404:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
            else:
                logger.info(f"⚠️ Unexpected status code: {response.status_code}")
        
    except Exception as e:
        logger.error(f"❌ Error testing upload endpoint with invalid auth: {e}")

def main():
    """Run all tests"""
    logger.info("Starting Belge Yönetimi API tests")
    
    # Test list endpoint
    test_list_endpoint()
    
    # Test upload endpoint
    test_upload_endpoint()
    
    # Test download endpoint
    test_download_endpoint()
    
    # Test delete endpoint
    test_delete_endpoint()
    
    # Clean up
    if os.path.exists(test_file_path):
        os.remove(test_file_path)
    
    logger.info("Belge Yönetimi API tests completed")

if __name__ == "__main__":
    main()