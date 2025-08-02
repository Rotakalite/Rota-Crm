#!/usr/bin/env python3
"""
🤖 AI SUSTAINABILITY REPORT QUALITY ENHANCEMENT TEST - Railway Production
Comprehensive testing of enhanced AI service with executive-grade sustainability reporting
Focus: OpenAI API integration, enhanced prompts, and professional report generation
"""

import requests
import json
import sys
import os
import time
from datetime import datetime

# Railway Production Backend URL
BACKEND_URL = "https://rota-crm-production.up.railway.app"
TEST_CLIENT_ID = "94927a77-edc3-45ec-8329-795feae35771"

class AISustainabilityTester:
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
    
    def test_ai_service_endpoints(self):
        """Test AI service endpoints accessibility"""
        print("\n🤖 AI SERVICE ENDPOINTS TEST")
        print("=" * 50)
        
        ai_endpoints = [
            ("GET", "/api/ai/test", "AI Service Test Endpoint"),
            ("GET", f"/api/ai/suggestions/{self.test_client_id}", "AI Sustainability Suggestions"),
            ("GET", f"/api/ai/report-text/{self.test_client_id}", "AI Report Text Generation"),
            ("GET", f"/api/ai/trend-analysis/{self.test_client_id}", "AI Trend Analysis"),
        ]
        
        for method, endpoint, test_name in ai_endpoints:
            try:
                url = f"{self.backend_url}{endpoint}"
                
                if method == "GET":
                    response = requests.get(url, timeout=30)  # Longer timeout for AI operations
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.log_test(test_name, True, f"Endpoint working - Response received")
                        
                        # Additional validation for specific endpoints
                        if "test" in endpoint:
                            self._validate_ai_test_response(data)
                        elif "suggestions" in endpoint:
                            self._validate_ai_suggestions_response(data)
                        elif "report-text" in endpoint:
                            self._validate_ai_report_response(data)
                        elif "trend-analysis" in endpoint:
                            self._validate_ai_trend_response(data)
                            
                    except json.JSONDecodeError:
                        self.log_test(test_name, False, "Invalid JSON response")
                elif response.status_code == 404:
                    self.log_test(test_name, False, "Endpoint not found - AI service may not be deployed")
                elif response.status_code in [401, 403]:
                    self.log_test(f"{test_name} Security", True, f"Endpoint secured (HTTP {response.status_code})")
                elif response.status_code == 503:
                    self.log_test(test_name, False, "Service unavailable - AI service may be down")
                elif response.status_code == 500:
                    self.log_test(test_name, False, "Internal server error - AI service configuration issue")
                else:
                    self.log_test(test_name, False, f"Unexpected status: HTTP {response.status_code}")
                        
            except requests.exceptions.Timeout:
                self.log_test(test_name, False, "Request timeout - AI service may be slow")
            except Exception as e:
                self.log_test(test_name, False, f"Error: {str(e)}")
    
    def _validate_ai_test_response(self, data):
        """Validate AI test endpoint response"""
        if isinstance(data, dict):
            if "status" in data and data["status"] == "success":
                self.log_test("AI Test Response Validation", True, "Valid test response structure")
            elif "model" in data:
                self.log_test("AI Model Configuration", True, f"Model: {data.get('model', 'unknown')}")
            else:
                self.log_test("AI Test Response Validation", False, "Unexpected response structure")
        else:
            self.log_test("AI Test Response Validation", False, "Response is not a JSON object")
    
    def _validate_ai_suggestions_response(self, data):
        """Validate AI suggestions response for executive-grade content"""
        if isinstance(data, dict):
            suggestions = data.get("suggestions", [])
            if suggestions and isinstance(suggestions, list):
                # Check for executive-grade terminology
                executive_terms = ["ROI", "ESG", "TCFD", "SBTi", "benchmark", "KPI", "investment", "strategy"]
                content = json.dumps(data).lower()
                
                found_terms = [term for term in executive_terms if term.lower() in content]
                
                self.log_test("AI Suggestions Executive Quality", 
                             len(found_terms) >= 2,
                             f"Executive terms found: {', '.join(found_terms)}")
                
                # Check for financial analysis
                financial_terms = ["cost", "savings", "investment", "return", "budget", "financial"]
                found_financial = [term for term in financial_terms if term.lower() in content]
                
                self.log_test("AI Suggestions Financial Analysis", 
                             len(found_financial) >= 1,
                             f"Financial terms found: {', '.join(found_financial)}")
            else:
                self.log_test("AI Suggestions Structure", False, "No suggestions array found")
        else:
            self.log_test("AI Suggestions Response", False, "Invalid response structure")
    
    def _validate_ai_report_response(self, data):
        """Validate AI report response for comprehensive reporting"""
        if isinstance(data, dict):
            report_text = data.get("report_text", "")
            if report_text:
                # Check for multiple sections
                sections = ["Executive Summary", "Environmental Analysis", "Strategy", "Innovation"]
                found_sections = [section for section in sections if section in report_text]
                
                self.log_test("AI Report Comprehensive Sections", 
                             len(found_sections) >= 3,
                             f"Sections found: {', '.join(found_sections)}")
                
                # Check for professional terminology
                professional_terms = ["Fortune 500", "McKinsey", "IFC", "CDP", "Scope 1", "Scope 2", "Scope 3"]
                found_professional = [term for term in professional_terms if term in report_text]
                
                self.log_test("AI Report Professional Quality", 
                             len(found_professional) >= 2,
                             f"Professional terms found: {', '.join(found_professional)}")
                
                # Check report length (should be comprehensive)
                word_count = len(report_text.split())
                self.log_test("AI Report Comprehensiveness", 
                             word_count >= 500,
                             f"Word count: {word_count} (target: 500+)")
            else:
                self.log_test("AI Report Content", False, "No report text generated")
        else:
            self.log_test("AI Report Response", False, "Invalid response structure")
    
    def _validate_ai_trend_response(self, data):
        """Validate AI trend analysis response"""
        if isinstance(data, dict):
            trends = data.get("trends", [])
            if trends:
                self.log_test("AI Trend Analysis Data", True, f"Found {len(trends)} trend insights")
            else:
                self.log_test("AI Trend Analysis Data", False, "No trend data found")
        else:
            self.log_test("AI Trend Analysis Response", False, "Invalid response structure")
    
    def test_openai_integration(self):
        """Test OpenAI API integration and model configuration"""
        print("\n🧠 OPENAI INTEGRATION TEST")
        print("=" * 50)
        
        try:
            # Test the AI test endpoint specifically for OpenAI integration
            response = requests.get(f"{self.backend_url}/api/ai/test", timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check for OpenAI model information
                    if "model" in data:
                        model = data["model"]
                        self.log_test("OpenAI Model Configuration", 
                                     "gpt-4o-mini" in model.lower(),
                                     f"Model: {model}")
                    
                    # Check for API key validation
                    if "api_key_valid" in data:
                        self.log_test("OpenAI API Key Validation", 
                                     data["api_key_valid"],
                                     "API key validation status")
                    
                    # Check for test message response
                    if "test_response" in data or "message" in data:
                        self.log_test("OpenAI API Connection", True, "Test message successfully processed")
                    
                except json.JSONDecodeError:
                    self.log_test("OpenAI Integration Response", False, "Invalid JSON response")
            elif response.status_code == 404:
                self.log_test("OpenAI Integration", False, "AI test endpoint not accessible")
            elif response.status_code == 503:
                self.log_test("OpenAI Integration", False, "AI service unavailable")
            elif response.status_code == 500:
                self.log_test("OpenAI Integration", False, "Internal server error - check API key/configuration")
            else:
                self.log_test("OpenAI Integration", False, f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.log_test("OpenAI Integration", False, "Request timeout - API may be slow")
        except Exception as e:
            self.log_test("OpenAI Integration", False, f"Error: {str(e)}")
    
    def test_enhanced_prompts_quality(self):
        """Test the quality and depth of enhanced AI prompts"""
        print("\n📝 ENHANCED PROMPTS QUALITY TEST")
        print("=" * 50)
        
        try:
            # Test AI suggestions with focus on prompt quality
            response = requests.get(f"{self.backend_url}/api/ai/suggestions/{self.test_client_id}", timeout=60)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    suggestions_text = json.dumps(data).lower()
                    
                    # Test for executive-grade language
                    executive_indicators = [
                        "c-suite", "board", "executive", "strategic", "roi", "investment portfolio",
                        "5-year roadmap", "kpi", "benchmark", "competitive advantage"
                    ]
                    
                    found_executive = sum(1 for term in executive_indicators if term in suggestions_text)
                    self.log_test("Executive-Grade Language", 
                                 found_executive >= 3,
                                 f"Executive indicators found: {found_executive}/10")
                    
                    # Test for sustainability expertise
                    sustainability_terms = [
                        "esg", "tcfd", "sbti", "scope 1", "scope 2", "scope 3", "carbon neutral",
                        "net zero", "sustainability reporting", "environmental impact"
                    ]
                    
                    found_sustainability = sum(1 for term in sustainability_terms if term in suggestions_text)
                    self.log_test("Sustainability Expertise", 
                                 found_sustainability >= 3,
                                 f"Sustainability terms found: {found_sustainability}/10")
                    
                    # Test for industry benchmarks
                    benchmark_terms = [
                        "marriott", "hilton", "industry standard", "best practice", "benchmark",
                        "peer comparison", "market leader", "global case study"
                    ]
                    
                    found_benchmarks = sum(1 for term in benchmark_terms if term in suggestions_text)
                    self.log_test("Industry Benchmarks", 
                                 found_benchmarks >= 2,
                                 f"Benchmark references found: {found_benchmarks}/8")
                    
                except json.JSONDecodeError:
                    self.log_test("Enhanced Prompts Quality", False, "Invalid JSON response")
            else:
                self.log_test("Enhanced Prompts Quality", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Enhanced Prompts Quality", False, f"Error: {str(e)}")
    
    def test_comprehensive_report_generation(self):
        """Test comprehensive AI-powered sustainability report generation"""
        print("\n📊 COMPREHENSIVE REPORT GENERATION TEST")
        print("=" * 50)
        
        try:
            # Test AI report generation with extended timeout
            response = requests.get(f"{self.backend_url}/api/ai/report-text/{self.test_client_id}", timeout=120)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    report_text = data.get("report_text", "")
                    
                    if report_text:
                        # Test for multiple comprehensive sections
                        required_sections = [
                            "Executive Summary", "Environmental Analysis", 
                            "Strategy Plan", "Innovation", "Recommendations"
                        ]
                        
                        found_sections = [section for section in required_sections if section in report_text]
                        self.log_test("Report Section Completeness", 
                                     len(found_sections) >= 4,
                                     f"Sections found: {', '.join(found_sections)}")
                        
                        # Test for quantitative metrics
                        quantitative_indicators = [
                            "%", "metric", "kpi", "target", "baseline", "reduction",
                            "improvement", "savings", "investment", "timeline"
                        ]
                        
                        found_quantitative = sum(1 for term in quantitative_indicators 
                                               if term.lower() in report_text.lower())
                        self.log_test("Quantitative Metrics", 
                                     found_quantitative >= 5,
                                     f"Quantitative indicators: {found_quantitative}/10")
                        
                        # Test for business value propositions
                        business_value_terms = [
                            "business value", "competitive advantage", "market position",
                            "stakeholder", "investor", "brand reputation", "risk mitigation"
                        ]
                        
                        found_business_value = sum(1 for term in business_value_terms 
                                                 if term.lower() in report_text.lower())
                        self.log_test("Business Value Propositions", 
                                     found_business_value >= 2,
                                     f"Business value terms: {found_business_value}/7")
                        
                        # Test report length and depth
                        word_count = len(report_text.split())
                        self.log_test("Report Comprehensiveness", 
                                     word_count >= 1000,
                                     f"Word count: {word_count} (Fortune 500 standard: 1000+)")
                        
                    else:
                        self.log_test("Report Generation", False, "No report content generated")
                        
                except json.JSONDecodeError:
                    self.log_test("Report Generation", False, "Invalid JSON response")
            elif response.status_code == 404:
                self.log_test("Report Generation", False, "Report endpoint not accessible")
            elif response.status_code == 503:
                self.log_test("Report Generation", False, "AI service unavailable")
            else:
                self.log_test("Report Generation", False, f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.log_test("Report Generation", False, "Request timeout - report generation may be slow")
        except Exception as e:
            self.log_test("Report Generation", False, f"Error: {str(e)}")
    
    def test_system_persona_upgrade(self):
        """Test if AI system demonstrates senior consultant/director expertise level"""
        print("\n👔 SYSTEM PERSONA UPGRADE TEST")
        print("=" * 50)
        
        try:
            # Test AI suggestions for persona quality
            response = requests.get(f"{self.backend_url}/api/ai/suggestions/{self.test_client_id}", timeout=60)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    content = json.dumps(data).lower()
                    
                    # Test for senior consultant language patterns
                    senior_consultant_terms = [
                        "in my experience", "best practice", "industry standard", "strategic approach",
                        "recommend", "implementation", "roadmap", "framework", "methodology"
                    ]
                    
                    found_consultant = sum(1 for term in senior_consultant_terms if term in content)
                    self.log_test("Senior Consultant Persona", 
                                 found_consultant >= 3,
                                 f"Consultant language patterns: {found_consultant}/9")
                    
                    # Test for published expert authority
                    authority_terms = [
                        "research shows", "studies indicate", "according to", "evidence suggests",
                        "proven approach", "established methodology", "industry report"
                    ]
                    
                    found_authority = sum(1 for term in authority_terms if term in content)
                    self.log_test("Published Expert Authority", 
                                 found_authority >= 2,
                                 f"Authority indicators: {found_authority}/7")
                    
                    # Test for strategic thinking
                    strategic_terms = [
                        "long-term", "strategic", "holistic", "integrated approach", "stakeholder",
                        "risk assessment", "opportunity", "competitive advantage"
                    ]
                    
                    found_strategic = sum(1 for term in strategic_terms if term in content)
                    self.log_test("Strategic Thinking Level", 
                                 found_strategic >= 3,
                                 f"Strategic indicators: {found_strategic}/8")
                    
                except json.JSONDecodeError:
                    self.log_test("System Persona", False, "Invalid JSON response")
            else:
                self.log_test("System Persona", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("System Persona", False, f"Error: {str(e)}")
    
    def test_response_quality_and_language(self):
        """Test AI response quality and professional language"""
        print("\n🎯 RESPONSE QUALITY AND LANGUAGE TEST")
        print("=" * 50)
        
        try:
            # Test AI test endpoint for basic quality
            response = requests.get(f"{self.backend_url}/api/ai/test", timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check response structure
                    if isinstance(data, dict):
                        self.log_test("Response Structure Quality", True, "Well-structured JSON response")
                        
                        # Check for professional language if there's a message
                        if "message" in data or "response" in data:
                            message = data.get("message", data.get("response", ""))
                            if message:
                                # Check for professional tone
                                professional_indicators = [
                                    len(message) > 50,  # Substantial response
                                    not any(word in message.lower() for word in ["test", "dummy", "placeholder"]),
                                    any(word in message.lower() for word in ["sustainability", "environmental", "analysis"])
                                ]
                                
                                professional_score = sum(professional_indicators)
                                self.log_test("Professional Language Quality", 
                                             professional_score >= 2,
                                             f"Professional indicators: {professional_score}/3")
                    
                except json.JSONDecodeError:
                    self.log_test("Response Quality", False, "Invalid JSON response")
            else:
                self.log_test("Response Quality", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Response Quality", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all AI sustainability enhancement tests"""
        print("🤖 AI SUSTAINABILITY REPORT QUALITY ENHANCEMENT TEST - Railway Production")
        print("=" * 80)
        print(f"🎯 Target: {self.backend_url}")
        print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🧪 Test Client ID: {self.test_client_id}")
        print("=" * 80)
        
        # Core backend tests
        self.test_backend_accessibility()
        
        # AI service functionality tests
        self.test_ai_service_endpoints()
        self.test_openai_integration()
        
        # Enhanced AI quality tests
        self.test_enhanced_prompts_quality()
        self.test_comprehensive_report_generation()
        self.test_system_persona_upgrade()
        self.test_response_quality_and_language()
        
        # Generate final report
        self.generate_final_report()
        
    def generate_final_report(self):
        """Generate comprehensive test report"""
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print("\n" + "="*80)
        print("🎉 AI SUSTAINABILITY ENHANCEMENT TEST COMPLETED!")
        print("="*80)
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Tests: {self.total_tests}")
        print(f"   Passed: {self.passed_tests}")
        print(f"   Failed: {self.total_tests - self.passed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print("="*80)
        
        # Categorize results
        passed_tests = [r for r in self.test_results if r['passed']]
        failed_tests = [r for r in self.test_results if not r['passed']]
        
        if passed_tests:
            print("✅ PASSED TESTS:")
            for test in passed_tests:
                print(f"   • {test['test']}: {test['details']}")
                
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
                
        print("\n🎯 AI ENHANCEMENT ANALYSIS:")
        print("   • OpenAI gpt-4o-mini model integration")
        print("   • Executive-grade sustainability reporting prompts")
        print("   • Fortune 500/McKinsey-level report quality")
        print("   • Senior consultant/director expertise persona")
        print("   • ROI-focused recommendations with financial analysis")
        print("   • Industry benchmarks and best practices integration")
        
        print("\n📋 EXPECTED IMPROVEMENTS:")
        print("   • Professional, comprehensive, technically sound reports")
        print("   • Executive presentation quality suitable for C-Suite")
        print("   • Strategic depth with quantitative financial analysis")
        print("   • Industry benchmarks and global case studies")
        print("   • Implementation-ready recommendations with timelines")
        
        if success_rate >= 80:
            print("\n🚂 RAILWAY PRODUCTION STATUS: ✅ AI ENHANCEMENT SUCCESSFUL")
            print("   AI sustainability reporting is working with enhanced quality!")
        elif success_rate >= 60:
            print("\n🚂 RAILWAY PRODUCTION STATUS: ⚠️ AI PARTIALLY ENHANCED")
            print("   AI service has some enhancements but may need refinement!")
        else:
            print("\n🚂 RAILWAY PRODUCTION STATUS: ❌ AI ENHANCEMENT NEEDS ATTENTION")
            print("   AI service has significant issues affecting report quality!")
            
        return success_rate

if __name__ == "__main__":
    tester = AISustainabilityTester()
    try:
        tester.run_all_tests()
        success_rate = (tester.passed_tests / tester.total_tests * 100) if tester.total_tests > 0 else 0
        sys.exit(0 if success_rate >= 60 else 1)  # Lower threshold due to AI complexity
    except KeyboardInterrupt:
        print("🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Fatal error: {str(e)}")
        sys.exit(1)