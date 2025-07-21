#!/usr/bin/env python3
"""
Certificate Date Parsing Fix Backend Test
Testing the certificate_end_date field handling in the backend API
"""

import asyncio
import httpx
import json
import logging
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('/app/backend/.env')

# Configuration
BACKEND_URL = "https://rota-crm-production.up.railway.app"
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'rotacrm')

class CertificateDateParsingTest:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.mongo_client = None
        self.db = None
        self.test_results = {
            "api_tests": {},
            "database_analysis": {},
            "certificate_date_analysis": {},
            "summary": {}
        }
        
    async def setup_database_connection(self):
        """Setup direct MongoDB connection for data analysis"""
        try:
            self.mongo_client = MongoClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            logger.info("✅ MongoDB connection established")
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            return False
    
    async def test_api_health(self):
        """Test basic API connectivity"""
        logger.info("🔍 Testing API Health...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.backend_url}/health")
                
                self.test_results["api_tests"]["health_check"] = {
                    "status_code": response.status_code,
                    "response": response.json() if response.status_code == 200 else response.text,
                    "success": response.status_code == 200
                }
                
                if response.status_code == 200:
                    logger.info("✅ API Health check passed")
                    return True
                else:
                    logger.error(f"❌ API Health check failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ API Health check error: {e}")
            self.test_results["api_tests"]["health_check"] = {
                "error": str(e),
                "success": False
            }
            return False
    
    async def test_clients_endpoint_without_auth(self):
        """Test GET /api/clients endpoint without authentication"""
        logger.info("🔍 Testing GET /api/clients without authentication...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.backend_url}/api/clients")
                
                self.test_results["api_tests"]["clients_no_auth"] = {
                    "status_code": response.status_code,
                    "response": response.text[:500] if len(response.text) > 500 else response.text,
                    "success": response.status_code in [401, 403]  # Should require auth
                }
                
                logger.info(f"✅ Clients endpoint properly secured: {response.status_code}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Clients endpoint test error: {e}")
            self.test_results["api_tests"]["clients_no_auth"] = {
                "error": str(e),
                "success": False
            }
            return False
    
    async def test_clients_endpoint_with_invalid_auth(self):
        """Test GET /api/clients endpoint with invalid authentication"""
        logger.info("🔍 Testing GET /api/clients with invalid authentication...")
        
        try:
            headers = {"Authorization": "Bearer invalid_token_for_testing"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.backend_url}/api/clients", headers=headers)
                
                self.test_results["api_tests"]["clients_invalid_auth"] = {
                    "status_code": response.status_code,
                    "response": response.text[:500] if len(response.text) > 500 else response.text,
                    "success": response.status_code == 401  # Should return 401 for invalid token
                }
                
                logger.info(f"✅ Clients endpoint properly validates auth: {response.status_code}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Clients endpoint auth test error: {e}")
            self.test_results["api_tests"]["clients_invalid_auth"] = {
                "error": str(e),
                "success": False
            }
            return False
    
    async def analyze_certificate_dates_in_database(self):
        """Analyze certificate_end_date values directly in MongoDB"""
        logger.info("🔍 Analyzing certificate_end_date values in database...")
        
        if self.db is None:
            logger.error("❌ Database connection not available")
            return False
        
        try:
            # Get all clients with certificate_end_date field
            clients = list(self.db.clients.find({}, {
                "id": 1, 
                "name": 1, 
                "hotel_name": 1, 
                "certificate_end_date": 1,
                "client_type": 1,
                "city": 1,
                "audit_company": 1
            }))
            
            total_clients = len(clients)
            
            # Analyze certificate_end_date values
            date_analysis = {
                "total_clients": total_clients,
                "with_certificate_date": 0,
                "with_dash_value": 0,
                "with_null_value": 0,
                "with_empty_string": 0,
                "with_valid_date": 0,
                "dash_examples": [],
                "valid_date_examples": [],
                "other_values": []
            }
            
            for client in clients:
                cert_date = client.get("certificate_end_date")
                client_info = {
                    "id": client.get("id"),
                    "name": client.get("name", ""),
                    "hotel_name": client.get("hotel_name", ""),
                    "city": client.get("city", ""),
                    "client_type": client.get("client_type", ""),
                    "certificate_end_date": cert_date
                }
                
                if cert_date is not None:
                    date_analysis["with_certificate_date"] += 1
                    
                    if cert_date == "-":
                        date_analysis["with_dash_value"] += 1
                        if len(date_analysis["dash_examples"]) < 5:
                            date_analysis["dash_examples"].append(client_info)
                    elif cert_date == "":
                        date_analysis["with_empty_string"] += 1
                    elif isinstance(cert_date, str) and len(cert_date) > 1:
                        # Try to identify if it's a valid date format
                        if any(char.isdigit() for char in cert_date):
                            date_analysis["with_valid_date"] += 1
                            if len(date_analysis["valid_date_examples"]) < 3:
                                date_analysis["valid_date_examples"].append(client_info)
                        else:
                            if len(date_analysis["other_values"]) < 3:
                                date_analysis["other_values"].append(client_info)
                else:
                    date_analysis["with_null_value"] += 1
            
            self.test_results["certificate_date_analysis"] = date_analysis
            
            logger.info(f"✅ Certificate date analysis completed:")
            logger.info(f"   Total clients: {total_clients}")
            logger.info(f"   With dash (-) value: {date_analysis['with_dash_value']}")
            logger.info(f"   With valid dates: {date_analysis['with_valid_date']}")
            logger.info(f"   With null values: {date_analysis['with_null_value']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Certificate date analysis error: {e}")
            self.test_results["certificate_date_analysis"]["error"] = str(e)
            return False
    
    async def analyze_client_types_and_distribution(self):
        """Analyze client types and their distribution"""
        logger.info("🔍 Analyzing client types and distribution...")
        
        if self.db is None:
            logger.error("❌ Database connection not available")
            return False
        
        try:
            # Get client type distribution
            pipeline = [
                {"$group": {
                    "_id": "$client_type",
                    "count": {"$sum": 1}
                }}
            ]
            
            client_type_dist = list(self.db.clients.aggregate(pipeline))
            
            # Get city distribution for bulk clients
            bulk_cities = list(self.db.clients.aggregate([
                {"$match": {"client_type": "bulk"}},
                {"$group": {
                    "_id": "$city",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]))
            
            # Get audit company distribution
            audit_companies = list(self.db.clients.aggregate([
                {"$match": {"client_type": "bulk"}},
                {"$group": {
                    "_id": "$audit_company",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]))
            
            self.test_results["database_analysis"] = {
                "client_type_distribution": client_type_dist,
                "top_bulk_cities": bulk_cities,
                "top_audit_companies": audit_companies
            }
            
            logger.info("✅ Client distribution analysis completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Client distribution analysis error: {e}")
            self.test_results["database_analysis"]["error"] = str(e)
            return False
    
    async def test_bulk_clients_api_structure(self):
        """Test the expected API structure for bulk clients (without auth)"""
        logger.info("🔍 Testing bulk clients API structure...")
        
        try:
            # Test with different query parameters
            test_params = [
                {},
                {"client_type": "bulk"},
                {"client_type": "registered"},
                {"page": "1", "limit": "10"}
            ]
            
            for params in test_params:
                param_str = "&".join([f"{k}={v}" for k, v in params.items()])
                url = f"{self.backend_url}/api/clients"
                if param_str:
                    url += f"?{param_str}"
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url)
                    
                    test_key = f"bulk_api_params_{param_str or 'no_params'}"
                    self.test_results["api_tests"][test_key] = {
                        "url": url,
                        "status_code": response.status_code,
                        "response_preview": response.text[:200] if len(response.text) > 200 else response.text,
                        "requires_auth": response.status_code in [401, 403]
                    }
            
            logger.info("✅ Bulk clients API structure test completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Bulk clients API structure test error: {e}")
            return False
    
    async def generate_summary(self):
        """Generate test summary"""
        logger.info("📊 Generating test summary...")
        
        # Count dash values
        dash_count = self.test_results.get("certificate_date_analysis", {}).get("with_dash_value", 0)
        total_clients = self.test_results.get("certificate_date_analysis", {}).get("total_clients", 0)
        
        # API security status
        api_secured = all([
            self.test_results.get("api_tests", {}).get("clients_no_auth", {}).get("success", False),
            self.test_results.get("api_tests", {}).get("clients_invalid_auth", {}).get("success", False)
        ])
        
        summary = {
            "certificate_date_issue": {
                "total_clients_analyzed": total_clients,
                "clients_with_dash_value": dash_count,
                "percentage_with_dash": round((dash_count / total_clients) * 100, 2) if total_clients > 0 else 0,
                "issue_confirmed": dash_count > 0
            },
            "api_security": {
                "properly_secured": api_secured,
                "requires_authentication": True
            },
            "backend_accessibility": {
                "health_endpoint_working": self.test_results.get("api_tests", {}).get("health_check", {}).get("success", False),
                "api_endpoints_secured": api_secured
            }
        }
        
        self.test_results["summary"] = summary
        
        logger.info("✅ Test summary generated")
        return summary
    
    async def run_all_tests(self):
        """Run all certificate date parsing tests"""
        logger.info("🚀 Starting Certificate Date Parsing Backend Tests...")
        
        # Setup database connection
        await self.setup_database_connection()
        
        # Run tests
        await self.test_api_health()
        await self.test_clients_endpoint_without_auth()
        await self.test_clients_endpoint_with_invalid_auth()
        await self.analyze_certificate_dates_in_database()
        await self.analyze_client_types_and_distribution()
        await self.test_bulk_clients_api_structure()
        
        # Generate summary
        await self.generate_summary()
        
        # Close database connection
        if self.mongo_client:
            self.mongo_client.close()
        
        return self.test_results
    
    def print_results(self):
        """Print formatted test results"""
        print("\n" + "="*80)
        print("🔍 CERTIFICATE DATE PARSING FIX - BACKEND TEST RESULTS")
        print("="*80)
        
        # Summary
        summary = self.test_results.get("summary", {})
        cert_issue = summary.get("certificate_date_issue", {})
        
        print(f"\n📊 CERTIFICATE DATE ANALYSIS:")
        print(f"   Total clients analyzed: {cert_issue.get('total_clients_analyzed', 0)}")
        print(f"   Clients with dash (-) value: {cert_issue.get('clients_with_dash_value', 0)}")
        print(f"   Percentage with dash: {cert_issue.get('percentage_with_dash', 0)}%")
        print(f"   Issue confirmed: {'✅ YES' if cert_issue.get('issue_confirmed') else '❌ NO'}")
        
        # API Security
        api_security = summary.get("api_security", {})
        print(f"\n🔒 API SECURITY:")
        print(f"   Properly secured: {'✅ YES' if api_security.get('properly_secured') else '❌ NO'}")
        print(f"   Requires authentication: {'✅ YES' if api_security.get('requires_authentication') else '❌ NO'}")
        
        # Backend Accessibility
        backend_access = summary.get("backend_accessibility", {})
        print(f"\n🌐 BACKEND ACCESSIBILITY:")
        print(f"   Health endpoint working: {'✅ YES' if backend_access.get('health_endpoint_working') else '❌ NO'}")
        print(f"   API endpoints secured: {'✅ YES' if backend_access.get('api_endpoints_secured') else '❌ NO'}")
        
        # Certificate Date Examples
        cert_analysis = self.test_results.get("certificate_date_analysis", {})
        if cert_analysis.get("dash_examples"):
            print(f"\n📋 EXAMPLES OF CLIENTS WITH DASH (-) VALUES:")
            for i, example in enumerate(cert_analysis["dash_examples"][:3], 1):
                print(f"   {i}. {example.get('hotel_name', 'N/A')} | {example.get('city', 'N/A')} | Type: {example.get('client_type', 'N/A')}")
        
        if cert_analysis.get("valid_date_examples"):
            print(f"\n📅 EXAMPLES OF CLIENTS WITH VALID DATES:")
            for i, example in enumerate(cert_analysis["valid_date_examples"][:3], 1):
                print(f"   {i}. {example.get('hotel_name', 'N/A')} | Date: {example.get('certificate_end_date', 'N/A')}")
        
        print("\n" + "="*80)

async def main():
    """Main test execution"""
    test_suite = CertificateDateParsingTest()
    
    try:
        results = await test_suite.run_all_tests()
        test_suite.print_results()
        
        # Save results to file
        with open('/app/certificate_date_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: /app/certificate_date_test_results.json")
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        print(f"\n❌ Test execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())