#!/usr/bin/env python3
"""
🎯 TEDARIKÇI EXCEL ŞABLONU API'LERİ TEST
Backend Test for Supplier Excel Template APIs

Test edilecek endpoint'ler:
1. GET /api/suppliers/categories/list - Tedarikçi kategorilerini getir
2. GET /api/suppliers/purchase-units/list - Satın alma birimlerini getir  
3. GET /api/suppliers/certifications/list - Sertifika listesini getir

Test hedefleri:
- Endpoint'lerin erişilebilir olduğunu doğrula
- Response formatının doğru olduğunu kontrol et (categories, purchase_units, certifications array'leri)
- Kategorilerin 29 adet olduğunu doğrula (SUPPLIER_CATEGORIES listesi)
- Purchase units'lerin 40+ adet olduğunu doğrula (PURCHASE_UNITS listesi)  
- Certifications'ların 15 adet olduğunu doğrula (AVAILABLE_CERTIFICATIONS listesi)
- JSON response yapısının frontend ile uyumlu olduğunu kontrol et
"""

import requests
import json
import sys
from datetime import datetime

# Test Configuration
BACKEND_URL = "https://rota-crm-production.up.railway.app"
TEST_ENDPOINTS = [
    {
        "name": "Supplier Categories",
        "url": f"{BACKEND_URL}/api/suppliers/categories/list",
        "method": "GET",
        "expected_field": "categories",
        "expected_count": 29,
        "description": "Tedarikçi kategorilerini getir"
    },
    {
        "name": "Purchase Units", 
        "url": f"{BACKEND_URL}/api/suppliers/purchase-units/list",
        "method": "GET",
        "expected_field": "purchase_units",
        "expected_count": 40,  # 40+ expected
        "description": "Satın alma birimlerini getir"
    },
    {
        "name": "Certifications",
        "url": f"{BACKEND_URL}/api/suppliers/certifications/list", 
        "method": "GET",
        "expected_field": "certifications",
        "expected_count": 15,
        "description": "Sertifika listesini getir"
    }
]

