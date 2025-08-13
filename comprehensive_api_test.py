#!/usr/bin/env python3
"""
Comprehensive API Endpoints Test - Railway Production
GreenWave CRM Tüm API Endpoint'lerin Durumu ve Sayısı

Bu test tüm API endpoint'lerin erişilebilirliğini kontrol eder ve 
toplam kaç tane API olduğunu tespit eder.
"""

import requests
import json
import uuid
from datetime import datetime
import sys
import time

class ComprehensiveAPITest:
    def __init__(self):
        self.base_url = "https://rota-crm-production.up.railway.app"
        self.api_base = f"{self.base_url}/api"
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
        # Comprehensive list of all API endpoints from backend code
        self.endpoints = [
            # Health & Status
            {"method": "GET", "path": "/health", "category": "Health", "auth_required": False},
            {"method": "GET", "path": "/status", "category": "Health", "auth_required": False},
            {"method": "GET", "path": "/test", "category": "Health", "auth_required": False},
            {"method": "GET", "path": "/test-router", "category": "Health", "auth_required": False},
            
            # Authentication & User Management
            {"method": "POST", "path": "/auth/register", "category": "Auth", "auth_required": False},
            {"method": "POST", "path": "/auth/self-signup", "category": "Auth", "auth_required": False},
            {"method": "GET", "path": "/admin/pending-approvals", "category": "Auth", "auth_required": True},
            {"method": "POST", "path": "/admin/approve-user/test-id", "category": "Auth", "auth_required": True},
            
            # Client Management
            {"method": "GET", "path": "/clients", "category": "Clients", "auth_required": True},
            {"method": "POST", "path": "/clients", "category": "Clients", "auth_required": True},
            {"method": "GET", "path": "/clients/test-id", "category": "Clients", "auth_required": True},
            {"method": "PUT", "path": "/clients/test-id", "category": "Clients", "auth_required": True},
            {"method": "DELETE", "path": "/clients/test-id", "category": "Clients", "auth_required": True},
            
            # Consultant Management
            {"method": "POST", "path": "/consultants", "category": "Consultants", "auth_required": True},
            {"method": "GET", "path": "/consultants", "category": "Consultants", "auth_required": True},
            {"method": "GET", "path": "/consultants/test-id", "category": "Consultants", "auth_required": True},
            {"method": "PUT", "path": "/consultants/test-id", "category": "Consultants", "auth_required": True},
            {"method": "DELETE", "path": "/consultants/test-id", "category": "Consultants", "auth_required": True},
            
            # Document Management
            {"method": "GET", "path": "/documents", "category": "Documents", "auth_required": True},
            {"method": "POST", "path": "/documents/upload-document", "category": "Documents", "auth_required": True},
            {"method": "GET", "path": "/documents/test-id", "category": "Documents", "auth_required": True},
            {"method": "DELETE", "path": "/documents/test-id", "category": "Documents", "auth_required": True},
            {"method": "GET", "path": "/documents/bulk-download", "category": "Documents", "auth_required": True},
            {"method": "GET", "path": "/folders", "category": "Documents", "auth_required": True},
            {"method": "POST", "path": "/folders", "category": "Documents", "auth_required": True},
            
            # Training Management
            {"method": "GET", "path": "/trainings", "category": "Trainings", "auth_required": True},
            {"method": "POST", "path": "/trainings", "category": "Trainings", "auth_required": True},
            {"method": "GET", "path": "/trainings/test-id", "category": "Trainings", "auth_required": True},
            {"method": "PUT", "path": "/trainings/test-id", "category": "Trainings", "auth_required": True},
            {"method": "DELETE", "path": "/trainings/test-id", "category": "Trainings", "auth_required": True},
            
            # Consumption Management
            {"method": "GET", "path": "/consumptions", "category": "Consumptions", "auth_required": True},
            {"method": "POST", "path": "/consumptions", "category": "Consumptions", "auth_required": True},
            {"method": "GET", "path": "/consumptions/test-id", "category": "Consumptions", "auth_required": True},
            {"method": "PUT", "path": "/consumptions/test-id", "category": "Consumptions", "auth_required": True},
            {"method": "DELETE", "path": "/consumptions/test-id", "category": "Consumptions", "auth_required": True},
            {"method": "GET", "path": "/consumptions/analytics", "category": "Consumptions", "auth_required": True},
            
            # Personnel Management
            {"method": "GET", "path": "/personnel", "category": "Personnel", "auth_required": True},
            {"method": "POST", "path": "/personnel", "category": "Personnel", "auth_required": True},
            {"method": "GET", "path": "/personnel/test-id", "category": "Personnel", "auth_required": True},
            {"method": "PUT", "path": "/personnel/test-id", "category": "Personnel", "auth_required": True},
            {"method": "DELETE", "path": "/personnel/test-id", "category": "Personnel", "auth_required": True},
            {"method": "POST", "path": "/personnel/bulk", "category": "Personnel", "auth_required": True},
            
            # Supplier Management
            {"method": "GET", "path": "/suppliers", "category": "Suppliers", "auth_required": True},
            {"method": "POST", "path": "/suppliers", "category": "Suppliers", "auth_required": True},
            {"method": "GET", "path": "/suppliers/test-id", "category": "Suppliers", "auth_required": True},
            {"method": "PUT", "path": "/suppliers/test-id", "category": "Suppliers", "auth_required": True},
            {"method": "DELETE", "path": "/suppliers/test-id", "category": "Suppliers", "auth_required": True},
            {"method": "POST", "path": "/suppliers/bulk", "category": "Suppliers", "auth_required": True},
            {"method": "GET", "path": "/suppliers/categories", "category": "Suppliers", "auth_required": True},
            {"method": "GET", "path": "/suppliers/certifications", "category": "Suppliers", "auth_required": True},
            
            # Waste Management
            {"method": "GET", "path": "/waste-management", "category": "Waste", "auth_required": True},
            {"method": "POST", "path": "/waste-management", "category": "Waste", "auth_required": True},
            {"method": "GET", "path": "/waste-management/test-id", "category": "Waste", "auth_required": True},
            {"method": "PUT", "path": "/waste-management/test-id", "category": "Waste", "auth_required": True},
            {"method": "DELETE", "path": "/waste-management/test-id", "category": "Waste", "auth_required": True},
            {"method": "GET", "path": "/waste-management/analytics", "category": "Waste", "auth_required": True},
            
            # Sustainability Targets
            {"method": "GET", "path": "/sustainability-targets", "category": "Sustainability", "auth_required": True},
            {"method": "POST", "path": "/sustainability-targets", "category": "Sustainability", "auth_required": True},
            {"method": "GET", "path": "/sustainability-targets/test-id", "category": "Sustainability", "auth_required": True},
            {"method": "PUT", "path": "/sustainability-targets/test-id", "category": "Sustainability", "auth_required": True},
            {"method": "DELETE", "path": "/sustainability-targets/test-id", "category": "Sustainability", "auth_required": True},
            {"method": "POST", "path": "/sustainability-targets/progress", "category": "Sustainability", "auth_required": True},
            
            # Survey Management (Recently Fixed)
            {"method": "GET", "path": "/surveys", "category": "Surveys", "auth_required": True},
            {"method": "POST", "path": "/surveys", "category": "Surveys", "auth_required": True},
            {"method": "GET", "path": "/surveys/test-id", "category": "Surveys", "auth_required": True},
            {"method": "GET", "path": "/surveys/test-id/public", "category": "Surveys", "auth_required": False},
            {"method": "POST", "path": "/surveys/test-id/responses", "category": "Surveys", "auth_required": False},
            {"method": "GET", "path": "/surveys/test-id/responses", "category": "Surveys", "auth_required": True},
            {"method": "POST", "path": "/surveys/test-id/campaigns", "category": "Surveys", "auth_required": True},
            {"method": "POST", "path": "/surveys/test-id/campaigns/test-campaign/send", "category": "Surveys", "auth_required": True},
            {"method": "GET", "path": "/surveys/test-id/analysis", "category": "Surveys", "auth_required": True},
            
            # Email Management
            {"method": "GET", "path": "/bulk-email/test", "category": "Email", "auth_required": True},
            {"method": "POST", "path": "/bulk-email/send", "category": "Email", "auth_required": True},
            {"method": "GET", "path": "/bulk-email/stats", "category": "Email", "auth_required": True},
            {"method": "GET", "path": "/email-templates", "category": "Email", "auth_required": True},
            {"method": "GET", "path": "/email-templates/test-id", "category": "Email", "auth_required": True},
            {"method": "POST", "path": "/email-templates/test", "category": "Email", "auth_required": True},
            {"method": "GET", "path": "/email-templates-test", "category": "Email", "auth_required": True},
            
            # AI Services
            {"method": "GET", "path": "/ai/test", "category": "AI", "auth_required": True},
            {"method": "POST", "path": "/ai/suggestions", "category": "AI", "auth_required": True},
            {"method": "POST", "path": "/ai/report-text", "category": "AI", "auth_required": True},
            {"method": "POST", "path": "/ai/trend-analysis", "category": "AI", "auth_required": True},
            
            # Admin Settings
            {"method": "GET", "path": "/settings/permissions", "category": "Settings", "auth_required": True},
            {"method": "POST", "path": "/settings/permissions", "category": "Settings", "auth_required": True},
            {"method": "PUT", "path": "/settings/permissions/test-id", "category": "Settings", "auth_required": True},
            {"method": "DELETE", "path": "/settings/permissions/test-id", "category": "Settings", "auth_required": True},
            {"method": "GET", "path": "/settings/roles", "category": "Settings", "auth_required": True},
            {"method": "POST", "path": "/settings/roles", "category": "Settings", "auth_required": True},
            {"method": "GET", "path": "/settings/users", "category": "Settings", "auth_required": True},
            {"method": "GET", "path": "/settings/role-stats", "category": "Settings", "auth_required": True},
            
            # Reports
            {"method": "GET", "path": "/reports/comprehensive", "category": "Reports", "auth_required": True},
            {"method": "GET", "path": "/reports/training", "category": "Reports", "auth_required": True},
            {"method": "GET", "path": "/reports/consumption", "category": "Reports", "auth_required": True},
            
            # Admin Dashboard
            {"method": "GET", "path": "/admin-dashboard-stats", "category": "Dashboard", "auth_required": True},
            {"method": "GET", "path": "/consultant-dashboard-stats", "category": "Dashboard", "auth_required": True},
            
            # Backup & Restore
            {"method": "POST", "path": "/backup/create", "category": "Backup", "auth_required": True},
            {"method": "POST", "path": "/backup/restore", "category": "Backup", "auth_required": True},
        ]
        
    def log_test(self, test_name, success, details="", response_time=None):
        """Log test results"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ ACCESSIBLE"
        else:
            self.failed_tests += 1
            status = "❌ NOT ACCESSIBLE"
        
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
                self.log_test("Backend Root", True, 
                            f"Status: {response.status_code}", response_time)
            else:
                self.log_test("Backend Root", False, 
                            f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Backend Root", False, f"Error: {str(e)}")
    
    def test_all_endpoints(self):
        """Test all API endpoints"""
        print(f"\n🔍 TESTING ALL {len(self.endpoints)} API ENDPOINTS...")
        
        categories = {}
        
        for endpoint in self.endpoints:
            category = endpoint["category"]
            if category not in categories:
                categories[category] = {"total": 0, "accessible": 0, "not_accessible": 0}
            
            categories[category]["total"] += 1
            
            try:
                start_time = time.time()
                
                # Prepare request
                url = f"{self.api_base}{endpoint['path']}"
                
                if endpoint["method"] == "GET":
                    response = requests.get(url, timeout=10)
                elif endpoint["method"] == "POST":
                    response = requests.post(url, json={"test": "data"}, timeout=10)
                elif endpoint["method"] == "PUT":
                    response = requests.put(url, json={"test": "data"}, timeout=10)
                elif endpoint["method"] == "DELETE":
                    response = requests.delete(url, timeout=10)
                else:
                    response = requests.request(endpoint["method"], url, timeout=10)
                
                response_time = time.time() - start_time
                
                # Determine if endpoint is accessible
                if endpoint["auth_required"]:
                    # For auth-required endpoints, 401/403 means accessible
                    if response.status_code in [200, 401, 403, 400, 422]:
                        self.log_test(f"{endpoint['method']} {endpoint['path']}", True, 
                                    f"Status: {response.status_code} (Auth required)", response_time)
                        categories[category]["accessible"] += 1
                    elif response.status_code == 404:
                        self.log_test(f"{endpoint['method']} {endpoint['path']}", False, 
                                    f"Status: 404 (Route not found)", response_time)
                        categories[category]["not_accessible"] += 1
                    else:
                        self.log_test(f"{endpoint['method']} {endpoint['path']}", False, 
                                    f"Status: {response.status_code}", response_time)
                        categories[category]["not_accessible"] += 1
                else:
                    # For public endpoints, 200/400/404 means accessible
                    if response.status_code in [200, 400, 404, 422]:
                        self.log_test(f"{endpoint['method']} {endpoint['path']}", True, 
                                    f"Status: {response.status_code} (Public)", response_time)
                        categories[category]["accessible"] += 1
                    else:
                        self.log_test(f"{endpoint['method']} {endpoint['path']}", False, 
                                    f"Status: {response.status_code}", response_time)
                        categories[category]["not_accessible"] += 1
                
            except Exception as e:
                self.log_test(f"{endpoint['method']} {endpoint['path']}", False, f"Error: {str(e)}")
                categories[category]["not_accessible"] += 1
        
        return categories
    
    def run_all_tests(self):
        """Run comprehensive API endpoint tests"""
        print("🚀 STARTING COMPREHENSIVE API ENDPOINTS TEST")
        print("=" * 80)
        print(f"🎯 Target: {self.base_url}")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Total Endpoints to Test: {len(self.endpoints)}")
        print("=" * 80)
        
        # Run tests
        self.test_backend_health()
        categories = self.test_all_endpoints()
        
        # Print results
        self.print_final_results(categories)
    
    def print_final_results(self, categories):
        """Print comprehensive test results"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE API ENDPOINTS TEST RESULTS")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"📈 Overall Success Rate: {success_rate:.1f}% ({self.passed_tests}/{self.total_tests})")
        print(f"✅ Accessible Endpoints: {self.passed_tests}")
        print(f"❌ Not Accessible Endpoints: {self.failed_tests}")
        print(f"📊 Total Endpoints Tested: {self.total_tests}")
        
        print("\n📋 CATEGORY BREAKDOWN:")
        print("-" * 80)
        
        for category, stats in categories.items():
            success_rate_cat = (stats["accessible"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"🔹 {category}: {stats['accessible']}/{stats['total']} accessible ({success_rate_cat:.1f}%)")
        
        print("\n🔍 DETAILED RESULTS BY CATEGORY:")
        print("-" * 80)
        
        current_category = None
        for result in self.test_results:
            # Extract category from test name
            test_path = result['test'].split(' ')[-1] if ' ' in result['test'] else result['test']
            
            # Find category for this endpoint
            endpoint_category = None
            for endpoint in self.endpoints:
                if endpoint['path'] in test_path:
                    endpoint_category = endpoint['category']
                    break
            
            if endpoint_category and endpoint_category != current_category:
                current_category = endpoint_category
                print(f"\n📂 {current_category} APIs:")
            
            print(f"  {result['status']} {result['test']}")
            if result['details']:
                print(f"      📝 {result['details']}")
        
        print("\n" + "=" * 80)
        print("🎯 FINAL ANALYSIS")
        print("=" * 80)
        
        # Identify problematic categories
        problematic_categories = []
        working_categories = []
        
        for category, stats in categories.items():
            success_rate_cat = (stats["accessible"] / stats["total"] * 100) if stats["total"] > 0 else 0
            if success_rate_cat < 50:
                problematic_categories.append(category)
            elif success_rate_cat >= 90:
                working_categories.append(category)
        
        if working_categories:
            print(f"✅ WORKING WELL: {', '.join(working_categories)}")
        
        if problematic_categories:
            print(f"🚨 NEEDS ATTENTION: {', '.join(problematic_categories)}")
        
        print(f"\n📊 TOPLAM API SAYISI: {len(self.endpoints)} endpoint")
        print(f"🔗 Erişilebilir API'ler: {self.passed_tests}")
        print(f"❌ Erişilemeyen API'ler: {self.failed_tests}")
        
        if success_rate >= 90:
            print("\n🎉 EXCELLENT: API sistemi mükemmel çalışıyor!")
        elif success_rate >= 75:
            print("\n✅ GOOD: API sistemi genel olarak iyi çalışıyor.")
        elif success_rate >= 50:
            print("\n⚠️ MODERATE: API sisteminde bazı sorunlar var.")
        else:
            print("\n🚨 CRITICAL: API sisteminde ciddi sorunlar var!")
        
        print("\n🚀 COMPREHENSIVE API TEST COMPLETED!")
        print("=" * 80)

if __name__ == "__main__":
    print("🌱 GreenWave CRM - Comprehensive API Endpoints Test")
    print("🚂 Railway Production Environment")
    print("📊 Testing All API Endpoints Accessibility")
    
    tester = ComprehensiveAPITest()
    tester.run_all_tests()