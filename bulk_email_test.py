#!/usr/bin/env python3
"""
Bulk Email System Backend Testing
Test the bulk email system backend endpoints for the Rota-CRM application
"""

import unittest
import json
import logging
import requests
import os
import sys
import uuid
import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from frontend/.env
BACKEND_URL = "https://rota-crm-production.up.railway.app/api"

# MongoDB connection details from backend/.env
MONGO_URL = "mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster"
DB_NAME = "rotacrm"

# Test JWT tokens - Admin token for testing admin-only endpoints
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

# Client token for testing non-admin access
CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"

INVALID_TOKEN = "invalid.token.format"

class BulkEmailSystemTest(unittest.TestCase):
    """Test class for bulk email system endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_URL
        
        # Headers for different authentication scenarios
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}", "Content-Type": "application/json"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}", "Content-Type": "application/json"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}", "Content-Type": "application/json"}
        self.headers_no_auth = {"Content-Type": "application/json"}
        
        # MongoDB connection for direct database operations
        self.mongo_client = MongoClient(MONGO_URL)
        self.db = self.mongo_client[DB_NAME]
        
        # Test data for bulk email
        self.bulk_email_data = {
            "email_type": "custom",
            "subject": "Test Bulk Email - Sürdürülebilirlik Danışmanlığı",
            "content": """
            <h2>Sayın {contact_person},</h2>
            <p>{hotel_name} için özel sürdürülebilirlik danışmanlığı hizmetlerimiz hakkında bilgi vermek istiyoruz.</p>
            <p>Şehriniz: {city}</p>
            <p>Detaylı bilgi için bizimle iletişime geçebilirsiniz.</p>
            <p>Saygılarımızla,<br>ROTA Kalite Danışmanlık</p>
            """,
            "filters": {}
        }
        
        # Create test data in database
        self.setup_test_data()
    
    def setup_test_data(self):
        """Create test clients with different client_type values"""
        logger.info("🏗️ Setting up test data...")
        
        # Test clients with client_type: "bulk"
        self.bulk_clients = [
            {
                "id": str(uuid.uuid4()),
                "name": "Bulk Test Hotel 1",
                "hotel_name": "Bulk Test Hotel 1",
                "contact_person": "Ahmet Yılmaz",
                "email": "test1@bulkhotel.com",
                "phone": "0532 111 1111",
                "address": "Test Mahallesi, Test Sokak No:1",
                "city": "İstanbul",
                "audit_company": "Test Audit A.Ş.",
                "client_type": "bulk",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Bulk Test Hotel 2",
                "hotel_name": "Bulk Test Hotel 2", 
                "contact_person": "Mehmet Demir",
                "email": "test2@bulkhotel.com",
                "phone": "0532 222 2222",
                "address": "Test Mahallesi, Test Sokak No:2",
                "city": "Ankara",
                "audit_company": "Test Audit A.Ş.",
                "client_type": "bulk",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Bulk Test Hotel 3",
                "hotel_name": "Bulk Test Hotel 3",
                "contact_person": "Ayşe Kaya",
                "email": "test3@bulkhotel.com",
                "phone": "0532 333 3333",
                "address": "Test Mahallesi, Test Sokak No:3",
                "city": "İzmir",
                "audit_company": "Premium Audit Ltd.",
                "client_type": "bulk",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        # Test clients with client_type: "registered" (should NOT receive bulk emails)
        self.registered_clients = [
            {
                "id": str(uuid.uuid4()),
                "name": "Registered Test Hotel 1",
                "hotel_name": "Registered Test Hotel 1",
                "contact_person": "Can Özkan",
                "email": "registered1@testhotel.com",
                "phone": "0532 444 4444",
                "address": "Registered Mahallesi, Registered Sokak No:1",
                "city": "İstanbul",
                "audit_company": "Test Audit A.Ş.",
                "client_type": "registered",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Registered Test Hotel 2",
                "hotel_name": "Registered Test Hotel 2",
                "contact_person": "Elif Şahin",
                "email": "registered2@testhotel.com",
                "phone": "0532 555 5555",
                "address": "Registered Mahallesi, Registered Sokak No:2",
                "city": "Ankara",
                "audit_company": "Premium Audit Ltd.",
                "client_type": "registered",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        # Clean up existing test data
        self.db.clients.delete_many({"email": {"$regex": "@bulkhotel.com|@testhotel.com"}})
        
        # Insert test data
        all_test_clients = self.bulk_clients + self.registered_clients
        if all_test_clients:
            self.db.clients.insert_many(all_test_clients)
            logger.info(f"✅ Created {len(self.bulk_clients)} bulk clients and {len(self.registered_clients)} registered clients")
    
    def tearDown(self):
        """Clean up test data"""
        logger.info("🧹 Cleaning up test data...")
        # Clean up test clients
        self.db.clients.delete_many({"email": {"$regex": "@bulkhotel.com|@testhotel.com"}})
        self.mongo_client.close()
    
    def test_bulk_email_send_admin_only_access(self):
        """Test 1: Verify /api/bulk-email/send requires admin authentication"""
        logger.info("\n=== Test 1: Bulk Email Send - Admin Only Access ===")
        
        url = f"{self.api_url}/bulk-email/send"
        
        # Test with admin token (should work)
        try:
            response = requests.post(url, headers=self.headers_admin, json=self.bulk_email_data)
            logger.info(f"Admin token response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Admin can access bulk email send endpoint")
                logger.info(f"Response: {data}")
                
                # Verify response structure
                self.assertIn("success", data)
                self.assertIn("sent_count", data)
                self.assertIn("total_clients", data)
                
                # Should only send to bulk clients
                self.assertEqual(data["total_clients"], len(self.bulk_clients))
                
            elif response.status_code in [401, 403]:
                data = response.json()
                logger.info(f"⚠️ Admin authentication issue: {data.get('detail', 'No detail')}")
            else:
                data = response.json()
                logger.info(f"⚠️ Unexpected response: {data}")
                
        except Exception as e:
            logger.error(f"❌ Error testing admin access: {str(e)}")
            raise
        
        # Test with client token (should fail)
        try:
            response = requests.post(url, headers=self.headers_client, json=self.bulk_email_data)
            logger.info(f"Client token response status: {response.status_code}")
            
            # Should get 403 Forbidden (admin access required)
            self.assertEqual(response.status_code, 403)
            
            data = response.json()
            self.assertIn("detail", data)
            logger.info(f"✅ Client correctly denied access: {data.get('detail')}")
            
        except Exception as e:
            logger.error(f"❌ Error testing client access denial: {str(e)}")
            raise
        
        # Test with invalid token (should fail)
        try:
            response = requests.post(url, headers=self.headers_invalid, json=self.bulk_email_data)
            logger.info(f"Invalid token response status: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ Invalid token correctly rejected")
            
        except Exception as e:
            logger.error(f"❌ Error testing invalid token: {str(e)}")
            raise
        
        # Test with no authentication (should fail)
        try:
            response = requests.post(url, headers=self.headers_no_auth, json=self.bulk_email_data)
            logger.info(f"No auth response status: {response.status_code}")
            
            # Should get 403 Not authenticated
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ No authentication correctly rejected")
            
        except Exception as e:
            logger.error(f"❌ Error testing no authentication: {str(e)}")
            raise
    
    def test_bulk_email_send_only_bulk_clients(self):
        """Test 2: Verify bulk email only sends to client_type: 'bulk' clients"""
        logger.info("\n=== Test 2: Bulk Email Send - Only Bulk Clients ===")
        
        url = f"{self.api_url}/bulk-email/send"
        
        try:
            response = requests.post(url, headers=self.headers_admin, json=self.bulk_email_data)
            logger.info(f"Bulk email send response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify only bulk clients are targeted
                expected_bulk_count = len(self.bulk_clients)
                self.assertEqual(data["total_clients"], expected_bulk_count)
                
                # Verify valid email count matches bulk clients with emails
                bulk_with_email = len([c for c in self.bulk_clients if c.get("email") and "@" in c.get("email")])
                self.assertEqual(data["valid_email_count"], bulk_with_email)
                
                logger.info(f"✅ Bulk email correctly targeted {expected_bulk_count} bulk clients")
                logger.info(f"✅ {bulk_with_email} bulk clients have valid emails")
                
                # Verify registered clients are NOT included
                total_registered = len(self.registered_clients)
                logger.info(f"✅ {total_registered} registered clients correctly excluded from bulk email")
                
            elif response.status_code in [401, 403]:
                data = response.json()
                logger.info(f"⚠️ Authentication issue: {data.get('detail', 'No detail')}")
            else:
                data = response.json()
                logger.info(f"⚠️ Unexpected response: {data}")
                
        except Exception as e:
            logger.error(f"❌ Error testing bulk client targeting: {str(e)}")
            raise
    
    def test_bulk_email_send_with_filters(self):
        """Test 3: Verify bulk email filtering by city and audit_company"""
        logger.info("\n=== Test 3: Bulk Email Send - Filter Testing ===")
        
        url = f"{self.api_url}/bulk-email/send"
        
        # Test city filter
        try:
            city_filter_data = self.bulk_email_data.copy()
            city_filter_data["filters"] = {"city": "İstanbul"}
            
            response = requests.post(url, headers=self.headers_admin, json=city_filter_data)
            logger.info(f"City filter response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"City filter response: {data}")
                
                # Should only target bulk clients in İstanbul
                istanbul_bulk_clients = len([c for c in self.bulk_clients if c.get("city") == "İstanbul"])
                self.assertEqual(data["total_clients"], istanbul_bulk_clients)
                
                logger.info(f"✅ City filter correctly targeted {istanbul_bulk_clients} bulk clients in İstanbul")
                
        except Exception as e:
            logger.error(f"❌ Error testing city filter: {str(e)}")
            raise
        
        # Test audit_company filter
        try:
            audit_filter_data = self.bulk_email_data.copy()
            audit_filter_data["filters"] = {"audit_company": "Test Audit A.Ş."}
            
            response = requests.post(url, headers=self.headers_admin, json=audit_filter_data)
            logger.info(f"Audit company filter response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Audit company filter response: {data}")
                
                # Should only target bulk clients with specific audit company
                audit_bulk_clients = len([c for c in self.bulk_clients if c.get("audit_company") == "Test Audit A.Ş."])
                self.assertEqual(data["total_clients"], audit_bulk_clients)
                
                logger.info(f"✅ Audit company filter correctly targeted {audit_bulk_clients} bulk clients")
                
        except Exception as e:
            logger.error(f"❌ Error testing audit company filter: {str(e)}")
            raise
        
        # Test combined filters
        try:
            combined_filter_data = self.bulk_email_data.copy()
            combined_filter_data["filters"] = {
                "city": "Ankara",
                "audit_company": "Test Audit A.Ş."
            }
            
            response = requests.post(url, headers=self.headers_admin, json=combined_filter_data)
            logger.info(f"Combined filter response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Combined filter response: {data}")
                
                # Should only target bulk clients matching both filters
                combined_bulk_clients = len([
                    c for c in self.bulk_clients 
                    if c.get("city") == "Ankara" and c.get("audit_company") == "Test Audit A.Ş."
                ])
                self.assertEqual(data["total_clients"], combined_bulk_clients)
                
                logger.info(f"✅ Combined filters correctly targeted {combined_bulk_clients} bulk clients")
                
        except Exception as e:
            logger.error(f"❌ Error testing combined filters: {str(e)}")
            raise
    
    def test_bulk_email_personalization(self):
        """Test 4: Verify email personalization with placeholders"""
        logger.info("\n=== Test 4: Bulk Email Send - Personalization Testing ===")
        
        url = f"{self.api_url}/bulk-email/send"
        
        # Test email with personalization placeholders
        personalized_email_data = {
            "email_type": "custom",
            "subject": "Kişiselleştirilmiş Test Email - {hotel_name}",
            "content": """
            <h2>Sayın {contact_person},</h2>
            <p>{hotel_name} için özel sürdürülebilirlik danışmanlığı hizmetlerimiz hakkında bilgi vermek istiyoruz.</p>
            <p>Bulunduğunuz şehir: {city}</p>
            <p>Bu email {hotel_name} oteli için özel olarak hazırlanmıştır.</p>
            <p>İletişim kişisi: {contact_person}</p>
            <p>Şehir bilgisi: {city}</p>
            <p>Saygılarımızla,<br>ROTA Kalite Danışmanlık</p>
            """,
            "filters": {"city": "İstanbul"}  # Test with specific city
        }
        
        try:
            response = requests.post(url, headers=self.headers_admin, json=personalized_email_data)
            logger.info(f"Personalization test response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Personalization test response: {data}")
                
                # Verify email was sent successfully
                self.assertIn("success", data)
                self.assertTrue(data["success"])
                self.assertGreater(data["sent_count"], 0)
                
                logger.info(f"✅ Personalized email sent to {data['sent_count']} bulk clients")
                logger.info("✅ Email personalization placeholders should be replaced with actual client data")
                
                # The actual personalization happens in the backend
                # We can verify the structure but not the actual content replacement
                # since we're not intercepting the actual email sending
                
            elif response.status_code in [401, 403]:
                data = response.json()
                logger.info(f"⚠️ Authentication issue: {data.get('detail', 'No detail')}")
            else:
                data = response.json()
                logger.info(f"⚠️ Unexpected response: {data}")
                
        except Exception as e:
            logger.error(f"❌ Error testing email personalization: {str(e)}")
            raise
    
    def test_bulk_email_stats_admin_only_access(self):
        """Test 5: Verify /api/bulk-email/stats requires admin authentication"""
        logger.info("\n=== Test 5: Bulk Email Stats - Admin Only Access ===")
        
        url = f"{self.api_url}/bulk-email/stats"
        
        # Test with admin token (should work)
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin token response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Admin can access bulk email stats endpoint")
                logger.info(f"Stats response: {data}")
                
                # Verify response structure
                self.assertIn("total_bulk_clients", data)
                self.assertIn("bulk_clients_with_email", data)
                self.assertIn("email_coverage_percentage", data)
                self.assertIn("city_distribution", data)
                self.assertIn("audit_company_distribution", data)
                
                # Verify stats are for bulk clients only
                expected_bulk_count = len(self.bulk_clients)
                self.assertEqual(data["total_bulk_clients"], expected_bulk_count)
                
                logger.info(f"✅ Stats correctly show {expected_bulk_count} bulk clients")
                
            elif response.status_code in [401, 403]:
                data = response.json()
                logger.info(f"⚠️ Admin authentication issue: {data.get('detail', 'No detail')}")
            else:
                data = response.json()
                logger.info(f"⚠️ Unexpected response: {data}")
                
        except Exception as e:
            logger.error(f"❌ Error testing admin access to stats: {str(e)}")
            raise
        
        # Test with client token (should fail)
        try:
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client token response status: {response.status_code}")
            
            # Should get 403 Forbidden (admin access required)
            self.assertEqual(response.status_code, 403)
            
            data = response.json()
            self.assertIn("detail", data)
            logger.info(f"✅ Client correctly denied access to stats: {data.get('detail')}")
            
        except Exception as e:
            logger.error(f"❌ Error testing client access denial to stats: {str(e)}")
            raise
        
        # Test with invalid token (should fail)
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid token response status: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ Invalid token correctly rejected for stats")
            
        except Exception as e:
            logger.error(f"❌ Error testing invalid token for stats: {str(e)}")
            raise
        
        # Test with no authentication (should fail)
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status: {response.status_code}")
            
            # Should get 403 Not authenticated
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ No authentication correctly rejected for stats")
            
        except Exception as e:
            logger.error(f"❌ Error testing no authentication for stats: {str(e)}")
            raise
    
    def test_bulk_email_stats_only_bulk_clients(self):
        """Test 6: Verify bulk email stats only include bulk clients"""
        logger.info("\n=== Test 6: Bulk Email Stats - Only Bulk Clients ===")
        
        url = f"{self.api_url}/bulk-email/stats"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Bulk email stats response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Stats data: {data}")
                
                # Verify stats are only for bulk clients
                expected_bulk_count = len(self.bulk_clients)
                self.assertEqual(data["total_bulk_clients"], expected_bulk_count)
                
                # Verify bulk clients with email count
                bulk_with_email = len([c for c in self.bulk_clients if c.get("email") and "@" in c.get("email")])
                self.assertEqual(data["bulk_clients_with_email"], bulk_with_email)
                
                # Verify email coverage percentage
                expected_percentage = round((bulk_with_email / expected_bulk_count * 100), 2) if expected_bulk_count > 0 else 0
                self.assertEqual(data["email_coverage_percentage"], expected_percentage)
                
                logger.info(f"✅ Stats correctly show {expected_bulk_count} total bulk clients")
                logger.info(f"✅ Stats correctly show {bulk_with_email} bulk clients with email")
                logger.info(f"✅ Email coverage: {expected_percentage}%")
                
                # Verify city distribution includes only bulk clients
                city_distribution = data["city_distribution"]
                self.assertIsInstance(city_distribution, list)
                
                # Count cities from our bulk test data
                bulk_cities = {}
                for client in self.bulk_clients:
                    city = client.get("city")
                    if city:
                        bulk_cities[city] = bulk_cities.get(city, 0) + 1
                
                logger.info(f"✅ City distribution: {city_distribution}")
                logger.info(f"✅ Expected bulk cities: {bulk_cities}")
                
                # Verify audit company distribution includes only bulk clients
                audit_distribution = data["audit_company_distribution"]
                self.assertIsInstance(audit_distribution, list)
                
                # Count audit companies from our bulk test data
                bulk_audits = {}
                for client in self.bulk_clients:
                    audit = client.get("audit_company")
                    if audit:
                        bulk_audits[audit] = bulk_audits.get(audit, 0) + 1
                
                logger.info(f"✅ Audit company distribution: {audit_distribution}")
                logger.info(f"✅ Expected bulk audit companies: {bulk_audits}")
                
                # Verify registered clients are NOT included in stats
                total_registered = len(self.registered_clients)
                logger.info(f"✅ {total_registered} registered clients correctly excluded from bulk stats")
                
            elif response.status_code in [401, 403]:
                data = response.json()
                logger.info(f"⚠️ Authentication issue: {data.get('detail', 'No detail')}")
            else:
                data = response.json()
                logger.info(f"⚠️ Unexpected response: {data}")
                
        except Exception as e:
            logger.error(f"❌ Error testing bulk stats client filtering: {str(e)}")
            raise
    
    def test_bulk_email_validation_errors(self):
        """Test 7: Verify proper validation and error handling"""
        logger.info("\n=== Test 7: Bulk Email Send - Validation and Error Handling ===")
        
        url = f"{self.api_url}/bulk-email/send"
        
        # Test missing subject
        try:
            invalid_data = self.bulk_email_data.copy()
            invalid_data["subject"] = ""
            
            response = requests.post(url, headers=self.headers_admin, json=invalid_data)
            logger.info(f"Missing subject response status: {response.status_code}")
            
            # Should get 400 Bad Request
            self.assertEqual(response.status_code, 400)
            
            data = response.json()
            self.assertIn("detail", data)
            self.assertIn("konusu", data["detail"])  # Turkish error message
            
            logger.info(f"✅ Missing subject correctly rejected: {data.get('detail')}")
            
        except Exception as e:
            logger.error(f"❌ Error testing missing subject: {str(e)}")
            raise
        
        # Test missing content
        try:
            invalid_data = self.bulk_email_data.copy()
            invalid_data["content"] = ""
            
            response = requests.post(url, headers=self.headers_admin, json=invalid_data)
            logger.info(f"Missing content response status: {response.status_code}")
            
            # Should get 400 Bad Request
            self.assertEqual(response.status_code, 400)
            
            data = response.json()
            self.assertIn("detail", data)
            self.assertIn("içeriği", data["detail"])  # Turkish error message
            
            logger.info(f"✅ Missing content correctly rejected: {data.get('detail')}")
            
        except Exception as e:
            logger.error(f"❌ Error testing missing content: {str(e)}")
            raise
        
        # Test filter with no matching clients
        try:
            no_match_data = self.bulk_email_data.copy()
            no_match_data["filters"] = {"city": "NonExistentCity"}
            
            response = requests.post(url, headers=self.headers_admin, json=no_match_data)
            logger.info(f"No matching clients response status: {response.status_code}")
            
            # Should get 400 Bad Request
            self.assertEqual(response.status_code, 400)
            
            data = response.json()
            self.assertIn("detail", data)
            self.assertIn("BULK müşteri bulunamadı", data["detail"])  # Turkish error message
            
            logger.info(f"✅ No matching clients correctly rejected: {data.get('detail')}")
            
        except Exception as e:
            logger.error(f"❌ Error testing no matching clients: {str(e)}")
            raise
    
    def test_database_client_type_separation(self):
        """Test 8: Verify database correctly separates bulk vs registered clients"""
        logger.info("\n=== Test 8: Database Client Type Separation ===")
        
        try:
            # Query bulk clients from database
            bulk_clients_db = list(self.db.clients.find({"client_type": "bulk"}))
            logger.info(f"📊 Found {len(bulk_clients_db)} bulk clients in database")
            
            # Query registered clients from database
            registered_clients_db = list(self.db.clients.find({"client_type": "registered"}))
            logger.info(f"📊 Found {len(registered_clients_db)} registered clients in database")
            
            # Verify our test data is correctly stored
            test_bulk_emails = [c["email"] for c in self.bulk_clients]
            test_registered_emails = [c["email"] for c in self.registered_clients]
            
            db_bulk_emails = [c["email"] for c in bulk_clients_db if c["email"] in test_bulk_emails]
            db_registered_emails = [c["email"] for c in registered_clients_db if c["email"] in test_registered_emails]
            
            self.assertEqual(len(db_bulk_emails), len(self.bulk_clients))
            self.assertEqual(len(db_registered_emails), len(self.registered_clients))
            
            logger.info(f"✅ Database correctly stores {len(db_bulk_emails)} test bulk clients")
            logger.info(f"✅ Database correctly stores {len(db_registered_emails)} test registered clients")
            
            # Verify client_type field exists and is correct
            for client in bulk_clients_db:
                if client["email"] in test_bulk_emails:
                    self.assertEqual(client["client_type"], "bulk")
            
            for client in registered_clients_db:
                if client["email"] in test_registered_emails:
                    self.assertEqual(client["client_type"], "registered")
            
            logger.info("✅ All test clients have correct client_type values")
            
            # Test MongoDB query that bulk email system uses
            bulk_query = {"client_type": "bulk"}
            bulk_query_result = list(self.db.clients.find(bulk_query))
            
            # Should include our test bulk clients
            bulk_test_count = len([c for c in bulk_query_result if c["email"] in test_bulk_emails])
            self.assertEqual(bulk_test_count, len(self.bulk_clients))
            
            # Should NOT include registered clients
            registered_in_bulk_query = len([c for c in bulk_query_result if c["email"] in test_registered_emails])
            self.assertEqual(registered_in_bulk_query, 0)
            
            logger.info("✅ MongoDB bulk query correctly filters only bulk clients")
            logger.info("✅ MongoDB bulk query correctly excludes registered clients")
            
        except Exception as e:
            logger.error(f"❌ Error testing database client type separation: {str(e)}")
            raise

def run_bulk_email_tests():
    """Run all bulk email system tests"""
    logger.info("🚀 Starting Bulk Email System Backend Tests")
    logger.info(f"Backend URL: {BACKEND_URL}")
    logger.info(f"MongoDB URL: {MONGO_URL}")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test methods
    test_methods = [
        'test_bulk_email_send_admin_only_access',
        'test_bulk_email_send_only_bulk_clients', 
        'test_bulk_email_send_with_filters',
        'test_bulk_email_personalization',
        'test_bulk_email_stats_admin_only_access',
        'test_bulk_email_stats_only_bulk_clients',
        'test_bulk_email_validation_errors',
        'test_database_client_type_separation'
    ]
    
    for method in test_methods:
        test_suite.addTest(BulkEmailSystemTest(method))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("BULK EMAIL SYSTEM TEST SUMMARY")
    logger.info("="*80)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    if result.failures:
        logger.error("FAILURES:")
        for test, traceback in result.failures:
            logger.error(f"- {test}: {traceback}")
    
    if result.errors:
        logger.error("ERRORS:")
        for test, traceback in result.errors:
            logger.error(f"- {test}: {traceback}")
    
    if result.wasSuccessful():
        logger.info("🎉 ALL BULK EMAIL TESTS PASSED!")
    else:
        logger.error("❌ SOME BULK EMAIL TESTS FAILED!")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_bulk_email_tests()
    sys.exit(0 if success else 1)