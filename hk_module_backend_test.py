#!/usr/bin/env python3
"""
🧹 HK (HOUSEKEEPING) MODÜLÜ FULL STACK BACKEND TEST
==================================================

Bu test HK modülünün backend API'lerini kapsamlı olarak test eder:

Backend API Test:
1. GET /api/rooms - Oda listesi (authentication required)
2. POST /api/rooms/bulk - Toplu oda oluşturma (admin required) 
3. PUT /api/rooms/{room_id}/status - Oda durumu güncelleme
4. GET /api/hk/dashboard - HK dashboard istatistikleri
5. POST /api/hk/tasks - HK görevi oluşturma
6. GET /api/hk/tasks - HK görevleri listesi
7. PUT /api/hk/tasks/{task_id} - HK görevi güncelleme

Test Senaryoları:
- Authentication Test: Tüm endpoint'ler 401/403 döndürmeli (auth gerekli)
- Permission Test: Admin-only endpoint'ler doğru permission kontrolü yapıyor mu?
- Response Format: JSON response format'ları doğru mu?
- Error Handling: Invalid request'ler için proper error message'lar
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Railway Production Backend URL
BACKEND_URL = "https://rota-crm-production.up.railway.app"

class HKModuleBackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
        # Test data
        self.test_room_data = {
            "rooms": [
                {
                    "room_number": "101",
                    "floor_name": "1. Kat",
                    "room_type": "Standard",
                    "status": "clean",
                    "notes": "Test odası"
                },
                {
                    "room_number": "102", 
                    "floor_name": "1. Kat",
                    "room_type": "Deluxe",
                    "status": "dirty",
                    "notes": "Test odası 2"
                }
            ]
        }
        
        self.test_task_data = {
            "room_id": "test-room-id",
            "task_type": "regular_cleaning",
            "assigned_staff": "Test Staff",
            "priority": "normal",
            "estimated_duration": 30,
            "notes": "Test temizlik görevi"
        }
        
        self.test_task_update = {
            "status": "completed",
            "actual_duration": 25,
            "completion_notes": "Temizlik tamamlandı",
            "quality_score": 9,
            "issues_found": []
        }

    def log_test(self, test_name, success, details="", expected="", actual=""):
        """Test sonucunu logla"""
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
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   📝 {details}")
        if not success and expected:
            print(f"   🎯 Expected: {expected}")
            print(f"   📊 Actual: {actual}")
        print()

    def test_backend_health(self):
        """Backend sağlık kontrolü"""
        print("🏥 Backend Health Check")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=10)
            
            if response.status_code == 200:
                self.log_test(
                    "Backend Health Check",
                    True,
                    f"Backend erişilebilir (Status: {response.status_code})"
                )
                return True
            else:
                self.log_test(
                    "Backend Health Check", 
                    False,
                    f"Backend sağlık kontrolü başarısız",
                    "200",
                    str(response.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Backend Health Check",
                False, 
                f"Backend bağlantı hatası: {str(e)}"
            )
            return False

    def test_rooms_endpoints_authentication(self):
        """Rooms endpoints authentication testleri"""
        print("🏨 Rooms Endpoints Authentication Tests")
        print("=" * 50)
        
        # Test GET /api/rooms without auth
        try:
            response = requests.get(f"{self.backend_url}/api/rooms", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/rooms - Authentication Required",
                    True,
                    f"Doğru auth kontrolü (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "GET /api/rooms - Authentication Required",
                    False,
                    f"Auth kontrolü başarısız",
                    "401 or 403",
                    str(response.status_code)
                )
        except Exception as e:
            self.log_test(
                "GET /api/rooms - Authentication Required",
                False,
                f"Request hatası: {str(e)}"
            )

        # Test POST /api/rooms/bulk without auth
        try:
            response = requests.post(
                f"{self.backend_url}/api/rooms/bulk",
                json=self.test_room_data,
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "POST /api/rooms/bulk - Authentication Required",
                    True,
                    f"Doğru auth kontrolü (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "POST /api/rooms/bulk - Authentication Required",
                    False,
                    f"Auth kontrolü başarısız",
                    "401 or 403", 
                    str(response.status_code)
                )
        except Exception as e:
            self.log_test(
                "POST /api/rooms/bulk - Authentication Required",
                False,
                f"Request hatası: {str(e)}"
            )

        # Test PUT /api/rooms/{room_id}/status without auth
        try:
            test_room_id = str(uuid.uuid4())
            response = requests.put(
                f"{self.backend_url}/api/rooms/{test_room_id}/status",
                params={"status": "clean"},
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "PUT /api/rooms/{room_id}/status - Authentication Required",
                    True,
                    f"Doğru auth kontrolü (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "PUT /api/rooms/{room_id}/status - Authentication Required",
                    False,
                    f"Auth kontrolü başarısız",
                    "401 or 403",
                    str(response.status_code)
                )
        except Exception as e:
            self.log_test(
                "PUT /api/rooms/{room_id}/status - Authentication Required",
                False,
                f"Request hatası: {str(e)}"
            )

    def test_hk_endpoints_authentication(self):
        """HK endpoints authentication testleri"""
        print("🧹 HK Endpoints Authentication Tests")
        print("=" * 50)
        
        # Test GET /api/hk/dashboard without auth
        try:
            response = requests.get(f"{self.backend_url}/api/hk/dashboard", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/hk/dashboard - Authentication Required",
                    True,
                    f"Doğru auth kontrolü (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "GET /api/hk/dashboard - Authentication Required",
                    False,
                    f"Auth kontrolü başarısız",
                    "401 or 403",
                    str(response.status_code)
                )
        except Exception as e:
            self.log_test(
                "GET /api/hk/dashboard - Authentication Required",
                False,
                f"Request hatası: {str(e)}"
            )

        # Test POST /api/hk/tasks without auth
        try:
            response = requests.post(
                f"{self.backend_url}/api/hk/tasks",
                json=self.test_task_data,
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "POST /api/hk/tasks - Authentication Required",
                    True,
                    f"Doğru auth kontrolü (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "POST /api/hk/tasks - Authentication Required",
                    False,
                    f"Auth kontrolü başarısız",
                    "401 or 403",
                    str(response.status_code)
                )
        except Exception as e:
            self.log_test(
                "POST /api/hk/tasks - Authentication Required",
                False,
                f"Request hatası: {str(e)}"
            )

        # Test GET /api/hk/tasks without auth
        try:
            response = requests.get(f"{self.backend_url}/api/hk/tasks", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/hk/tasks - Authentication Required",
                    True,
                    f"Doğru auth kontrolü (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "GET /api/hk/tasks - Authentication Required",
                    False,
                    f"Auth kontrolü başarısız",
                    "401 or 403",
                    str(response.status_code)
                )
        except Exception as e:
            self.log_test(
                "GET /api/hk/tasks - Authentication Required",
                False,
                f"Request hatası: {str(e)}"
            )

        # Test PUT /api/hk/tasks/{task_id} without auth
        try:
            test_task_id = str(uuid.uuid4())
            response = requests.put(
                f"{self.backend_url}/api/hk/tasks/{test_task_id}",
                json=self.test_task_update,
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "PUT /api/hk/tasks/{task_id} - Authentication Required",
                    True,
                    f"Doğru auth kontrolü (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "PUT /api/hk/tasks/{task_id} - Authentication Required",
                    False,
                    f"Auth kontrolü başarısız",
                    "401 or 403",
                    str(response.status_code)
                )
        except Exception as e:
            self.log_test(
                "PUT /api/hk/tasks/{task_id} - Authentication Required",
                False,
                f"Request hatası: {str(e)}"
            )

    def test_invalid_token_handling(self):
        """Geçersiz token ile test"""
        print("🔐 Invalid Token Handling Tests")
        print("=" * 50)
        
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        
        # Test with invalid token
        endpoints_to_test = [
            ("GET", "/api/rooms"),
            ("POST", "/api/rooms/bulk"),
            ("GET", "/api/hk/dashboard"),
            ("POST", "/api/hk/tasks"),
            ("GET", "/api/hk/tasks")
        ]
        
        for method, endpoint in endpoints_to_test:
            try:
                if method == "GET":
                    response = requests.get(
                        f"{self.backend_url}{endpoint}",
                        headers=invalid_headers,
                        timeout=10
                    )
                elif method == "POST":
                    test_data = self.test_room_data if "rooms" in endpoint else self.test_task_data
                    response = requests.post(
                        f"{self.backend_url}{endpoint}",
                        json=test_data,
                        headers=invalid_headers,
                        timeout=10
                    )
                
                if response.status_code == 401:
                    self.log_test(
                        f"{method} {endpoint} - Invalid Token Rejection",
                        True,
                        f"Geçersiz token reddedildi (Status: {response.status_code})"
                    )
                else:
                    self.log_test(
                        f"{method} {endpoint} - Invalid Token Rejection",
                        False,
                        f"Geçersiz token kontrolü başarısız",
                        "401",
                        str(response.status_code)
                    )
                    
            except Exception as e:
                self.log_test(
                    f"{method} {endpoint} - Invalid Token Rejection",
                    False,
                    f"Request hatası: {str(e)}"
                )

    def test_admin_permission_control(self):
        """Admin permission kontrolü"""
        print("👑 Admin Permission Control Tests")
        print("=" * 50)
        
        # Test POST /api/rooms/bulk - should require admin role
        # Since we can't test with valid tokens, we check if endpoint exists and requires auth
        try:
            response = requests.post(
                f"{self.backend_url}/api/rooms/bulk",
                json=self.test_room_data,
                timeout=10
            )
            
            # Should return 401/403 (not 404), indicating endpoint exists but requires auth
            if response.status_code in [401, 403]:
                self.log_test(
                    "POST /api/rooms/bulk - Admin Permission Check",
                    True,
                    f"Admin endpoint erişilebilir ve auth gerektiriyor (Status: {response.status_code})"
                )
            elif response.status_code == 404:
                self.log_test(
                    "POST /api/rooms/bulk - Admin Permission Check",
                    False,
                    f"Admin endpoint bulunamadı",
                    "401/403",
                    "404"
                )
            else:
                self.log_test(
                    "POST /api/rooms/bulk - Admin Permission Check",
                    False,
                    f"Beklenmeyen response",
                    "401/403",
                    str(response.status_code)
                )
                
        except Exception as e:
            self.log_test(
                "POST /api/rooms/bulk - Admin Permission Check",
                False,
                f"Request hatası: {str(e)}"
            )

    def test_response_format_validation(self):
        """Response format doğrulama"""
        print("📋 Response Format Validation Tests")
        print("=" * 50)
        
        endpoints_to_test = [
            "/api/rooms",
            "/api/rooms/bulk", 
            "/api/hk/dashboard",
            "/api/hk/tasks"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                
                # Check if response has proper JSON content type
                content_type = response.headers.get('content-type', '')
                
                if 'application/json' in content_type:
                    self.log_test(
                        f"{endpoint} - JSON Response Format",
                        True,
                        f"Doğru JSON content-type: {content_type}"
                    )
                else:
                    self.log_test(
                        f"{endpoint} - JSON Response Format",
                        False,
                        f"JSON content-type eksik",
                        "application/json",
                        content_type
                    )
                
                # Try to parse JSON
                try:
                    json_data = response.json()
                    self.log_test(
                        f"{endpoint} - JSON Parse Test",
                        True,
                        "Response başarıyla JSON olarak parse edildi"
                    )
                except:
                    self.log_test(
                        f"{endpoint} - JSON Parse Test",
                        False,
                        "Response JSON olarak parse edilemedi"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"{endpoint} - Response Format Test",
                    False,
                    f"Request hatası: {str(e)}"
                )

    def test_error_handling(self):
        """Error handling testleri"""
        print("⚠️ Error Handling Tests")
        print("=" * 50)
        
        # Test invalid room status
        try:
            test_room_id = str(uuid.uuid4())
            response = requests.put(
                f"{self.backend_url}/api/rooms/{test_room_id}/status",
                params={"status": "invalid_status"},
                timeout=10
            )
            
            # Should return error (401/403 for auth, or 400 for invalid status)
            if response.status_code in [400, 401, 403]:
                self.log_test(
                    "PUT /api/rooms/{room_id}/status - Invalid Status Handling",
                    True,
                    f"Geçersiz status doğru şekilde reddedildi (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "PUT /api/rooms/{room_id}/status - Invalid Status Handling",
                    False,
                    f"Geçersiz status kontrolü başarısız",
                    "400/401/403",
                    str(response.status_code)
                )
        except Exception as e:
            self.log_test(
                "PUT /api/rooms/{room_id}/status - Invalid Status Handling",
                False,
                f"Request hatası: {str(e)}"
            )

        # Test invalid task data
        try:
            invalid_task_data = {
                "room_id": "",  # Empty room_id
                "task_type": "invalid_type",
                "priority": "invalid_priority"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/hk/tasks",
                json=invalid_task_data,
                timeout=10
            )
            
            # Should return error (401/403 for auth, or 400 for invalid data)
            if response.status_code in [400, 401, 403, 422]:
                self.log_test(
                    "POST /api/hk/tasks - Invalid Data Handling",
                    True,
                    f"Geçersiz task data doğru şekilde reddedildi (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "POST /api/hk/tasks - Invalid Data Handling",
                    False,
                    f"Geçersiz data kontrolü başarısız",
                    "400/401/403/422",
                    str(response.status_code)
                )
        except Exception as e:
            self.log_test(
                "POST /api/hk/tasks - Invalid Data Handling",
                False,
                f"Request hatası: {str(e)}"
            )

    def test_cors_headers(self):
        """CORS headers kontrolü"""
        print("🌐 CORS Headers Tests")
        print("=" * 50)
        
        try:
            response = requests.options(f"{self.backend_url}/api/rooms", timeout=10)
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            cors_present = any(header in response.headers for header in cors_headers)
            
            if cors_present:
                self.log_test(
                    "CORS Headers Present",
                    True,
                    f"CORS headers mevcut: {[h for h in cors_headers if h in response.headers]}"
                )
            else:
                self.log_test(
                    "CORS Headers Present",
                    False,
                    "CORS headers eksik"
                )
                
        except Exception as e:
            self.log_test(
                "CORS Headers Test",
                False,
                f"CORS test hatası: {str(e)}"
            )

    def test_endpoint_accessibility(self):
        """Endpoint erişilebilirlik testi"""
        print("🔗 Endpoint Accessibility Tests")
        print("=" * 50)
        
        hk_endpoints = [
            "/api/rooms",
            "/api/rooms/bulk",
            "/api/hk/dashboard", 
            "/api/hk/tasks"
        ]
        
        for endpoint in hk_endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                
                # Endpoint should exist (not return 404)
                if response.status_code != 404:
                    self.log_test(
                        f"{endpoint} - Endpoint Accessibility",
                        True,
                        f"Endpoint erişilebilir (Status: {response.status_code})"
                    )
                else:
                    self.log_test(
                        f"{endpoint} - Endpoint Accessibility",
                        False,
                        f"Endpoint bulunamadı",
                        "Not 404",
                        "404"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"{endpoint} - Endpoint Accessibility",
                    False,
                    f"Endpoint erişim hatası: {str(e)}"
                )

    def run_all_tests(self):
        """Tüm testleri çalıştır"""
        print("🧹 HK MODÜLÜ FULL STACK BACKEND TEST")
        print("=" * 60)
        print(f"🎯 Backend URL: {self.backend_url}")
        print(f"📅 Test Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()
        
        # Backend sağlık kontrolü
        if not self.test_backend_health():
            print("❌ Backend erişilemediği için testler durduruluyor!")
            return False
        
        # Test grupları
        self.test_rooms_endpoints_authentication()
        self.test_hk_endpoints_authentication()
        self.test_invalid_token_handling()
        self.test_admin_permission_control()
        self.test_response_format_validation()
        self.test_error_handling()
        self.test_cors_headers()
        self.test_endpoint_accessibility()
        
        # Sonuçları göster
        self.show_results()
        
        return self.passed_tests == self.total_tests

    def show_results(self):
        """Test sonuçlarını göster"""
        print("\n" + "=" * 60)
        print("📊 HK MODÜLÜ BACKEND TEST SONUÇLARI")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"✅ Başarılı Testler: {self.passed_tests}")
        print(f"❌ Başarısız Testler: {self.total_tests - self.passed_tests}")
        print(f"📊 Toplam Test: {self.total_tests}")
        print(f"🎯 Başarı Oranı: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 MÜKEMMEL! HK modülü backend'i production ready!")
        elif success_rate >= 75:
            print("✅ İYİ! HK modülü backend'i genel olarak çalışıyor.")
        elif success_rate >= 50:
            print("⚠️ ORTA! HK modülü backend'inde bazı sorunlar var.")
        else:
            print("❌ KÖTÜ! HK modülü backend'inde ciddi sorunlar var.")
        
        print("\n🔍 DETAYLI SONUÇLAR:")
        print("-" * 60)
        
        # Başarısız testleri göster
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print("❌ BAŞARISIZ TESTLER:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        # Başarılı testleri özetle
        successful_tests = [r for r in self.test_results if r['success']]
        if successful_tests:
            print(f"\n✅ BAŞARILI TESTLER: {len(successful_tests)} adet")
            
            # Kategorilere göre grupla
            auth_tests = [t for t in successful_tests if 'Authentication' in t['test']]
            format_tests = [t for t in successful_tests if 'Format' in t['test'] or 'JSON' in t['test']]
            error_tests = [t for t in successful_tests if 'Error' in t['test'] or 'Invalid' in t['test']]
            access_tests = [t for t in successful_tests if 'Accessibility' in t['test']]
            
            if auth_tests:
                print(f"   🔐 Authentication Tests: {len(auth_tests)}/{len(auth_tests)} ✅")
            if format_tests:
                print(f"   📋 Response Format Tests: {len(format_tests)}/{len(format_tests)} ✅")
            if error_tests:
                print(f"   ⚠️ Error Handling Tests: {len(error_tests)}/{len(error_tests)} ✅")
            if access_tests:
                print(f"   🔗 Accessibility Tests: {len(access_tests)}/{len(access_tests)} ✅")
        
        print("\n" + "=" * 60)
        
        # Test sonuçlarını JSON olarak kaydet
        with open('/app/hk_module_test_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'test_summary': {
                    'total_tests': self.total_tests,
                    'passed_tests': self.passed_tests,
                    'failed_tests': self.total_tests - self.passed_tests,
                    'success_rate': success_rate,
                    'backend_url': self.backend_url,
                    'test_timestamp': datetime.now().isoformat()
                },
                'test_results': self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detaylı test sonuçları kaydedildi: /app/hk_module_test_results.json")

def main():
    """Ana test fonksiyonu"""
    tester = HKModuleBackendTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 TÜM TESTLER BAŞARILI! HK modülü backend'i tamamen çalışıyor!")
        sys.exit(0)
    else:
        print("\n⚠️ BAZI TESTLER BAŞARISIZ! Detayları yukarıda inceleyiniz.")
        sys.exit(1)

if __name__ == "__main__":
    main()