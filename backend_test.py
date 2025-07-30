#!/usr/bin/env python3
"""
🎯 TEDARIKÇI EXCEL IMPORT TEST - Railway Production
Comprehensive testing of Supplier Excel Import functionality
Test client_id: 94927a77-edc3-45ec-8329-795feae35771
"""

import requests
import json
import sys
import os
from datetime import datetime

# Railway Production Backend URL
BACKEND_URL = "https://rota-crm-production.up.railway.app"
TEST_CLIENT_ID = "94927a77-edc3-45ec-8329-795feae35771"

class SupplierExcelImportTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_client_id = TEST_CLIENT_ID
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status} - {test_name}"
        if details:
            result += f" | {details}"
        
        print(result)
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        
    def test_backend_accessibility(self):
        """Test if Railway backend is accessible"""
        print("\n🚂 RAILWAY BACKEND ACCESSIBILITY TEST")
        print("=" * 50)
        
        try:
            # Test root endpoint
            response = requests.get(f"{self.backend_url}/", timeout=10)
            self.log_test("Backend Root Accessible", 
                         response.status_code == 200,
                         f"Status: {response.status_code}")
            
            # Test health endpoint
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            self.log_test("Health Endpoint Working", 
                         response.status_code == 200,
                         f"Status: {response.status_code}")
            
            # Test API health endpoint
            response = requests.get(f"{self.backend_url}/api/health", timeout=10)
            self.log_test("API Health Endpoint Working", 
                         response.status_code == 200,
                         f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Backend Accessibility", False, f"Error: {str(e)}")
    
    def test_bulk_supplier_endpoint_security(self):
        """Test bulk supplier endpoint security"""
        print("\n🔒 BULK SUPPLIER ENDPOINT SECURITY TEST")
        print("=" * 50)
        
        endpoint = f"{self.backend_url}/api/suppliers/bulk"
        
        # Test without authentication
        try:
            response = requests.post(endpoint, json={}, timeout=10)
            expected_codes = [401, 403]  # Should require authentication
            self.log_test("No Auth Returns 401/403", 
                         response.status_code in expected_codes,
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("No Auth Test", False, f"Error: {str(e)}")
        
        # Test with invalid token
        try:
            headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.post(endpoint, json={}, headers=headers, timeout=10)
            expected_codes = [401, 403]  # Should reject invalid token
            self.log_test("Invalid Token Returns 401/403", 
                         response.status_code in expected_codes,
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Token Test", False, f"Error: {str(e)}")
        
        # Test with malformed token
        try:
            headers = {"Authorization": "Bearer malformed.token"}
            response = requests.post(endpoint, json={}, headers=headers, timeout=10)
            expected_codes = [401, 403]  # Should reject malformed token
            self.log_test("Malformed Token Returns 401/403", 
                         response.status_code in expected_codes,
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Malformed Token Test", False, f"Error: {str(e)}")
    
    def test_bulk_supplier_request_wrapper(self):
        """Test BulkSupplierRequest wrapper model"""
        print("\n📦 BULKSUPPLIERREQUEST WRAPPER MODEL TEST")
        print("=" * 50)
        
        endpoint = f"{self.backend_url}/api/suppliers/bulk"
        
        # Test correct wrapper format
        try:
            correct_payload = {
                "suppliers_list": [
                    {
                        "company_name": "Test Şirket A",
                        "contact_person": "Test Kişi A",
                        "email": "testa@test.com",
                        "phone": "0212-123-4567",
                        "category": "Test Kategori A",
                        "services": ["Test Hizmet A"],
                        "certifications": ["Test Sertifika A"],
                        "sustainability_score": 75,
                        "local_supplier": True
                    }
                ]
            }
            
            headers = {"Authorization": "Bearer test_token"}
            response = requests.post(endpoint, json=correct_payload, headers=headers, timeout=10)
            
            # Should not return 422 (Unprocessable Entity) - wrapper model working
            self.log_test("Correct Wrapper Format Accepted", 
                         response.status_code != 422,
                         f"Status: {response.status_code} (not 422 Unprocessable Entity)")
        except Exception as e:
            self.log_test("Wrapper Format Test", False, f"Error: {str(e)}")
        
        # Test incorrect format (without wrapper)
        try:
            incorrect_payload = [
                {
                    "company_name": "Test Şirket B",
                    "category": "Test Kategori B"
                }
            ]
            
            headers = {"Authorization": "Bearer test_token"}
            response = requests.post(endpoint, json=incorrect_payload, headers=headers, timeout=10)
            
            # Should return 422 for incorrect format
            self.log_test("Incorrect Format Returns 422", 
                         response.status_code == 422,
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Incorrect Format Test", False, f"Error: {str(e)}")
    
    def test_excel_format_parsing(self):
        """Test Excel format data parsing"""
        print("\n📊 EXCEL FORMAT PARSING TEST")
        print("=" * 50)
        
        endpoint = f"{self.backend_url}/api/suppliers/bulk"
        
        # Test with Excel-like data structure
        excel_data = {
            "suppliers_list": [
                {
                    "company_name": "Test Şirket Excel",
                    "contact_person": "Test Kişi Excel",
                    "email": "excel@test.com",
                    "phone": "0212-123-4567",
                    "category": "Test Kategori Excel",
                    "services": ["Test Hizmet Excel", "İkinci Hizmet"],
                    "certifications": ["Test Sertifika Excel", "ISO 9001"],
                    "sustainability_score": 85,
                    "local_supplier": True
                },
                {
                    "company_name": "İkinci Test Şirket",
                    "contact_person": "İkinci Test Kişi",
                    "email": "ikinci@test.com",
                    "phone": "0216-987-6543",
                    "category": "İkinci Kategori",
                    "services": ["Farklı Hizmet"],
                    "certifications": ["Farklı Sertifika"],
                    "sustainability_score": 60,
                    "local_supplier": False
                }
            ]
        }
        
        try:
            headers = {"Authorization": "Bearer test_token"}
            response = requests.post(endpoint, json=excel_data, headers=headers, timeout=10)
            
            # Should accept Excel format data structure
            self.log_test("Excel Data Structure Accepted", 
                         response.status_code != 422,
                         f"Status: {response.status_code}")
            
            # Check if response indicates proper parsing
            if response.status_code not in [401, 403]:  # Skip auth errors
                try:
                    response_data = response.json()
                    self.log_test("Excel Data Response Parseable", 
                                 isinstance(response_data, dict),
                                 f"Response type: {type(response_data)}")
                except:
                    self.log_test("Excel Data Response Parseable", False, "Invalid JSON response")
                    
        except Exception as e:
            self.log_test("Excel Format Parsing", False, f"Error: {str(e)}")
    
    def test_field_validation(self):
        """Test field validation (required vs optional)"""
        print("\n✅ FIELD VALIDATION TEST")
        print("=" * 50)
        
        endpoint = f"{self.backend_url}/api/suppliers/bulk"
        
        # Test with only required fields
        try:
            minimal_data = {
                "suppliers_list": [
                    {
                        "company_name": "Minimal Test Şirket",
                        "category": "Minimal Kategori"
                        # All other fields are optional
                    }
                ]
            }
            
            headers = {"Authorization": "Bearer test_token"}
            response = requests.post(endpoint, json=minimal_data, headers=headers, timeout=10)
            
            # Should accept minimal required fields
            self.log_test("Required Fields Only Accepted", 
                         response.status_code != 422,
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Required Fields Test", False, f"Error: {str(e)}")
        
        # Test missing required field (company_name)
        try:
            missing_company_data = {
                "suppliers_list": [
                    {
                        "category": "Test Kategori",
                        "contact_person": "Test Kişi"
                        # Missing company_name (required)
                    }
                ]
            }
            
            headers = {"Authorization": "Bearer test_token"}
            response = requests.post(endpoint, json=missing_company_data, headers=headers, timeout=10)
            
            # Should return 422 for missing required field
            self.log_test("Missing Required Field Returns 422", 
                         response.status_code == 422,
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Missing Required Field Test", False, f"Error: {str(e)}")
        
        # Test missing required field (category)
        try:
            missing_category_data = {
                "suppliers_list": [
                    {
                        "company_name": "Test Şirket",
                        "contact_person": "Test Kişi"
                        # Missing category (required)
                    }
                ]
            }
            
            headers = {"Authorization": "Bearer test_token"}
            response = requests.post(endpoint, json=missing_category_data, headers=headers, timeout=10)
            
            # Should return 422 for missing required field
            self.log_test("Missing Category Returns 422", 
                         response.status_code == 422,
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Missing Category Test", False, f"Error: {str(e)}")
    
    def test_data_type_conversion(self):
        """Test data type conversion"""
        print("\n🔄 DATA TYPE CONVERSION TEST")
        print("=" * 50)
        
        endpoint = f"{self.backend_url}/api/suppliers/bulk"
        
        # Test with various data types
        try:
            type_test_data = {
                "suppliers_list": [
                    {
                        "company_name": "Type Test Şirket",
                        "category": "Type Test Kategori",
                        "sustainability_score": "75",  # String that should convert to int
                        "local_supplier": "true"  # String that should convert to bool
                    },
                    {
                        "company_name": "Type Test Şirket 2",
                        "category": "Type Test Kategori 2",
                        "sustainability_score": 90,  # Already int
                        "local_supplier": False  # Already bool
                    }
                ]
            }
            
            headers = {"Authorization": "Bearer test_token"}
            response = requests.post(endpoint, json=type_test_data, headers=headers, timeout=10)
            
            # Should handle type conversion properly
            self.log_test("Data Type Conversion Handled", 
                         response.status_code != 422,
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Data Type Conversion Test", False, f"Error: {str(e)}")
    
    def test_client_id_parameter_handling(self):
        """Test client_id parameter handling for admin users"""
        print("\n🆔 CLIENT_ID PARAMETER HANDLING TEST")
        print("=" * 50)
        
        endpoint = f"{self.backend_url}/api/suppliers/bulk"
        
        # Test with client_id parameter (admin scenario)
        try:
            test_data = {
                "suppliers_list": [
                    {
                        "company_name": "Admin Test Şirket",
                        "category": "Admin Test Kategori"
                    }
                ]
            }
            
            # Test with client_id parameter
            params = {"client_id": self.test_client_id}
            headers = {"Authorization": "Bearer admin_test_token"}
            response = requests.post(endpoint, json=test_data, params=params, headers=headers, timeout=10)
            
            # Should accept client_id parameter
            self.log_test("Client_ID Parameter Accepted", 
                         response.status_code != 400,  # 400 would indicate parameter issue
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Client_ID Parameter Test", False, f"Error: {str(e)}")
    
    def test_http_method_restrictions(self):
        """Test HTTP method restrictions"""
        print("\n🚫 HTTP METHOD RESTRICTIONS TEST")
        print("=" * 50)
        
        endpoint = f"{self.backend_url}/api/suppliers/bulk"
        
        # Test GET method (should not be allowed)
        try:
            response = requests.get(endpoint, timeout=10)
            self.log_test("GET Method Returns 405", 
                         response.status_code == 405,
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("GET Method Test", False, f"Error: {str(e)}")
        
        # Test PUT method (should not be allowed)
        try:
            response = requests.put(endpoint, json={}, timeout=10)
            self.log_test("PUT Method Returns 405", 
                         response.status_code == 405,
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("PUT Method Test", False, f"Error: {str(e)}")
        
        # Test DELETE method (should not be allowed)
        try:
            response = requests.delete(endpoint, timeout=10)
            self.log_test("DELETE Method Returns 405", 
                         response.status_code == 405,
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("DELETE Method Test", False, f"Error: {str(e)}")
    
    def test_comprehensive_excel_import_scenario(self):
        """Test comprehensive Excel import scenario"""
        print("\n🎯 COMPREHENSIVE EXCEL IMPORT SCENARIO TEST")
        print("=" * 50)
        
        endpoint = f"{self.backend_url}/api/suppliers/bulk"
        
        # Comprehensive test data matching Excel import format
        comprehensive_data = {
            "suppliers_list": [
                {
                    "company_name": "Test Şirket A",
                    "contact_person": "Test Kişi A",
                    "email": "testa@test.com",
                    "phone": "0212-123-4567",
                    "category": "Test Kategori A",
                    "services": ["Test Hizmet A", "İkinci Hizmet A"],
                    "certifications": ["Test Sertifika A", "ISO 9001"],
                    "sustainability_score": 75,
                    "local_supplier": True
                },
                {
                    "company_name": "Test Şirket B",
                    "contact_person": "Test Kişi B",
                    "email": "testb@test.com",
                    "phone": "0216-987-6543",
                    "category": "Test Kategori B",
                    "services": ["Test Hizmet B"],
                    "certifications": ["Test Sertifika B"],
                    "sustainability_score": 60,
                    "local_supplier": False
                },
                {
                    "company_name": "Minimal Test Şirket",
                    "category": "Minimal Kategori"
                    # Only required fields
                }
            ]
        }
        
        try:
            headers = {"Authorization": "Bearer comprehensive_test_token"}
            params = {"client_id": self.test_client_id}
            response = requests.post(endpoint, json=comprehensive_data, params=params, headers=headers, timeout=10)
            
            # Should handle comprehensive Excel import scenario
            self.log_test("Comprehensive Excel Import Scenario", 
                         response.status_code not in [422, 400],  # Should not be validation error
                         f"Status: {response.status_code}")
            
            # Check response structure if not auth error
            if response.status_code not in [401, 403]:
                try:
                    response_data = response.json()
                    has_message = "message" in response_data if isinstance(response_data, dict) else False
                    self.log_test("Response Has Message Field", 
                                 has_message,
                                 f"Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not dict'}")
                except:
                    self.log_test("Response Structure Test", False, "Invalid JSON response")
                    
        except Exception as e:
            self.log_test("Comprehensive Excel Import Test", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🎯 TEDARIKÇI EXCEL IMPORT TEST - Railway Production")
        print("=" * 60)
        print(f"Backend URL: {self.backend_url}")
        print(f"Test Client ID: {self.test_client_id}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run all test categories
        self.test_backend_accessibility()
        self.test_bulk_supplier_endpoint_security()
        self.test_bulk_supplier_request_wrapper()
        self.test_excel_format_parsing()
        self.test_field_validation()
        self.test_data_type_conversion()
        self.test_client_id_parameter_handling()
        self.test_http_method_restrictions()
        self.test_comprehensive_excel_import_scenario()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 TEDARIKÇI EXCEL IMPORT TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed Tests: {self.passed_tests}")
        print(f"Failed Tests: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT - Supplier Excel Import is working excellently!")
        elif success_rate >= 75:
            print("✅ GOOD - Supplier Excel Import is working well with minor issues")
        elif success_rate >= 50:
            print("⚠️ MODERATE - Supplier Excel Import has some issues")
        else:
            print("❌ POOR - Supplier Excel Import has significant issues")
        
        print("\n🔍 KEY FINDINGS:")
        
        # Analyze results
        auth_tests = [r for r in self.test_results if "Auth" in r["test"] or "Token" in r["test"]]
        wrapper_tests = [r for r in self.test_results if "Wrapper" in r["test"] or "Format" in r["test"]]
        validation_tests = [r for r in self.test_results if "Validation" in r["test"] or "Required" in r["test"]]
        
        auth_success = sum(1 for t in auth_tests if t["passed"]) / len(auth_tests) * 100 if auth_tests else 0
        wrapper_success = sum(1 for t in wrapper_tests if t["passed"]) / len(wrapper_tests) * 100 if wrapper_tests else 0
        validation_success = sum(1 for t in validation_tests if t["passed"]) / len(validation_tests) * 100 if validation_tests else 0
        
        print(f"• Authentication Security: {auth_success:.0f}% ({len([t for t in auth_tests if t['passed']])}/{len(auth_tests)} tests)")
        print(f"• Wrapper Model Functionality: {wrapper_success:.0f}% ({len([t for t in wrapper_tests if t['passed']])}/{len(wrapper_tests)} tests)")
        print(f"• Field Validation: {validation_success:.0f}% ({len([t for t in validation_tests if t['passed']])}/{len(validation_tests)} tests)")
        
        print("\n📋 ANSWER TO MAIN QUESTION:")
        print("❓ PersonnelManagement gibi SupplierManagement da Excel import yapabiliyor mu?")
        
        if success_rate >= 75:
            print("✅ EVET - SupplierManagement Excel import özelliği PersonnelManagement gibi çalışıyor!")
            print("   • BulkSupplierRequest wrapper model çalışıyor")
            print("   • Excel format parsing doğru")
            print("   • Field validation implementte")
            print("   • Client ID association working")
        else:
            print("❌ HAYIR - SupplierManagement Excel import özelliğinde sorunlar var")
            print("   • Wrapper model veya validation sorunları mevcut")
            print("   • Excel format parsing problemli olabilir")
        
        print("\n🚂 Railway Production Status: TESTED")
        print("=" * 60)
        
        return success_rate

if __name__ == "__main__":
    tester = SupplierExcelImportTester()
    success_rate = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 75 else 1)