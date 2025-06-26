#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta
import os
import sys
import time
import base64
import io
import tempfile

# Get the backend URL from the frontend/.env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1] + '/api'
            break

print(f"Using backend URL: {BACKEND_URL}")

# Test data - Turkish hotel information
test_client = {
    "name": "Akdeniz Turizm A.Ş.",
    "hotel_name": "Grand Antalya Resort & Spa",
    "contact_person": "Mehmet Yılmaz",
    "email": "myilmaz@grandantalya.com",
    "phone": "+90 242 123 4567",
    "address": "Lara Caddesi No:123, Antalya, Türkiye"
}

# Create a sample PDF content (base64 encoded)
def create_sample_pdf():
    # This is a minimal valid PDF file
    pdf_content = b'''%PDF-1.0
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
0000000000 65535 f
0000000010 00000 n
0000000053 00000 n
0000000102 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
178
%%EOF'''
    return pdf_content

class GCSIntegrationTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.client_id = None
        self.document_id = None
        self.download_url = None
        
        # For simplicity, we'll use the same headers for both admin and client
        # In a real scenario, these would be different tokens
        self.admin_headers = {"Authorization": "Bearer admin-test-token"}
        self.client_headers = {"Authorization": "Bearer client-test-token"}
        
        self.test_results = {
            "client_creation": {"status": "Not tested", "details": []},
            "file_upload": {"status": "Not tested", "details": []},
            "file_download": {"status": "Not tested", "details": []},
            "permissions": {"status": "Not tested", "details": []}
        }
    
    def run_all_tests(self):
        """Run all GCS integration tests in sequence"""
        print("Starting Google Cloud Storage integration tests...")
        
        # Step 1: Create a test client
        self.test_create_client()
        
        if self.client_id:
            # Step 2: Test file upload
            self.test_file_upload()
            
            # Step 3: Test file download
            if self.document_id:
                self.test_file_download()
            
            # Step 4: Test permissions
            self.test_permissions()
        
        # Print summary
        self.print_summary()
    
    def test_create_client(self):
        """Create a test client for document testing"""
        print("\n=== Step 1: Creating Test Client ===")
        
        try:
            response = requests.post(f"{self.base_url}/clients", json=test_client, headers=self.admin_headers)
            if response.status_code == 200:
                client_data = response.json()
                self.client_id = client_data["id"]
                print(f"✅ Successfully created client with ID: {self.client_id}")
                self.test_results["client_creation"]["status"] = "Success"
                self.test_results["client_creation"]["details"].append({
                    "endpoint": "POST /api/clients",
                    "status": "Success",
                    "response": client_data
                })
            else:
                print(f"❌ Failed to create client: {response.status_code} - {response.text}")
                self.test_results["client_creation"]["status"] = "Failed"
                self.test_results["client_creation"]["details"].append({
                    "endpoint": "POST /api/clients",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when creating client: {str(e)}")
            self.test_results["client_creation"]["status"] = "Error"
            self.test_results["client_creation"]["details"].append({
                "endpoint": "POST /api/clients",
                "status": "Error",
                "error": str(e)
            })
    
    def test_file_upload(self):
        """Test document file upload to Google Cloud Storage"""
        print("\n=== Step 2: Testing File Upload ===")
        
        try:
            # Create a sample PDF file
            pdf_content = create_sample_pdf()
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_file_path = temp_file.name
            
            # Prepare multipart form data
            files = {
                'file': ('sample_document.pdf', open(temp_file_path, 'rb'), 'application/pdf')
            }
            
            data = {
                'client_id': self.client_id,
                'document_name': 'Sürdürülebilir Turizm Sertifikası',
                'document_type': 'Türkiye Sürdürülebilir Turizm Programı Kriterleri (TR-I)',
                'stage': 'I.Aşama'
            }
            
            # Upload the file
            print("\nTesting POST /api/upload-document")
            response = requests.post(
                f"{self.base_url}/upload-document", 
                files=files,
                data=data,
                headers=self.admin_headers
            )
            
            # Clean up the temporary file
            os.unlink(temp_file_path)
            
            if response.status_code == 200:
                upload_result = response.json()
                self.document_id = upload_result["document_id"]
                print(f"✅ Successfully uploaded document with ID: {self.document_id}")
                print(f"   File URL: {upload_result.get('file_url', 'N/A')}")
                print(f"   File Size: {upload_result.get('file_size', 'N/A')} bytes")
                print(f"   Mock Upload: {upload_result.get('mock_upload', False)}")
                
                self.test_results["file_upload"]["status"] = "Success"
                self.test_results["file_upload"]["details"].append({
                    "endpoint": "POST /api/upload-document",
                    "status": "Success",
                    "response": upload_result
                })
            else:
                print(f"❌ Failed to upload document: {response.status_code} - {response.text}")
                self.test_results["file_upload"]["status"] = "Failed"
                self.test_results["file_upload"]["details"].append({
                    "endpoint": "POST /api/upload-document",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when uploading document: {str(e)}")
            self.test_results["file_upload"]["status"] = "Error"
            self.test_results["file_upload"]["details"].append({
                "endpoint": "POST /api/upload-document",
                "status": "Error",
                "error": str(e)
            })
    
    def test_file_download(self):
        """Test document file download from Google Cloud Storage"""
        print("\n=== Step 3: Testing File Download ===")
        
        try:
            print(f"\nTesting GET /api/documents/{self.document_id}/download")
            response = requests.get(
                f"{self.base_url}/documents/{self.document_id}/download", 
                headers=self.admin_headers
            )
            
            if response.status_code == 200:
                download_result = response.json()
                self.download_url = download_result["download_url"]
                print(f"✅ Successfully got download URL: {self.download_url}")
                print(f"   Filename: {download_result.get('filename', 'N/A')}")
                print(f"   File Size: {download_result.get('file_size', 'N/A')} bytes")
                print(f"   Document Type: {download_result.get('document_type', 'N/A')}")
                
                # Try to access the download URL
                if self.download_url and self.download_url != "#":
                    try:
                        download_response = requests.get(self.download_url)
                        if download_response.status_code == 200:
                            print(f"✅ Successfully accessed the download URL")
                            print(f"   Content length: {len(download_response.content)} bytes")
                        else:
                            print(f"⚠️ Download URL returned status code: {download_response.status_code}")
                    except Exception as e:
                        print(f"⚠️ Could not access download URL: {str(e)}")
                
                self.test_results["file_download"]["status"] = "Success"
                self.test_results["file_download"]["details"].append({
                    "endpoint": f"GET /api/documents/{self.document_id}/download",
                    "status": "Success",
                    "response": download_result
                })
            else:
                print(f"❌ Failed to get download URL: {response.status_code} - {response.text}")
                self.test_results["file_download"]["status"] = "Failed"
                self.test_results["file_download"]["details"].append({
                    "endpoint": f"GET /api/documents/{self.document_id}/download",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when getting download URL: {str(e)}")
            self.test_results["file_download"]["status"] = "Error"
            self.test_results["file_download"]["details"].append({
                "endpoint": f"GET /api/documents/{self.document_id}/download",
                "status": "Error",
                "error": str(e)
            })
    
    def test_permissions(self):
        """Test permissions for file operations"""
        print("\n=== Step 4: Testing Permissions ===")
        
        # Test 1: Client can access their own document
        print("\nTest 1: Client can access their own document")
        try:
            response = requests.get(
                f"{self.base_url}/documents/{self.document_id}/download", 
                headers=self.client_headers
            )
            
            if response.status_code == 200:
                print(f"✅ Client can access their own document")
                self.test_results["permissions"]["details"].append({
                    "test": "Client access to own document",
                    "status": "Success"
                })
            else:
                print(f"❌ Client cannot access their own document: {response.status_code} - {response.text}")
                self.test_results["permissions"]["details"].append({
                    "test": "Client access to own document",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when testing client access: {str(e)}")
            self.test_results["permissions"]["details"].append({
                "test": "Client access to own document",
                "status": "Error",
                "error": str(e)
            })
        
        # Test 2: Create another client and try to access first client's document
        print("\nTest 2: Client cannot access another client's document")
        try:
            # Create another client
            another_client = test_client.copy()
            another_client["name"] = "Ege Turizm Ltd."
            another_client["hotel_name"] = "Blue Paradise Bodrum"
            another_client["email"] = "info@blueparadise.com"
            
            response = requests.post(f"{self.base_url}/clients", json=another_client, headers=self.admin_headers)
            if response.status_code == 200:
                another_client_id = response.json()["id"]
                print(f"✅ Created another client with ID: {another_client_id}")
                
                # Try to access first client's document with second client's credentials
                # For simulation, we'll use a different header
                another_client_headers = {"Authorization": "Bearer another-client-token"}
                
                response = requests.get(
                    f"{self.base_url}/documents/{self.document_id}/download", 
                    headers=another_client_headers
                )
                
                if response.status_code == 403:  # Expecting access denied
                    print(f"✅ Second client correctly denied access to first client's document")
                    self.test_results["permissions"]["details"].append({
                        "test": "Client access to another client's document",
                        "status": "Success"
                    })
                else:
                    print(f"❌ Permission check failed: {response.status_code} - {response.text}")
                    self.test_results["permissions"]["details"].append({
                        "test": "Client access to another client's document",
                        "status": "Failed",
                        "error": f"Expected 403, got {response.status_code}"
                    })
            else:
                print(f"⚠️ Could not create second client for permission test: {response.status_code}")
                self.test_results["permissions"]["details"].append({
                    "test": "Client access to another client's document",
                    "status": "Skipped",
                    "reason": "Could not create second client"
                })
        except Exception as e:
            print(f"❌ Exception when testing cross-client access: {str(e)}")
            self.test_results["permissions"]["details"].append({
                "test": "Client access to another client's document",
                "status": "Error",
                "error": str(e)
            })
        
        # Set overall permissions test status
        success_count = sum(1 for detail in self.test_results["permissions"]["details"] if detail["status"] == "Success")
        total_count = len(self.test_results["permissions"]["details"])
        
        if success_count == total_count:
            self.test_results["permissions"]["status"] = "Success"
        elif success_count > 0:
            self.test_results["permissions"]["status"] = "Partial Success"
        else:
            self.test_results["permissions"]["status"] = "Failed"
    
    def print_summary(self):
        """Print a summary of all test results"""
        print("\n=== TEST SUMMARY ===")
        for category, result in self.test_results.items():
            status_symbol = "✅" if result["status"] == "Success" else "⚠️" if result["status"] == "Partial Success" else "❌"
            print(f"{status_symbol} {category.replace('_', ' ').title()}: {result['status']}")

if __name__ == "__main__":
    tester = GCSIntegrationTester(BACKEND_URL)
    tester.run_all_tests()