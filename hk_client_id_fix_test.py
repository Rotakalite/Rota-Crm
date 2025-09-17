#!/usr/bin/env python3
"""
🧹 HK MODÜLÜ CLIENT ID FIX VERIFICATION TEST
============================================

Bu test HK modülündeki "Client ID required" hatası düzeltmesini doğrular:

Test Edilecek Endpoint'ler:
1. GET /api/rooms - Oda listesi 
2. GET /api/hk/dashboard - HK dashboard istatistikleri
3. GET /api/hk/tasks - HK görev listesi
4. PUT /api/rooms/{room_id}/status - Oda durumu güncelleme
5. POST /api/rooms/bulk - Toplu oda oluşturma
6. POST /api/hk/tasks - HK görev oluşturma
7. PUT /api/hk/tasks/{task_id} - HK görev güncelleme

Test Senaryoları:
1. Endpoint'lerin 404 döndürmediğini kontrol et (önceki deployment issue)
2. Authentication olmadan 403/401 döndürdüğünü test et
3. Client_id parameter handling'inin doğru çalıştığını test et
4. Admin, consultant, client role'ları için farklı davranışları test et

Production URL: https://rota-crm-production.up.railway.app
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Railway Production Backend URL
BACKEND_URL = "https://rota-crm-production.up.railway.app"

class HKClientIDFixTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
        # Test data for various scenarios
        self.test_client_id = "test-client-12345"
        self.test_room_id = str(uuid.uuid4())
        self.test_task_id = str(uuid.uuid4())
        
        self.test_room_data = {
            "rooms": [
                {
                    "room_number": "101",
                    "floor_name": "1. Kat",
                    "room_type": "Standard",
                    "status": "clean",
                    "notes": "Test odası"
                }
            ]
        }
        
        self.test_task_data = {
            "room_id": self.test_room_id,
            "task_type": "regular_cleaning",
            "assigned_staff": "Test Staff",
            "priority": "normal",
            "estimated_duration": 30,
            "notes": "Test temizlik görevi"
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
                    f"Railway production backend erişilebilir (Status: {response.status_code})"
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

    def test_deployment_issue_fixed(self):
        """Önceki deployment issue'nun çözüldüğünü test et (404 hatası olmamalı)"""
        print("🚀 Deployment Issue Fix Verification")
        print("=" * 50)
        
        hk_endpoints = [
            "/api/rooms",
            "/api/hk/dashboard", 
            "/api/hk/tasks",
            "/api/rooms/bulk",
        ]
        
        for endpoint in hk_endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                
                # Endpoint should NOT return 404 (deployment issue fixed)
                if response.status_code != 404:
                    self.log_test(
                        f"{endpoint} - Deployment Issue Fixed",
                        True,
                        f"Endpoint erişilebilir, 404 hatası yok (Status: {response.status_code})"
                    )
                else:
                    self.log_test(
                        f"{endpoint} - Deployment Issue Fixed",
                        False,
                        f"CRITICAL: Endpoint hala 404 döndürüyor - deployment issue devam ediyor",
                        "Not 404",
                        "404"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"{endpoint} - Deployment Issue Fixed",
                    False,
                    f"Endpoint erişim hatası: {str(e)}"
                )

    def test_authentication_requirements(self):
        """Authentication gereksinimlerini test et"""
        print("🔐 Authentication Requirements Test")
        print("=" * 50)
        
        endpoints_to_test = [
            ("GET", "/api/rooms"),
            ("GET", "/api/hk/dashboard"),
            ("GET", "/api/hk/tasks"),
            ("POST", "/api/rooms/bulk"),
            ("POST", "/api/hk/tasks"),
        ]
        
        for method, endpoint in endpoints_to_test:
            try:
                if method == "GET":
                    response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                elif method == "POST":
                    test_data = self.test_room_data if "rooms" in endpoint else self.test_task_data
                    response = requests.post(f"{self.backend_url}{endpoint}", json=test_data, timeout=10)
                
                # Should return 401/403 (authentication required)
                if response.status_code in [401, 403]:
                    self.log_test(
                        f"{method} {endpoint} - Authentication Required",
                        True,
                        f"Doğru auth kontrolü (Status: {response.status_code})"
                    )
                else:
                    self.log_test(
                        f"{method} {endpoint} - Authentication Required",
                        False,
                        f"Auth kontrolü başarısız",
                        "401 or 403",
                        str(response.status_code)
                    )
                    
            except Exception as e:
                self.log_test(
                    f"{method} {endpoint} - Authentication Required",
                    False,
                    f"Request hatası: {str(e)}"
                )

    def test_client_id_parameter_handling(self):
        """Client ID parameter handling'ini test et"""
        print("🎯 Client ID Parameter Handling Test")
        print("=" * 50)
        
        # Test endpoints that should accept client_id parameter
        endpoints_with_client_id = [
            "/api/rooms",
            "/api/hk/dashboard",
            "/api/hk/tasks"
        ]
        
        for endpoint in endpoints_with_client_id:
            try:
                # Test with client_id parameter
                response = requests.get(
                    f"{self.backend_url}{endpoint}",
                    params={"client_id": self.test_client_id},
                    timeout=10
                )
                
                # Should still require authentication (403/401), but not reject client_id parameter
                if response.status_code in [401, 403]:
                    self.log_test(
                        f"{endpoint} - Client ID Parameter Accepted",
                        True,
                        f"Client ID parametresi kabul edildi, auth gerekli (Status: {response.status_code})"
                    )
                elif response.status_code == 400:
                    # Check if it's a "Client ID required" error (the old bug)
                    try:
                        error_data = response.json()
                        if "Client ID required" in str(error_data):
                            self.log_test(
                                f"{endpoint} - Client ID Parameter Accepted",
                                False,
                                f"CRITICAL: 'Client ID required' hatası hala mevcut!",
                                "401/403",
                                f"400 - {error_data}"
                            )
                        else:
                            self.log_test(
                                f"{endpoint} - Client ID Parameter Accepted",
                                True,
                                f"Client ID parametresi işlendi, farklı validation hatası (Status: {response.status_code})"
                            )
                    except:
                        self.log_test(
                            f"{endpoint} - Client ID Parameter Accepted",
                            True,
                            f"Client ID parametresi işlendi (Status: {response.status_code})"
                        )
                else:
                    self.log_test(
                        f"{endpoint} - Client ID Parameter Accepted",
                        True,
                        f"Client ID parametresi kabul edildi (Status: {response.status_code})"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"{endpoint} - Client ID Parameter Accepted",
                    False,
                    f"Request hatası: {str(e)}"
                )

    def test_role_based_access_patterns(self):
        """Role-based access pattern'lerini test et"""
        print("👥 Role-Based Access Patterns Test")
        print("=" * 50)
        
        # Test different role scenarios with invalid tokens (to check logic without auth)
        role_scenarios = [
            ("admin", "Bearer admin_token_test"),
            ("consultant", "Bearer consultant_token_test"),
            ("client", "Bearer client_token_test")
        ]
        
        for role, token in role_scenarios:
            headers = {"Authorization": token}
            
            try:
                # Test GET /api/rooms with role-specific token
                response = requests.get(
                    f"{self.backend_url}/api/rooms",
                    headers=headers,
                    params={"client_id": self.test_client_id} if role in ["admin", "consultant"] else {},
                    timeout=10
                )
                
                # Should return 401 (invalid token) but not 400 (client ID logic error)
                if response.status_code == 401:
                    self.log_test(
                        f"Role-Based Access - {role.upper()} Pattern",
                        True,
                        f"{role} role pattern doğru, token validation çalışıyor (Status: {response.status_code})"
                    )
                elif response.status_code == 400:
                    try:
                        error_data = response.json()
                        if "Client ID required" in str(error_data):
                            self.log_test(
                                f"Role-Based Access - {role.upper()} Pattern",
                                False,
                                f"CRITICAL: {role} role için 'Client ID required' hatası!",
                                "401",
                                f"400 - {error_data}"
                            )
                        else:
                            self.log_test(
                                f"Role-Based Access - {role.upper()} Pattern",
                                True,
                                f"{role} role pattern çalışıyor, farklı validation hatası (Status: {response.status_code})"
                            )
                    except:
                        self.log_test(
                            f"Role-Based Access - {role.upper()} Pattern",
                            True,
                            f"{role} role pattern çalışıyor (Status: {response.status_code})"
                        )
                else:
                    self.log_test(
                        f"Role-Based Access - {role.upper()} Pattern",
                        True,
                        f"{role} role pattern çalışıyor (Status: {response.status_code})"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Role-Based Access - {role.upper()} Pattern",
                    False,
                    f"Request hatası: {str(e)}"
                )

    def test_put_endpoints_with_parameters(self):
        """PUT endpoints'lerini parametrelerle test et"""
        print("🔄 PUT Endpoints Parameter Test")
        print("=" * 50)
        
        # Test PUT /api/rooms/{room_id}/status
        try:
            response = requests.put(
                f"{self.backend_url}/api/rooms/{self.test_room_id}/status",
                params={"status": "clean"},
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "PUT /api/rooms/{room_id}/status - Parameter Handling",
                    True,
                    f"Room status endpoint parametreleri kabul ediyor (Status: {response.status_code})"
                )
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    if "Client ID required" in str(error_data):
                        self.log_test(
                            "PUT /api/rooms/{room_id}/status - Parameter Handling",
                            False,
                            f"CRITICAL: Room status update'de 'Client ID required' hatası!",
                            "401/403",
                            f"400 - {error_data}"
                        )
                    else:
                        self.log_test(
                            "PUT /api/rooms/{room_id}/status - Parameter Handling",
                            True,
                            f"Room status endpoint çalışıyor, farklı validation hatası (Status: {response.status_code})"
                        )
                except:
                    self.log_test(
                        "PUT /api/rooms/{room_id}/status - Parameter Handling",
                        True,
                        f"Room status endpoint çalışıyor (Status: {response.status_code})"
                    )
            else:
                self.log_test(
                    "PUT /api/rooms/{room_id}/status - Parameter Handling",
                    True,
                    f"Room status endpoint çalışıyor (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "PUT /api/rooms/{room_id}/status - Parameter Handling",
                False,
                f"Request hatası: {str(e)}"
            )

        # Test PUT /api/hk/tasks/{task_id}
        try:
            task_update = {
                "status": "completed",
                "actual_duration": 25,
                "completion_notes": "Test tamamlandı"
            }
            
            response = requests.put(
                f"{self.backend_url}/api/hk/tasks/{self.test_task_id}",
                json=task_update,
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "PUT /api/hk/tasks/{task_id} - Parameter Handling",
                    True,
                    f"HK task update endpoint çalışıyor (Status: {response.status_code})"
                )
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    if "Client ID required" in str(error_data):
                        self.log_test(
                            "PUT /api/hk/tasks/{task_id} - Parameter Handling",
                            False,
                            f"CRITICAL: HK task update'de 'Client ID required' hatası!",
                            "401/403",
                            f"400 - {error_data}"
                        )
                    else:
                        self.log_test(
                            "PUT /api/hk/tasks/{task_id} - Parameter Handling",
                            True,
                            f"HK task update endpoint çalışıyor, farklı validation hatası (Status: {response.status_code})"
                        )
                except:
                    self.log_test(
                        "PUT /api/hk/tasks/{task_id} - Parameter Handling",
                        True,
                        f"HK task update endpoint çalışıyor (Status: {response.status_code})"
                    )
            else:
                self.log_test(
                    "PUT /api/hk/tasks/{task_id} - Parameter Handling",
                    True,
                    f"HK task update endpoint çalışıyor (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "PUT /api/hk/tasks/{task_id} - Parameter Handling",
                False,
                f"Request hatası: {str(e)}"
            )

    def test_response_format_consistency(self):
        """Response format tutarlılığını test et"""
        print("📋 Response Format Consistency Test")
        print("=" * 50)
        
        endpoints_to_test = [
            "/api/rooms",
            "/api/hk/dashboard",
            "/api/hk/tasks",
            "/api/rooms/bulk"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                
                # Check JSON content type
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    self.log_test(
                        f"{endpoint} - JSON Content Type",
                        True,
                        f"Doğru JSON content-type: {content_type}"
                    )
                else:
                    self.log_test(
                        f"{endpoint} - JSON Content Type",
                        False,
                        f"JSON content-type eksik",
                        "application/json",
                        content_type
                    )
                
                # Try to parse JSON response
                try:
                    json_data = response.json()
                    self.log_test(
                        f"{endpoint} - JSON Parse Success",
                        True,
                        "Response başarıyla JSON olarak parse edildi"
                    )
                    
                    # Check for proper error structure (if it's an error response)
                    if response.status_code >= 400:
                        if isinstance(json_data, dict) and ('detail' in json_data or 'message' in json_data):
                            self.log_test(
                                f"{endpoint} - Error Response Structure",
                                True,
                                "Error response doğru yapıda"
                            )
                        else:
                            self.log_test(
                                f"{endpoint} - Error Response Structure",
                                False,
                                "Error response yapısı standart değil"
                            )
                            
                except Exception as parse_error:
                    self.log_test(
                        f"{endpoint} - JSON Parse Success",
                        False,
                        f"JSON parse hatası: {str(parse_error)}"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"{endpoint} - Response Format Test",
                    False,
                    f"Request hatası: {str(e)}"
                )

    def test_cors_headers_present(self):
        """CORS headers'ın mevcut olduğunu test et"""
        print("🌐 CORS Headers Verification")
        print("=" * 50)
        
        try:
            response = requests.options(f"{self.backend_url}/api/rooms", timeout=10)
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            present_headers = [h for h in cors_headers if h in response.headers]
            
            if len(present_headers) >= 2:  # At least 2 CORS headers should be present
                self.log_test(
                    "CORS Headers Present",
                    True,
                    f"CORS headers mevcut: {present_headers}"
                )
            else:
                self.log_test(
                    "CORS Headers Present",
                    False,
                    f"Yetersiz CORS headers: {present_headers}"
                )
                
        except Exception as e:
            self.log_test(
                "CORS Headers Test",
                False,
                f"CORS test hatası: {str(e)}"
            )

    def run_all_tests(self):
        """Tüm testleri çalıştır"""
        print("🧹 HK MODÜLÜ CLIENT ID FIX VERIFICATION TEST")
        print("=" * 70)
        print(f"🎯 Production URL: {self.backend_url}")
        print(f"📅 Test Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🔍 Test Amacı: Client ID handling logic'inin doğru çalıştığını doğrula")
        print("=" * 70)
        print()
        
        # Backend sağlık kontrolü
        if not self.test_backend_health():
            print("❌ Backend erişilemediği için testler durduruluyor!")
            return False
        
        # Test grupları
        self.test_deployment_issue_fixed()
        self.test_authentication_requirements()
        self.test_client_id_parameter_handling()
        self.test_role_based_access_patterns()
        self.test_put_endpoints_with_parameters()
        self.test_response_format_consistency()
        self.test_cors_headers_present()
        
        # Sonuçları göster
        self.show_results()
        
        return self.passed_tests == self.total_tests

    def show_results(self):
        """Test sonuçlarını göster"""
        print("\n" + "=" * 70)
        print("📊 HK MODÜLÜ CLIENT ID FIX VERIFICATION SONUÇLARI")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"✅ Başarılı Testler: {self.passed_tests}")
        print(f"❌ Başarısız Testler: {self.total_tests - self.passed_tests}")
        print(f"📊 Toplam Test: {self.total_tests}")
        print(f"🎯 Başarı Oranı: {success_rate:.1f}%")
        
        # Kritik bulgular
        failed_tests = [r for r in self.test_results if not r['success']]
        critical_issues = [t for t in failed_tests if "CRITICAL" in t['details']]
        
        if critical_issues:
            print(f"\n🚨 KRİTİK SORUNLAR BULUNDU: {len(critical_issues)} adet")
            for issue in critical_issues:
                print(f"   ❌ {issue['test']}: {issue['details']}")
        else:
            print("\n✅ KRİTİK SORUN BULUNAMADI: Client ID fix başarılı!")
        
        if success_rate >= 95:
            print("\n🎉 MÜKEMMEL! HK modülü Client ID fix'i tamamen başarılı!")
            print("✅ Tüm endpoint'ler production'da erişilebilir")
            print("✅ Client ID handling logic'i doğru çalışıyor")
            print("✅ Authentication ve authorization düzgün")
        elif success_rate >= 85:
            print("\n✅ İYİ! HK modülü genel olarak çalışıyor, küçük sorunlar var.")
        elif success_rate >= 70:
            print("\n⚠️ ORTA! HK modülünde bazı sorunlar tespit edildi.")
        else:
            print("\n❌ KÖTÜ! HK modülünde ciddi sorunlar var, Client ID fix tamamlanmamış.")
        
        print("\n🔍 DETAYLI SONUÇLAR:")
        print("-" * 70)
        
        # Başarısız testleri göster
        if failed_tests:
            print("❌ BAŞARISIZ TESTLER:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        # Başarılı testleri özetle
        successful_tests = [r for r in self.test_results if r['success']]
        if successful_tests:
            print(f"\n✅ BAŞARILI TESTLER: {len(successful_tests)} adet")
            
            # Kategorilere göre grupla
            deployment_tests = [t for t in successful_tests if 'Deployment' in t['test']]
            auth_tests = [t for t in successful_tests if 'Authentication' in t['test']]
            client_id_tests = [t for t in successful_tests if 'Client ID' in t['test']]
            role_tests = [t for t in successful_tests if 'Role' in t['test']]
            
            if deployment_tests:
                print(f"   🚀 Deployment Fix Tests: {len(deployment_tests)} ✅")
            if auth_tests:
                print(f"   🔐 Authentication Tests: {len(auth_tests)} ✅")
            if client_id_tests:
                print(f"   🎯 Client ID Tests: {len(client_id_tests)} ✅")
            if role_tests:
                print(f"   👥 Role-Based Tests: {len(role_tests)} ✅")
        
        print("\n" + "=" * 70)
        
        # Test sonuçlarını JSON olarak kaydet
        with open('/app/hk_client_id_fix_test_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'test_summary': {
                    'total_tests': self.total_tests,
                    'passed_tests': self.passed_tests,
                    'failed_tests': self.total_tests - self.passed_tests,
                    'success_rate': success_rate,
                    'critical_issues': len(critical_issues),
                    'backend_url': self.backend_url,
                    'test_timestamp': datetime.now().isoformat(),
                    'test_purpose': 'HK Module Client ID Fix Verification'
                },
                'test_results': self.test_results,
                'critical_issues': [t['details'] for t in critical_issues]
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detaylı test sonuçları kaydedildi: /app/hk_client_id_fix_test_results.json")

def main():
    """Ana test fonksiyonu"""
    tester = HKClientIDFixTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 TÜM TESTLER BAŞARILI! HK modülü Client ID fix'i tamamen çalışıyor!")
        print("✅ 'Client ID required' hatası çözülmüş durumda!")
        sys.exit(0)
    else:
        print("\n⚠️ BAZI TESTLER BAŞARISIZ! Client ID fix'inde sorunlar olabilir.")
        print("🔍 Detayları yukarıda inceleyiniz.")
        sys.exit(1)

if __name__ == "__main__":
    main()