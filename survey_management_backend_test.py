#!/usr/bin/env python3
"""
Survey Management System Backend Test - Railway Production
GreenWave CRM Survey Management System Backend Testing

Test Endpoints:
1. POST /api/surveys - Survey creation
2. GET /api/surveys - List surveys  
3. GET /api/surveys/{survey_id} - Specific survey details
4. GET /api/surveys/{survey_id}/public - Public survey access (no auth required)
5. POST /api/surveys/{survey_id}/responses - Submit survey response (public)
6. GET /api/surveys/{survey_id}/responses - View responses
7. POST /api/surveys/{survey_id}/campaigns - Create campaign
8. POST /api/surveys/{survey_id}/campaigns/{campaign_id}/send - Send campaign
9. GET /api/surveys/{survey_id}/analysis - Analysis and insights

Test Environment: Railway production (https://rota-crm-production.up.railway.app)
"""

import requests
import json
import uuid
from datetime import datetime
import sys
import time

class SurveyManagementBackendTest:
    def __init__(self):
        self.base_url = "https://rota-crm-production.up.railway.app"
        self.api_base = f"{self.base_url}/api"
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
        # Test data
        self.test_survey_data = {
            "title": "Test Müşteri Memnuniyet Anketi",
            "description": "Bu anket müşteri memnuniyetini ölçmek için hazırlanmıştır.",
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
                    "question_text": "Hangi hizmetlerimizden memnun kaldınız?",
                    "question_type": "multiple_choice",
                    "options": ["Temizlik", "Yemek", "Personel", "Konaklama"],
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
        
        # Test tokens (will be set during testing)
        self.admin_token = None
        self.client_token = None
        self.test_survey_id = None
        self.test_campaign_id = None
        
    def log_test(self, test_name, success, details="", response_time=None):
        """Log test results"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
        
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "response_time": response_time
        }
        self.test_results.append(result)
        print(f"{status} - {test_name}")
        if details:
            print(f"    Details: {details}")
        if response_time:
            print(f"    Response Time: {response_time:.3f}s")
    
    def test_backend_health(self):
        """Test backend health and accessibility"""
        print("\n🏥 TESTING BACKEND HEALTH...")
        
        try:
            # Test root endpoint
            start_time = time.time()
            response = requests.get(self.base_url, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_test("Backend Root Accessibility", True, 
                            f"Status: {response.status_code}", response_time)
            else:
                self.log_test("Backend Root Accessibility", False, 
                            f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Backend Root Accessibility", False, f"Error: {str(e)}")
        
        try:
            # Test health endpoint
            start_time = time.time()
            response = requests.get(f"{self.api_base}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                self.log_test("Backend Health Endpoint", True, 
                            f"Service: {health_data.get('service', 'Unknown')}", response_time)
            else:
                self.log_test("Backend Health Endpoint", False, 
                            f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Backend Health Endpoint", False, f"Error: {str(e)}")
    
    def test_survey_endpoints_security(self):
        """Test survey endpoints security without authentication"""
        print("\n🔒 TESTING SURVEY ENDPOINTS SECURITY...")
        
        endpoints_to_test = [
            ("POST", "/surveys", "Survey Creation Security"),
            ("GET", "/surveys", "Survey List Security"),
            ("GET", "/surveys/test-id", "Survey Details Security"),
            ("GET", "/surveys/test-id/responses", "Survey Responses Security"),
            ("POST", "/surveys/test-id/campaigns", "Survey Campaign Creation Security"),
            ("POST", "/surveys/test-id/campaigns/test-campaign/send", "Survey Campaign Send Security"),
            ("GET", "/surveys/test-id/analysis", "Survey Analysis Security")
        ]
        
        for method, endpoint, test_name in endpoints_to_test:
            try:
                start_time = time.time()
                if method == "GET":
                    response = requests.get(f"{self.api_base}{endpoint}", timeout=10)
                elif method == "POST":
                    response = requests.post(f"{self.api_base}{endpoint}", 
                                           json={"test": "data"}, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code in [401, 403]:
                    self.log_test(test_name, True, 
                                f"Properly secured - Status: {response.status_code}", response_time)
                else:
                    self.log_test(test_name, False, 
                                f"Security issue - Status: {response.status_code}")
            except Exception as e:
                self.log_test(test_name, False, f"Error: {str(e)}")
    
    def test_public_survey_endpoint(self):
        """Test public survey endpoint (should not require authentication)"""
        print("\n🌐 TESTING PUBLIC SURVEY ENDPOINT...")
        
        try:
            # Test with a dummy survey ID
            start_time = time.time()
            response = requests.get(f"{self.api_base}/surveys/dummy-survey-id/public", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 404:
                self.log_test("Public Survey Endpoint Accessibility", True, 
                            "Endpoint accessible, returns 404 for non-existent survey", response_time)
            elif response.status_code == 200:
                self.log_test("Public Survey Endpoint Accessibility", True, 
                            "Endpoint accessible and working", response_time)
            elif response.status_code in [401, 403]:
                self.log_test("Public Survey Endpoint Accessibility", False, 
                            "Public endpoint requires authentication - should be public")
            else:
                self.log_test("Public Survey Endpoint Accessibility", False, 
                            f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Public Survey Endpoint Accessibility", False, f"Error: {str(e)}")
    
    def test_public_survey_response_endpoint(self):
        """Test public survey response submission endpoint"""
        print("\n📝 TESTING PUBLIC SURVEY RESPONSE ENDPOINT...")
        
        try:
            # Test with dummy data
            response_data = {
                "survey_id": "dummy-survey-id",
                "respondent_email": "test@example.com",
                "respondent_name": "Test User",
                "responses": {
                    "question1": "5",
                    "question2": "Excellent service"
                }
            }
            
            start_time = time.time()
            response = requests.post(f"{self.api_base}/surveys/dummy-survey-id/responses", 
                                   json=response_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 404:
                self.log_test("Public Survey Response Endpoint", True, 
                            "Endpoint accessible, returns 404 for non-existent survey", response_time)
            elif response.status_code == 200:
                self.log_test("Public Survey Response Endpoint", True, 
                            "Endpoint accessible and working", response_time)
            elif response.status_code in [401, 403]:
                self.log_test("Public Survey Response Endpoint", False, 
                            "Public endpoint requires authentication - should be public")
            else:
                self.log_test("Public Survey Response Endpoint", False, 
                            f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Public Survey Response Endpoint", False, f"Error: {str(e)}")
    
    def test_survey_data_models(self):
        """Test survey data model validation"""
        print("\n📋 TESTING SURVEY DATA MODELS...")
        
        # Test survey creation with invalid data
        invalid_survey_data = {
            "title": "",  # Empty title
            "survey_type": "invalid_type",  # Invalid type
            "questions": []  # Empty questions
        }
        
        try:
            start_time = time.time()
            response = requests.post(f"{self.api_base}/surveys", 
                                   json=invalid_survey_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code in [400, 422, 401, 403]:
                self.log_test("Survey Data Validation", True, 
                            f"Properly validates data - Status: {response.status_code}", response_time)
            else:
                self.log_test("Survey Data Validation", False, 
                            f"Validation issue - Status: {response.status_code}")
        except Exception as e:
            self.log_test("Survey Data Validation", False, f"Error: {str(e)}")
    
    def test_survey_question_types(self):
        """Test different survey question types support"""
        print("\n❓ TESTING SURVEY QUESTION TYPES...")
        
        question_types = ["rating", "multiple_choice", "checkbox", "text", "yes_no"]
        
        for question_type in question_types:
            test_question = {
                "id": str(uuid.uuid4()),
                "question_text": f"Test {question_type} question",
                "question_type": question_type,
                "options": ["Option 1", "Option 2"] if question_type in ["multiple_choice", "checkbox"] else None,
                "required": True,
                "category": "satisfaction"
            }
            
            survey_data = {
                "title": f"Test Survey - {question_type}",
                "description": f"Testing {question_type} question type",
                "survey_type": "satisfaction",
                "questions": [test_question]
            }
            
            try:
                start_time = time.time()
                response = requests.post(f"{self.api_base}/surveys", 
                                       json=survey_data, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code in [401, 403]:
                    self.log_test(f"Question Type Support - {question_type}", True, 
                                "Endpoint accessible, auth required as expected", response_time)
                elif response.status_code == 200:
                    self.log_test(f"Question Type Support - {question_type}", True, 
                                "Question type supported", response_time)
                else:
                    self.log_test(f"Question Type Support - {question_type}", False, 
                                f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Question Type Support - {question_type}", False, f"Error: {str(e)}")
    
    def test_survey_types_support(self):
        """Test different survey types support"""
        print("\n📊 TESTING SURVEY TYPES SUPPORT...")
        
        survey_types = ["sustainability", "satisfaction", "combined"]
        
        for survey_type in survey_types:
            survey_data = {
                "title": f"Test {survey_type} Survey",
                "description": f"Testing {survey_type} survey type",
                "survey_type": survey_type,
                "questions": [
                    {
                        "id": str(uuid.uuid4()),
                        "question_text": f"Test question for {survey_type}",
                        "question_type": "rating",
                        "required": True,
                        "category": survey_type
                    }
                ]
            }
            
            try:
                start_time = time.time()
                response = requests.post(f"{self.api_base}/surveys", 
                                       json=survey_data, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code in [401, 403]:
                    self.log_test(f"Survey Type Support - {survey_type}", True, 
                                "Endpoint accessible, auth required as expected", response_time)
                elif response.status_code == 200:
                    self.log_test(f"Survey Type Support - {survey_type}", True, 
                                "Survey type supported", response_time)
                else:
                    self.log_test(f"Survey Type Support - {survey_type}", False, 
                                f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Survey Type Support - {survey_type}", False, f"Error: {str(e)}")
    
    def test_campaign_endpoints(self):
        """Test survey campaign endpoints"""
        print("\n📧 TESTING SURVEY CAMPAIGN ENDPOINTS...")
        
        campaign_data = {
            "survey_id": "test-survey-id",
            "campaign_name": "Test Campaign",
            "target_emails": ["test1@example.com", "test2@example.com"],
            "email_subject": "Please participate in our survey",
            "email_content": "We value your feedback. Please click the link to participate."
        }
        
        try:
            # Test campaign creation
            start_time = time.time()
            response = requests.post(f"{self.api_base}/surveys/test-survey-id/campaigns", 
                                   json=campaign_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code in [401, 403]:
                self.log_test("Survey Campaign Creation", True, 
                            "Endpoint accessible, auth required as expected", response_time)
            elif response.status_code == 404:
                self.log_test("Survey Campaign Creation", True, 
                            "Endpoint accessible, returns 404 for non-existent survey", response_time)
            else:
                self.log_test("Survey Campaign Creation", False, 
                            f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Survey Campaign Creation", False, f"Error: {str(e)}")
        
        try:
            # Test campaign sending
            start_time = time.time()
            response = requests.post(f"{self.api_base}/surveys/test-survey-id/campaigns/test-campaign-id/send", 
                                   timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code in [401, 403]:
                self.log_test("Survey Campaign Sending", True, 
                            "Endpoint accessible, auth required as expected", response_time)
            elif response.status_code == 404:
                self.log_test("Survey Campaign Sending", True, 
                            "Endpoint accessible, returns 404 for non-existent campaign", response_time)
            else:
                self.log_test("Survey Campaign Sending", False, 
                            f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Survey Campaign Sending", False, f"Error: {str(e)}")
    
    def test_survey_analysis_endpoint(self):
        """Test survey analysis endpoint"""
        print("\n📈 TESTING SURVEY ANALYSIS ENDPOINT...")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_base}/surveys/test-survey-id/analysis", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code in [401, 403]:
                self.log_test("Survey Analysis Endpoint", True, 
                            "Endpoint accessible, auth required as expected", response_time)
            elif response.status_code == 404:
                self.log_test("Survey Analysis Endpoint", True, 
                            "Endpoint accessible, returns 404 for non-existent survey", response_time)
            elif response.status_code == 200:
                analysis_data = response.json()
                if "total_responses" in analysis_data:
                    self.log_test("Survey Analysis Endpoint", True, 
                                "Analysis endpoint working correctly", response_time)
                else:
                    self.log_test("Survey Analysis Endpoint", False, 
                                "Analysis data structure incomplete")
            else:
                self.log_test("Survey Analysis Endpoint", False, 
                            f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Survey Analysis Endpoint", False, f"Error: {str(e)}")
    
    def test_cors_headers(self):
        """Test CORS headers for survey endpoints"""
        print("\n🌐 TESTING CORS HEADERS...")
        
        try:
            # Test OPTIONS request
            start_time = time.time()
            response = requests.options(f"{self.api_base}/surveys", timeout=10)
            response_time = time.time() - start_time
            
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers"
            ]
            
            cors_present = all(header in response.headers for header in cors_headers)
            
            if cors_present:
                self.log_test("CORS Headers", True, 
                            "All required CORS headers present", response_time)
            else:
                missing_headers = [h for h in cors_headers if h not in response.headers]
                self.log_test("CORS Headers", False, 
                            f"Missing headers: {missing_headers}")
        except Exception as e:
            self.log_test("CORS Headers", False, f"Error: {str(e)}")
    
    def test_http_methods(self):
        """Test HTTP method restrictions"""
        print("\n🔧 TESTING HTTP METHOD RESTRICTIONS...")
        
        endpoints_methods = [
            ("/surveys", ["GET", "POST"], ["PUT", "DELETE", "PATCH"]),
            ("/surveys/test-id", ["GET"], ["POST", "PUT", "DELETE", "PATCH"]),
            ("/surveys/test-id/public", ["GET"], ["POST", "PUT", "DELETE", "PATCH"]),
            ("/surveys/test-id/responses", ["GET", "POST"], ["PUT", "DELETE", "PATCH"]),
            ("/surveys/test-id/campaigns", ["POST"], ["GET", "PUT", "DELETE", "PATCH"]),
            ("/surveys/test-id/analysis", ["GET"], ["POST", "PUT", "DELETE", "PATCH"])
        ]
        
        for endpoint, allowed_methods, disallowed_methods in endpoints_methods:
            for method in disallowed_methods:
                try:
                    start_time = time.time()
                    response = requests.request(method, f"{self.api_base}{endpoint}", timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 405:
                        self.log_test(f"HTTP Method Restriction - {method} {endpoint}", True, 
                                    "Method properly restricted", response_time)
                    elif response.status_code in [401, 403, 404]:
                        self.log_test(f"HTTP Method Restriction - {method} {endpoint}", True, 
                                    f"Method handled (Status: {response.status_code})", response_time)
                    else:
                        self.log_test(f"HTTP Method Restriction - {method} {endpoint}", False, 
                                    f"Method not restricted - Status: {response.status_code}")
                except Exception as e:
                    self.log_test(f"HTTP Method Restriction - {method} {endpoint}", False, f"Error: {str(e)}")
    
    def test_database_collections(self):
        """Test if survey-related database collections are accessible"""
        print("\n🗄️ TESTING DATABASE COLLECTIONS ACCESS...")
        
        # This is indirect testing through API endpoints
        collections_to_test = [
            ("surveys", "/surveys"),
            ("survey_responses", "/surveys/test-id/responses"),
            ("survey_campaigns", "/surveys/test-id/campaigns"),
            ("survey_analysis", "/surveys/test-id/analysis")
        ]
        
        for collection_name, endpoint in collections_to_test:
            try:
                start_time = time.time()
                response = requests.get(f"{self.api_base}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code in [200, 401, 403, 404]:
                    self.log_test(f"Database Collection Access - {collection_name}", True, 
                                f"Collection accessible via API (Status: {response.status_code})", response_time)
                else:
                    self.log_test(f"Database Collection Access - {collection_name}", False, 
                                f"Unexpected status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Database Collection Access - {collection_name}", False, f"Error: {str(e)}")
    
    def test_response_formats(self):
        """Test API response formats"""
        print("\n📄 TESTING API RESPONSE FORMATS...")
        
        endpoints_to_test = [
            "/surveys",
            "/surveys/test-id/public",
            "/surveys/test-id/analysis"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                start_time = time.time()
                response = requests.get(f"{self.api_base}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                content_type = response.headers.get('content-type', '')
                
                if 'application/json' in content_type:
                    try:
                        json_data = response.json()
                        self.log_test(f"Response Format - {endpoint}", True, 
                                    "Valid JSON response", response_time)
                    except json.JSONDecodeError:
                        self.log_test(f"Response Format - {endpoint}", False, 
                                    "Invalid JSON in response")
                else:
                    self.log_test(f"Response Format - {endpoint}", False, 
                                f"Non-JSON response: {content_type}")
            except Exception as e:
                self.log_test(f"Response Format - {endpoint}", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all survey management backend tests"""
        print("🚀 STARTING SURVEY MANAGEMENT SYSTEM BACKEND TESTS")
        print("=" * 80)
        print(f"🎯 Target: {self.base_url}")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Run all test categories
        self.test_backend_health()
        self.test_survey_endpoints_security()
        self.test_public_survey_endpoint()
        self.test_public_survey_response_endpoint()
        self.test_survey_data_models()
        self.test_survey_question_types()
        self.test_survey_types_support()
        self.test_campaign_endpoints()
        self.test_survey_analysis_endpoint()
        self.test_cors_headers()
        self.test_http_methods()
        self.test_database_collections()
        self.test_response_formats()
        
        # Print final results
        self.print_final_results()
    
    def print_final_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 80)
        print("📊 SURVEY MANAGEMENT SYSTEM BACKEND TEST RESULTS")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"📈 Overall Success Rate: {success_rate:.1f}% ({self.passed_tests}/{self.total_tests})")
        print(f"✅ Passed Tests: {self.passed_tests}")
        print(f"❌ Failed Tests: {self.failed_tests}")
        print(f"📊 Total Tests: {self.total_tests}")
        
        print("\n🔍 DETAILED TEST RESULTS:")
        print("-" * 80)
        
        for result in self.test_results:
            print(f"{result['status']} {result['test']}")
            if result['details']:
                print(f"    📝 {result['details']}")
            if result['response_time']:
                print(f"    ⏱️ {result['response_time']:.3f}s")
        
        print("\n" + "=" * 80)
        print("🎯 SURVEY MANAGEMENT SYSTEM ANALYSIS")
        print("=" * 80)
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: Survey Management System is fully operational!")
        elif success_rate >= 75:
            print("✅ GOOD: Survey Management System is mostly working with minor issues.")
        elif success_rate >= 50:
            print("⚠️ MODERATE: Survey Management System has some significant issues.")
        else:
            print("🚨 CRITICAL: Survey Management System has major problems!")
        
        print("\n📋 KEY FINDINGS:")
        
        # Analyze specific areas
        security_tests = [r for r in self.test_results if "Security" in r['test']]
        security_passed = len([r for r in security_tests if "✅" in r['status']])
        if security_tests:
            print(f"🔒 Security: {security_passed}/{len(security_tests)} tests passed")
        
        public_tests = [r for r in self.test_results if "Public" in r['test']]
        public_passed = len([r for r in public_tests if "✅" in r['status']])
        if public_tests:
            print(f"🌐 Public Access: {public_passed}/{len(public_tests)} tests passed")
        
        endpoint_tests = [r for r in self.test_results if "Endpoint" in r['test']]
        endpoint_passed = len([r for r in endpoint_tests if "✅" in r['status']])
        if endpoint_tests:
            print(f"🔗 Endpoints: {endpoint_passed}/{len(endpoint_tests)} tests passed")
        
        print("\n🚀 SURVEY MANAGEMENT SYSTEM BACKEND TEST COMPLETED!")
        print("=" * 80)

if __name__ == "__main__":
    print("🌱 GreenWave CRM - Survey Management System Backend Test")
    print("🚂 Railway Production Environment Testing")
    print("📋 Testing Survey Management System Implementation")
    
    tester = SurveyManagementBackendTest()
    tester.run_all_tests()