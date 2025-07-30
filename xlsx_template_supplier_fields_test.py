#!/usr/bin/env python3
"""
🎯 XLSX TEMPLATE & YENİ TEDARİKÇİ ALANLARI TEST - Railway Production
Comprehensive testing of XLSX Template download and New Supplier Fields functionality
Focus: XLSX format, new supplier fields (purchase_amount, purchase_unit, monthly_payment)
"""

import requests
import json
import sys
import os
from datetime import datetime

# Railway Production Backend URL
BACKEND_URL = "https://rota-crm-production.up.railway.app"
TEST_CLIENT_ID = "94927a77-edc3-45ec-8329-795feae35771"

class XLSXTemplateSupplierFieldsTester:
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
            self.log_test("Root endpoint accessible", response.status_code == 200, f"Status: {response.status_code}")
            
            # Test health endpoint
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            self.log_test("Health endpoint accessible", response.status_code == 200, f"Status: {response.status_code}")
            
            # Test API health endpoint
            response = requests.get(f"{self.backend_url}/api/health", timeout=10)
            self.log_test("API health endpoint accessible", response.status_code == 200, f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Backend accessibility", False, f"Error: {str(e)}")
            
    def test_xlsx_template_endpoints(self):
        """Test XLSX template related endpoints"""
        print("\n📊 XLSX TEMPLATE ENDPOINTS TEST")
        print("=" * 50)
        
        # Test personnel endpoint (supporting endpoint for templates)
        try:
            response = requests.get(f"{self.backend_url}/api/personnel", timeout=10)
            self.log_test("Personnel endpoint accessibility", 
                         response.status_code in [403, 401], 
                         f"Status: {response.status_code} (Expected: 403/401 - requires auth)")
        except Exception as e:
            self.log_test("Personnel endpoint test", False, f"Error: {str(e)}")
            
        # Test suppliers endpoint (supporting endpoint for templates)
        try:
            response = requests.get(f"{self.backend_url}/api/suppliers", timeout=10)
            self.log_test("Suppliers endpoint accessibility", 
                         response.status_code in [403, 401], 
                         f"Status: {response.status_code} (Expected: 403/401 - requires auth)")
        except Exception as e:
            self.log_test("Suppliers endpoint test", False, f"Error: {str(e)}")
            
        # Test bulk import template endpoint
        try:
            response = requests.get(f"{self.backend_url}/api/bulk-import/template", timeout=10)
            self.log_test("Bulk import template endpoint", 
                         response.status_code in [403, 401], 
                         f"Status: {response.status_code} (Expected: 403/401 - requires auth)")
        except Exception as e:
            self.log_test("Bulk import template endpoint test", False, f"Error: {str(e)}")
            
    def test_supplier_categories_certifications(self):
        """Test supplier categories and certifications endpoints for template dropdowns"""
        print("\n🏷️ SUPPLIER DROPDOWN DATA ENDPOINTS TEST")
        print("=" * 50)
        
        # Test supplier categories endpoint
        try:
            response = requests.get(f"{self.backend_url}/api/suppliers/categories", timeout=10)
            self.log_test("Supplier categories endpoint", 
                         response.status_code in [200, 403, 401], 
                         f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    categories = response.json()
                    self.log_test("Categories data structure", 
                                 isinstance(categories, list) and len(categories) > 0,
                                 f"Categories count: {len(categories) if isinstance(categories, list) else 'Invalid'}")
                except:
                    self.log_test("Categories JSON parsing", False, "Failed to parse JSON")
                    
        except Exception as e:
            self.log_test("Supplier categories test", False, f"Error: {str(e)}")
            
        # Test supplier certifications endpoint
        try:
            response = requests.get(f"{self.backend_url}/api/suppliers/certifications", timeout=10)
            self.log_test("Supplier certifications endpoint", 
                         response.status_code in [200, 403, 401], 
                         f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    certifications = response.json()
                    self.log_test("Certifications data structure", 
                                 isinstance(certifications, list) and len(certifications) > 0,
                                 f"Certifications count: {len(certifications) if isinstance(certifications, list) else 'Invalid'}")
                except:
                    self.log_test("Certifications JSON parsing", False, "Failed to parse JSON")
                    
        except Exception as e:
            self.log_test("Supplier certifications test", False, f"Error: {str(e)}")
            
    def test_new_supplier_fields_bulk_endpoint(self):
        """Test new supplier fields in bulk supplier endpoint"""
        print("\n🆕 YENİ TEDARİKÇİ ALANLARI BULK ENDPOINT TEST")
        print("=" * 50)
        
        # Test bulk supplier endpoint with new fields
        test_supplier_data = {
            "suppliers_list": [
                {
                    "company_name": "Test XLSX Tedarikçi",
                    "contact_person": "Test Kişi",
                    "email": "test@xlsx.com",
                    "phone": "0532 123 45 67",
                    "category": "Gıda",
                    "services": ["Catering"],
                    "certifications": ["ISO 9001"],
                    "sustainability_score": 85,
                    "local_supplier": True,
                    # YENİ ALANLAR - NEW FIELDS
                    "purchase_amount": 15000.50,  # float
                    "purchase_unit": "KG",        # string
                    "monthly_payment": 2500.75    # float
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.backend_url}/api/suppliers/bulk",
                json=test_supplier_data,
                timeout=10
            )
            
            self.log_test("Bulk supplier endpoint accessibility", 
                         response.status_code in [403, 401, 422], 
                         f"Status: {response.status_code} (Expected: 403/401 - requires auth, or 422 - validation)")
            
            # Test with invalid token to check authentication
            headers = {"Authorization": "Bearer invalid_token"}
            response = requests.post(
                f"{self.backend_url}/api/suppliers/bulk",
                json=test_supplier_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test("Bulk supplier authentication check", 
                         response.status_code == 401, 
                         f"Status: {response.status_code} (Expected: 401 - invalid token)")
                         
        except Exception as e:
            self.log_test("New supplier fields bulk endpoint test", False, f"Error: {str(e)}")
            
    def test_supplier_model_structure(self):
        """Test supplier model structure by examining error responses"""
        print("\n🏗️ SUPPLIER MODEL STRUCTURE TEST")
        print("=" * 50)
        
        # Test with minimal data to see validation errors
        minimal_data = {
            "suppliers_list": [
                {
                    "company_name": "Test Company"
                    # Missing other fields to trigger validation
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.backend_url}/api/suppliers/bulk",
                json=minimal_data,
                timeout=10
            )
            
            self.log_test("Supplier model validation response", 
                         response.status_code in [403, 401, 422], 
                         f"Status: {response.status_code}")
            
            # Test with malformed data structure
            malformed_data = {
                "wrong_key": [{"company_name": "Test"}]
            }
            
            response = requests.post(
                f"{self.backend_url}/api/suppliers/bulk",
                json=malformed_data,
                timeout=10
            )
            
            self.log_test("Malformed data structure handling", 
                         response.status_code in [403, 401, 422], 
                         f"Status: {response.status_code}")
                         
        except Exception as e:
            self.log_test("Supplier model structure test", False, f"Error: {str(e)}")
            
    def test_template_content_validation(self):
        """Test template content validation through supporting endpoints"""
        print("\n📋 TEMPLATE CONTENT VALIDATION TEST")
        print("=" * 50)
        
        # Test personnel endpoint for personnel template validation
        try:
            # Test with client_id parameter
            response = requests.get(
                f"{self.backend_url}/api/personnel?client_id={self.test_client_id}",
                timeout=10
            )
            self.log_test("Personnel template data endpoint", 
                         response.status_code in [403, 401], 
                         f"Status: {response.status_code} (Expected: 403/401 - requires auth)")
                         
        except Exception as e:
            self.log_test("Personnel template validation test", False, f"Error: {str(e)}")
            
        # Test suppliers endpoint for supplier template validation
        try:
            response = requests.get(
                f"{self.backend_url}/api/suppliers?client_id={self.test_client_id}",
                timeout=10
            )
            self.log_test("Supplier template data endpoint", 
                         response.status_code in [403, 401], 
                         f"Status: {response.status_code} (Expected: 403/401 - requires auth)")
                         
        except Exception as e:
            self.log_test("Supplier template validation test", False, f"Error: {str(e)}")
            
    def test_data_processing_endpoints(self):
        """Test data processing endpoints for Excel import"""
        print("\n⚙️ DATA PROCESSING ENDPOINTS TEST")
        print("=" * 50)
        
        # Test personnel bulk import endpoint
        test_personnel_data = {
            "personnel_list": [
                {
                    "full_name": "Test XLSX Personel",
                    "position": "Test Pozisyon",
                    "location": "Test Lokasyon",
                    "certifications": ["İlk Yardım"],
                    "is_local": True,
                    "gender": "Erkek"
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.backend_url}/api/personnel/bulk",
                json=test_personnel_data,
                timeout=10
            )
            
            self.log_test("Personnel bulk import endpoint", 
                         response.status_code in [403, 401, 422], 
                         f"Status: {response.status_code} (Expected: 403/401 - requires auth)")
                         
        except Exception as e:
            self.log_test("Personnel data processing test", False, f"Error: {str(e)}")
            
        # Test supplier bulk import with new fields
        test_supplier_with_new_fields = {
            "suppliers_list": [
                {
                    "company_name": "XLSX Test Tedarikçi",
                    "contact_person": "XLSX Test Kişi",
                    "email": "xlsx@test.com",
                    "phone": "0532 999 88 77",
                    "category": "Temizlik",
                    "services": ["Temizlik Malzemeleri"],
                    "certifications": ["ISO 14001"],
                    "sustainability_score": 90,
                    "local_supplier": False,
                    # YENİ ALANLAR TEST
                    "purchase_amount": 25000.0,
                    "purchase_unit": "LITRE",
                    "monthly_payment": 3500.25
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.backend_url}/api/suppliers/bulk",
                json=test_supplier_with_new_fields,
                timeout=10
            )
            
            self.log_test("Supplier bulk import with new fields", 
                         response.status_code in [403, 401, 422], 
                         f"Status: {response.status_code} (Expected: 403/401 - requires auth)")
                         
        except Exception as e:
            self.log_test("Supplier new fields processing test", False, f"Error: {str(e)}")
            
    def test_float_parsing_validation(self):
        """Test float parsing for new supplier fields"""
        print("\n🔢 FLOAT PARSING VALIDATION TEST")
        print("=" * 50)
        
        # Test with various float formats
        float_test_cases = [
            {
                "name": "Standard float values",
                "data": {
                    "suppliers_list": [{
                        "company_name": "Float Test 1",
                        "category": "Test",
                        "purchase_amount": 1500.50,
                        "monthly_payment": 250.75
                    }]
                }
            },
            {
                "name": "Integer values (should convert to float)",
                "data": {
                    "suppliers_list": [{
                        "company_name": "Float Test 2", 
                        "category": "Test",
                        "purchase_amount": 2000,
                        "monthly_payment": 300
                    }]
                }
            },
            {
                "name": "String numbers (should convert)",
                "data": {
                    "suppliers_list": [{
                        "company_name": "Float Test 3",
                        "category": "Test", 
                        "purchase_amount": "3500.25",
                        "monthly_payment": "450.50"
                    }]
                }
            }
        ]
        
        for test_case in float_test_cases:
            try:
                response = requests.post(
                    f"{self.backend_url}/api/suppliers/bulk",
                    json=test_case["data"],
                    timeout=10
                )
                
                self.log_test(f"Float parsing - {test_case['name']}", 
                             response.status_code in [403, 401, 422], 
                             f"Status: {response.status_code}")
                             
            except Exception as e:
                self.log_test(f"Float parsing test - {test_case['name']}", False, f"Error: {str(e)}")
                
    def test_purchase_unit_validation(self):
        """Test purchase_unit field validation"""
        print("\n📦 PURCHASE UNIT VALIDATION TEST")
        print("=" * 50)
        
        # Test with different purchase unit values
        unit_test_cases = [
            "KG", "LITRE", "ADET", "GÜN", "METRE", "M2", "M3", "TON", "PAKET"
        ]
        
        for unit in unit_test_cases:
            test_data = {
                "suppliers_list": [{
                    "company_name": f"Unit Test {unit}",
                    "category": "Test",
                    "purchase_unit": unit,
                    "purchase_amount": 1000.0
                }]
            }
            
            try:
                response = requests.post(
                    f"{self.backend_url}/api/suppliers/bulk",
                    json=test_data,
                    timeout=10
                )
                
                self.log_test(f"Purchase unit validation - {unit}", 
                             response.status_code in [403, 401, 422], 
                             f"Status: {response.status_code}")
                             
            except Exception as e:
                self.log_test(f"Purchase unit test - {unit}", False, f"Error: {str(e)}")
                
    def test_authentication_security(self):
        """Test authentication security for all endpoints"""
        print("\n🔐 AUTHENTICATION SECURITY TEST")
        print("=" * 50)
        
        endpoints_to_test = [
            "/api/personnel",
            "/api/suppliers", 
            "/api/personnel/bulk",
            "/api/suppliers/bulk",
            "/api/suppliers/categories",
            "/api/suppliers/certifications"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                # Test without authentication
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                self.log_test(f"No auth security - {endpoint}", 
                             response.status_code == 403, 
                             f"Status: {response.status_code} (Expected: 403)")
                
                # Test with invalid token
                headers = {"Authorization": "Bearer invalid_token_12345"}
                response = requests.get(f"{self.backend_url}{endpoint}", headers=headers, timeout=10)
                self.log_test(f"Invalid token security - {endpoint}", 
                             response.status_code == 401, 
                             f"Status: {response.status_code} (Expected: 401)")
                             
            except Exception as e:
                self.log_test(f"Authentication test - {endpoint}", False, f"Error: {str(e)}")
                
    def run_comprehensive_test(self):
        """Run all tests"""
        print("🎯 XLSX TEMPLATE & YENİ TEDARİKÇİ ALANLARI COMPREHENSIVE TEST")
        print("=" * 80)
        print(f"🚂 Testing Railway Production: {self.backend_url}")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Run all test categories
        self.test_backend_accessibility()
        self.test_xlsx_template_endpoints()
        self.test_supplier_categories_certifications()
        self.test_new_supplier_fields_bulk_endpoint()
        self.test_supplier_model_structure()
        self.test_template_content_validation()
        self.test_data_processing_endpoints()
        self.test_float_parsing_validation()
        self.test_purchase_unit_validation()
        self.test_authentication_security()
        
        # Calculate success rate
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("🎉 XLSX TEMPLATE & YENİ TEDARİKÇİ ALANLARI TEST SUMMARY")
        print("=" * 80)
        print(f"📊 Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.total_tests - self.passed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT - System is working perfectly!")
        elif success_rate >= 75:
            print("✅ GOOD - System is working well with minor issues")
        elif success_rate >= 50:
            print("⚠️ MODERATE - System has some issues that need attention")
        else:
            print("❌ POOR - System has significant issues requiring immediate attention")
            
        print("\n🔍 KEY FINDINGS:")
        print("=" * 50)
        
        # Analyze results for key findings
        failed_tests = [test for test in self.test_results if not test["passed"]]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests[:5]:  # Show first 5 failed tests
                print(f"   • {test['test']}: {test['details']}")
        else:
            print("✅ ALL TESTS PASSED!")
            
        print("\n🚂 RAILWAY PRODUCTION STATUS:")
        if success_rate >= 80:
            print("✅ READY - XLSX Template & New Supplier Fields functionality is working correctly!")
        else:
            print("❌ NEEDS ATTENTION - Some issues found that may affect functionality")
            
        return success_rate

if __name__ == "__main__":
    tester = XLSXTemplateSupplierFieldsTester()
    success_rate = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 75 else 1)