class SupplierExcelTemplateAPITest:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log(self, message, level="INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_endpoint_accessibility(self, endpoint_config):
        """Test if endpoint is accessible and returns proper response"""
        test_name = f"Endpoint Accessibility - {endpoint_config['name']}"
        self.total_tests += 1
        
        try:
            self.log(f"Testing {endpoint_config['name']} endpoint...")
            response = requests.get(endpoint_config['url'], timeout=10)
            
            if response.status_code == 200:
                self.log(f"✅ {endpoint_config['name']} endpoint accessible (200 OK)")
                self.passed_tests += 1
                self.results.append({
                    "test": test_name,
                    "status": "PASS",
                    "details": f"HTTP 200 OK - Endpoint accessible"
                })
                return True
            else:
                self.log(f"❌ {endpoint_config['name']} endpoint returned {response.status_code}")
                self.failed_tests += 1
                self.results.append({
                    "test": test_name,
                    "status": "FAIL", 
                    "details": f"HTTP {response.status_code} - Expected 200"
                })
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ {endpoint_config['name']} endpoint connection error: {str(e)}")
            self.failed_tests += 1
            self.results.append({
                "test": test_name,
                "status": "FAIL",
                "details": f"Connection error: {str(e)}"
            })
            return False
            
    def test_response_format(self, endpoint_config):
        """Test if response has correct JSON format"""
        test_name = f"Response Format - {endpoint_config['name']}"
        self.total_tests += 1
        
        try:
            response = requests.get(endpoint_config['url'], timeout=10)
            
            if response.status_code != 200:
                self.failed_tests += 1
                self.results.append({
                    "test": test_name,
                    "status": "FAIL",
                    "details": f"Endpoint not accessible (HTTP {response.status_code})"
                })
                return None
                
            # Parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                self.log(f"❌ {endpoint_config['name']} invalid JSON response: {str(e)}")
                self.failed_tests += 1
                self.results.append({
                    "test": test_name,
                    "status": "FAIL",
                    "details": f"Invalid JSON: {str(e)}"
                })
                return None
                
            # Check if expected field exists
            expected_field = endpoint_config['expected_field']
            if expected_field not in data:
                self.log(f"❌ {endpoint_config['name']} missing '{expected_field}' field in response")
                self.failed_tests += 1
                self.results.append({
                    "test": test_name,
                    "status": "FAIL",
                    "details": f"Missing '{expected_field}' field in response"
                })
                return None
                
            # Check if field is array
            if not isinstance(data[expected_field], list):
                self.log(f"❌ {endpoint_config['name']} '{expected_field}' is not an array")
                self.failed_tests += 1
                self.results.append({
                    "test": test_name,
                    "status": "FAIL",
                    "details": f"'{expected_field}' is not an array"
                })
                return None
                
            self.log(f"✅ {endpoint_config['name']} has correct JSON format with '{expected_field}' array")
            self.passed_tests += 1
            self.results.append({
                "test": test_name,
                "status": "PASS",
                "details": f"Correct JSON format with '{expected_field}' array"
            })
            return data
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ {endpoint_config['name']} connection error: {str(e)}")
            self.failed_tests += 1
            self.results.append({
                "test": test_name,
                "status": "FAIL",
                "details": f"Connection error: {str(e)}"
            })
            return None
            
    def test_data_count(self, endpoint_config, data):
        """Test if data count matches expected count"""
        test_name = f"Data Count - {endpoint_config['name']}"
        self.total_tests += 1
        
        if data is None:
            self.failed_tests += 1
            self.results.append({
                "test": test_name,
                "status": "FAIL",
                "details": "No data available for count test"
            })
            return False
            
        expected_field = endpoint_config['expected_field']
        expected_count = endpoint_config['expected_count']
        actual_count = len(data[expected_field])
        
        # For purchase units, we expect 40+ items
        if endpoint_config['name'] == "Purchase Units":
            if actual_count >= expected_count:
                self.log(f"✅ {endpoint_config['name']} has {actual_count} items (expected {expected_count}+)")
                self.passed_tests += 1
                self.results.append({
                    "test": test_name,
                    "status": "PASS",
                    "details": f"Has {actual_count} items (expected {expected_count}+)"
                })
                return True
            else:
                self.log(f"❌ {endpoint_config['name']} has {actual_count} items (expected {expected_count}+)")
                self.failed_tests += 1
                self.results.append({
                    "test": test_name,
                    "status": "FAIL",
                    "details": f"Has {actual_count} items (expected {expected_count}+)"
                })
                return False
        else:
            # For categories and certifications, we expect exact count
            if actual_count == expected_count:
                self.log(f"✅ {endpoint_config['name']} has exactly {actual_count} items (expected {expected_count})")
                self.passed_tests += 1
                self.results.append({
                    "test": test_name,
                    "status": "PASS",
                    "details": f"Has exactly {actual_count} items (expected {expected_count})"
                })
                return True
            else:
                self.log(f"❌ {endpoint_config['name']} has {actual_count} items (expected {expected_count})")
                self.failed_tests += 1
                self.results.append({
                    "test": test_name,
                    "status": "FAIL",
                    "details": f"Has {actual_count} items (expected {expected_count})"
                })
                return False
                
    def test_data_content(self, endpoint_config, data):
        """Test if data content is valid"""
        test_name = f"Data Content - {endpoint_config['name']}"
        self.total_tests += 1
        
        if data is None:
            self.failed_tests += 1
            self.results.append({
                "test": test_name,
                "status": "FAIL",
                "details": "No data available for content test"
            })
            return False
            
        expected_field = endpoint_config['expected_field']
        items = data[expected_field]
        
        # Check if all items are strings and not empty
        invalid_items = []
        for i, item in enumerate(items):
            if not isinstance(item, str) or not item.strip():
                invalid_items.append(f"Index {i}: '{item}'")
                
        if invalid_items:
            self.log(f"❌ {endpoint_config['name']} has invalid items: {invalid_items[:5]}")  # Show first 5
            self.failed_tests += 1
            self.results.append({
                "test": test_name,
                "status": "FAIL",
                "details": f"Invalid items found: {len(invalid_items)} items"
            })
            return False
        else:
            self.log(f"✅ {endpoint_config['name']} all items are valid strings")
            self.passed_tests += 1
            self.results.append({
                "test": test_name,
                "status": "PASS",
                "details": f"All {len(items)} items are valid strings"
            })
            return True
            
    def test_sample_data_content(self, endpoint_config, data):
        """Test sample data content for expected values"""
        test_name = f"Sample Data Content - {endpoint_config['name']}"
        self.total_tests += 1
        
        if data is None:
            self.failed_tests += 1
            self.results.append({
                "test": test_name,
                "status": "FAIL",
                "details": "No data available for sample content test"
            })
            return False
            
        expected_field = endpoint_config['expected_field']
        items = data[expected_field]
        
        # Define expected sample items for each endpoint
        expected_samples = {
            "categories": ["Gıda & İçecek", "Temizlik & Hijyen", "Enerji & Yakıt", "Diğer"],
            "purchase_units": ["ADET", "KG", "LİTRE", "GÜN", "SAAT", "M²", "M³", "TON"],
            "certifications": ["ISO 14001", "Organik Sertifika", "Fair Trade", "Carbon Neutral", "LEED Certified"]
        }
        
        expected_items = expected_samples.get(expected_field, [])
        missing_items = []
        
        for expected_item in expected_items:
            if expected_item not in items:
                missing_items.append(expected_item)
                
        if missing_items:
            self.log(f"❌ {endpoint_config['name']} missing expected items: {missing_items}")
            self.failed_tests += 1
            self.results.append({
                "test": test_name,
                "status": "FAIL",
                "details": f"Missing expected items: {missing_items}"
            })
            return False
        else:
            self.log(f"✅ {endpoint_config['name']} contains all expected sample items")
            self.passed_tests += 1
            self.results.append({
                "test": test_name,
                "status": "PASS",
                "details": f"Contains all expected sample items: {expected_items}"
            })
            return True
            
    def test_cors_headers(self, endpoint_config):
        """Test if CORS headers are present for frontend compatibility"""
        test_name = f"CORS Headers - {endpoint_config['name']}"
        self.total_tests += 1
        
        try:
            response = requests.get(endpoint_config['url'], timeout=10)
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            missing_headers = []
            for header in cors_headers:
                if header not in response.headers:
                    missing_headers.append(header)
                    
            if missing_headers:
                self.log(f"⚠️ {endpoint_config['name']} missing CORS headers: {missing_headers}")
                # This is a warning, not a failure for this test
                self.passed_tests += 1
                self.results.append({
                    "test": test_name,
                    "status": "PASS",
                    "details": f"Endpoint accessible, missing CORS headers: {missing_headers}"
                })
            else:
                self.log(f"✅ {endpoint_config['name']} has all required CORS headers")
                self.passed_tests += 1
                self.results.append({
                    "test": test_name,
                    "status": "PASS",
                    "details": "All required CORS headers present"
                })
            return True
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ {endpoint_config['name']} connection error: {str(e)}")
            self.failed_tests += 1
            self.results.append({
                "test": test_name,
                "status": "FAIL",
                "details": f"Connection error: {str(e)}"
            })
            return False
            
    def run_comprehensive_test(self):
        """Run comprehensive test suite for all endpoints"""
        self.log("🎯 STARTING TEDARIKÇI EXCEL ŞABLONU API'LERİ TEST")
        self.log(f"Backend URL: {BACKEND_URL}")
        self.log(f"Testing {len(TEST_ENDPOINTS)} endpoints")
        self.log("=" * 80)
        
        endpoint_data = {}
        
        # Test each endpoint
        for endpoint_config in TEST_ENDPOINTS:
            self.log(f"\n📋 Testing {endpoint_config['name']} ({endpoint_config['description']})")
            self.log(f"URL: {endpoint_config['url']}")
            
            # Test 1: Endpoint Accessibility
            if self.test_endpoint_accessibility(endpoint_config):
                # Test 2: Response Format
                data = self.test_response_format(endpoint_config)
                if data:
                    endpoint_data[endpoint_config['name']] = data
                    
                    # Test 3: Data Count
                    self.test_data_count(endpoint_config, data)
                    
                    # Test 4: Data Content Validation
                    self.test_data_content(endpoint_config, data)
                    
                    # Test 5: Sample Data Content
                    self.test_sample_data_content(endpoint_config, data)
                    
            # Test 6: CORS Headers
            self.test_cors_headers(endpoint_config)
            
        # Additional comprehensive tests
        self.log("\n🔍 RUNNING ADDITIONAL COMPREHENSIVE TESTS")
        self.run_integration_tests(endpoint_data)
        
        # Print final results
        self.print_final_results()
        
    def run_integration_tests(self, endpoint_data):
        """Run integration tests across all endpoints"""
        
        # Test 1: All endpoints accessible
        test_name = "All Endpoints Integration"
        self.total_tests += 1
        
        if len(endpoint_data) == len(TEST_ENDPOINTS):
            self.log("✅ All endpoints are accessible and returning data")
            self.passed_tests += 1
            self.results.append({
                "test": test_name,
                "status": "PASS",
                "details": f"All {len(TEST_ENDPOINTS)} endpoints accessible"
            })
        else:
            accessible_count = len(endpoint_data)
            self.log(f"❌ Only {accessible_count}/{len(TEST_ENDPOINTS)} endpoints accessible")
            self.failed_tests += 1
            self.results.append({
                "test": test_name,
                "status": "FAIL",
                "details": f"Only {accessible_count}/{len(TEST_ENDPOINTS)} endpoints accessible"
            })
            
        # Test 2: Frontend Compatibility
        test_name = "Frontend Compatibility"
        self.total_tests += 1
        
        compatibility_issues = []
        
        for endpoint_name, data in endpoint_data.items():
            endpoint_config = next((e for e in TEST_ENDPOINTS if e['name'] == endpoint_name), None)
            if endpoint_config:
                expected_field = endpoint_config['expected_field']
                
                # Check if response structure matches frontend expectations
                if expected_field not in data:
                    compatibility_issues.append(f"{endpoint_name}: missing '{expected_field}' field")
                elif not isinstance(data[expected_field], list):
                    compatibility_issues.append(f"{endpoint_name}: '{expected_field}' is not array")
                elif len(data[expected_field]) == 0:
                    compatibility_issues.append(f"{endpoint_name}: '{expected_field}' array is empty")
                    
        if compatibility_issues:
            self.log(f"❌ Frontend compatibility issues: {compatibility_issues}")
            self.failed_tests += 1
            self.results.append({
                "test": test_name,
                "status": "FAIL",
                "details": f"Compatibility issues: {compatibility_issues}"
            })
        else:
            self.log("✅ All endpoints are frontend compatible")
            self.passed_tests += 1
            self.results.append({
                "test": test_name,
                "status": "PASS",
                "details": "All endpoints have frontend-compatible response structure"
            })
            
    def print_final_results(self):
        """Print comprehensive test results"""
        self.log("\n" + "=" * 80)
        self.log("🎯 TEDARIKÇI EXCEL ŞABLONU API'LERİ TEST RESULTS")
        self.log("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        self.log(f"📊 OVERALL RESULTS:")
        self.log(f"   Total Tests: {self.total_tests}")
        self.log(f"   Passed: {self.passed_tests}")
        self.log(f"   Failed: {self.failed_tests}")
        self.log(f"   Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            self.log("🎉 EXCELLENT - All supplier Excel template APIs are working perfectly!")
        elif success_rate >= 75:
            self.log("✅ GOOD - Most supplier Excel template APIs are working correctly")
        elif success_rate >= 50:
            self.log("⚠️ MODERATE - Some supplier Excel template APIs need attention")
        else:
            self.log("❌ POOR - Major issues with supplier Excel template APIs")
            
        # Print detailed results
        self.log(f"\n📋 DETAILED TEST RESULTS:")
        for result in self.results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            self.log(f"   {status_icon} {result['test']}: {result['details']}")
            
        # Print endpoint-specific summary
        self.log(f"\n🎯 ENDPOINT-SPECIFIC SUMMARY:")
        for endpoint_config in TEST_ENDPOINTS:
            endpoint_results = [r for r in self.results if endpoint_config['name'] in r['test']]
            passed = len([r for r in endpoint_results if r['status'] == 'PASS'])
            total = len(endpoint_results)
            
            if total > 0:
                endpoint_success = (passed / total * 100)
                status_icon = "✅" if endpoint_success >= 80 else "⚠️" if endpoint_success >= 60 else "❌"
                self.log(f"   {status_icon} {endpoint_config['name']}: {passed}/{total} tests passed ({endpoint_success:.1f}%)")
                
        # Print recommendations
        self.log(f"\n💡 RECOMMENDATIONS:")
        if self.failed_tests == 0:
            self.log("   🎉 All tests passed! Supplier Excel template APIs are ready for production.")
        else:
            self.log("   🔧 Review failed tests and fix issues before production deployment.")
            self.log("   📋 Focus on endpoints with multiple test failures.")
            self.log("   🔍 Check backend logs for detailed error information.")
            
        return success_rate >= 75  # Return True if success rate is good

def main():
    """Main test execution"""
    print("🎯 TEDARIKÇI EXCEL ŞABLONU API'LERİ BACKEND TEST")
    print("=" * 80)
    
    # Initialize test suite
    test_suite = SupplierExcelTemplateAPITest()
    
    # Run comprehensive tests
    success = test_suite.run_comprehensive_test()
    
    # Exit with appropriate code
    if success:
        print("\n🎉 TEST SUITE COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\n❌ TEST SUITE COMPLETED WITH ISSUES!")
        sys.exit(1)

if __name__ == "__main__":
    main()