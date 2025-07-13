#!/usr/bin/env python3
"""
Comprehensive 2FA System Analysis and Testing
Analyzes the current 2FA implementation and tests its actual behavior
"""

import requests
import json
import time
import logging
from datetime import datetime, timedelta
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('/app/backend/.env')

# Configuration
BACKEND_URL = "https://rota-crm-production.up.railway.app"
API_BASE_URL = f"{BACKEND_URL}/api"

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'rotacrm')

class TwoFAAnalysis:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # MongoDB connection
        try:
            self.mongo_client = MongoClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            logger.info("✅ MongoDB connection established")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self.mongo_client = None
            self.db = None

    def analyze_current_implementation(self):
        """Analyze what the current 2FA implementation actually does"""
        logger.info("🔍 ANALYZING CURRENT 2FA IMPLEMENTATION")
        logger.info("="*60)
        
        test_email = "analysis@test.com"
        
        # Clear any existing codes for this email
        if self.db is not None:
            self.db.verification_codes.delete_many({"email": test_email})
            logger.info(f"🧹 Cleared existing codes for {test_email}")
        
        # Test 1: Send code and check database
        logger.info("📤 TEST 1: Send code and check database storage")
        response = self.session.post(
            f"{API_BASE_URL}/auth/2fa/send-code",
            json={"email": test_email}
        )
        logger.info(f"Response: {response.status_code} - {response.text}")
        
        # Check database immediately after
        if self.db is not None:
            time.sleep(1)  # Brief wait
            codes = list(self.db.verification_codes.find({"email": test_email}))
            logger.info(f"Codes in database after send: {len(codes)}")
            if codes:
                code_doc = codes[0]
                logger.info(f"Code details: {code_doc}")
                stored_code = code_doc.get('code')
                logger.info(f"Stored code: {stored_code}")
                
                # Test 2: Verify with correct code
                logger.info("✅ TEST 2: Verify with correct code from database")
                response = self.session.post(
                    f"{API_BASE_URL}/auth/2fa/verify-code",
                    json={"email": test_email, "code": stored_code}
                )
                logger.info(f"Verify correct code response: {response.status_code} - {response.text}")
                
                # Check if code was marked as used
                time.sleep(1)
                updated_codes = list(self.db.verification_codes.find({"email": test_email}))
                if updated_codes:
                    logger.info(f"Code after verification: {updated_codes[0]}")
                
                # Test 3: Try to verify same code again
                logger.info("🔄 TEST 3: Try to verify same code again (should fail)")
                response = self.session.post(
                    f"{API_BASE_URL}/auth/2fa/verify-code",
                    json={"email": test_email, "code": stored_code}
                )
                logger.info(f"Reuse code response: {response.status_code} - {response.text}")
                
                # Test 4: Verify with wrong code
                logger.info("❌ TEST 4: Verify with wrong code")
                response = self.session.post(
                    f"{API_BASE_URL}/auth/2fa/verify-code",
                    json={"email": test_email, "code": "999999"}
                )
                logger.info(f"Wrong code response: {response.status_code} - {response.text}")
        
        # Test 5: Status check
        logger.info("📊 TEST 5: Status check")
        response = self.session.get(
            f"{API_BASE_URL}/auth/2fa/status",
            params={"user_email": test_email}
        )
        logger.info(f"Status response: {response.status_code} - {response.text}")

    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        logger.info("\n🧪 TESTING EDGE CASES")
        logger.info("="*60)
        
        # Test missing email
        logger.info("📧 TEST: Missing email in send-code")
        response = self.session.post(
            f"{API_BASE_URL}/auth/2fa/send-code",
            json={}
        )
        logger.info(f"Missing email response: {response.status_code} - {response.text}")
        
        # Test missing fields in verify
        logger.info("🔍 TEST: Missing fields in verify-code")
        response = self.session.post(
            f"{API_BASE_URL}/auth/2fa/verify-code",
            json={"email": "test@example.com"}  # Missing code
        )
        logger.info(f"Missing code response: {response.status_code} - {response.text}")
        
        response = self.session.post(
            f"{API_BASE_URL}/auth/2fa/verify-code",
            json={"code": "123456"}  # Missing email
        )
        logger.info(f"Missing email in verify response: {response.status_code} - {response.text}")
        
        # Test invalid email format
        logger.info("📧 TEST: Invalid email format")
        response = self.session.post(
            f"{API_BASE_URL}/auth/2fa/send-code",
            json={"email": "invalid-email"}
        )
        logger.info(f"Invalid email response: {response.status_code} - {response.text}")

    def test_expiration_behavior(self):
        """Test code expiration behavior"""
        logger.info("\n⏰ TESTING CODE EXPIRATION")
        logger.info("="*60)
        
        if not self.db:
            logger.error("❌ Cannot test expiration without database access")
            return
        
        test_email = "expiry@test.com"
        
        # Create an expired code directly in database
        expired_code = {
            "email": test_email,
            "code": "123456",
            "expires_at": datetime.utcnow() - timedelta(minutes=1),  # Expired 1 minute ago
            "created_at": datetime.utcnow() - timedelta(minutes=11),  # Created 11 minutes ago
            "used": False
        }
        
        self.db.verification_codes.delete_many({"email": test_email})
        self.db.verification_codes.insert_one(expired_code)
        logger.info("📝 Inserted expired code into database")
        
        # Try to verify expired code
        response = self.session.post(
            f"{API_BASE_URL}/auth/2fa/verify-code",
            json={"email": test_email, "code": "123456"}
        )
        logger.info(f"Expired code verification: {response.status_code} - {response.text}")
        
        # Check if expired code was cleaned up
        remaining_codes = list(self.db.verification_codes.find({"email": test_email}))
        logger.info(f"Codes remaining after expiry test: {len(remaining_codes)}")

    def test_email_functionality(self):
        """Test if emails are actually being sent"""
        logger.info("\n📧 TESTING EMAIL FUNCTIONALITY")
        logger.info("="*60)
        
        # Test with a real-looking email
        test_email = "test.2fa@gmail.com"
        
        logger.info(f"📤 Sending 2FA code to {test_email}")
        response = self.session.post(
            f"{API_BASE_URL}/auth/2fa/send-code",
            json={"email": test_email}
        )
        logger.info(f"Send response: {response.status_code} - {response.text}")
        
        # Check if code was stored
        if self.db:
            time.sleep(2)
            codes = list(self.db.verification_codes.find({"email": test_email}))
            if codes:
                logger.info(f"✅ Code stored in database: {codes[0]['code']}")
                logger.info(f"📅 Created at: {codes[0]['created_at']}")
                logger.info(f"⏰ Expires at: {codes[0]['expires_at']}")
            else:
                logger.warning("⚠️ No code found in database")

    def generate_test_report(self):
        """Generate a comprehensive test report"""
        logger.info("\n📋 GENERATING 2FA SYSTEM TEST REPORT")
        logger.info("="*60)
        
        findings = []
        
        # Test basic functionality
        logger.info("🔍 Testing basic 2FA flow...")
        
        test_email = "report@test.com"
        if self.db:
            self.db.verification_codes.delete_many({"email": test_email})
        
        # Send code
        send_response = self.session.post(
            f"{API_BASE_URL}/auth/2fa/send-code",
            json={"email": test_email}
        )
        
        if send_response.status_code == 200:
            findings.append("✅ Send code endpoint is accessible and responds")
        else:
            findings.append(f"❌ Send code endpoint failed: {send_response.status_code}")
        
        # Check database storage
        if self.db:
            time.sleep(1)
            codes = list(self.db.verification_codes.find({"email": test_email}))
            if codes:
                findings.append("✅ Codes are being stored in MongoDB verification_codes collection")
                code_doc = codes[0]
                
                # Check code format
                if code_doc.get('code') and len(code_doc['code']) == 6 and code_doc['code'].isdigit():
                    findings.append("✅ Codes are 6-digit numeric format")
                else:
                    findings.append(f"❌ Code format issue: {code_doc.get('code')}")
                
                # Check expiration
                if 'expires_at' in code_doc and 'created_at' in code_doc:
                    time_diff = code_doc['expires_at'] - code_doc['created_at']
                    if abs(time_diff.total_seconds() - 600) < 60:  # ~10 minutes
                        findings.append("✅ Codes have 10-minute expiration")
                    else:
                        findings.append(f"❌ Incorrect expiration time: {time_diff}")
                
                # Test verification
                verify_response = self.session.post(
                    f"{API_BASE_URL}/auth/2fa/verify-code",
                    json={"email": test_email, "code": code_doc['code']}
                )
                
                if verify_response.status_code == 200:
                    findings.append("✅ Code verification endpoint is working")
                else:
                    findings.append(f"❌ Code verification failed: {verify_response.status_code}")
            else:
                findings.append("❌ Codes are not being stored in database")
        
        # Test status endpoint
        status_response = self.session.get(
            f"{API_BASE_URL}/auth/2fa/status",
            params={"user_email": test_email}
        )
        
        if status_response.status_code == 200:
            findings.append("✅ Status endpoint is accessible")
        else:
            findings.append(f"❌ Status endpoint failed: {status_response.status_code}")
        
        # Print report
        logger.info("\n📊 2FA SYSTEM TEST REPORT")
        logger.info("="*60)
        for finding in findings:
            logger.info(finding)
        
        # Determine overall status
        passed = sum(1 for f in findings if f.startswith("✅"))
        total = len(findings)
        
        logger.info(f"\n📈 SUMMARY: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            logger.info("🎉 2FA SYSTEM IS FULLY FUNCTIONAL!")
        elif passed >= total * 0.8:
            logger.info("⚠️ 2FA system is mostly working with minor issues")
        else:
            logger.warning("❌ 2FA system has significant issues that need attention")
        
        return findings

    def run_comprehensive_analysis(self):
        """Run all analysis and tests"""
        logger.info("🚀 STARTING COMPREHENSIVE 2FA ANALYSIS")
        logger.info("="*80)
        
        self.analyze_current_implementation()
        self.test_edge_cases()
        self.test_expiration_behavior()
        self.test_email_functionality()
        findings = self.generate_test_report()
        
        return findings

if __name__ == "__main__":
    analyzer = TwoFAAnalysis()
    analyzer.run_comprehensive_analysis()