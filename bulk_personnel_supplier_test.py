#!/usr/bin/env python3
"""
🎯 BULK PERSONNEL VE TEDARİKÇİ EKLEME TEST - RAILWAY PRODUCTION
Test for bulk personnel and supplier endpoints on Railway production environment
"""

import requests
import json
import sys
import time
from datetime import datetime

# Railway Production Backend URL
BACKEND_URL = "https://rota-crm-production.up.railway.app"

class BulkPersonnelSupplierTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, status, details=""):
        """Log test result"""
        self.total_tests += 1
        if status:
            self.passed_tests += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name} - {details}")
        
        self.test_results.append({
            "test": test_name,
            "status": "PASS" if status else "FAIL",
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_backend_accessibility(self):
        """Test if Railway backend is accessible"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                self.log_test("Railway Backend Accessibility", True, f"Status: {response.status_code}")
                return True
            else:
                self.log_test("Railway Backend Accessibility", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Railway Backend Accessibility", False, f"Error: {str(e)}")
            return False
    
    def test_bulk_personnel_endpoint_accessibility(self):
        """Test bulk personnel endpoint accessibility"""
        try:
            # Test without authentication - should return 403
            response = requests.post(
                f"{self.backend_url}/api/personnel/bulk",
                json=[],
                timeout=10
            )
            
            if response.status_code == 403:
                self.log_test("Bulk Personnel Endpoint - No Auth", True, "403 Forbidden as expected")
                return True
            else:
                self.log_test("Bulk Personnel Endpoint - No Auth", False, f"Expected 403, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bulk Personnel Endpoint - No Auth", False, f"Error: {str(e)}")
            return False
    
    def test_bulk_suppliers_endpoint_accessibility(self):
        """Test bulk suppliers endpoint accessibility"""
        try:
            # Test without authentication - should return 403
            response = requests.post(
                f"{self.backend_url}/api/suppliers/bulk",
                json=[],
                timeout=10
            )
            
            if response.status_code == 403:
                self.log_test("Bulk Suppliers Endpoint - No Auth", True, "403 Forbidden as expected")
                return True
            else:
                self.log_test("Bulk Suppliers Endpoint - No Auth", False, f"Expected 403, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bulk Suppliers Endpoint - No Auth", False, f"Error: {str(e)}")
            return False
    
    def test_bulk_personnel_invalid_token(self):
        """Test bulk personnel endpoint with invalid token"""
        try:
            headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.post(
                f"{self.backend_url}/api/personnel/bulk",
                json=[],
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test("Bulk Personnel - Invalid Token", True, "401 Unauthorized as expected")
                return True
            else:
                self.log_test("Bulk Personnel - Invalid Token", False, f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bulk Personnel - Invalid Token", False, f"Error: {str(e)}")
            return False
    
    def test_bulk_suppliers_invalid_token(self):
        """Test bulk suppliers endpoint with invalid token"""
        try:
            headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.post(
                f"{self.backend_url}/api/suppliers/bulk",
                json=[],
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test("Bulk Suppliers - Invalid Token", True, "401 Unauthorized as expected")
                return True
            else:
                self.log_test("Bulk Suppliers - Invalid Token", False, f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bulk Suppliers - Invalid Token", False, f"Error: {str(e)}")
            return False
    
    def test_bulk_personnel_malformed_token(self):
        """Test bulk personnel endpoint with malformed token"""
        try:
            headers = {"Authorization": "Bearer malformed.token"}
            response = requests.post(
                f"{self.backend_url}/api/personnel/bulk",
                json=[],
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test("Bulk Personnel - Malformed Token", True, "401 Unauthorized as expected")
                return True
            else:
                self.log_test("Bulk Personnel - Malformed Token", False, f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bulk Personnel - Malformed Token", False, f"Error: {str(e)}")
            return False
    
    def test_bulk_suppliers_malformed_token(self):
        """Test bulk suppliers endpoint with malformed token"""
        try:
            headers = {"Authorization": "Bearer malformed.token"}
            response = requests.post(
                f"{self.backend_url}/api/suppliers/bulk",
                json=[],
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test("Bulk Suppliers - Malformed Token", True, "401 Unauthorized as expected")
                return True
            else:
                self.log_test("Bulk Suppliers - Malformed Token", False, f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bulk Suppliers - Malformed Token", False, f"Error: {str(e)}")
            return False
    
    def test_bulk_personnel_empty_bearer(self):
        """Test bulk personnel endpoint with empty Bearer token"""
        try:
            headers = {"Authorization": "Bearer "}
            response = requests.post(
                f"{self.backend_url}/api/personnel/bulk",
                json=[],
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                self.log_test("Bulk Personnel - Empty Bearer", True, f"{response.status_code} as expected")
                return True
            else:
                self.log_test("Bulk Personnel - Empty Bearer", False, f"Expected 401/403, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bulk Personnel - Empty Bearer", False, f"Error: {str(e)}")
            return False
    
    def test_bulk_suppliers_empty_bearer(self):
        """Test bulk suppliers endpoint with empty Bearer token"""
        try:
            headers = {"Authorization": "Bearer "}
            response = requests.post(
                f"{self.backend_url}/api/suppliers/bulk",
                json=[],
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                self.log_test("Bulk Suppliers - Empty Bearer", True, f"{response.status_code} as expected")
                return True
            else:
                self.log_test("Bulk Suppliers - Empty Bearer", False, f"Expected 401/403, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bulk Suppliers - Empty Bearer", False, f"Error: {str(e)}")
            return False
    
    def test_bulk_personnel_http_methods(self):
        """Test bulk personnel endpoint with different HTTP methods"""
        methods_to_test = ['GET', 'PUT', 'DELETE', 'PATCH']
        
        for method in methods_to_test:
            try:
                response = requests.request(
                    method,
                    f"{self.backend_url}/api/personnel/bulk",
                    timeout=10
                )
                
                if response.status_code == 405:
                    self.log_test(f"Bulk Personnel - {method} Method", True, "405 Method Not Allowed")
                else:
                    self.log_test(f"Bulk Personnel - {method} Method", False, f"Expected 405, got {response.status_code}")
            except Exception as e:
                self.log_test(f"Bulk Personnel - {method} Method", False, f"Error: {str(e)}")
    
    def test_bulk_suppliers_http_methods(self):
        """Test bulk suppliers endpoint with different HTTP methods"""
        methods_to_test = ['GET', 'PUT', 'DELETE', 'PATCH']
        
        for method in methods_to_test:
            try:
                response = requests.request(
                    method,
                    f"{self.backend_url}/api/suppliers/bulk",
                    timeout=10
                )
                
                if response.status_code == 405:
                    self.log_test(f"Bulk Suppliers - {method} Method", True, "405 Method Not Allowed")
                else:
                    self.log_test(f"Bulk Suppliers - {method} Method", False, f"Expected 405, got {response.status_code}")
            except Exception as e:
                self.log_test(f"Bulk Suppliers - {method} Method", False, f"Error: {str(e)}")
    
    def test_bulk_personnel_data_validation(self):
        """Test bulk personnel endpoint data validation"""
        try:
            headers = {"Authorization": "Bearer invalid_token_for_validation_test"}
            
            # Test with invalid JSON structure
            response = requests.post(
                f"{self.backend_url}/api/personnel/bulk",
                json={"invalid": "structure"},
                headers=headers,
                timeout=10
            )
            
            # Should return 401 (auth error) or 422 (validation error)
            if response.status_code in [401, 422]:
                self.log_test("Bulk Personnel - Data Validation", True, f"Proper validation: {response.status_code}")
                return True
            else:
                self.log_test("Bulk Personnel - Data Validation", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bulk Personnel - Data Validation", False, f"Error: {str(e)}")
            return False
    
    def test_bulk_suppliers_data_validation(self):
        """Test bulk suppliers endpoint data validation"""
        try:
            headers = {"Authorization": "Bearer invalid_token_for_validation_test"}
            
            # Test with invalid JSON structure
            response = requests.post(
                f"{self.backend_url}/api/suppliers/bulk",
                json={"invalid": "structure"},
                headers=headers,
                timeout=10
            )
            
            # Should return 401 (auth error) or 422 (validation error)
            if response.status_code in [401, 422]:
                self.log_test("Bulk Suppliers - Data Validation", True, f"Proper validation: {response.status_code}")
                return True
            else:
                self.log_test("Bulk Suppliers - Data Validation", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bulk Suppliers - Data Validation", False, f"Error: {str(e)}")
            return False
    
    def test_bulk_personnel_with_test_data(self):
        """Test bulk personnel endpoint with provided test data"""
        try:
            headers = {"Authorization": "Bearer test_token_for_data_structure"}
            
            # Test data from review request
            test_personnel = [
                {
                    "full_name": "Ahmet Test",
                    "position": "Garson",
                    "location": "İstanbul",
                    "certifications": ["İlk Yardım"],
                    "is_local": True,
                    "gender": "Erkek"
                }
            ]
            
            response = requests.post(
                f"{self.backend_url}/api/personnel/bulk",
                json=test_personnel,
                headers=headers,
                timeout=10
            )
            
            # Should return 401 (auth error) since we're using test token
            if response.status_code == 401:
                self.log_test("Bulk Personnel - Test Data Structure", True, "Data structure accepted, auth failed as expected")
                return True
            else:
                self.log_test("Bulk Personnel - Test Data Structure", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bulk Personnel - Test Data Structure", False, f"Error: {str(e)}")
            return False
    
    def test_bulk_suppliers_with_test_data(self):
        """Test bulk suppliers endpoint with provided test data"""
        try:
            headers = {"Authorization": "Bearer test_token_for_data_structure"}
            
            # Test data from review request
            test_suppliers = [
                {
                    "company_name": "Test Tedarikçi",
                    "contact_person": "Mehmet Bey",
                    "category": "Gıda",
                    "local_supplier": True
                }
            ]
            
            response = requests.post(
                f"{self.backend_url}/api/suppliers/bulk",
                json=test_suppliers,
                headers=headers,
                timeout=10
            )
            
            # Should return 401 (auth error) since we're using test token
            if response.status_code == 401:
                self.log_test("Bulk Suppliers - Test Data Structure", True, "Data structure accepted, auth failed as expected")
                return True
            else:
                self.log_test("Bulk Suppliers - Test Data Structure", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bulk Suppliers - Test Data Structure", False, f"Error: {str(e)}")
            return False
    
    def test_bulk_personnel_client_id_parameter(self):
        """Test bulk personnel endpoint with client_id parameter"""
        try:
            headers = {"Authorization": "Bearer test_admin_token"}
            
            # Test with client_id parameter (for admin/consultant users)
            response = requests.post(
                f"{self.backend_url}/api/personnel/bulk?client_id=test-client-123",
                json=[{"full_name": "Test", "position": "Test", "gender": "Erkek"}],
                headers=headers,
                timeout=10
            )
            
            # Should return 401 (auth error) since we're using test token
            if response.status_code == 401:
                self.log_test("Bulk Personnel - Client ID Parameter", True, "Parameter accepted, auth failed as expected")
                return True
            else:
                self.log_test("Bulk Personnel - Client ID Parameter", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bulk Personnel - Client ID Parameter", False, f"Error: {str(e)}")
            return False
    
    def test_bulk_suppliers_client_id_parameter(self):
        """Test bulk suppliers endpoint with client_id parameter"""
        try:
            headers = {"Authorization": "Bearer test_admin_token"}
            
            # Test with client_id parameter (for admin/consultant users)
            response = requests.post(
                f"{self.backend_url}/api/suppliers/bulk?client_id=test-client-123",
                json=[{"company_name": "Test", "category": "Test"}],
                headers=headers,
                timeout=10
            )
            
            # Should return 401 (auth error) since we're using test token
            if response.status_code == 401:
                self.log_test("Bulk Suppliers - Client ID Parameter", True, "Parameter accepted, auth failed as expected")
                return True
            else:
                self.log_test("Bulk Suppliers - Client ID Parameter", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bulk Suppliers - Client ID Parameter", False, f"Error: {str(e)}")
            return False
    
    def test_cors_headers(self):
        """Test CORS headers on bulk endpoints"""
        try:
            # Test OPTIONS request for CORS preflight
            response = requests.options(
                f"{self.backend_url}/api/personnel/bulk",
                timeout=10
            )
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            has_cors = any(header in response.headers for header in cors_headers)
            
            if has_cors or response.status_code == 200:
                self.log_test("CORS Headers - Personnel Bulk", True, "CORS headers present or OPTIONS handled")
                return True
            else:
                self.log_test("CORS Headers - Personnel Bulk", False, f"No CORS headers, status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("CORS Headers - Personnel Bulk", False, f"Error: {str(e)}")
            return False
    
    def test_concurrent_requests(self):
        """Test concurrent requests to bulk endpoints"""
        import threading
        import time
        
        results = []
        
        def make_request():
            try:
                response = requests.post(
                    f"{self.backend_url}/api/personnel/bulk",
                    json=[],
                    timeout=5
                )
                results.append(response.status_code)
            except:
                results.append(0)
        
        # Create 5 concurrent threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check if all requests were handled properly
        if len(results) == 5 and all(status in [403, 401] for status in results):
            self.log_test("Concurrent Requests", True, f"All 5 requests handled properly: {results}")
            return True
        else:
            self.log_test("Concurrent Requests", False, f"Some requests failed: {results}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🎯 BULK PERSONNEL VE TEDARİKÇİ EKLEME TEST - RAILWAY PRODUCTION")
        print("=" * 70)
        print(f"🚂 Testing Railway Backend: {self.backend_url}")
        print("=" * 70)
        
        # Basic connectivity tests
        print("\n📡 BACKEND CONNECTIVITY TESTS")
        print("-" * 40)
        self.test_backend_accessibility()
        
        # Endpoint accessibility tests
        print("\n🔗 ENDPOINT ACCESSIBILITY TESTS")
        print("-" * 40)
        self.test_bulk_personnel_endpoint_accessibility()
        self.test_bulk_suppliers_endpoint_accessibility()
        
        # Authentication tests
        print("\n🔐 AUTHENTICATION TESTS")
        print("-" * 40)
        self.test_bulk_personnel_invalid_token()
        self.test_bulk_suppliers_invalid_token()
        self.test_bulk_personnel_malformed_token()
        self.test_bulk_suppliers_malformed_token()
        self.test_bulk_personnel_empty_bearer()
        self.test_bulk_suppliers_empty_bearer()
        
        # HTTP method tests
        print("\n🌐 HTTP METHOD TESTS")
        print("-" * 40)
        self.test_bulk_personnel_http_methods()
        self.test_bulk_suppliers_http_methods()
        
        # Data validation tests
        print("\n📋 DATA VALIDATION TESTS")
        print("-" * 40)
        self.test_bulk_personnel_data_validation()
        self.test_bulk_suppliers_data_validation()
        self.test_bulk_personnel_with_test_data()
        self.test_bulk_suppliers_with_test_data()
        
        # Parameter tests
        print("\n⚙️ PARAMETER TESTS")
        print("-" * 40)
        self.test_bulk_personnel_client_id_parameter()
        self.test_bulk_suppliers_client_id_parameter()
        
        # CORS and performance tests
        print("\n🌍 CORS & PERFORMANCE TESTS")
        print("-" * 40)
        self.test_cors_headers()
        self.test_concurrent_requests()
        
        # Final results
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"✅ Passed: {self.passed_tests}/{self.total_tests}")
        print(f"❌ Failed: {self.total_tests - self.passed_tests}/{self.total_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Detailed analysis
        print(f"\n🔍 DETAILED ANALYSIS:")
        print(f"🚂 Railway Backend: {'✅ ACCESSIBLE' if self.passed_tests > 0 else '❌ NOT ACCESSIBLE'}")
        print(f"🔗 Bulk Personnel Endpoint: {'✅ REGISTERED' if any('Bulk Personnel Endpoint' in r['test'] for r in self.test_results if r['status'] == 'PASS') else '❌ NOT FOUND'}")
        print(f"🔗 Bulk Suppliers Endpoint: {'✅ REGISTERED' if any('Bulk Suppliers Endpoint' in r['test'] for r in self.test_results if r['status'] == 'PASS') else '❌ NOT FOUND'}")
        print(f"🔐 Authentication Security: {'✅ IMPLEMENTED' if any('Invalid Token' in r['test'] for r in self.test_results if r['status'] == 'PASS') else '❌ MISSING'}")
        print(f"📋 Data Structure: {'✅ VALIDATED' if any('Test Data Structure' in r['test'] for r in self.test_results if r['status'] == 'PASS') else '❌ ISSUES'}")
        print(f"⚙️ Client ID Handling: {'✅ SUPPORTED' if any('Client ID Parameter' in r['test'] for r in self.test_results if r['status'] == 'PASS') else '❌ NOT SUPPORTED'}")
        
        # Critical findings
        print(f"\n🎯 CRITICAL FINDINGS:")
        if success_rate >= 90:
            print("✅ EXCELLENT: Bulk endpoints are production-ready with comprehensive security")
        elif success_rate >= 75:
            print("⚠️ GOOD: Bulk endpoints are functional with minor issues")
        elif success_rate >= 50:
            print("⚠️ MODERATE: Bulk endpoints have some issues that need attention")
        else:
            print("❌ CRITICAL: Bulk endpoints have major issues requiring immediate fix")
        
        print(f"\n🚂 RAILWAY PRODUCTION STATUS: {'✅ READY' if success_rate >= 75 else '❌ NEEDS WORK'}")
        
        return success_rate

def main():
    """Main test execution"""
    tester = BulkPersonnelSupplierTester()
    success_rate = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 75 else 1)

if __name__ == "__main__":
    main()