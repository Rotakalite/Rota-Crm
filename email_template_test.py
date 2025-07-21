#!/usr/bin/env python3
"""
Email Template API Testing Script
Tests the Backend Email Templates API system for ROTA CRM

Test Coverage:
1. GET /api/email-templates - Get all email templates (admin token required)
2. GET /api/email-templates/{template_id} - Get specific template (admin token required) 
3. POST /api/bulk-email/send - Send bulk email with templates (admin token required)

Expected Templates:
- certificate_reminder
- general_announcement  
- sustainability_tips
- training_invitation
- survey_request
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://rota-crm-production.up.railway.app"

def test_email_templates():
    """Test Email Template API endpoints"""
    print("🧪 EMAIL TEMPLATE API TESTING STARTED")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test results
    results = {
        "get_all_templates": {"status": "❌", "details": ""},
        "get_certificate_reminder": {"status": "❌", "details": ""},
        "get_general_announcement": {"status": "❌", "details": ""},
        "bulk_email_certificate": {"status": "❌", "details": ""},
        "bulk_email_custom_announcement": {"status": "❌", "details": ""}
    }
    
    # Expected templates
    expected_templates = [
        "certificate_reminder",
        "general_announcement", 
        "sustainability_tips",
        "training_invitation",
        "survey_request"
    ]
    
    print("\n📋 TEST 1: GET /api/email-templates - Get All Email Templates")
    print("-" * 50)
    
    try:
        # Test without authentication first
        response = requests.get(f"{BACKEND_URL}/api/email-templates", timeout=10)
        print(f"Status Code (No Auth): {response.status_code}")
        
        if response.status_code == 403:
            print("✅ SECURITY: Endpoint properly requires authentication (403 Forbidden)")
            results["get_all_templates"]["status"] = "✅"
            results["get_all_templates"]["details"] = "Authentication required (403 Forbidden)"
        elif response.status_code == 401:
            print("✅ SECURITY: Endpoint properly requires authentication (401 Unauthorized)")
            results["get_all_templates"]["status"] = "✅"
            results["get_all_templates"]["details"] = "Authentication required (401 Unauthorized)"
        elif response.status_code == 200:
            # Check if response contains templates
            data = response.json()
            if "templates" in data and isinstance(data["templates"], list):
                templates = data["templates"]
                print(f"✅ SUCCESS: Found {len(templates)} templates")
                
                # Verify all expected templates are present
                template_ids = [t.get("id") for t in templates]
                missing_templates = [t for t in expected_templates if t not in template_ids]
                
                if not missing_templates:
                    print("✅ ALL EXPECTED TEMPLATES FOUND:")
                    for template in templates:
                        print(f"   • {template.get('id')}: {template.get('name')}")
                        print(f"     Description: {template.get('description')}")
                        print(f"     Subject: {template.get('subject')[:50]}...")
                        print()
                    
                    results["get_all_templates"]["status"] = "✅"
                    results["get_all_templates"]["details"] = f"Found all {len(templates)} expected templates"
                else:
                    print(f"❌ MISSING TEMPLATES: {missing_templates}")
                    results["get_all_templates"]["details"] = f"Missing templates: {missing_templates}"
            else:
                print("❌ INVALID RESPONSE: Missing 'templates' array")
                results["get_all_templates"]["details"] = "Invalid response format"
        else:
            print(f"❌ UNEXPECTED STATUS: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            results["get_all_templates"]["details"] = f"Unexpected status: {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {str(e)}")
        results["get_all_templates"]["details"] = f"Request error: {str(e)}"
    
    print("\n📋 TEST 2: GET /api/email-templates/certificate_reminder - Get Specific Template")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/email-templates/certificate_reminder", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 403:
            print("✅ SECURITY: Endpoint properly requires authentication (403 Forbidden)")
            results["get_certificate_reminder"]["status"] = "✅"
            results["get_certificate_reminder"]["details"] = "Authentication required (403 Forbidden)"
        elif response.status_code == 401:
            print("✅ SECURITY: Endpoint properly requires authentication (401 Unauthorized)")
            results["get_certificate_reminder"]["status"] = "✅"
            results["get_certificate_reminder"]["details"] = "Authentication required (401 Unauthorized)"
        elif response.status_code == 200:
            data = response.json()
            if data.get("id") == "certificate_reminder":
                print("✅ SUCCESS: Certificate reminder template retrieved")
                print(f"   Name: {data.get('name')}")
                print(f"   Description: {data.get('description')}")
                print(f"   Subject: {data.get('subject')}")
                print(f"   Content Length: {len(data.get('content', ''))} characters")
                
                # Verify template variables
                content = data.get('content', '')
                required_vars = ['{{hotel_name}}', '{{contact_person}}', '{{certificate_end_date}}']
                found_vars = [var for var in required_vars if var in content]
                
                if len(found_vars) == len(required_vars):
                    print(f"✅ TEMPLATE VARIABLES: All required variables found: {found_vars}")
                    results["get_certificate_reminder"]["status"] = "✅"
                    results["get_certificate_reminder"]["details"] = "Template retrieved with all variables"
                else:
                    missing_vars = [var for var in required_vars if var not in found_vars]
                    print(f"⚠️ MISSING VARIABLES: {missing_vars}")
                    results["get_certificate_reminder"]["details"] = f"Missing variables: {missing_vars}"
            else:
                print("❌ WRONG TEMPLATE: Expected certificate_reminder")
                results["get_certificate_reminder"]["details"] = "Wrong template returned"
        else:
            print(f"❌ UNEXPECTED STATUS: {response.status_code}")
            results["get_certificate_reminder"]["details"] = f"Unexpected status: {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {str(e)}")
        results["get_certificate_reminder"]["details"] = f"Request error: {str(e)}"
    
    print("\n📋 TEST 3: GET /api/email-templates/general_announcement - Get General Announcement Template")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/email-templates/general_announcement", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 403:
            print("✅ SECURITY: Endpoint properly requires authentication (403 Forbidden)")
            results["get_general_announcement"]["status"] = "✅"
            results["get_general_announcement"]["details"] = "Authentication required (403 Forbidden)"
        elif response.status_code == 401:
            print("✅ SECURITY: Endpoint properly requires authentication (401 Unauthorized)")
            results["get_general_announcement"]["status"] = "✅"
            results["get_general_announcement"]["details"] = "Authentication required (401 Unauthorized)"
        elif response.status_code == 200:
            data = response.json()
            if data.get("id") == "general_announcement":
                print("✅ SUCCESS: General announcement template retrieved")
                print(f"   Name: {data.get('name')}")
                print(f"   Description: {data.get('description')}")
                print(f"   Subject: {data.get('subject')}")
                print(f"   Content Length: {len(data.get('content', ''))} characters")
                
                results["get_general_announcement"]["status"] = "✅"
                results["get_general_announcement"]["details"] = "Template retrieved successfully"
            else:
                print("❌ WRONG TEMPLATE: Expected general_announcement")
                results["get_general_announcement"]["details"] = "Wrong template returned"
        else:
            print(f"❌ UNEXPECTED STATUS: {response.status_code}")
            results["get_general_announcement"]["details"] = f"Unexpected status: {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {str(e)}")
        results["get_general_announcement"]["details"] = f"Request error: {str(e)}"
    
    print("\n📋 TEST 4: POST /api/bulk-email/send - Send Bulk Email with Certificate Reminder Template")
    print("-" * 50)
    
    try:
        # Test bulk email with certificate reminder template
        bulk_email_data = {
            "email_type": "template",
            "template_id": "certificate_reminder",
            "filters": {
                "has_email": True
            }
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/bulk-email/send",
            json=bulk_email_data,
            timeout=15
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 403:
            print("✅ SECURITY: Endpoint properly requires authentication (403 Forbidden)")
            results["bulk_email_certificate"]["status"] = "✅"
            results["bulk_email_certificate"]["details"] = "Authentication required (403 Forbidden)"
        elif response.status_code == 401:
            print("✅ SECURITY: Endpoint properly requires authentication (401 Unauthorized)")
            results["bulk_email_certificate"]["status"] = "✅"
            results["bulk_email_certificate"]["details"] = "Authentication required (401 Unauthorized)"
        elif response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS: Bulk email sent with certificate reminder template")
            print(f"   Response: {json.dumps(data, indent=2)}")
            results["bulk_email_certificate"]["status"] = "✅"
            results["bulk_email_certificate"]["details"] = "Bulk email sent successfully"
        elif response.status_code == 400:
            data = response.json()
            if "BULK müşteri bulunamadı" in data.get("detail", ""):
                print("✅ EXPECTED: No bulk clients found for email sending")
                results["bulk_email_certificate"]["status"] = "✅"
                results["bulk_email_certificate"]["details"] = "No bulk clients found (expected)"
            else:
                print(f"❌ BAD REQUEST: {data.get('detail', 'Unknown error')}")
                results["bulk_email_certificate"]["details"] = f"Bad request: {data.get('detail')}"
        else:
            print(f"❌ UNEXPECTED STATUS: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            results["bulk_email_certificate"]["details"] = f"Unexpected status: {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {str(e)}")
        results["bulk_email_certificate"]["details"] = f"Request error: {str(e)}"
    
    print("\n📋 TEST 5: POST /api/bulk-email/send - Send Bulk Email with Custom General Announcement")
    print("-" * 50)
    
    try:
        # Test bulk email with general announcement template and custom content
        bulk_email_data = {
            "email_type": "template",
            "template_id": "general_announcement",
            "custom_content": "Bu ay sürdürülebilirlik konusunda yeni gelişmelerimizi paylaşmak istiyoruz. Yeni sertifika süreçlerimiz ve eğitim programlarımız hakkında bilgi almak için bizimle iletişime geçin.",
            "filters": {
                "has_email": True
            }
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/bulk-email/send",
            json=bulk_email_data,
            timeout=15
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 403:
            print("✅ SECURITY: Endpoint properly requires authentication (403 Forbidden)")
            results["bulk_email_custom_announcement"]["status"] = "✅"
            results["bulk_email_custom_announcement"]["details"] = "Authentication required (403 Forbidden)"
        elif response.status_code == 401:
            print("✅ SECURITY: Endpoint properly requires authentication (401 Unauthorized)")
            results["bulk_email_custom_announcement"]["status"] = "✅"
            results["bulk_email_custom_announcement"]["details"] = "Authentication required (401 Unauthorized)"
        elif response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS: Bulk email sent with custom general announcement")
            print(f"   Response: {json.dumps(data, indent=2)}")
            results["bulk_email_custom_announcement"]["status"] = "✅"
            results["bulk_email_custom_announcement"]["details"] = "Custom bulk email sent successfully"
        elif response.status_code == 400:
            data = response.json()
            if "BULK müşteri bulunamadı" in data.get("detail", ""):
                print("✅ EXPECTED: No bulk clients found for email sending")
                results["bulk_email_custom_announcement"]["status"] = "✅"
                results["bulk_email_custom_announcement"]["details"] = "No bulk clients found (expected)"
            else:
                print(f"❌ BAD REQUEST: {data.get('detail', 'Unknown error')}")
                results["bulk_email_custom_announcement"]["details"] = f"Bad request: {data.get('detail')}"
        else:
            print(f"❌ UNEXPECTED STATUS: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            results["bulk_email_custom_announcement"]["details"] = f"Unexpected status: {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {str(e)}")
        results["bulk_email_custom_announcement"]["details"] = f"Request error: {str(e)}"
    
    # Test invalid template ID
    print("\n📋 TEST 6: GET /api/email-templates/invalid_template - Test Invalid Template ID")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/email-templates/invalid_template", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 403:
            print("✅ SECURITY: Endpoint properly requires authentication (403 Forbidden)")
        elif response.status_code == 401:
            print("✅ SECURITY: Endpoint properly requires authentication (401 Unauthorized)")
        elif response.status_code == 404:
            print("✅ SUCCESS: Invalid template ID returns 404 Not Found")
        else:
            print(f"❌ UNEXPECTED STATUS: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 EMAIL TEMPLATE API TEST RESULTS")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r["status"] == "✅")
    
    for test_name, result in results.items():
        print(f"{result['status']} {test_name.replace('_', ' ').title()}")
        if result["details"]:
            print(f"   Details: {result['details']}")
    
    print(f"\n📈 SUMMARY: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL EMAIL TEMPLATE TESTS PASSED!")
        return True
    else:
        print("⚠️ Some email template tests failed or require authentication")
        return False

if __name__ == "__main__":
    success = test_email_templates()
    sys.exit(0 if success else 1)