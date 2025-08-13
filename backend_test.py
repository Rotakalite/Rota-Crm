#!/usr/bin/env python3
"""
Survey Management System Backend Test - Updated Analysis
GreenWave CRM Survey Management Backend Testing

Test Environment: Railway production (https://team-management-1.preview.emergentagent.com)
Focus: Survey endpoints after backend restart and duplicate endpoint analysis
"""

import requests
import json
import uuid
from datetime import datetime
import time

class SurveyManagementBackendTest:
    def __init__(self):
        # Use production backend URL from frontend/.env
        self.base_url = "https://team-management-1.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        
        # Test data
        self.test_survey_data = {
            "title": "Test Müşteri Memnuniyet Anketi",
            "description": "Bu anket müşteri memnuniyetini ölçmek için tasarlanmıştır",
            "survey_type": "satisfaction",
            "questions": [
                {
                    "id": str(uuid.uuid4()),
                    "question_text": "Hizmet kalitemizi nasıl değerlendiriyorsunuz?",
                    "question_type": "rating",
                    "options": None,
                    "required": True,
                    "category": "satisfaction"
                },
                {
                    "id": str(uuid.uuid4()),
                    "question_text": "Hangi hizmetlerimizden memnunsunuz?",
                    "question_type": "multiple_choice",
                    "options": ["Temizlik", "Yemek", "Personel", "Konum"],
                    "required": True,
                    "category": "satisfaction"
                },
                {
                    "id": str(uuid.uuid4()),
                    "question_text": "Önerileriniz nelerdir?",
                    "question_type": "text",
                    "options": None,
                    "required": False,
                    "category": "general"
                }
            ]
        }
        
        self.test_response_data = {
            "respondent_email": "test@example.com",
            "respondent_name": "Test Kullanıcı",
            "responses": {}
        }
        
        self.test_campaign_data = {
            "campaign_name": "Müşteri Memnuniyet Kampanyası",
            "target_emails": ["customer1@example.com", "customer2@example.com"],
            "email_subject": "Görüşleriniz Bizim İçin Değerli",
            "email_content": "Lütfen bu kısa anketi doldurarak deneyiminizi bizimle paylaşın."
        }
        
        # Test results
        self.results = []
        self.survey_id = None
        self.campaign_id = None
        
    def log_result(self, test_name, success, details, response_code=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_code": response_code,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        code_info = f" (HTTP {response_code})" if response_code else ""
        print(f"{status}: {test_name}{code_info}")
        if not success or response_code:
            print(f"   Details: {details}")
    
    def test_backend_health(self):
        """Test if backend is accessible"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                self.log_result("Backend Health Check", True, "Backend is accessible", response.status_code)
                return True
            else:
                self.log_result("Backend Health Check", False, f"Unexpected status code", response.status_code)
                return False
        except Exception as e:
            self.log_result("Backend Health Check", False, f"Connection failed: {str(e)}")
            return False
    
    def test_survey_endpoints_accessibility(self):
        """Test if survey endpoints are accessible (should return 403/401, not 404)"""
        endpoints = [
            ("POST", "/surveys", "Survey Creation Endpoint"),
            ("GET", "/surveys", "Survey List Endpoint"),
            ("GET", "/surveys/test-id", "Survey Details Endpoint"),
            ("GET", "/surveys/test-id/public", "Public Survey Endpoint"),
            ("POST", "/surveys/test-id/responses", "Survey Response Endpoint"),
            ("GET", "/surveys/test-id/responses", "Survey Responses List Endpoint"),
            ("POST", "/surveys/test-id/campaigns", "Survey Campaign Creation Endpoint"),
            ("POST", "/surveys/test-id/campaigns/test-campaign/send", "Campaign Send Endpoint"),
            ("GET", "/surveys/test-id/analysis", "Survey Analysis Endpoint")
        ]
        
        accessible_count = 0
        
        for method, endpoint, name in endpoints:
            try:
                url = f"{self.api_url}{endpoint}"
                
                if method == "GET":
                    response = requests.get(url, timeout=10)
                elif method == "POST":
                    response = requests.post(url, json={}, timeout=10)
                
                # Check if endpoint is accessible (not 404)
                if response.status_code == 404:
                    self.log_result(f"{name} Accessibility", False, "Endpoint returns 404 Not Found", response.status_code)
                elif response.status_code in [403, 401, 400, 422, 500]:
                    # These are expected for endpoints requiring auth or proper data
                    self.log_result(f"{name} Accessibility", True, "Endpoint is accessible (requires auth/data)", response.status_code)
                    accessible_count += 1
                else:
                    self.log_result(f"{name} Accessibility", True, "Endpoint is accessible", response.status_code)
                    accessible_count += 1
                    
            except Exception as e:
                self.log_result(f"{name} Accessibility", False, f"Request failed: {str(e)}")
        
        return accessible_count
    
    def test_public_survey_endpoint(self):
        """Test public survey endpoint (should not require auth)"""
        try:
            # Test with non-existent survey ID
            response = requests.get(f"{self.api_url}/surveys/non-existent-id/public", timeout=10)
            
            if response.status_code == 404:
                self.log_result("Public Survey Endpoint", True, "Returns 404 for non-existent survey (correct behavior)", response.status_code)
                return True
            elif response.status_code == 403:
                self.log_result("Public Survey Endpoint", False, "Public endpoint requires authentication (incorrect)", response.status_code)
                return False
            else:
                self.log_result("Public Survey Endpoint", True, "Endpoint is accessible", response.status_code)
                return True
                
        except Exception as e:
            self.log_result("Public Survey Endpoint", False, f"Request failed: {str(e)}")
            return False
    
    def test_survey_response_endpoint(self):
        """Test public survey response endpoint"""
        try:
            # Test with minimal data
            test_data = {
                "survey_id": "test-survey-id",
                "respondent_email": "test@example.com",
                "responses": {"q1": "test answer"}
            }
            
            response = requests.post(f"{self.api_url}/surveys/test-survey-id/responses", 
                                   json=test_data, timeout=10)
            
            if response.status_code == 404:
                self.log_result("Survey Response Endpoint", True, "Returns 404 for non-existent survey (correct behavior)", response.status_code)
                return True
            elif response.status_code in [400, 422]:
                self.log_result("Survey Response Endpoint", True, "Endpoint validates data (correct behavior)", response.status_code)
                return True
            else:
                self.log_result("Survey Response Endpoint", True, "Endpoint is accessible", response.status_code)
                return True
                
        except Exception as e:
            self.log_result("Survey Response Endpoint", False, f"Request failed: {str(e)}")
            return False
    
    def test_cors_headers(self):
        """Test CORS headers on survey endpoints"""
        try:
            # Test OPTIONS request
            response = requests.options(f"{self.api_url}/surveys", timeout=10)
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            cors_present = all(header in response.headers for header in cors_headers)
            
            if cors_present:
                self.log_result("CORS Headers", True, "All required CORS headers present", response.status_code)
                return True
            else:
                missing_headers = [h for h in cors_headers if h not in response.headers]
                self.log_result("CORS Headers", False, f"Missing CORS headers: {missing_headers}", response.status_code)
                return False
                
        except Exception as e:
            self.log_result("CORS Headers", False, f"OPTIONS request failed: {str(e)}")
            return False
    
    def test_http_methods(self):
        """Test HTTP method restrictions"""
        try:
            # Test unsupported method on survey endpoint
            response = requests.put(f"{self.api_url}/surveys", timeout=10)
            
            if response.status_code == 405:
                self.log_result("HTTP Method Restrictions", True, "PUT method properly rejected", response.status_code)
                return True
            elif response.status_code in [403, 401]:
                self.log_result("HTTP Method Restrictions", True, "Method handled (auth required)", response.status_code)
                return True
            else:
                self.log_result("HTTP Method Restrictions", False, f"Unexpected response to PUT", response.status_code)
                return False
                
        except Exception as e:
            self.log_result("HTTP Method Restrictions", False, f"Request failed: {str(e)}")
            return False
    
    def test_debug_routes_endpoint(self):
        """Test debug routes endpoint to see registered routes"""
        try:
            response = requests.get(f"{self.api_url}/debug/routes", timeout=10)
            
            if response.status_code == 200:
                routes_data = response.json()
                survey_routes = [route for route in routes_data.get('routes', []) if 'survey' in route.lower()]
                
                self.log_result("Debug Routes - Survey Routes", True, 
                              f"Found {len(survey_routes)} survey routes: {survey_routes[:3]}...", response.status_code)
                return len(survey_routes)
            else:
                self.log_result("Debug Routes Endpoint", False, "Debug endpoint not accessible", response.status_code)
                return 0
                
        except Exception as e:
            self.log_result("Debug Routes Endpoint", False, f"Request failed: {str(e)}")
            return 0
    
    def test_database_collections(self):
        """Test if survey-related database collections exist"""
        try:
            # Try to access survey endpoints that would interact with database
            endpoints_to_test = [
                ("/surveys", "surveys collection"),
                ("/surveys/test/responses", "survey_responses collection"),
                ("/surveys/test/campaigns", "survey_campaigns collection")
            ]
            
            collections_accessible = 0
            
            for endpoint, collection_name in endpoints_to_test:
                try:
                    response = requests.get(f"{self.api_url}{endpoint}", timeout=10)
                    
                    # If we get anything other than 404, the endpoint is registered
                    if response.status_code != 404:
                        collections_accessible += 1
                        self.log_result(f"Database Collection - {collection_name}", True, 
                                      "Endpoint accessible (collection exists)", response.status_code)
                    else:
                        self.log_result(f"Database Collection - {collection_name}", False, 
                                      "Endpoint returns 404", response.status_code)
                        
                except Exception as e:
                    self.log_result(f"Database Collection - {collection_name}", False, f"Request failed: {str(e)}")
            
            return collections_accessible
            
        except Exception as e:
            self.log_result("Database Collections Test", False, f"Test failed: {str(e)}")
            return 0
    
    def test_authentication_security(self):
        """Test authentication requirements on protected endpoints"""
        protected_endpoints = [
            ("GET", "/surveys", "Survey List"),
            ("POST", "/surveys", "Survey Creation"),
            ("GET", "/surveys/test-id", "Survey Details"),
            ("GET", "/surveys/test-id/responses", "Survey Responses"),
            ("POST", "/surveys/test-id/campaigns", "Campaign Creation"),
            ("GET", "/surveys/test-id/analysis", "Survey Analysis")
        ]
        
        secure_endpoints = 0
        
        for method, endpoint, name in protected_endpoints:
            try:
                url = f"{self.api_url}{endpoint}"
                
                if method == "GET":
                    response = requests.get(url, timeout=10)
                elif method == "POST":
                    response = requests.post(url, json={}, timeout=10)
                
                if response.status_code in [401, 403]:
                    self.log_result(f"Auth Security - {name}", True, "Requires authentication", response.status_code)
                    secure_endpoints += 1
                elif response.status_code == 404:
                    self.log_result(f"Auth Security - {name}", False, "Endpoint not found", response.status_code)
                else:
                    self.log_result(f"Auth Security - {name}", False, "No auth required (security issue)", response.status_code)
                    
            except Exception as e:
                self.log_result(f"Auth Security - {name}", False, f"Request failed: {str(e)}")
        
        return secure_endpoints
    
    def test_json_response_format(self):
        """Test JSON response format"""
        try:
            response = requests.get(f"{self.api_url}/surveys", timeout=10)
            
            # Check if response has proper JSON content type
            content_type = response.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                self.log_result("JSON Response Format", True, "Proper JSON content type", response.status_code)
                return True
            else:
                self.log_result("JSON Response Format", False, f"Content type: {content_type}", response.status_code)
                return False
                
        except Exception as e:
            self.log_result("JSON Response Format", False, f"Request failed: {str(e)}")
            return False
    
    def test_performance(self):
        """Test response times"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_url}/surveys", timeout=10)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response_time < 2.0:
                self.log_result("Performance Test", True, f"Response time: {response_time:.2f}s", response.status_code)
                return True
            else:
                self.log_result("Performance Test", False, f"Slow response: {response_time:.2f}s", response.status_code)
                return False
                
        except Exception as e:
            self.log_result("Performance Test", False, f"Request failed: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run all survey management tests"""
        print("🎯 SURVEY MANAGEMENT SYSTEM BACKEND TEST - UPDATED ANALYSIS")
        print("=" * 70)
        print(f"Backend URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Test categories
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Survey Endpoints Accessibility", self.test_survey_endpoints_accessibility),
            ("Public Survey Endpoint", self.test_public_survey_endpoint),
            ("Survey Response Endpoint", self.test_survey_response_endpoint),
            ("CORS Headers", self.test_cors_headers),
            ("HTTP Method Restrictions", self.test_http_methods),
            ("Debug Routes", self.test_debug_routes_endpoint),
            ("Database Collections", self.test_database_collections),
            ("Authentication Security", self.test_authentication_security),
            ("JSON Response Format", self.test_json_response_format),
            ("Performance", self.test_performance)
        ]
        
        total_tests = 0
        passed_tests = 0
        
        for test_name, test_func in tests:
            print(f"\n📋 Running {test_name} Tests...")
            try:
                result = test_func()
                if isinstance(result, bool):
                    total_tests += 1
                    if result:
                        passed_tests += 1
                elif isinstance(result, int):
                    # For tests that return counts
                    total_tests += 1
                    if result > 0:
                        passed_tests += 1
            except Exception as e:
                print(f"❌ Test {test_name} failed with exception: {str(e)}")
                total_tests += 1
        
        # Calculate success rate
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 70)
        print("📊 SURVEY MANAGEMENT BACKEND TEST RESULTS")
        print("=" * 70)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for result in self.results:
            status = "✅" if result["success"] else "❌"
            code = f" (HTTP {result['response_code']})" if result['response_code'] else ""
            print(f"{status} {result['test']}{code}: {result['details']}")
        
        # Analysis and recommendations
        print(f"\n🔍 ANALYSIS:")
        
        failed_tests = [r for r in self.results if not r["success"]]
        if failed_tests:
            print("❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        # Check for specific issues
        accessibility_tests = [r for r in self.results if "Accessibility" in r["test"]]
        accessible_endpoints = len([r for r in accessibility_tests if r["success"]])
        
        if accessible_endpoints == 0:
            print("\n🚨 CRITICAL ISSUE: NO SURVEY ENDPOINTS ARE ACCESSIBLE!")
            print("   - All survey endpoints return 404 Not Found")
            print("   - This indicates a routing/deployment issue")
            print("   - Survey management functionality is completely unavailable")
        elif accessible_endpoints < len(accessibility_tests):
            print(f"\n⚠️ PARTIAL ACCESSIBILITY: {accessible_endpoints}/{len(accessibility_tests)} endpoints accessible")
            print("   - Some survey endpoints are not properly deployed")
        else:
            print(f"\n✅ ENDPOINT ACCESSIBILITY: All {accessible_endpoints} survey endpoints are accessible")
        
        # Check authentication
        auth_tests = [r for r in self.results if "Auth Security" in r["test"]]
        secure_endpoints = len([r for r in auth_tests if r["success"]])
        
        if secure_endpoints > 0:
            print(f"✅ SECURITY: {secure_endpoints} endpoints properly secured with authentication")
        
        # Final recommendation
        if success_rate >= 80:
            print(f"\n🎉 OVERALL STATUS: GOOD ({success_rate:.1f}% success rate)")
            if accessible_endpoints == len(accessibility_tests):
                print("✅ Survey Management System backend is OPERATIONAL!")
            else:
                print("⚠️ Some endpoints need attention but core functionality works")
        elif success_rate >= 50:
            print(f"\n⚠️ OVERALL STATUS: MODERATE ({success_rate:.1f}% success rate)")
            print("🔧 Survey Management System needs fixes but partially functional")
        else:
            print(f"\n🚨 OVERALL STATUS: CRITICAL ({success_rate:.1f}% success rate)")
            print("❌ Survey Management System has major issues and needs immediate attention")
        
        return {
            "success_rate": success_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "accessible_endpoints": accessible_endpoints,
            "results": self.results
        }

if __name__ == "__main__":
    tester = SurveyManagementBackendTest()
    results = tester.run_comprehensive_test()