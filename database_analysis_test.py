#!/usr/bin/env python3
"""
🔍 DATABASE ANALYSIS TEST - RAILWAY PRODUCTION
Analyze production database to verify folder and document counts for ZIP fix

Test Requirements:
1. Count total folders in production database
2. Count total documents in production database  
3. Verify client_id: 94927a77-edc3-45ec-8329-795feae35771 exists
4. Count folders for test client
5. Count documents for test client
6. Verify document query structure
"""

import os
import sys
import logging
from datetime import datetime
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB Configuration (from backend/.env)
MONGO_URL = "mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster"
DB_NAME = "rotacrm"
TEST_CLIENT_ID = "94927a77-edc3-45ec-8329-795feae35771"

class DatabaseAnalyzer:
    def __init__(self):
        self.mongo_url = MONGO_URL
        self.db_name = DB_NAME
        self.test_client_id = TEST_CLIENT_ID
        self.client = None
        self.db = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if details:
            logger.info(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def connect_to_database(self):
        """Test 1: Connect to production database"""
        try:
            self.client = MongoClient(self.mongo_url)
            self.db = self.client[self.db_name]
            
            # Test connection
            server_info = self.client.server_info()
            self.log_test("Database Connection", True, 
                        f"Connected to MongoDB {server_info.get('version', 'unknown')}")
            return True
        except Exception as e:
            self.log_test("Database Connection", False, str(e))
            return False
    
    def test_database_collections(self):
        """Test 2: Verify required collections exist"""
        try:
            collections = self.db.list_collection_names()
            required_collections = ["clients", "documents", "folders"]
            
            missing_collections = []
            for collection in required_collections:
                if collection not in collections:
                    missing_collections.append(collection)
            
            if not missing_collections:
                self.log_test("Database Collections", True, 
                            f"All required collections exist: {required_collections}")
                return True
            else:
                self.log_test("Database Collections", False, 
                            f"Missing collections: {missing_collections}")
                return False
        except Exception as e:
            self.log_test("Database Collections", False, str(e))
            return False
    
    def count_total_clients(self):
        """Test 3: Count total clients in database"""
        try:
            total_clients = self.db.clients.count_documents({})
            self.log_test("Total Clients Count", True, 
                        f"Found {total_clients} clients in database")
            return True
        except Exception as e:
            self.log_test("Total Clients Count", False, str(e))
            return False
    
    def count_total_folders(self):
        """Test 4: Count total folders in database"""
        try:
            total_folders = self.db.folders.count_documents({})
            self.log_test("Total Folders Count", True, 
                        f"Found {total_folders} folders in database")
            return True
        except Exception as e:
            self.log_test("Total Folders Count", False, str(e))
            return False
    
    def count_total_documents(self):
        """Test 5: Count total documents in database"""
        try:
            total_documents = self.db.documents.count_documents({})
            self.log_test("Total Documents Count", True, 
                        f"Found {total_documents} documents in database")
            return True
        except Exception as e:
            self.log_test("Total Documents Count", False, str(e))
            return False
    
    def verify_test_client_exists(self):
        """Test 6: Verify test client exists"""
        try:
            client = self.db.clients.find_one({"id": self.test_client_id})
            if client:
                client_name = client.get("hotel_name") or client.get("name", "Unknown")
                self.log_test("Test Client Exists", True, 
                            f"Client found: {client_name} (ID: {self.test_client_id})")
                return True
            else:
                self.log_test("Test Client Exists", False, 
                            f"Client not found: {self.test_client_id}")
                return False
        except Exception as e:
            self.log_test("Test Client Exists", False, str(e))
            return False
    
    def count_test_client_folders(self):
        """Test 7: Count folders for test client"""
        try:
            client_folders = self.db.folders.count_documents({"client_id": self.test_client_id})
            self.log_test("Test Client Folders", True, 
                        f"Found {client_folders} folders for test client")
            
            # Also get folder details
            if client_folders > 0:
                folders = list(self.db.folders.find({"client_id": self.test_client_id}, 
                                                  {"name": 1, "level": 1, "parent_folder_id": 1}))
                folder_names = [f["name"] for f in folders[:10]]  # First 10 folder names
                logger.info(f"   Sample folder names: {folder_names}")
            
            return True
        except Exception as e:
            self.log_test("Test Client Folders", False, str(e))
            return False
    
    def count_test_client_documents(self):
        """Test 8: Count documents for test client"""
        try:
            client_documents = self.db.documents.count_documents({"client_id": self.test_client_id})
            self.log_test("Test Client Documents", True, 
                        f"Found {client_documents} documents for test client")
            
            # Also get document details
            if client_documents > 0:
                documents = list(self.db.documents.find({"client_id": self.test_client_id}, 
                                                       {"name": 1, "original_filename": 1, "folder_id": 1}))
                doc_names = [d.get("original_filename", d.get("name", "Unknown")) for d in documents[:5]]
                logger.info(f"   Sample document names: {doc_names}")
            
            return True
        except Exception as e:
            self.log_test("Test Client Documents", False, str(e))
            return False
    
    def test_document_query_structure(self):
        """Test 9: Test document query structure for ZIP download"""
        try:
            # Test the exact query that would be used in ZIP download
            doc_query = {"client_id": self.test_client_id}
            documents = list(self.db.documents.find(doc_query))
            
            self.log_test("Document Query Structure", True, 
                        f"Query {doc_query} returned {len(documents)} documents")
            
            # Verify document structure
            if documents:
                sample_doc = documents[0]
                required_fields = ["id", "client_id", "name"]
                missing_fields = [field for field in required_fields if field not in sample_doc]
                
                if not missing_fields:
                    logger.info(f"   Document structure is valid")
                else:
                    logger.info(f"   Missing fields in documents: {missing_fields}")
            
            return True
        except Exception as e:
            self.log_test("Document Query Structure", False, str(e))
            return False
    
    def test_folder_hierarchy(self):
        """Test 10: Test folder hierarchy for test client"""
        try:
            folders = list(self.db.folders.find({"client_id": self.test_client_id}))
            
            # Count folders by level
            level_counts = {}
            for folder in folders:
                level = folder.get("level", 0)
                level_counts[level] = level_counts.get(level, 0) + 1
            
            self.log_test("Folder Hierarchy", True, 
                        f"Folder levels: {level_counts}")
            
            # Check for root folders (level 0)
            root_folders = [f for f in folders if f.get("level", 0) == 0]
            if root_folders:
                root_names = [f["name"] for f in root_folders[:5]]
                logger.info(f"   Root folders: {root_names}")
            
            return True
        except Exception as e:
            self.log_test("Folder Hierarchy", False, str(e))
            return False
    
    def test_document_folder_mapping(self):
        """Test 11: Test document to folder mapping"""
        try:
            # Get documents with folder_id
            documents_with_folders = list(self.db.documents.find({
                "client_id": self.test_client_id,
                "folder_id": {"$exists": True, "$ne": None}
            }))
            
            # Get documents without folder_id
            documents_without_folders = list(self.db.documents.find({
                "client_id": self.test_client_id,
                "$or": [
                    {"folder_id": {"$exists": False}},
                    {"folder_id": None},
                    {"folder_id": ""}
                ]
            }))
            
            self.log_test("Document Folder Mapping", True, 
                        f"Documents with folders: {len(documents_with_folders)}, "
                        f"without folders: {len(documents_without_folders)}")
            
            return True
        except Exception as e:
            self.log_test("Document Folder Mapping", False, str(e))
            return False
    
    def test_zip_download_simulation(self):
        """Test 12: Simulate ZIP download query"""
        try:
            # Simulate the exact process that happens in ZIP download
            
            # 1. Get client info
            client = self.db.clients.find_one({"id": self.test_client_id})
            if not client:
                self.log_test("ZIP Download Simulation", False, "Client not found")
                return False
            
            # 2. Build document query (NO folder filter)
            doc_query = {"client_id": self.test_client_id}
            documents = list(self.db.documents.find(doc_query))
            
            # 3. Get all folders for path reconstruction
            folders = list(self.db.folders.find({"client_id": self.test_client_id}))
            
            # 4. Create folder mapping
            folder_map = {f["id"]: f for f in folders}
            
            # 5. Count documents that would be included in ZIP
            valid_documents = 0
            for doc in documents:
                if doc.get("binary_storage") or doc.get("gridfs_id"):
                    valid_documents += 1
            
            self.log_test("ZIP Download Simulation", True, 
                        f"Would include {valid_documents}/{len(documents)} documents in ZIP, "
                        f"using {len(folders)} folders for structure")
            
            return True
        except Exception as e:
            self.log_test("ZIP Download Simulation", False, str(e))
            return False
    
    def analyze_client_types(self):
        """Test 13: Analyze client types in database"""
        try:
            # Count by client type
            registered_clients = self.db.clients.count_documents({"client_type": "registered"})
            bulk_clients = self.db.clients.count_documents({"client_type": "bulk"})
            no_type_clients = self.db.clients.count_documents({
                "$or": [
                    {"client_type": {"$exists": False}},
                    {"client_type": None},
                    {"client_type": ""}
                ]
            })
            
            # Check test client type
            test_client = self.db.clients.find_one({"id": self.test_client_id})
            test_client_type = test_client.get("client_type", "unknown") if test_client else "not found"
            
            self.log_test("Client Types Analysis", True, 
                        f"Registered: {registered_clients}, Bulk: {bulk_clients}, "
                        f"No type: {no_type_clients}, Test client type: {test_client_type}")
            
            return True
        except Exception as e:
            self.log_test("Client Types Analysis", False, str(e))
            return False
    
    def close_connection(self):
        """Close database connection"""
        if self.client:
            self.client.close()
    
    def run_all_tests(self):
        """Run all database analysis tests"""
        logger.info("🔍 STARTING DATABASE ANALYSIS - RAILWAY PRODUCTION")
        logger.info(f"🎯 Target Database: {self.db_name}")
        logger.info(f"🆔 Test Client ID: {self.test_client_id}")
        logger.info("=" * 80)
        
        # Run all tests
        test_methods = [
            self.connect_to_database,
            self.test_database_collections,
            self.count_total_clients,
            self.count_total_folders,
            self.count_total_documents,
            self.verify_test_client_exists,
            self.count_test_client_folders,
            self.count_test_client_documents,
            self.test_document_query_structure,
            self.test_folder_hierarchy,
            self.test_document_folder_mapping,
            self.test_zip_download_simulation,
            self.analyze_client_types
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            try:
                if test_method():
                    passed_tests += 1
            except Exception as e:
                logger.error(f"❌ Test method {test_method.__name__} failed: {str(e)}")
        
        # Close connection
        self.close_connection()
        
        # Generate final report
        logger.info("=" * 80)
        logger.info("📊 DATABASE ANALYSIS REPORT")
        logger.info("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        logger.info(f"🎯 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        if success_rate >= 90:
            logger.info("🎉 EXCELLENT: Database is properly configured for ZIP folder fix!")
        elif success_rate >= 75:
            logger.info("✅ GOOD: Database is mostly ready with minor issues")
        else:
            logger.info("❌ ISSUES: Database has problems that may affect ZIP functionality")
        
        logger.info(f"\n📋 Analysis completed at: {datetime.now().isoformat()}")
        
        return success_rate

def main():
    """Main test execution"""
    analyzer = DatabaseAnalyzer()
    success_rate = analyzer.run_all_tests()
    
    # Exit with appropriate code
    if success_rate >= 90:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Some issues found

if __name__ == "__main__":
    main()