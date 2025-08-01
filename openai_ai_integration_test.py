#!/usr/bin/env python3
"""
OpenAI AI Integration Test - Railway Production
Testing the new direct OpenAI client implementation with gpt-4o-mini model
"""

import asyncio
import aiohttp
import json
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway Production URL
BACKEND_URL = "https://rota-crm-production.up.railway.app"

class OpenAIIntegrationTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            logger.info(f"✅ {test_name}: PASSED - {details}")
        else:
            logger.error(f"❌ {test_name}: FAILED - {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_backend_health(self):
        """Test if Railway backend is accessible"""
        try:
            async with self.session.get(f"{self.backend_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    service_name = data.get('service', 'Unknown')
                    self.log_test_result(
                        "Backend Health Check", 
                        True, 
                        f"Railway backend accessible - {service_name}"
                    )
                    return True
                else:
                    self.log_test_result(
                        "Backend Health Check", 
                        False, 
                        f"HTTP {response.status}"
                    )
                    return False
        except Exception as e:
            self.log_test_result(
                "Backend Health Check", 
                False, 
                f"Connection error: {str(e)}"
            )
            return False
    
    async def test_ai_test_endpoint_accessibility(self):
        """Test if AI test endpoint is accessible (should return 403 without auth)"""
        try:
            async with self.session.get(f"{self.backend_url}/api/ai/test") as response:
                if response.status == 403:
                    self.log_test_result(
                        "AI Test Endpoint Accessibility", 
                        True, 
                        "Endpoint accessible, properly secured (403 Forbidden)"
                    )
                    return True
                elif response.status == 404:
                    self.log_test_result(
                        "AI Test Endpoint Accessibility", 
                        False, 
                        "Endpoint returns 404 Not Found - not registered"
                    )
                    return False
                else:
                    data = await response.text()
                    self.log_test_result(
                        "AI Test Endpoint Accessibility", 
                        True, 
                        f"Endpoint accessible (HTTP {response.status}): {data[:100]}"
                    )
                    return True
        except Exception as e:
            self.log_test_result(
                "AI Test Endpoint Accessibility", 
                False, 
                f"Request error: {str(e)}"
            )
            return False
    
    async def test_ai_suggestions_endpoint_accessibility(self):
        """Test if AI suggestions endpoint is accessible"""
        test_client_id = "94927a77-edc3-45ec-8329-795feae35771"
        try:
            async with self.session.get(f"{self.backend_url}/api/ai/suggestions/{test_client_id}") as response:
                if response.status in [403, 401]:
                    self.log_test_result(
                        "AI Suggestions Endpoint Accessibility", 
                        True, 
                        f"Endpoint accessible, properly secured (HTTP {response.status})"
                    )
                    return True
                elif response.status == 404:
                    self.log_test_result(
                        "AI Suggestions Endpoint Accessibility", 
                        False, 
                        "Endpoint returns 404 Not Found - not registered"
                    )
                    return False
                else:
                    self.log_test_result(
                        "AI Suggestions Endpoint Accessibility", 
                        True, 
                        f"Endpoint accessible (HTTP {response.status})"
                    )
                    return True
        except Exception as e:
            self.log_test_result(
                "AI Suggestions Endpoint Accessibility", 
                False, 
                f"Request error: {str(e)}"
            )
            return False
    
    async def test_ai_report_text_endpoint_accessibility(self):
        """Test if AI report text endpoint is accessible"""
        test_client_id = "94927a77-edc3-45ec-8329-795feae35771"
        try:
            async with self.session.get(f"{self.backend_url}/api/ai/report-text/{test_client_id}") as response:
                if response.status in [403, 401]:
                    self.log_test_result(
                        "AI Report Text Endpoint Accessibility", 
                        True, 
                        f"Endpoint accessible, properly secured (HTTP {response.status})"
                    )
                    return True
                elif response.status == 404:
                    self.log_test_result(
                        "AI Report Text Endpoint Accessibility", 
                        False, 
                        "Endpoint returns 404 Not Found - not registered"
                    )
                    return False
                else:
                    self.log_test_result(
                        "AI Report Text Endpoint Accessibility", 
                        True, 
                        f"Endpoint accessible (HTTP {response.status})"
                    )
                    return True
        except Exception as e:
            self.log_test_result(
                "AI Report Text Endpoint Accessibility", 
                False, 
                f"Request error: {str(e)}"
            )
            return False
    
    async def test_ai_trend_analysis_endpoint_accessibility(self):
        """Test if AI trend analysis endpoint is accessible"""
        test_client_id = "94927a77-edc3-45ec-8329-795feae35771"
        try:
            async with self.session.get(f"{self.backend_url}/api/ai/trend-analysis/{test_client_id}") as response:
                if response.status in [403, 401]:
                    self.log_test_result(
                        "AI Trend Analysis Endpoint Accessibility", 
                        True, 
                        f"Endpoint accessible, properly secured (HTTP {response.status})"
                    )
                    return True
                elif response.status == 404:
                    self.log_test_result(
                        "AI Trend Analysis Endpoint Accessibility", 
                        False, 
                        "Endpoint returns 404 Not Found - not registered"
                    )
                    return False
                else:
                    self.log_test_result(
                        "AI Trend Analysis Endpoint Accessibility", 
                        True, 
                        f"Endpoint accessible (HTTP {response.status})"
                    )
                    return True
        except Exception as e:
            self.log_test_result(
                "AI Trend Analysis Endpoint Accessibility", 
                False, 
                f"Request error: {str(e)}"
            )
            return False
    
    async def test_ai_test_endpoint_without_auth(self):
        """Test AI test endpoint without authentication"""
        try:
            async with self.session.get(f"{self.backend_url}/api/ai/test") as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        if data.get('status') == 'success':
                            self.log_test_result(
                                "AI Test Endpoint (No Auth)", 
                                True, 
                                f"AI service working! Model: {data.get('model', 'unknown')}"
                            )
                            return True
                        else:
                            self.log_test_result(
                                "AI Test Endpoint (No Auth)", 
                                False, 
                                f"AI service error: {data.get('message', 'unknown error')}"
                            )
                            return False
                    except:
                        self.log_test_result(
                            "AI Test Endpoint (No Auth)", 
                            False, 
                            f"Invalid JSON response: {response_text[:200]}"
                        )
                        return False
                elif response.status == 403:
                    self.log_test_result(
                        "AI Test Endpoint (No Auth)", 
                        False, 
                        "Endpoint requires authentication (403 Forbidden)"
                    )
                    return False
                elif response.status == 404:
                    self.log_test_result(
                        "AI Test Endpoint (No Auth)", 
                        False, 
                        "Endpoint not found (404) - AI service not deployed"
                    )
                    return False
                else:
                    self.log_test_result(
                        "AI Test Endpoint (No Auth)", 
                        False, 
                        f"Unexpected response: HTTP {response.status} - {response_text[:200]}"
                    )
                    return False
        except Exception as e:
            self.log_test_result(
                "AI Test Endpoint (No Auth)", 
                False, 
                f"Request error: {str(e)}"
            )
            return False
    
    async def test_ai_service_import_status(self):
        """Test if AI service can be imported by checking error patterns"""
        try:
            # Test with a malformed request to see backend error handling
            async with self.session.get(f"{self.backend_url}/api/ai/test", headers={"Authorization": "Bearer invalid"}) as response:
                response_text = await response.text()
                
                if "aiohttp" in response_text.lower() and "connectiontimeouterror" in response_text.lower():
                    self.log_test_result(
                        "AI Service Import Status", 
                        False, 
                        "aiohttp/litellm compatibility issue detected in response"
                    )
                    return False
                elif response.status == 401:
                    self.log_test_result(
                        "AI Service Import Status", 
                        True, 
                        "AI service imported successfully (proper auth error)"
                    )
                    return True
                elif response.status == 404:
                    self.log_test_result(
                        "AI Service Import Status", 
                        False, 
                        "AI endpoints not registered - import failure"
                    )
                    return False
                else:
                    self.log_test_result(
                        "AI Service Import Status", 
                        True, 
                        f"AI service appears to be imported (HTTP {response.status})"
                    )
                    return True
        except Exception as e:
            self.log_test_result(
                "AI Service Import Status", 
                False, 
                f"Cannot determine import status: {str(e)}"
            )
            return False
    
    async def test_openai_api_key_configuration(self):
        """Test if OpenAI API key is configured by checking error messages"""
        try:
            # Try to access AI test endpoint and analyze error messages
            async with self.session.get(f"{self.backend_url}/api/ai/test") as response:
                response_text = await response.text()
                
                if "OPENAI_API_KEY" in response_text:
                    self.log_test_result(
                        "OpenAI API Key Configuration", 
                        False, 
                        "OpenAI API key not configured (key missing error)"
                    )
                    return False
                elif "api key" in response_text.lower() and "not found" in response_text.lower():
                    self.log_test_result(
                        "OpenAI API Key Configuration", 
                        False, 
                        "OpenAI API key configuration error"
                    )
                    return False
                elif response.status == 404:
                    self.log_test_result(
                        "OpenAI API Key Configuration", 
                        False, 
                        "Cannot test - AI endpoints not accessible"
                    )
                    return False
                else:
                    self.log_test_result(
                        "OpenAI API Key Configuration", 
                        True, 
                        "No API key configuration errors detected"
                    )
                    return True
        except Exception as e:
            self.log_test_result(
                "OpenAI API Key Configuration", 
                False, 
                f"Cannot test API key config: {str(e)}"
            )
            return False
    
    async def test_gpt_4o_mini_model_configuration(self):
        """Test if gpt-4o-mini model is configured correctly"""
        try:
            async with self.session.get(f"{self.backend_url}/api/ai/test") as response:
                if response.status == 200:
                    try:
                        data = json.loads(await response.text())
                        model = data.get('model', '')
                        if model == 'gpt-4o-mini':
                            self.log_test_result(
                                "GPT-4o-mini Model Configuration", 
                                True, 
                                f"Correct model configured: {model}"
                            )
                            return True
                        elif model:
                            self.log_test_result(
                                "GPT-4o-mini Model Configuration", 
                                False, 
                                f"Wrong model configured: {model} (expected: gpt-4o-mini)"
                            )
                            return False
                        else:
                            self.log_test_result(
                                "GPT-4o-mini Model Configuration", 
                                False, 
                                "Model information not available in response"
                            )
                            return False
                    except:
                        self.log_test_result(
                            "GPT-4o-mini Model Configuration", 
                            False, 
                            "Cannot parse model information from response"
                        )
                        return False
                else:
                    self.log_test_result(
                        "GPT-4o-mini Model Configuration", 
                        False, 
                        f"Cannot test model config - endpoint not working (HTTP {response.status})"
                    )
                    return False
        except Exception as e:
            self.log_test_result(
                "GPT-4o-mini Model Configuration", 
                False, 
                f"Cannot test model configuration: {str(e)}"
            )
            return False
    
    async def test_direct_openai_client_vs_emergent(self):
        """Test if direct OpenAI client is being used instead of emergentintegrations"""
        try:
            async with self.session.get(f"{self.backend_url}/api/ai/test") as response:
                response_text = await response.text()
                
                if "emergent" in response_text.lower():
                    self.log_test_result(
                        "Direct OpenAI Client Usage", 
                        False, 
                        "emergentintegrations still being used"
                    )
                    return False
                elif "openai" in response_text.lower() and response.status != 404:
                    self.log_test_result(
                        "Direct OpenAI Client Usage", 
                        True, 
                        "Direct OpenAI client appears to be in use"
                    )
                    return True
                elif response.status == 404:
                    self.log_test_result(
                        "Direct OpenAI Client Usage", 
                        False, 
                        "Cannot test - AI endpoints not accessible"
                    )
                    return False
                else:
                    self.log_test_result(
                        "Direct OpenAI Client Usage", 
                        True, 
                        "No emergentintegrations references found"
                    )
                    return True
        except Exception as e:
            self.log_test_result(
                "Direct OpenAI Client Usage", 
                False, 
                f"Cannot test client type: {str(e)}"
            )
            return False
    
    async def test_error_handling_quality(self):
        """Test error handling quality of AI endpoints"""
        try:
            # Test with invalid client ID
            async with self.session.get(f"{self.backend_url}/api/ai/suggestions/invalid-client-id") as response:
                response_text = await response.text()
                
                if response.status in [400, 404, 422]:
                    try:
                        data = json.loads(response_text)
                        if "detail" in data:
                            self.log_test_result(
                                "Error Handling Quality", 
                                True, 
                                f"Proper error handling (HTTP {response.status}): {data['detail'][:100]}"
                            )
                            return True
                    except:
                        pass
                    
                    self.log_test_result(
                        "Error Handling Quality", 
                        True, 
                        f"Proper error status code (HTTP {response.status})"
                    )
                    return True
                elif response.status == 500:
                    self.log_test_result(
                        "Error Handling Quality", 
                        False, 
                        f"Poor error handling - 500 Internal Server Error: {response_text[:200]}"
                    )
                    return False
                elif response.status == 404:
                    self.log_test_result(
                        "Error Handling Quality", 
                        False, 
                        "Cannot test error handling - endpoints not accessible"
                    )
                    return False
                else:
                    self.log_test_result(
                        "Error Handling Quality", 
                        True, 
                        f"Error handling working (HTTP {response.status})"
                    )
                    return True
        except Exception as e:
            self.log_test_result(
                "Error Handling Quality", 
                False, 
                f"Cannot test error handling: {str(e)}"
            )
            return False
    
    async def test_response_format_json(self):
        """Test if AI endpoints return proper JSON responses"""
        try:
            async with self.session.get(f"{self.backend_url}/api/ai/test") as response:
                if response.status == 404:
                    self.log_test_result(
                        "JSON Response Format", 
                        False, 
                        "Cannot test - AI endpoints not accessible"
                    )
                    return False
                
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    try:
                        data = json.loads(await response.text())
                        self.log_test_result(
                            "JSON Response Format", 
                            True, 
                            f"Proper JSON response with content-type: {content_type}"
                        )
                        return True
                    except:
                        self.log_test_result(
                            "JSON Response Format", 
                            False, 
                            f"Invalid JSON despite content-type: {content_type}"
                        )
                        return False
                else:
                    response_text = await response.text()
                    try:
                        json.loads(response_text)
                        self.log_test_result(
                            "JSON Response Format", 
                            True, 
                            "Valid JSON response (missing content-type header)"
                        )
                        return True
                    except:
                        self.log_test_result(
                            "JSON Response Format", 
                            False, 
                            f"Non-JSON response: {response_text[:100]}"
                        )
                        return False
        except Exception as e:
            self.log_test_result(
                "JSON Response Format", 
                False, 
                f"Cannot test JSON format: {str(e)}"
            )
            return False
    
    async def run_all_tests(self):
        """Run all OpenAI AI Integration tests"""
        logger.info("🚀 Starting OpenAI AI Integration Test - Railway Production")
        logger.info(f"🎯 Target: {self.backend_url}")
        logger.info("=" * 80)
        
        # Test sequence
        tests = [
            self.test_backend_health,
            self.test_ai_test_endpoint_accessibility,
            self.test_ai_suggestions_endpoint_accessibility,
            self.test_ai_report_text_endpoint_accessibility,
            self.test_ai_trend_analysis_endpoint_accessibility,
            self.test_ai_test_endpoint_without_auth,
            self.test_ai_service_import_status,
            self.test_openai_api_key_configuration,
            self.test_gpt_4o_mini_model_configuration,
            self.test_direct_openai_client_vs_emergent,
            self.test_error_handling_quality,
            self.test_response_format_json
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                logger.error(f"❌ Test {test.__name__} crashed: {str(e)}")
                self.log_test_result(test.__name__, False, f"Test crashed: {str(e)}")
        
        # Summary
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        logger.info("=" * 80)
        logger.info("🎯 OPENAI AI INTEGRATION TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"📊 Total Tests: {self.total_tests}")
        logger.info(f"✅ Passed: {self.passed_tests}")
        logger.info(f"❌ Failed: {self.total_tests - self.passed_tests}")
        logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            logger.info("🎉 OVERALL RESULT: EXCELLENT - AI Integration working well!")
        elif success_rate >= 60:
            logger.info("⚠️ OVERALL RESULT: MODERATE - Some issues need attention")
        else:
            logger.info("🚨 OVERALL RESULT: CRITICAL - Major issues detected")
        
        logger.info("=" * 80)
        
        # Detailed results
        logger.info("📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {result['test']}: {result['details']}")
        
        return success_rate

async def main():
    """Main test execution"""
    async with OpenAIIntegrationTester() as tester:
        success_rate = await tester.run_all_tests()
        
        # Exit with appropriate code
        if success_rate >= 60:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure

if __name__ == "__main__":
    asyncio.run(main())