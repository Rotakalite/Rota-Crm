import requests
import logging
import json
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from frontend/.env
BACKEND_URL = "https://1ec08c3c-6aac-4fbe-a51f-120fca82320d.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

def test_folders_endpoint_for_frontend():
    """Test if the folders endpoint is working for the frontend to populate the folder dropdown"""
    logger.info("\n=== Testing if the folders endpoint is working for the frontend ===")
    
    # Step 1: Check if the endpoint is accessible
    logger.info("Step 1: Checking if the endpoint is accessible...")
    url = f"{API_URL}/folders"
    
    try:
        response = requests.get(url)
        logger.info(f"Response status code: {response.status_code}")
        
        # Check if the endpoint is accessible
        if response.status_code in [200, 401, 403]:
            logger.info("✅ Folders endpoint is accessible")
            
            # Step 2: Check the response format
            logger.info("Step 2: Checking the response format...")
            
            try:
                error_data = response.json()
                logger.info("✅ Response is valid JSON")
                
                # If we got a 401/403, this is expected without authentication
                if response.status_code in [401, 403]:
                    logger.info("✅ Authentication is required (expected behavior)")
                    logger.info(f"Error message: {error_data.get('detail', 'No detail provided')}")
                    
                    # Step 3: Check the backend implementation
                    logger.info("Step 3: Checking the backend implementation...")
                    
                    # Read the server.py file
                    with open('/app/backend/server.py', 'r') as f:
                        server_code = f.read()
                    
                    # Check if the folders endpoint is implemented
                    if '@api_router.get("/folders")' in server_code:
                        logger.info("✅ GET /api/folders endpoint is implemented in the backend")
                        
                        # Check if the implementation looks correct
                        if 'async def get_folders(current_user: User = Depends(get_current_user)):' in server_code:
                            logger.info("✅ Folders endpoint requires authentication")
                            
                            if 'folders = await db.folders.find(' in server_code:
                                logger.info("✅ Folders endpoint queries the database")
                                
                                if 'return folders' in server_code:
                                    logger.info("✅ Folders endpoint returns the folders data")
                                    
                                    logger.info("✅ The folders endpoint is properly implemented and should work for the frontend when authenticated")
                                    return True
                                else:
                                    logger.error("❌ Folders endpoint may not return the folders data")
                            else:
                                logger.error("❌ Folders endpoint may not query the database")
                        else:
                            logger.error("❌ Folders endpoint may not require authentication")
                    else:
                        logger.error("❌ GET /api/folders endpoint is not implemented in the backend")
                        return False
                else:
                    # We got a 200 response, check the data structure
                    logger.info("✅ Folders endpoint returned data without authentication")
                    logger.info(f"Found {len(error_data)} folders")
                    
                    if len(error_data) > 0:
                        folder = error_data[0]
                        logger.info(f"Sample folder: {json.dumps(folder, indent=2)}")
                        
                        # Check if the data structure is correct for the frontend
                        required_fields = ["id", "client_id", "name", "level", "folder_path"]
                        missing_fields = [field for field in required_fields if field not in folder]
                        
                        if not missing_fields:
                            logger.info("✅ Folder data structure is correct for the frontend")
                            return True
                        else:
                            logger.error(f"❌ Folder data structure is missing fields: {missing_fields}")
                            return False
                    else:
                        logger.info("No folders found in the response (this may be expected in a new system)")
                        return True
            except:
                logger.error("❌ Response is not valid JSON")
                logger.info(f"Response body: {response.text[:500]}...")
                return False
        else:
            logger.error(f"❌ Folders endpoint returned unexpected status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:500]}...")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing folders endpoint: {str(e)}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting folder endpoint tests for frontend...")
    
    # Test folders endpoint for frontend
    frontend_result = test_folders_endpoint_for_frontend()
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Folders endpoint for frontend test: {'PASSED' if frontend_result else 'FAILED'}")
    
    # Return exit code based on test result
    return 0 if frontend_result else 1

if __name__ == "__main__":
    sys.exit(main())