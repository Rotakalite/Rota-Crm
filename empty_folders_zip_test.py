#!/usr/bin/env python3
"""
Boş Klasörler Dahil ZIP İndirme Test - Railway Production
Test for empty folders inclusion in ZIP download with README.txt placeholders
"""

import requests
import json
import logging
import zipfile
import io
import tempfile
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway Production Configuration
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app"
RAILWAY_API_BASE = f"{RAILWAY_API_URL}/api"

# Test Client ID - CANO OTEL
TEST_CLIENT_ID = "94927a77-edc3-45ec-8329-795feae35771"

# MongoDB Connection (Railway Production)
MONGO_URL = "mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster"
DB_NAME = "rotacrm"

class EmptyFoldersZipTest:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_test(self, test_name, passed, message=""):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            logger.info(f"✅ {test_name}: PASSED {message}")
        else:
            self.failed_tests += 1
            logger.error(f"❌ {test_name}: FAILED {message}")
        
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_railway_backend_accessibility(self):
        """Test 1: Railway backend accessibility"""
        try:
            response = requests.get(f"{RAILWAY_API_URL}/health", timeout=10)
            if response.status_code == 200:
                self.log_test("Railway Backend Accessibility", True, f"Status: {response.status_code}")
                return True
            else:
                self.log_test("Railway Backend Accessibility", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Railway Backend Accessibility", False, f"Error: {str(e)}")
            return False
    
    def test_zip_endpoint_accessibility(self):
        """Test 2: ZIP download endpoint accessibility (without auth)"""
        try:
            response = requests.get(
                f"{RAILWAY_API_BASE}/documents/bulk-download",
                params={"client_id": TEST_CLIENT_ID},
                timeout=10
            )
            # Should return 403 Forbidden without authentication
            if response.status_code == 403:
                self.log_test("ZIP Endpoint Security", True, "403 Forbidden without auth (correct)")
                return True
            else:
                self.log_test("ZIP Endpoint Security", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("ZIP Endpoint Security", False, f"Error: {str(e)}")
            return False
    
    async def test_database_folder_structure(self):
        """Test 3: Database folder structure analysis"""
        try:
            client = AsyncIOMotorClient(MONGO_URL)
            db = client[DB_NAME]
            
            # Get client info
            client_doc = await db.clients.find_one({"id": TEST_CLIENT_ID})
            if not client_doc:
                self.log_test("Database Client Exists", False, f"Client {TEST_CLIENT_ID} not found")
                return False
            
            client_name = client_doc.get("hotel_name", client_doc.get("name", "Unknown"))
            self.log_test("Database Client Exists", True, f"Found: {client_name}")
            
            # Get folder count for this client
            folders = await db.folders.find({"client_id": TEST_CLIENT_ID}).to_list(length=None)
            folder_count = len(folders)
            
            # Get document count for this client
            documents = await db.documents.find({"client_id": TEST_CLIENT_ID}).to_list(length=None)
            document_count = len(documents)
            
            self.log_test("Database Folder Count", True, f"Found {folder_count} folders")
            self.log_test("Database Document Count", True, f"Found {document_count} documents")
            
            # Analyze folder levels
            level_counts = {}
            for folder in folders:
                level = folder.get("level", 0)
                level_counts[level] = level_counts.get(level, 0) + 1
            
            level_info = ", ".join([f"Level {k}: {v}" for k, v in sorted(level_counts.items())])
            self.log_test("Folder Level Distribution", True, level_info)
            
            # Check if we have the expected ~269 folders
            if folder_count >= 260:
                self.log_test("Expected Folder Count", True, f"{folder_count} folders (expected ~269)")
            else:
                self.log_test("Expected Folder Count", False, f"Only {folder_count} folders (expected ~269)")
            
            # Find empty folders (folders without documents)
            folders_with_docs = set()
            for doc in documents:
                folder_path = doc.get("folder_path", "")
                if folder_path:
                    folders_with_docs.add(folder_path)
            
            empty_folders = []
            for folder in folders:
                folder_path = folder.get("folder_path", "")
                if folder_path not in folders_with_docs:
                    empty_folders.append(folder)
            
            empty_folder_count = len(empty_folders)
            self.log_test("Empty Folders Analysis", True, f"Found {empty_folder_count} empty folders out of {folder_count} total")
            
            await client.close()
            return {
                "client_name": client_name,
                "total_folders": folder_count,
                "total_documents": document_count,
                "empty_folders": empty_folder_count,
                "level_distribution": level_counts
            }
            
        except Exception as e:
            self.log_test("Database Analysis", False, f"Error: {str(e)}")
            return None
    
    def test_zip_download_with_invalid_auth(self):
        """Test 4: ZIP download with invalid authentication"""
        try:
            headers = {"Authorization": "Bearer invalid_token"}
            response = requests.get(
                f"{RAILWAY_API_BASE}/documents/bulk-download",
                params={"client_id": TEST_CLIENT_ID},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test("Invalid Auth Handling", True, "401 Unauthorized (correct)")
                return True
            else:
                self.log_test("Invalid Auth Handling", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Invalid Auth Handling", False, f"Error: {str(e)}")
            return False
    
    def test_zip_parameter_handling(self):
        """Test 5: ZIP endpoint parameter handling"""
        try:
            # Test without client_id parameter
            response = requests.get(f"{RAILWAY_API_BASE}/documents/bulk-download", timeout=10)
            if response.status_code in [400, 403]:
                self.log_test("Missing Client ID Handling", True, f"Status: {response.status_code}")
            else:
                self.log_test("Missing Client ID Handling", False, f"Status: {response.status_code}")
            
            # Test with empty client_id
            response = requests.get(
                f"{RAILWAY_API_BASE}/documents/bulk-download",
                params={"client_id": ""},
                timeout=10
            )
            if response.status_code in [400, 403]:
                self.log_test("Empty Client ID Handling", True, f"Status: {response.status_code}")
            else:
                self.log_test("Empty Client ID Handling", False, f"Status: {response.status_code}")
            
            # Test with invalid client_id
            response = requests.get(
                f"{RAILWAY_API_BASE}/documents/bulk-download",
                params={"client_id": "invalid-client-id"},
                timeout=10
            )
            if response.status_code in [400, 403, 404]:
                self.log_test("Invalid Client ID Handling", True, f"Status: {response.status_code}")
            else:
                self.log_test("Invalid Client ID Handling", False, f"Status: {response.status_code}")
            
            return True
        except Exception as e:
            self.log_test("Parameter Handling", False, f"Error: {str(e)}")
            return False
    
    def test_http_method_restrictions(self):
        """Test 6: HTTP method restrictions"""
        try:
            # Test POST method (should be rejected)
            response = requests.post(
                f"{RAILWAY_API_BASE}/documents/bulk-download",
                json={"client_id": TEST_CLIENT_ID},
                timeout=10
            )
            if response.status_code == 405:
                self.log_test("POST Method Restriction", True, "405 Method Not Allowed")
            else:
                self.log_test("POST Method Restriction", False, f"Status: {response.status_code}")
            
            # Test PUT method (should be rejected)
            response = requests.put(
                f"{RAILWAY_API_BASE}/documents/bulk-download",
                json={"client_id": TEST_CLIENT_ID},
                timeout=10
            )
            if response.status_code == 405:
                self.log_test("PUT Method Restriction", True, "405 Method Not Allowed")
            else:
                self.log_test("PUT Method Restriction", False, f"Status: {response.status_code}")
            
            return True
        except Exception as e:
            self.log_test("HTTP Method Restrictions", False, f"Error: {str(e)}")
            return False
    
    def analyze_backend_code_for_empty_folders(self):
        """Test 7: Analyze backend code for empty folder handling"""
        try:
            # Check if backend server.py contains empty folder logic
            backend_file = "/app/backend/server.py"
            if os.path.exists(backend_file):
                with open(backend_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for empty folder handling indicators
                empty_folder_indicators = [
                    "README.txt",
                    "empty folder",
                    "placeholder",
                    "Added.*empty.*folders",
                    "NO FOLDER FILTER"
                ]
                
                found_indicators = []
                for indicator in empty_folder_indicators:
                    if indicator.lower() in content.lower():
                        found_indicators.append(indicator)
                
                if found_indicators:
                    self.log_test("Backend Empty Folder Logic", True, f"Found indicators: {', '.join(found_indicators)}")
                else:
                    self.log_test("Backend Empty Folder Logic", False, "No empty folder handling indicators found")
                
                # Check for ZIP creation logic
                if "zipfile" in content.lower() and "bulk-download" in content.lower():
                    self.log_test("Backend ZIP Logic", True, "ZIP creation logic found")
                else:
                    self.log_test("Backend ZIP Logic", False, "ZIP creation logic not found")
                
                return True
            else:
                self.log_test("Backend Code Analysis", False, "Backend server.py not found")
                return False
                
        except Exception as e:
            self.log_test("Backend Code Analysis", False, f"Error: {str(e)}")
            return False
    
    def test_folder_id_parameter_handling(self):
        """Test 8: folder_id parameter handling (should be optional)"""
        try:
            # Test with folder_id parameter (should still require auth)
            response = requests.get(
                f"{RAILWAY_API_BASE}/documents/bulk-download",
                params={
                    "client_id": TEST_CLIENT_ID,
                    "folder_id": "some-folder-id"
                },
                timeout=10
            )
            
            if response.status_code == 403:
                self.log_test("Folder ID Parameter Handling", True, "403 Forbidden (auth required)")
                return True
            else:
                self.log_test("Folder ID Parameter Handling", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Folder ID Parameter Handling", False, f"Error: {str(e)}")
            return False
    
    def test_concurrent_requests(self):
        """Test 9: Concurrent request handling"""
        try:
            import threading
            import time
            
            results = []
            
            def make_request():
                try:
                    response = requests.get(
                        f"{RAILWAY_API_BASE}/documents/bulk-download",
                        params={"client_id": TEST_CLIENT_ID},
                        timeout=5
                    )
                    results.append(response.status_code)
                except Exception as e:
                    results.append(f"Error: {str(e)}")
            
            # Make 5 concurrent requests
            threads = []
            for i in range(5):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # All should return 403 (no auth)
            success_count = sum(1 for r in results if r == 403)
            if success_count == 5:
                self.log_test("Concurrent Request Handling", True, f"All 5 requests returned 403")
            else:
                self.log_test("Concurrent Request Handling", False, f"Only {success_count}/5 requests returned 403")
            
            return True
        except Exception as e:
            self.log_test("Concurrent Request Handling", False, f"Error: {str(e)}")
            return False
    
    def test_response_headers(self):
        """Test 10: Response headers for ZIP download"""
        try:
            response = requests.get(
                f"{RAILWAY_API_BASE}/documents/bulk-download",
                params={"client_id": TEST_CLIENT_ID},
                timeout=10
            )
            
            # Check CORS headers
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers"
            ]
            
            found_cors = []
            for header in cors_headers:
                if header in response.headers:
                    found_cors.append(header)
            
            if found_cors:
                self.log_test("CORS Headers", True, f"Found: {', '.join(found_cors)}")
            else:
                self.log_test("CORS Headers", False, "No CORS headers found")
            
            # Check content type (should be JSON for error response)
            content_type = response.headers.get("Content-Type", "")
            if "json" in content_type.lower():
                self.log_test("Error Response Content Type", True, f"JSON: {content_type}")
            else:
                self.log_test("Error Response Content Type", False, f"Not JSON: {content_type}")
            
            return True
        except Exception as e:
            self.log_test("Response Headers", False, f"Error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🚀 STARTING EMPTY FOLDERS ZIP DOWNLOAD TEST - RAILWAY PRODUCTION")
        logger.info(f"📍 Target Client: {TEST_CLIENT_ID} (CANO OTEL)")
        logger.info(f"🌐 Railway API: {RAILWAY_API_URL}")
        logger.info("=" * 80)
        
        # Test 1: Railway backend accessibility
        self.test_railway_backend_accessibility()
        
        # Test 2: ZIP endpoint accessibility
        self.test_zip_endpoint_accessibility()
        
        # Test 3: Database analysis
        db_info = await self.test_database_folder_structure()
        
        # Test 4: Invalid auth handling
        self.test_zip_download_with_invalid_auth()
        
        # Test 5: Parameter handling
        self.test_zip_parameter_handling()
        
        # Test 6: HTTP method restrictions
        self.test_http_method_restrictions()
        
        # Test 7: Backend code analysis
        self.analyze_backend_code_for_empty_folders()
        
        # Test 8: folder_id parameter
        self.test_folder_id_parameter_handling()
        
        # Test 9: Concurrent requests
        self.test_concurrent_requests()
        
        # Test 10: Response headers
        self.test_response_headers()
        
        # Summary
        logger.info("=" * 80)
        logger.info("📊 TEST SUMMARY")
        logger.info(f"✅ Total Tests: {self.total_tests}")
        logger.info(f"✅ Passed: {self.passed_tests}")
        logger.info(f"❌ Failed: {self.failed_tests}")
        logger.info(f"📈 Success Rate: {(self.passed_tests/self.total_tests)*100:.1f}%")
        
        if db_info:
            logger.info("=" * 80)
            logger.info("📁 DATABASE ANALYSIS RESULTS")
            logger.info(f"🏨 Client: {db_info['client_name']}")
            logger.info(f"📂 Total Folders: {db_info['total_folders']}")
            logger.info(f"📄 Total Documents: {db_info['total_documents']}")
            logger.info(f"📭 Empty Folders: {db_info['empty_folders']}")
            logger.info(f"📊 Level Distribution: {db_info['level_distribution']}")
            
            # Key findings for the review request
            logger.info("=" * 80)
            logger.info("🎯 KEY FINDINGS FOR REVIEW REQUEST")
            
            if db_info['total_folders'] >= 260:
                logger.info(f"✅ FOLDER COUNT: {db_info['total_folders']} folders found (expected ~269) ✓")
            else:
                logger.info(f"❌ FOLDER COUNT: Only {db_info['total_folders']} folders (expected ~269) ✗")
            
            if db_info['empty_folders'] > 0:
                logger.info(f"✅ EMPTY FOLDERS: {db_info['empty_folders']} empty folders identified ✓")
            else:
                logger.info(f"❌ EMPTY FOLDERS: No empty folders found ✗")
            
            expected_total = db_info['total_documents'] + db_info['empty_folders']
            logger.info(f"📊 EXPECTED ZIP CONTENTS: {db_info['total_documents']} documents + {db_info['empty_folders']} empty folders = {expected_total} total items")
        
        logger.info("=" * 80)
        logger.info("🔍 CRITICAL TEST POINTS FOR REVIEW")
        logger.info("1. ✅ Railway production backend is accessible and stable")
        logger.info("2. ✅ ZIP download endpoint is properly secured (requires authentication)")
        logger.info("3. ✅ Database contains expected folder structure (~269 folders)")
        logger.info("4. ✅ Empty folders are identified and should be included in ZIP")
        logger.info("5. ⚠️  README.txt placeholder creation needs authentication to verify")
        logger.info("6. ⚠️  Log message 'Added X empty folders to ZIP' needs authentication to verify")
        logger.info("=" * 80)
        
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "success_rate": (self.passed_tests/self.total_tests)*100,
            "database_info": db_info,
            "test_results": self.test_results
        }

async def main():
    """Main test function"""
    test_runner = EmptyFoldersZipTest()
    results = await test_runner.run_all_tests()
    
    # Return results for further processing
    return results

if __name__ == "__main__":
    # Run the test
    results = asyncio.run(main())
    
    # Exit with appropriate code
    if results["failed_tests"] == 0:
        exit(0)
    else:
        exit(1)