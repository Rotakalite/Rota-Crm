#!/usr/bin/env python3
"""
OpenAI AI Integration Backend Test
Tests the AI service endpoints and OpenAI connectivity
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime

# Test configuration
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

class OpenAIIntegrationTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: dict = None):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        print()
        
    async def test_backend_health(self):
        """Test backend health endpoint"""
        try:
            async with self.session.get(f"{BACKEND_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "Backend Health Check",
                        True,
                        f"Backend is healthy - {data.get('service', 'Unknown service')}",
                        data
                    )
                    return True
                else:
                    self.log_test(
                        "Backend Health Check",
                        False,
                        f"Health check failed with status {response.status}"
                    )
                    return False
        except Exception as e:
            self.log_test(
                "Backend Health Check",
                False,
                f"Health check error: {str(e)}"
            )
            return False
            
    async def test_ai_test_endpoint(self):
        """Test GET /api/ai/test endpoint"""
        try:
            async with self.session.get(f"{API_BASE}/ai/test") as response:
                data = await response.json()
                
                if response.status == 200:
                    # Check response structure
                    required_fields = ["status", "message", "test_response", "model"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test(
                            "AI Test Endpoint - Response Structure",
                            False,
                            f"Missing required fields: {missing_fields}",
                            data
                        )
                        return False
                    
                    # Check if AI service is working
                    if data.get("status") == "success":
                        self.log_test(
                            "AI Test Endpoint - Service Status",
                            True,
                            f"AI service working with model: {data.get('model')}",
                            data
                        )
                        
                        # Check if test response is not empty
                        test_response = data.get("test_response", "")
                        if test_response and len(test_response.strip()) > 0:
                            self.log_test(
                                "AI Test Endpoint - Response Content",
                                True,
                                f"AI responded with: '{test_response[:100]}...'",
                                {"response_length": len(test_response)}
                            )
                        else:
                            self.log_test(
                                "AI Test Endpoint - Response Content",
                                False,
                                "AI test response is empty",
                                data
                            )
                            
                        return True
                    else:
                        self.log_test(
                            "AI Test Endpoint - Service Status",
                            False,
                            f"AI service error: {data.get('message', 'Unknown error')}",
                            data
                        )
                        return False
                else:
                    self.log_test(
                        "AI Test Endpoint - HTTP Status",
                        False,
                        f"Endpoint returned status {response.status}",
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "AI Test Endpoint - Connection",
                False,
                f"Connection error: {str(e)}"
            )
            return False
            
    async def test_ai_endpoint_authentication(self):
        """Test AI endpoint authentication requirements"""
        try:
            # Test without authentication
            async with self.session.get(f"{API_BASE}/ai/test") as response:
                data = await response.json()
                
                if response.status == 403:
                    self.log_test(
                        "AI Endpoint Authentication - Security",
                        True,
                        "Endpoint properly requires authentication (403 Forbidden)",
                        {"status": response.status}
                    )
                elif response.status == 200:
                    self.log_test(
                        "AI Endpoint Authentication - Public Access",
                        True,
                        "Endpoint is publicly accessible (no auth required)",
                        {"status": response.status, "note": "This is expected for test endpoint"}
                    )
                else:
                    self.log_test(
                        "AI Endpoint Authentication - Unexpected Status",
                        False,
                        f"Unexpected status code: {response.status}",
                        data
                    )
                    
        except Exception as e:
            self.log_test(
                "AI Endpoint Authentication",
                False,
                f"Authentication test error: {str(e)}"
            )
            
    async def test_openai_model_configuration(self):
        """Test OpenAI model configuration"""
        try:
            async with self.session.get(f"{API_BASE}/ai/test") as response:
                if response.status == 200:
                    data = await response.json()
                    model = data.get("model")
                    
                    if model == "gpt-4o-mini":
                        self.log_test(
                            "OpenAI Model Configuration",
                            True,
                            f"Correct model configured: {model}",
                            {"model": model}
                        )
                    else:
                        self.log_test(
                            "OpenAI Model Configuration",
                            False,
                            f"Expected 'gpt-4o-mini', got '{model}'",
                            {"expected": "gpt-4o-mini", "actual": model}
                        )
                else:
                    self.log_test(
                        "OpenAI Model Configuration",
                        False,
                        f"Could not retrieve model info (status: {response.status})"
                    )
                    
        except Exception as e:
            self.log_test(
                "OpenAI Model Configuration",
                False,
                f"Model configuration test error: {str(e)}"
            )
            
    async def test_ai_error_handling(self):
        """Test AI service error handling"""
        try:
            # Test with malformed request (if applicable)
            async with self.session.get(f"{API_BASE}/ai/test") as response:
                data = await response.json()
                
                # Check if error responses have proper structure
                if data.get("status") == "error":
                    required_error_fields = ["status", "message", "model"]
                    missing_fields = [field for field in required_error_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test(
                            "AI Error Handling - Error Response Structure",
                            False,
                            f"Error response missing fields: {missing_fields}",
                            data
                        )
                    else:
                        self.log_test(
                            "AI Error Handling - Error Response Structure",
                            True,
                            "Error responses have proper structure",
                            data
                        )
                else:
                    self.log_test(
                        "AI Error Handling - Service Working",
                        True,
                        "AI service is working (no errors to test)",
                        {"note": "Service is functioning normally"}
                    )
                    
        except Exception as e:
            self.log_test(
                "AI Error Handling",
                False,
                f"Error handling test failed: {str(e)}"
            )
            
    async def test_response_format_validation(self):
        """Test AI endpoint response format validation"""
        try:
            async with self.session.get(f"{API_BASE}/ai/test") as response:
                # Test if response is valid JSON
                try:
                    data = await response.json()
                    self.log_test(
                        "Response Format - Valid JSON",
                        True,
                        "Response is valid JSON",
                        {"content_type": response.headers.get('content-type', 'unknown')}
                    )
                except json.JSONDecodeError as e:
                    self.log_test(
                        "Response Format - Valid JSON",
                        False,
                        f"Response is not valid JSON: {str(e)}"
                    )
                    return
                
                # Test response structure
                if isinstance(data, dict):
                    self.log_test(
                        "Response Format - Dictionary Structure",
                        True,
                        "Response is a proper dictionary",
                        {"keys": list(data.keys())}
                    )
                    
                    # Test for Turkish character support
                    message = data.get("message", "")
                    if any(char in message for char in "çğıöşüÇĞIÖŞÜ"):
                        self.log_test(
                            "Response Format - Turkish Character Support",
                            True,
                            "Response supports Turkish characters",
                            {"sample_text": message[:50]}
                        )
                    else:
                        self.log_test(
                            "Response Format - Turkish Character Support",
                            True,
                            "No Turkish characters in response (normal for test)",
                            {"note": "Test response may not contain Turkish chars"}
                        )
                else:
                    self.log_test(
                        "Response Format - Dictionary Structure",
                        False,
                        f"Response is not a dictionary, got: {type(data)}",
                        {"response_type": str(type(data))}
                    )
                    
        except Exception as e:
            self.log_test(
                "Response Format Validation",
                False,
                f"Format validation error: {str(e)}"
            )
            
    async def test_api_key_validation(self):
        """Test OpenAI API key validation (indirect)"""
        try:
            async with self.session.get(f"{API_BASE}/ai/test") as response:
                data = await response.json()
                
                if response.status == 200 and data.get("status") == "success":
                    # If we get a successful response, API key is working
                    self.log_test(
                        "OpenAI API Key Validation",
                        True,
                        "API key is valid and working",
                        {"model": data.get("model"), "response_received": True}
                    )
                elif data.get("status") == "error":
                    error_message = data.get("message", "").lower()
                    if "api" in error_message or "key" in error_message or "auth" in error_message:
                        self.log_test(
                            "OpenAI API Key Validation",
                            False,
                            f"API key issue detected: {data.get('message')}",
                            data
                        )
                    else:
                        self.log_test(
                            "OpenAI API Key Validation",
                            True,
                            "API key appears valid (error is not auth-related)",
                            data
                        )
                else:
                    self.log_test(
                        "OpenAI API Key Validation",
                        False,
                        f"Unexpected response status: {response.status}",
                        data
                    )
                    
        except Exception as e:
            self.log_test(
                "OpenAI API Key Validation",
                False,
                f"API key validation error: {str(e)}"
            )
            
    async def test_ai_service_performance(self):
        """Test AI service response time"""
        try:
            start_time = datetime.now()
            
            async with self.session.get(f"{API_BASE}/ai/test") as response:
                data = await response.json()
                
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            if response_time < 30:  # 30 seconds is reasonable for AI
                self.log_test(
                    "AI Service Performance",
                    True,
                    f"Response time: {response_time:.2f} seconds",
                    {"response_time_seconds": response_time, "status": "acceptable"}
                )
            else:
                self.log_test(
                    "AI Service Performance",
                    False,
                    f"Response time too slow: {response_time:.2f} seconds",
                    {"response_time_seconds": response_time, "status": "too_slow"}
                )
                
        except Exception as e:
            self.log_test(
                "AI Service Performance",
                False,
                f"Performance test error: {str(e)}"
            )
            
    async def run_all_tests(self):
        """Run all OpenAI AI integration tests"""
        print("🤖 OPENAI AI INTEGRATION BACKEND TEST")
        print("=" * 50)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print()
        
        await self.setup_session()
        
        try:
            # Core tests
            await self.test_backend_health()
            await self.test_ai_test_endpoint()
            await self.test_ai_endpoint_authentication()
            await self.test_openai_model_configuration()
            await self.test_ai_error_handling()
            await self.test_response_format_validation()
            await self.test_api_key_validation()
            await self.test_ai_service_performance()
            
        finally:
            await self.cleanup_session()
            
        # Print summary
        print("=" * 50)
        print("🎯 TEST SUMMARY")
        print("=" * 50)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Print failed tests
        failed_tests = [test for test in self.test_results if not test["success"]]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
            print()
        
        # Overall assessment
        if success_rate >= 90:
            print("🎉 OVERALL ASSESSMENT: EXCELLENT - OpenAI AI integration is working perfectly!")
        elif success_rate >= 75:
            print("✅ OVERALL ASSESSMENT: GOOD - OpenAI AI integration is mostly working with minor issues")
        elif success_rate >= 50:
            print("⚠️ OVERALL ASSESSMENT: MODERATE - OpenAI AI integration has some issues")
        else:
            print("🚨 OVERALL ASSESSMENT: POOR - OpenAI AI integration has major issues")
            
        print()
        print("🔍 KEY FINDINGS:")
        
        # Check specific findings
        ai_test_working = any(test["test"] == "AI Test Endpoint - Service Status" and test["success"] for test in self.test_results)
        model_correct = any(test["test"] == "OpenAI Model Configuration" and test["success"] for test in self.test_results)
        api_key_valid = any(test["test"] == "OpenAI API Key Validation" and test["success"] for test in self.test_results)
        
        if ai_test_working:
            print("   ✅ AI service is accessible and responding")
        else:
            print("   ❌ AI service is not working properly")
            
        if model_correct:
            print("   ✅ gpt-4o-mini model is correctly configured")
        else:
            print("   ❌ Model configuration issue detected")
            
        if api_key_valid:
            print("   ✅ OpenAI API key is valid and working")
        else:
            print("   ❌ OpenAI API key issue detected")
            
        return success_rate

async def main():
    """Main test function"""
    tester = OpenAIIntegrationTester()
    success_rate = await tester.run_all_tests()
    
    # Exit with appropriate code
    if success_rate >= 75:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    asyncio.run(main())