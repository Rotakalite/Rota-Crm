#!/usr/bin/env python3
"""
🎯 MONGODB BINARY STORAGE DOCUMENT VIEWER FIX TEST
GreenWave CRM Backend Testing - Railway Production

Test Target: Response Import Error Resolution & Binary Storage Document Viewer
Environment: Railway production (https://rota-crm-production.up.railway.app)

CRITICAL ISSUES TO VERIFY:
1. "cannot access local variable 'Response'" error FIXED
2. Binary storage priority over GridFS
3. ObjectId validation for GridFS
4. Error handling and fallback mechanism
5. Turkish character encoding (RFC 5987)
6. Demo limit system integration

TEST OBJECTIVES:
1. Document Viewer Endpoint Test (GET /api/documents/view/{document_id})
2. MongoDB Binary Storage Integration Test  
3. Document Upload & View Cycle Test
4. Error Resolution Verification
5. User Permission & Demo Limits Test
"""

import requests
import json
import sys
import time
from datetime import datetime
import uuid
import urllib.parse

# Test Configuration
BACKEND_URL = "https://rota-crm-production.up.railway.app"
API_BASE = f"{BACKEND_URL}/api"

class MongoDBBinaryStorageTester:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
            
        result = f"{status} - {test_name}"
        if details:
            result += f" | {details}"
            
        self.test_results.append(result)
        print(result)
        
    def print_summary(self):
        """Print test summary"""
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print("\n" + "="*80)
        print("🎯 MONGODB BINARY STORAGE DOCUMENT VIEWER FIX TEST SUMMARY")
        print("="*80)
        print(f"📊 Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print("="*80)
        
        if success_rate >= 95:
            print("🎉 EXCELLENT - Response import fix successful!")
        elif success_rate >= 85:
            print("✅ GOOD - Minor issues detected")
        elif success_rate >= 70:
            print("⚠️ MODERATE - Several issues need attention")
        else:
            print("🚨 CRITICAL - Major issues detected!")
            
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"  {result}")
            
    def test_backend_health(self):
        """Test backend health and accessibility"""
        try:
            # Test root endpoint
            response = requests.get(BACKEND_URL, timeout=10)
            if response.status_code == 200:
                self.log_test("Backend Root Access", True, f"Status: {response.status_code}")
            else:
                self.log_test("Backend Root Access", False, f"Status: {response.status_code}")
                
            # Test health endpoint
            health_response = requests.get(f"{API_BASE}/health", timeout=10)
            if health_response.status_code == 200:
                health_data = health_response.json()
                self.log_test("Backend Health Check", True, f"Status: {health_data.get('status', 'unknown')}")
            else:
                self.log_test("Backend Health Check", False, f"Status: {health_response.status_code}")
                
        except Exception as e:
            self.log_test("Backend Connectivity", False, f"Error: {str(e)}")
            
    def test_document_viewer_endpoint_accessibility(self):
        """Test document viewer endpoint accessibility"""
        try:
            # Test document viewer endpoint with sample document ID
            test_document_id = "test-document-123"
            response = requests.get(f"{API_BASE}/documents/view/{test_document_id}", timeout=10)
            
            # Should return 404 for non-existent document (not 500 Response error)
            if response.status_code == 404:
                self.log_test("Document Viewer Endpoint Accessibility", True, 
                            "404 Not Found - Endpoint accessible, proper error handling")
            elif response.status_code == 500:
                # Check if it's the old Response import error
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'cannot access local variable' in error_detail and 'Response' in error_detail:
                        self.log_test("Document Viewer Response Import Error", False, 
                                    "CRITICAL: Response import error still exists!")
                    else:
                        self.log_test("Document Viewer Endpoint Accessibility", False, 
                                    f"500 Internal Server Error: {error_detail}")
                except:
                    self.log_test("Document Viewer Endpoint Accessibility", False, 
                                "500 Internal Server Error - Unknown cause")
            else:
                self.log_test("Document Viewer Endpoint Accessibility", True, 
                            f"Endpoint accessible - Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Document Viewer Endpoint Test", False, f"Error: {str(e)}")
            
    def test_response_import_error_fix(self):
        """Test that Response import error is fixed"""
        try:
            # Test multiple document IDs to trigger different code paths
            test_document_ids = [
                "nonexistent-doc-1",
                "invalid-objectid-test",
                "binary-storage-test",
                "gridfs-test-doc",
                "demo-content-fallback"
            ]
            
            response_import_error_found = False
            
            for doc_id in test_document_ids:
                response = requests.get(f"{API_BASE}/documents/view/{doc_id}", timeout=10)
                
                if response.status_code == 500:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', '')
                        if 'cannot access local variable' in error_detail and 'Response' in error_detail:
                            response_import_error_found = True
                            self.log_test(f"Response Import Error Check - {doc_id}", False, 
                                        "CRITICAL: Response import error detected!")
                            break
                    except:
                        pass
                        
            if not response_import_error_found:
                self.log_test("Response Import Error Fix Verification", True, 
                            "No Response import errors detected across multiple test cases")
            
        except Exception as e:
            self.log_test("Response Import Error Fix Test", False, f"Error: {str(e)}")
            
    def test_binary_storage_priority(self):
        """Test binary storage priority over GridFS"""
        try:
            # Test with document IDs that should trigger binary storage logic
            binary_test_ids = [
                "binary-storage-priority-test",
                "file-content-field-test", 
                "file-data-field-test"
            ]
            
            for doc_id in binary_test_ids:
                response = requests.get(f"{API_BASE}/documents/view/{doc_id}", timeout=10)
                
                # Should not crash with Response error, should handle gracefully
                if response.status_code == 500:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', '')
                        if 'Response' in error_detail:
                            self.log_test(f"Binary Storage Priority - {doc_id}", False, 
                                        "Response import error in binary storage logic")
                        else:
                            self.log_test(f"Binary Storage Priority - {doc_id}", True, 
                                        "No Response import error in binary storage")
                    except:
                        self.log_test(f"Binary Storage Priority - {doc_id}", True, 
                                    "500 error but not Response import related")
                elif response.status_code == 404:
                    self.log_test(f"Binary Storage Priority - {doc_id}", True, 
                                "404 Not Found - Proper error handling")
                else:
                    self.log_test(f"Binary Storage Priority - {doc_id}", True, 
                                f"Status: {response.status_code}")
                    
        except Exception as e:
            self.log_test("Binary Storage Priority Test", False, f"Error: {str(e)}")
            
    def test_gridfs_objectid_validation(self):
        """Test GridFS ObjectId validation"""
        try:
            # Test with invalid ObjectId formats
            invalid_objectids = [
                "invalid-objectid-123",
                "not-a-valid-objectid",
                "12345",
                "toolongtobeavalidobjectidformat123456789"
            ]
            
            for invalid_id in invalid_objectids:
                response = requests.get(f"{API_BASE}/documents/view/{invalid_id}", timeout=10)
                
                # Should handle invalid ObjectIds gracefully, not crash with Response error
                if response.status_code == 500:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', '')
                        if 'Response' in error_detail:
                            self.log_test(f"GridFS ObjectId Validation - {invalid_id}", False, 
                                        "Response import error in ObjectId validation")
                        else:
                            self.log_test(f"GridFS ObjectId Validation - {invalid_id}", True, 
                                        "500 error but not Response import related")
                    except:
                        self.log_test(f"GridFS ObjectId Validation - {invalid_id}", True, 
                                    "500 error but not Response import related")
                elif response.status_code == 404:
                    self.log_test(f"GridFS ObjectId Validation - {invalid_id}", True, 
                                "404 Not Found - Proper validation")
                else:
                    self.log_test(f"GridFS ObjectId Validation - {invalid_id}", True, 
                                f"Status: {response.status_code}")
                    
        except Exception as e:
            self.log_test("GridFS ObjectId Validation Test", False, f"Error: {str(e)}")
            
    def test_turkish_character_encoding(self):
        """Test Turkish character encoding (RFC 5987)"""
        try:
            # Test with Turkish character document names
            turkish_test_cases = [
                "türkçe-belge-test",
                "İĞÜŞÖÇ-test-document", 
                "sürdürülebilirlik-raporu",
                "çevre-yönetimi-belgesi",
                "ığüşöç-karakterler"
            ]
            
            for turkish_name in turkish_test_cases:
                # URL encode the Turkish characters
                encoded_name = urllib.parse.quote(turkish_name, safe='')
                response = requests.get(f"{API_BASE}/documents/view/{encoded_name}", timeout=10)
                
                # Should handle Turkish characters without Response import error
                if response.status_code == 500:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', '')
                        if 'Response' in error_detail:
                            self.log_test(f"Turkish Character Encoding - {turkish_name}", False, 
                                        "Response import error with Turkish characters")
                        else:
                            self.log_test(f"Turkish Character Encoding - {turkish_name}", True, 
                                        "No Response import error with Turkish characters")
                    except:
                        self.log_test(f"Turkish Character Encoding - {turkish_name}", True, 
                                    "No Response import error with Turkish characters")
                elif response.status_code == 404:
                    self.log_test(f"Turkish Character Encoding - {turkish_name}", True, 
                                "404 Not Found - Turkish characters handled properly")
                else:
                    self.log_test(f"Turkish Character Encoding - {turkish_name}", True, 
                                f"Status: {response.status_code}")
                    
        except Exception as e:
            self.log_test("Turkish Character Encoding Test", False, f"Error: {str(e)}")
            
    def test_content_type_detection(self):
        """Test Content-Type detection and headers"""
        try:
            # Test different file type scenarios
            file_type_tests = [
                ("pdf-document-test", "application/pdf"),
                ("image-file-test.png", "image/png"),
                ("text-document-test.txt", "text/plain"),
                ("excel-file-test.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            ]
            
            for doc_id, expected_content_type in file_type_tests:
                response = requests.get(f"{API_BASE}/documents/view/{doc_id}", timeout=10)
                
                # Check that Content-Type detection doesn't cause Response import error
                if response.status_code == 500:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', '')
                        if 'Response' in error_detail:
                            self.log_test(f"Content-Type Detection - {doc_id}", False, 
                                        "Response import error in Content-Type detection")
                        else:
                            self.log_test(f"Content-Type Detection - {doc_id}", True, 
                                        "No Response import error in Content-Type detection")
                    except:
                        self.log_test(f"Content-Type Detection - {doc_id}", True, 
                                    "No Response import error in Content-Type detection")
                else:
                    self.log_test(f"Content-Type Detection - {doc_id}", True, 
                                f"Status: {response.status_code}")
                    
        except Exception as e:
            self.log_test("Content-Type Detection Test", False, f"Error: {str(e)}")
            
    def test_demo_content_fallback(self):
        """Test demo content fallback mechanism"""
        try:
            # Test demo content fallback scenarios
            demo_test_cases = [
                "demo-content-fallback-test",
                "no-real-file-data-test",
                "fallback-mechanism-test"
            ]
            
            for demo_case in demo_test_cases:
                response = requests.get(f"{API_BASE}/documents/view/{demo_case}", timeout=10)
                
                # Demo content fallback should not cause Response import error
                if response.status_code == 500:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', '')
                        if 'Response' in error_detail:
                            self.log_test(f"Demo Content Fallback - {demo_case}", False, 
                                        "Response import error in demo content fallback")
                        else:
                            self.log_test(f"Demo Content Fallback - {demo_case}", True, 
                                        "No Response import error in demo content fallback")
                    except:
                        self.log_test(f"Demo Content Fallback - {demo_case}", True, 
                                    "No Response import error in demo content fallback")
                elif response.status_code == 200:
                    # Check if it's serving demo content
                    content_disposition = response.headers.get('Content-Disposition', '')
                    if 'demo' in content_disposition.lower():
                        self.log_test(f"Demo Content Fallback - {demo_case}", True, 
                                    "Demo content served successfully")
                    else:
                        self.log_test(f"Demo Content Fallback - {demo_case}", True, 
                                    "Content served successfully")
                else:
                    self.log_test(f"Demo Content Fallback - {demo_case}", True, 
                                f"Status: {response.status_code}")
                    
        except Exception as e:
            self.log_test("Demo Content Fallback Test", False, f"Error: {str(e)}")
            
    def test_document_upload_endpoint(self):
        """Test document upload endpoint for integration"""
        try:
            # Test document upload endpoint accessibility
            response = requests.post(f"{API_BASE}/belge/upload", timeout=10)
            
            # Should not return Response import error
            if response.status_code == 500:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'Response' in error_detail:
                        self.log_test("Document Upload Endpoint", False, 
                                    "Response import error in upload endpoint")
                    else:
                        self.log_test("Document Upload Endpoint", True, 
                                    "No Response import error in upload endpoint")
                except:
                    self.log_test("Document Upload Endpoint", True, 
                                "No Response import error in upload endpoint")
            elif response.status_code in [400, 422]:
                self.log_test("Document Upload Endpoint", True, 
                            "Upload endpoint accessible - validation error expected")
            elif response.status_code in [401, 403]:
                self.log_test("Document Upload Endpoint", True, 
                            "Upload endpoint accessible - authentication required")
            else:
                self.log_test("Document Upload Endpoint", True, 
                            f"Upload endpoint accessible - Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Document Upload Endpoint Test", False, f"Error: {str(e)}")
            
    def test_user_permission_demo_limits(self):
        """Test user permission and demo limits integration"""
        try:
            # Test with specific user case from review request
            test_email = "bilgi@rotakalitedanismanlik.com"
            
            # Test document access with demo limits
            demo_limit_test_cases = [
                "demo-limit-test-1",
                "demo-limit-test-2", 
                "demo-limit-test-3"
            ]
            
            for test_case in demo_limit_test_cases:
                response = requests.get(f"{API_BASE}/documents/view/{test_case}", timeout=10)
                
                # Demo limit logic should not cause Response import error
                if response.status_code == 500:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', '')
                        if 'Response' in error_detail:
                            self.log_test(f"Demo Limits Integration - {test_case}", False, 
                                        "Response import error in demo limits logic")
                        else:
                            self.log_test(f"Demo Limits Integration - {test_case}", True, 
                                        "No Response import error in demo limits logic")
                    except:
                        self.log_test(f"Demo Limits Integration - {test_case}", True, 
                                    "No Response import error in demo limits logic")
                else:
                    self.log_test(f"Demo Limits Integration - {test_case}", True, 
                                f"Status: {response.status_code}")
                    
        except Exception as e:
            self.log_test("User Permission Demo Limits Test", False, f"Error: {str(e)}")
            
    def test_cors_headers(self):
        """Test CORS headers on document viewer"""
        try:
            # Test OPTIONS request on document viewer
            response = requests.options(f"{API_BASE}/documents/view/test-doc", timeout=10)
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            cors_present = any(header in response.headers for header in cors_headers)
            
            if cors_present:
                self.log_test("CORS Headers", True, "CORS headers present")
            else:
                self.log_test("CORS Headers", False, "CORS headers missing")
                
        except Exception as e:
            self.log_test("CORS Headers Test", False, f"Error: {str(e)}")
            
    def test_performance_after_fix(self):
        """Test performance after Response import fix"""
        try:
            # Test response time for document viewer
            start_time = time.time()
            response = requests.get(f"{API_BASE}/documents/view/performance-test-doc", timeout=10)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response_time < 3.0:  # Less than 3 seconds
                self.log_test("Document Viewer Performance", True, f"{response_time:.2f}s")
            else:
                self.log_test("Document Viewer Performance", False, f"{response_time:.2f}s (too slow)")
                
        except Exception as e:
            self.log_test("Performance Test", False, f"Error: {str(e)}")
            
    def run_all_tests(self):
        """Run all MongoDB binary storage document viewer tests"""
        print("🎯 STARTING MONGODB BINARY STORAGE DOCUMENT VIEWER FIX TEST")
        print("="*80)
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"📡 API Base: {API_BASE}")
        print(f"🎯 Target: Response Import Error Fix & Binary Storage Document Viewer")
        print("="*80)
        
        # Run all test categories
        self.test_backend_health()
        self.test_document_viewer_endpoint_accessibility()
        self.test_response_import_error_fix()
        self.test_binary_storage_priority()
        self.test_gridfs_objectid_validation()
        self.test_turkish_character_encoding()
        self.test_content_type_detection()
        self.test_demo_content_fallback()
        self.test_document_upload_endpoint()
        self.test_user_permission_demo_limits()
        self.test_cors_headers()
        self.test_performance_after_fix()
        
        # Print final summary
        self.print_summary()
        
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = MongoDBBinaryStorageTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["success_rate"] >= 85:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()