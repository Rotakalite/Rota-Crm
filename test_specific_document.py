import requests
import logging
import pymongo
from bson import ObjectId
import gridfs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API URL
API_URL = "https://7397d81a-245d-49b9-a61b-31977569672c.preview.emergentagent.com/api"

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "rotacrm"

# Test JWT token
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

# Headers for authentication
headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

# Connect to MongoDB
mongo_client = pymongo.MongoClient(MONGO_URL)
db = mongo_client[DB_NAME]
fs = gridfs.GridFS(db)

# Get a document with gridfs_id
doc = db.documents.find_one({"gridfs_id": {"$exists": True}})

if doc:
    document_id = doc.get("id")
    document_name = doc.get("name")
    gridfs_id = doc.get("gridfs_id")
    
    logger.info(f"Testing document download for document ID: {document_id}")
    logger.info(f"Document Name: {document_name}")
    logger.info(f"GridFS ID: {gridfs_id}")
    
    # Check if the file exists in GridFS
    try:
        file_id_obj = ObjectId(gridfs_id)
        exists = fs.exists(file_id_obj)
        logger.info(f"File exists in GridFS: {exists}")
        
        if exists:
            # Get the file from GridFS
            grid_file = fs.get(file_id_obj)
            
            # Check file metadata
            logger.info(f"GridFS file info: filename={grid_file.filename}, content_type={grid_file.content_type}, length={grid_file.length}")
            
            # Read the file content
            gridfs_content = grid_file.read()
            
            # Check if content is a PDF (starts with %PDF)
            is_pdf = gridfs_content.startswith(b"%PDF-")
            logger.info(f"Is PDF: {is_pdf}")
            
            # Check if content is text (contains placeholder text)
            is_placeholder = b"This is a placeholder document content" in gridfs_content
            logger.info(f"Is Placeholder: {is_placeholder}")
            
            # Download the document
            download_url = f"{API_URL}/documents/{document_id}/download"
            
            response = requests.get(download_url, headers=headers)
            logger.info(f"Download response status code: {response.status_code}")
            
            if response.status_code == 200:
                # Check content type
                content_type = response.headers.get("Content-Type")
                logger.info(f"Content-Type: {content_type}")
                
                # Check content disposition
                content_disposition = response.headers.get("Content-Disposition")
                logger.info(f"Content-Disposition: {content_disposition}")
                
                # Check content length
                content_length = response.headers.get("Content-Length")
                logger.info(f"Content-Length: {content_length}")
                
                # Get the content
                downloaded_content = response.content
                
                # Check if content is a PDF (starts with %PDF)
                is_pdf = downloaded_content.startswith(b"%PDF-")
                logger.info(f"Downloaded content is PDF: {is_pdf}")
                
                # Check if content is text (contains placeholder text)
                is_placeholder = b"This is a placeholder document content" in downloaded_content
                logger.info(f"Downloaded content is placeholder: {is_placeholder}")
                
                # Compare with GridFS content
                content_matches = gridfs_content == downloaded_content
                logger.info(f"GridFS content matches downloaded content: {content_matches}")
                
                # Print the first 50 bytes of both contents as hex
                logger.info(f"First 50 bytes of GridFS content: {gridfs_content[:50].hex()}")
                logger.info(f"First 50 bytes of downloaded content: {downloaded_content[:50].hex()}")
                
                if not content_matches:
                    logger.error("Content mismatch! The downloaded content does not match the GridFS content.")
                    
                    # Check if the downloaded content is a placeholder text
                    if is_placeholder:
                        logger.error("The downloaded content is a placeholder text, not the actual file content.")
                    
                    # Check if the downloaded content is a PDF
                    if not is_pdf and grid_file.content_type == "application/pdf":
                        logger.error("The downloaded content is not a PDF, but the GridFS file is a PDF.")
                    
                    # Check content lengths
                    logger.error(f"GridFS content length: {len(gridfs_content)}")
                    logger.error(f"Downloaded content length: {len(downloaded_content)}")
                else:
                    logger.info("Content match! The downloaded content matches the GridFS content.")
            else:
                logger.error(f"Download failed with status code: {response.status_code}")
                
                if response.status_code == 401:
                    logger.error("Authentication failed. The token may be invalid or expired.")
                elif response.status_code == 403:
                    logger.error("Access denied. The user may not have permission to access this document.")
                elif response.status_code == 404:
                    logger.error("Document not found. The document ID may be invalid.")
                else:
                    logger.error(f"Unexpected status code: {response.status_code}")
                    
                    # Try to parse the response content
                    try:
                        error_data = response.json()
                        logger.error(f"Error data: {error_data}")
                    except:
                        logger.error(f"Response content: {response.content}")
    except Exception as e:
        logger.error(f"Error checking GridFS or downloading document: {str(e)}")
else:
    logger.error("No documents with gridfs_id found in the database.")

# Close MongoDB connection
mongo_client.close()