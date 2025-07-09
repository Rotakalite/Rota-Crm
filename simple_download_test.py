import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API URL
API_URL = "https://539ffbd1-9de6-4314-8bdd-a94fe4106807.preview.emergentagent.com/api"

# Test JWT token
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

# Headers for authentication
headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

# Document ID to test
document_id = "75e917fb-97cc-466b-a370-66528f96631c"

# First, get the document list to verify the document exists
logger.info("Getting document list...")
list_url = f"{API_URL}/documents"
list_response = requests.get(list_url, headers=headers)
logger.info(f"Document list response status code: {list_response.status_code}")

if list_response.status_code == 200:
    documents = list_response.json()
    logger.info(f"Found {len(documents)} documents")
    
    # Find the document with the specified ID
    document = next((doc for doc in documents if doc["id"] == document_id), None)
    
    if document:
        logger.info(f"Found document: {document['title']}")
        
        # Download the document
        logger.info(f"Downloading document {document_id}...")
        download_url = f"{API_URL}/documents/{document_id}/download"
        download_response = requests.get(download_url, headers=headers)
        logger.info(f"Download response status code: {download_response.status_code}")
        
        if download_response.status_code == 200:
            # Check content type
            content_type = download_response.headers.get("Content-Type")
            logger.info(f"Content-Type: {content_type}")
            
            # Check content disposition
            content_disposition = download_response.headers.get("Content-Disposition")
            logger.info(f"Content-Disposition: {content_disposition}")
            
            # Check content length
            content_length = download_response.headers.get("Content-Length")
            logger.info(f"Content-Length: {content_length}")
            
            # Get the content
            content = download_response.content
            
            # Check if content is a PDF (starts with %PDF)
            is_pdf = content.startswith(b"%PDF-")
            logger.info(f"Is PDF: {is_pdf}")
            
            # Check if content is text (contains placeholder text)
            is_placeholder = b"This is a placeholder document content" in content
            logger.info(f"Is Placeholder: {is_placeholder}")
            
            # Print the first 50 bytes as hex
            logger.info(f"First 50 bytes: {content[:50].hex()}")
            
            # Save the content to a file
            with open("/tmp/downloaded_document.bin", "wb") as f:
                f.write(content)
            logger.info("Saved content to /tmp/downloaded_document.bin")
        else:
            logger.error(f"Download failed with status code: {download_response.status_code}")
            
            # Try to parse the response content
            try:
                error_data = download_response.json()
                logger.error(f"Error data: {error_data}")
            except:
                logger.error(f"Response content: {download_response.content}")
    else:
        logger.error(f"Document with ID {document_id} not found in the document list")
else:
    logger.error(f"Failed to get document list: {list_response.status_code}")
    
    # Try to parse the response content
    try:
        error_data = list_response.json()
        logger.error(f"Error data: {error_data}")
    except:
        logger.error(f"Response content: {list_response.content}")