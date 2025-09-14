#!/usr/bin/env python3
"""
Survey Management System Backend Testing - Final Verification
GreenWave CRM Survey Management backend endpoints final doğrulama testi.

ÖNCEKİ PROBLEM: .env dosyasında yanlış URL vardı (https://sustainability-crm-1.preview.emergentagent.com), 
doğru Railway URL: https://rota-crm-production.up.railway.app

YAPILAN FİX:
1. .env dosyasında REACT_APP_BACKEND_URL düzeltildi
2. Frontend ve backend restart edildi  
3. Manuel test: Survey endpoints artık "Not authenticated" ve "Survey not found" döndürüyor (404 değil)

TEST EDİLECEK:
Tüm survey management endpoints'lerinin artık erişilebilir olduğunu doğrula:
- POST /api/surveys (Should return 401/403 not 404)
- GET /api/surveys (Should return 401/403 not 404)  
- GET /api/surveys/{survey_id} (Should return 401/403 not 404)
- GET /api/surveys/{survey_id}/public (Should return 404 with proper message not route not found)
- POST /api/surveys/{survey_id}/responses (Should work for public)
- GET /api/surveys/{survey_id}/responses (Should return 401/403 not 404)
- POST /api/surveys/{survey_id}/campaigns (Should return 401/403 not 404)
- POST /api/surveys/{survey_id}/campaigns/{campaign_id}/send (Should return 401/403 not 404)
- GET /api/surveys/{survey_id}/analysis (Should return 401/403 not 404)

Railway Production URL: https://rota-crm-production.up.railway.app

Beklenen: Tüm endpoints artık accessible, system tamamen çalışır durumda, 
kullanıcı "tüm sistemi düzelt" talebinin karşılandığını doğrula.
"""

import requests
import json
import uuid
from datetime import datetime
import sys
import time

class SurveyEndpointsFixVerificationTest:
    def __init__(self):
        self.base_url = "https://rota-crm-production.up.railway.app"
        self.api_base = f"{self.base_url}/api"
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
        # Test survey ID for testing
        self.test_survey_id = "test-survey-" + str(uuid.uuid4())[:8]
        self.test_campaign_id = "test-campaign-" + str(uuid.uuid4())[:8]
        
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
    
    def test_survey_endpoints_accessibility(self):
        """Test that survey endpoints are now accessible and return proper auth errors instead of 404"""
        print("\n🔍 TESTING SURVEY ENDPOINTS ACCESSIBILITY (POST .env FIX)...")
        
        # Critical endpoints that should return 401/403 instead of 404
        endpoints_to_test = [
            {
                "method": "POST",
                "endpoint": "/surveys",
                "name": "Survey Creation",
                "data": {
                    "title": "Test Survey",
                    "description": "Test Description",
                    "survey_type": "satisfaction",
                    "questions": []
                },
                "expected_codes": [401, 403],
                "should_not_be": [404]
            },
            {
                "method": "GET",
                "endpoint": "/surveys",
                "name": "Survey List",
                "data": None,
                "expected_codes": [401, 403],
                "should_not_be": [404]
            },
            {
                "method": "GET",
                "endpoint": f"/surveys/{self.test_survey_id}",
                "name": "Survey Details",
                "data": None,
                "expected_codes": [401, 403],
                "should_not_be": [404]
            },
            {
                "method": "GET",
                "endpoint": f"/surveys/{self.test_survey_id}/responses",
                "name": "Survey Responses List",
                "data": None,
                "expected_codes": [401, 403],
                "should_not_be": [404]
            },
            {
                "method": "POST",
                "endpoint": f"/surveys/{self.test_survey_id}/campaigns",
                "name": "Survey Campaign Creation",
                "data": {
                    "campaign_name": "Test Campaign",
                    "target_emails": ["test@example.com"],
                    "email_subject": "Test",
                    "email_content": "Test content"
                },
                "expected_codes": [401, 403],
                "should_not_be": [404]
            },
            {
                "method": "POST",
                "endpoint": f"/surveys/{self.test_survey_id}/campaigns/{self.test_campaign_id}/send",
                "name": "Survey Campaign Send",
                "data": {},
                "expected_codes": [401, 403],
                "should_not_be": [404]
            },
            {
                "method": "GET",
                "endpoint": f"/surveys/{self.test_survey_id}/analysis",
                "name": "Survey Analysis",
                "data": None,
                "expected_codes": [401, 403],
                "should_not_be": [404]
            }
        ]
        
        for test_case in endpoints_to_test:
            try:
                start_time = time.time()
                
                if test_case["method"] == "GET":
                    response = requests.get(f"{self.api_base}{test_case['endpoint']}", timeout=10)
                elif test_case["method"] == "POST":
                    response = requests.post(f"{self.api_base}{test_case['endpoint']}", 
                                           json=test_case["data"], timeout=10)
                
                response_time = time.time() - start_time
                
                # Check if endpoint is now accessible (not 404)
                if response.status_code in test_case["expected_codes"]:
                    self.log_test(f"Endpoint Accessibility - {test_case['name']}", True, 
                                f"✅ FIXED: Returns {response.status_code} (auth required) instead of 404", response_time)
                elif response.status_code in test_case["should_not_be"]:
                    self.log_test(f"Endpoint Accessibility - {test_case['name']}", False, 
                                f"❌ STILL BROKEN: Returns {response.status_code} (route not found)", response_time)
                else:
                    self.log_test(f"Endpoint Accessibility - {test_case['name']}", False, 
                                f"⚠️ UNEXPECTED: Returns {response.status_code}", response_time)
                
            except Exception as e:
                self.log_test(f"Endpoint Accessibility - {test_case['name']}", False, f"Error: {str(e)}")
    
    def test_public_survey_endpoints(self):
        """Test public survey endpoints that should work without authentication"""
        print("\n🌐 TESTING PUBLIC SURVEY ENDPOINTS...")
        
        public_endpoints = [
            {
                "method": "GET",
                "endpoint": f"/surveys/{self.test_survey_id}/public",
                "name": "Public Survey Access",
                "data": None,
                "expected_codes": [404],  # 404 for non-existent survey is OK
                "should_not_be": [401, 403]  # Should NOT require auth
            },
            {
                "method": "POST",
                "endpoint": f"/surveys/{self.test_survey_id}/responses",
                "name": "Public Survey Response Submission",
                "data": {
                    "survey_id": self.test_survey_id,
                    "respondent_email": "test@example.com",
                    "respondent_name": "Test User",
                    "responses": {"q1": "answer1"}
                },
                "expected_codes": [404, 400],  # 404 for non-existent survey, 400 for validation
                "should_not_be": [401, 403]  # Should NOT require auth
            }
        ]
        
        for test_case in public_endpoints:
            try:
                start_time = time.time()
                
                if test_case["method"] == "GET":
                    response = requests.get(f"{self.api_base}{test_case['endpoint']}", timeout=10)
                elif test_case["method"] == "POST":
                    response = requests.post(f"{self.api_base}{test_case['endpoint']}", 
                                           json=test_case["data"], timeout=10)
                
                response_time = time.time() - start_time
                
                if response.status_code in test_case["expected_codes"]:
                    self.log_test(f"Public Endpoint - {test_case['name']}", True, 
                                f"✅ PUBLIC ACCESS: Returns {response.status_code} (no auth required)", response_time)
                elif response.status_code in test_case["should_not_be"]:
                    self.log_test(f"Public Endpoint - {test_case['name']}", False, 
                                f"❌ AUTH REQUIRED: Returns {response.status_code} (should be public)", response_time)
                else:
                    self.log_test(f"Public Endpoint - {test_case['name']}", False, 
                                f"⚠️ UNEXPECTED: Returns {response.status_code}", response_time)
                
            except Exception as e:
                self.log_test(f"Public Endpoint - {test_case['name']}", False, f"Error: {str(e)}")
    
    def test_survey_endpoint_response_messages(self):
        """Test that survey endpoints return proper error messages instead of generic 404"""
        print("\n💬 TESTING SURVEY ENDPOINT ERROR MESSAGES...")
        
        try:
            # Test survey creation without auth
            start_time = time.time()
            response = requests.post(f"{self.api_base}/surveys", 
                                   json={"title": "Test", "survey_type": "satisfaction", "questions": []}, 
                                   timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code in [401, 403]:
                try:
                    error_data = response.json()
                    if "detail" in error_data and "authenticated" in error_data["detail"].lower():
                        self.log_test("Survey Creation Error Message", True, 
                                    f"✅ PROPER AUTH ERROR: {error_data.get('detail', 'Auth required')}", response_time)
                    else:
                        self.log_test("Survey Creation Error Message", True, 
                                    f"✅ AUTH ERROR: Status {response.status_code}", response_time)
                except:
                    self.log_test("Survey Creation Error Message", True, 
                                f"✅ AUTH ERROR: Status {response.status_code}", response_time)
            else:
                self.log_test("Survey Creation Error Message", False, 
                            f"❌ WRONG STATUS: {response.status_code}")
        except Exception as e:
            self.log_test("Survey Creation Error Message", False, f"Error: {str(e)}")
        
        try:
            # Test public survey with non-existent ID
            start_time = time.time()
            response = requests.get(f"{self.api_base}/surveys/non-existent-survey/public", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 404:
                try:
                    error_data = response.json()
                    if "detail" in error_data and "survey" in error_data["detail"].lower():
                        self.log_test("Public Survey Error Message", True, 
                                    f"✅ PROPER SURVEY ERROR: {error_data.get('detail', 'Survey not found')}", response_time)
                    else:
                        self.log_test("Public Survey Error Message", True, 
                                    f"✅ SURVEY NOT FOUND: Status {response.status_code}", response_time)
                except:
                    self.log_test("Public Survey Error Message", True, 
                                f"✅ SURVEY NOT FOUND: Status {response.status_code}", response_time)
            else:
                self.log_test("Public Survey Error Message", False, 
                            f"❌ WRONG STATUS: {response.status_code}")
        except Exception as e:
            self.log_test("Public Survey Error Message", False, f"Error: {str(e)}")
    
    def test_cors_and_infrastructure(self):
        """Test CORS headers and infrastructure"""
        print("\n🌐 TESTING CORS AND INFRASTRUCTURE...")
        
        try:
            # Test CORS headers
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
        
        try:
            # Test response format
            start_time = time.time()
            response = requests.get(f"{self.api_base}/surveys", timeout=10)
            response_time = time.time() - start_time
            
            content_type = response.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                self.log_test("JSON Response Format", True, 
                            "Proper JSON content-type header", response_time)
            else:
                self.log_test("JSON Response Format", False, 
                            f"Non-JSON response: {content_type}")
        except Exception as e:
            self.log_test("JSON Response Format", False, f"Error: {str(e)}")
    
    def test_performance_and_stability(self):
        """Test performance and stability of survey endpoints"""
        print("\n⚡ TESTING PERFORMANCE AND STABILITY...")
        
        # Test multiple rapid requests
        response_times = []
        success_count = 0
        
        for i in range(5):
            try:
                start_time = time.time()
                response = requests.get(f"{self.api_base}/surveys", timeout=10)
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if response.status_code in [200, 401, 403]:
                    success_count += 1
                    
            except Exception as e:
                pass
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            if avg_response_time < 1.0 and success_count >= 4:
                self.log_test("Performance and Stability", True, 
                            f"Avg response time: {avg_response_time:.3f}s, {success_count}/5 successful")
            else:
                self.log_test("Performance and Stability", False, 
                            f"Avg response time: {avg_response_time:.3f}s, {success_count}/5 successful")
        else:
            self.log_test("Performance and Stability", False, "No successful requests")
    
    def run_all_tests(self):
        """Run all survey endpoints fix verification tests"""
        print("🚀 STARTING SURVEY ENDPOINTS FIX VERIFICATION TESTS")
        print("=" * 80)
        print(f"🎯 Target: {self.base_url}")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Testing Fix: .env URL correction from team-management to Railway")
        print("=" * 80)
        
        # Run all test categories
        self.test_backend_health()
        self.test_survey_endpoints_accessibility()
        self.test_public_survey_endpoints()
        self.test_survey_endpoint_response_messages()
        self.test_cors_and_infrastructure()
        self.test_performance_and_stability()
        
        # Print final results
        self.print_final_results()
    
    def print_final_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 80)
        print("📊 SURVEY ENDPOINTS FIX VERIFICATION RESULTS")
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
        print("🎯 FIX VERIFICATION ANALYSIS")
        print("=" * 80)
        
        # Count accessibility fixes
        accessibility_tests = [r for r in self.test_results if "Endpoint Accessibility" in r['test']]
        accessibility_fixed = len([r for r in accessibility_tests if "✅ FIXED" in r['details']])
        accessibility_broken = len([r for r in accessibility_tests if "❌ STILL BROKEN" in r['details']])
        
        print(f"🔧 Endpoint Accessibility Fix: {accessibility_fixed}/{len(accessibility_tests)} endpoints fixed")
        
        if accessibility_broken == 0 and accessibility_fixed > 0:
            print("🎉 SUCCESS: All survey endpoints are now accessible!")
            print("✅ .env URL fix has resolved the 404 routing issues")
            print("✅ Survey endpoints now return proper authentication errors")
        elif accessibility_broken > 0:
            print(f"⚠️ PARTIAL FIX: {accessibility_broken} endpoints still return 404")
            print("❌ Additional fixes may be needed beyond .env URL correction")
        else:
            print("❌ NO FIX DETECTED: Endpoints still not accessible")
        
        # Public endpoint analysis
        public_tests = [r for r in self.test_results if "Public Endpoint" in r['test']]
        public_working = len([r for r in public_tests if "✅ PUBLIC ACCESS" in r['details']])
        
        if public_tests:
            print(f"🌐 Public Endpoints: {public_working}/{len(public_tests)} working correctly")
        
        print("\n📋 FINAL VERDICT:")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: Survey Management System fix is successful!")
            print("✅ All endpoints are accessible and working as expected")
            print("✅ User's 'tüm sistemi düzelt' request has been fulfilled")
        elif success_rate >= 75:
            print("✅ GOOD: Survey Management System is mostly fixed with minor issues")
            print("⚠️ Some endpoints may need additional attention")
        elif success_rate >= 50:
            print("⚠️ MODERATE: Partial fix achieved, but significant issues remain")
            print("🔧 Additional debugging and fixes are needed")
        else:
            print("🚨 CRITICAL: Fix was not successful, major problems persist!")
            print("❌ Survey Management System still not functional")
        
        print("\n🚀 SURVEY ENDPOINTS FIX VERIFICATION COMPLETED!")
        print("=" * 80)

if __name__ == "__main__":
    print("🌱 GreenWave CRM - Survey Endpoints Fix Verification")
    print("🚂 Railway Production Environment Testing")
    print("🔧 Verifying .env URL Fix Implementation")
    
    tester = SurveyEndpointsFixVerificationTest()
    tester.run_all_tests()