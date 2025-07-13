#!/usr/bin/env python3
"""
Consultant Client Assignment Investigation Test
==============================================

This test investigates the specific issues mentioned in the review request:
1. Which clients are assigned to consultants?
2. Are both DENİZ OTEL and BELO assigned to same consultant?
3. Backend stats logic for consultant users
4. Backend clients logic for consultant users
5. Database client assignment verification

Context: Frontend shows 1 client (DENİZ OTEL) but database has 2 clients,
BELO client is missing from consultant dashboard.
"""

import logging
import requests
import json
from pymongo import MongoClient
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"
MONGO_URL = "mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster"
DB_NAME = "rotacrm"

# Test tokens (these are sample tokens - in real scenario they would be valid JWT tokens)
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
CONSULTANT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ09OU1VMVEFOVF8wMDEiLCJlbWFpbCI6ImNvbnN1bHRhbnRAZXhhbXBsZS5jb20iLCJuYW1lIjoiQ29uc3VsdGFudCBVc2VyIn0.signature"

class ConsultantAssignmentInvestigation:
    """Investigation class for consultant client assignments"""
    
    def __init__(self):
        self.api_url = RAILWAY_API_URL
        self.mongo_url = MONGO_URL
        self.db_name = DB_NAME
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_no_auth = {}
        
        # Investigation results
        self.investigation_results = {
            "database_clients": [],
            "database_consultants": [],
            "database_users": [],
            "api_clients_admin": None,
            "api_clients_consultant": None,
            "api_stats_admin": None,
            "api_stats_consultant": None,
            "findings": []
        }
    
    def log_finding(self, finding):
        """Log and store a finding"""
        logger.info(f"🔍 FINDING: {finding}")
        self.investigation_results["findings"].append(finding)
    
    def investigate_database_assignments(self):
        """Investigate client assignments directly in the database"""
        logger.info("\n" + "="*80)
        logger.info("1. DATABASE CLIENT ASSIGNMENT INVESTIGATION")
        logger.info("="*80)
        
        try:
            # Connect to MongoDB
            mongo_client = MongoClient(self.mongo_url)
            db = mongo_client[self.db_name]
            
            # Get all clients
            clients = list(db.clients.find({}))
            logger.info(f"📊 Found {len(clients)} clients in database")
            
            # Get all consultants
            consultants = list(db.consultants.find({}))
            logger.info(f"📊 Found {len(consultants)} consultants in database")
            
            # Get all users
            users = list(db.users.find({}))
            logger.info(f"📊 Found {len(users)} users in database")
            
            # Store results
            self.investigation_results["database_clients"] = clients
            self.investigation_results["database_consultants"] = consultants
            self.investigation_results["database_users"] = users
            
            # Analyze client assignments
            logger.info("\n📋 CLIENT ASSIGNMENT ANALYSIS:")
            deniz_otel_found = False
            belo_found = False
            
            for i, client in enumerate(clients):
                client_name = client.get("name", "Unknown")
                hotel_name = client.get("hotel_name", "Unknown")
                consultant_id = client.get("consultant_id", None)
                
                logger.info(f"  Client {i+1}: {client_name} / {hotel_name}")
                logger.info(f"    ID: {client.get('id', 'No ID')}")
                logger.info(f"    Consultant ID: {consultant_id}")
                logger.info(f"    Current Stage: {client.get('current_stage', 'Unknown')}")
                
                # Check for specific clients mentioned in the review
                if "DENİZ" in client_name.upper() or "DENIZ" in client_name.upper():
                    deniz_otel_found = True
                    self.log_finding(f"DENİZ OTEL found - Name: {client_name}, Consultant ID: {consultant_id}")
                
                if "BELO" in client_name.upper():
                    belo_found = True
                    self.log_finding(f"BELO found - Name: {client_name}, Consultant ID: {consultant_id}")
            
            # Check if both clients are assigned to the same consultant
            if deniz_otel_found and belo_found:
                deniz_consultant = None
                belo_consultant = None
                
                for client in clients:
                    if "DENİZ" in client.get("name", "").upper() or "DENIZ" in client.get("name", "").upper():
                        deniz_consultant = client.get("consultant_id")
                    if "BELO" in client.get("name", "").upper():
                        belo_consultant = client.get("consultant_id")
                
                if deniz_consultant and belo_consultant:
                    if deniz_consultant == belo_consultant:
                        self.log_finding(f"DENİZ OTEL and BELO are assigned to SAME consultant: {deniz_consultant}")
                    else:
                        self.log_finding(f"DENİZ OTEL and BELO are assigned to DIFFERENT consultants: {deniz_consultant} vs {belo_consultant}")
                else:
                    self.log_finding(f"One or both clients missing consultant assignment - DENİZ: {deniz_consultant}, BELO: {belo_consultant}")
            
            # Analyze consultant assignments
            logger.info("\n📋 CONSULTANT ANALYSIS:")
            for i, consultant in enumerate(consultants):
                consultant_id = consultant.get("id")
                company_name = consultant.get("company_name", "Unknown")
                
                # Count clients assigned to this consultant
                assigned_clients = [c for c in clients if c.get("consultant_id") == consultant_id]
                
                logger.info(f"  Consultant {i+1}: {company_name}")
                logger.info(f"    ID: {consultant_id}")
                logger.info(f"    Assigned Clients: {len(assigned_clients)}")
                
                for client in assigned_clients:
                    logger.info(f"      - {client.get('name', 'Unknown')} / {client.get('hotel_name', 'Unknown')}")
            
            # Analyze user roles
            logger.info("\n📋 USER ROLE ANALYSIS:")
            consultant_users = [u for u in users if u.get("role") == "consultant"]
            client_users = [u for u in users if u.get("role") == "client"]
            admin_users = [u for u in users if u.get("role") == "admin"]
            
            logger.info(f"  Admin users: {len(admin_users)}")
            logger.info(f"  Consultant users: {len(consultant_users)}")
            logger.info(f"  Client users: {len(client_users)}")
            
            for user in consultant_users:
                logger.info(f"    Consultant User: {user.get('name', 'Unknown')} ({user.get('email', 'Unknown')})")
                logger.info(f"      Consultant ID: {user.get('consultant_id', 'None')}")
            
            mongo_client.close()
            
        except Exception as e:
            logger.error(f"❌ Error investigating database: {str(e)}")
            self.log_finding(f"Database investigation failed: {str(e)}")
    
    def test_api_clients_endpoint(self):
        """Test GET /api/clients endpoint with different user types"""
        logger.info("\n" + "="*80)
        logger.info("2. API CLIENTS ENDPOINT INVESTIGATION")
        logger.info("="*80)
        
        url = f"{self.api_url}/clients"
        
        # Test with admin user
        logger.info("\n🔧 Testing /api/clients with ADMIN user:")
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"  Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"  Response: {len(data)} clients returned")
                
                self.investigation_results["api_clients_admin"] = data
                
                for i, client in enumerate(data):
                    logger.info(f"    Client {i+1}: {client.get('name', 'Unknown')} / {client.get('hotel_name', 'Unknown')}")
                    logger.info(f"      Consultant ID: {client.get('consultant_id', 'None')}")
                
                self.log_finding(f"Admin can see {len(data)} clients via API")
                
            elif response.status_code == 401:
                logger.info(f"  401 Unauthorized - Token validation working")
                self.log_finding("Admin API access requires valid authentication")
            else:
                logger.info(f"  Unexpected response: {response.text}")
                self.log_finding(f"Admin API clients endpoint returned {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing admin API clients: {str(e)}")
            self.log_finding(f"Admin API clients test failed: {str(e)}")
        
        # Test with consultant user
        logger.info("\n🔧 Testing /api/clients with CONSULTANT user:")
        try:
            response = requests.get(url, headers=self.headers_consultant)
            logger.info(f"  Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"  Response: {len(data)} clients returned")
                
                self.investigation_results["api_clients_consultant"] = data
                
                for i, client in enumerate(data):
                    logger.info(f"    Client {i+1}: {client.get('name', 'Unknown')} / {client.get('hotel_name', 'Unknown')}")
                    logger.info(f"      Consultant ID: {client.get('consultant_id', 'None')}")
                
                self.log_finding(f"Consultant can see {len(data)} clients via API")
                
                # Check if consultant sees only assigned clients
                if len(data) == 1:
                    self.log_finding("Consultant sees only 1 client - filtering appears to be working")
                elif len(data) > 1:
                    self.log_finding(f"Consultant sees {len(data)} clients - may see all clients or multiple assigned")
                else:
                    self.log_finding("Consultant sees 0 clients - possible assignment issue")
                
            elif response.status_code == 401:
                logger.info(f"  401 Unauthorized - Token validation working")
                self.log_finding("Consultant API access requires valid authentication")
            elif response.status_code == 403:
                logger.info(f"  403 Forbidden - Access denied")
                self.log_finding("Consultant API access denied - possible role/assignment issue")
            else:
                logger.info(f"  Unexpected response: {response.text}")
                self.log_finding(f"Consultant API clients endpoint returned {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing consultant API clients: {str(e)}")
            self.log_finding(f"Consultant API clients test failed: {str(e)}")
        
        # Test with no authentication
        logger.info("\n🔧 Testing /api/clients with NO authentication:")
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"  Status Code: {response.status_code}")
            
            if response.status_code == 403:
                logger.info(f"  403 Forbidden - Authentication properly enforced")
                self.log_finding("API clients endpoint properly requires authentication")
            else:
                logger.info(f"  Unexpected response: {response.text}")
                self.log_finding(f"API clients endpoint without auth returned {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing no auth API clients: {str(e)}")
    
    def test_api_stats_endpoint(self):
        """Test GET /api/stats endpoint with different user types"""
        logger.info("\n" + "="*80)
        logger.info("3. API STATS ENDPOINT INVESTIGATION")
        logger.info("="*80)
        
        url = f"{self.api_url}/stats"
        
        # Test with admin user
        logger.info("\n🔧 Testing /api/stats with ADMIN user:")
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"  Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"  Response: {json.dumps(data, indent=2)}")
                
                self.investigation_results["api_stats_admin"] = data
                
                # Analyze stats structure
                total_clients = data.get("total_clients", 0)
                total_documents = data.get("total_documents", 0)
                total_trainings = data.get("total_trainings", 0)
                
                logger.info(f"  Admin Stats - Clients: {total_clients}, Documents: {total_documents}, Trainings: {total_trainings}")
                self.log_finding(f"Admin stats show {total_clients} clients, {total_documents} documents, {total_trainings} trainings")
                
            elif response.status_code == 401:
                logger.info(f"  401 Unauthorized - Token validation working")
                self.log_finding("Admin stats API access requires valid authentication")
            else:
                logger.info(f"  Unexpected response: {response.text}")
                self.log_finding(f"Admin stats API endpoint returned {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing admin API stats: {str(e)}")
            self.log_finding(f"Admin API stats test failed: {str(e)}")
        
        # Test with consultant user
        logger.info("\n🔧 Testing /api/stats with CONSULTANT user:")
        try:
            response = requests.get(url, headers=self.headers_consultant)
            logger.info(f"  Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"  Response: {json.dumps(data, indent=2)}")
                
                self.investigation_results["api_stats_consultant"] = data
                
                # Analyze stats structure
                total_clients = data.get("total_clients", 0)
                total_documents = data.get("total_documents", 0)
                total_trainings = data.get("total_trainings", 0)
                
                logger.info(f"  Consultant Stats - Clients: {total_clients}, Documents: {total_documents}, Trainings: {total_trainings}")
                self.log_finding(f"Consultant stats show {total_clients} clients, {total_documents} documents, {total_trainings} trainings")
                
                # Compare with admin stats if available
                admin_stats = self.investigation_results.get("api_stats_admin")
                if admin_stats:
                    admin_clients = admin_stats.get("total_clients", 0)
                    if total_clients == admin_clients:
                        self.log_finding("Consultant sees SAME client count as admin - no filtering applied")
                    elif total_clients < admin_clients:
                        self.log_finding(f"Consultant sees FEWER clients ({total_clients}) than admin ({admin_clients}) - filtering working")
                    else:
                        self.log_finding(f"Consultant sees MORE clients ({total_clients}) than admin ({admin_clients}) - unexpected")
                
            elif response.status_code == 401:
                logger.info(f"  401 Unauthorized - Token validation working")
                self.log_finding("Consultant stats API access requires valid authentication")
            elif response.status_code == 403:
                logger.info(f"  403 Forbidden - Access denied")
                self.log_finding("Consultant stats API access denied - possible role/assignment issue")
            else:
                logger.info(f"  Unexpected response: {response.text}")
                self.log_finding(f"Consultant stats API endpoint returned {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing consultant API stats: {str(e)}")
            self.log_finding(f"Consultant API stats test failed: {str(e)}")
    
    def analyze_filtering_logic(self):
        """Analyze the filtering logic based on collected data"""
        logger.info("\n" + "="*80)
        logger.info("4. FILTERING LOGIC ANALYSIS")
        logger.info("="*80)
        
        # Compare database vs API results
        db_clients = self.investigation_results.get("database_clients", [])
        api_clients_admin = self.investigation_results.get("api_clients_admin", [])
        api_clients_consultant = self.investigation_results.get("api_clients_consultant", [])
        
        logger.info(f"\n📊 CLIENT COUNT COMPARISON:")
        logger.info(f"  Database: {len(db_clients)} clients")
        logger.info(f"  API Admin: {len(api_clients_admin) if api_clients_admin else 'N/A'} clients")
        logger.info(f"  API Consultant: {len(api_clients_consultant) if api_clients_consultant else 'N/A'} clients")
        
        # Analyze specific clients
        if db_clients:
            deniz_in_db = any("DENİZ" in c.get("name", "").upper() or "DENIZ" in c.get("name", "").upper() for c in db_clients)
            belo_in_db = any("BELO" in c.get("name", "").upper() for c in db_clients)
            
            logger.info(f"\n📋 SPECIFIC CLIENT PRESENCE:")
            logger.info(f"  DENİZ OTEL in database: {deniz_in_db}")
            logger.info(f"  BELO in database: {belo_in_db}")
            
            if api_clients_consultant:
                deniz_in_api = any("DENİZ" in c.get("name", "").upper() or "DENIZ" in c.get("name", "").upper() for c in api_clients_consultant)
                belo_in_api = any("BELO" in c.get("name", "").upper() for c in api_clients_consultant)
                
                logger.info(f"  DENİZ OTEL in consultant API: {deniz_in_api}")
                logger.info(f"  BELO in consultant API: {belo_in_api}")
                
                if deniz_in_db and not deniz_in_api:
                    self.log_finding("DENİZ OTEL exists in database but NOT visible to consultant via API")
                if belo_in_db and not belo_in_api:
                    self.log_finding("BELO exists in database but NOT visible to consultant via API")
                if deniz_in_api and not belo_in_api:
                    self.log_finding("Consultant can see DENİZ OTEL but NOT BELO - possible assignment difference")
                if not deniz_in_api and not belo_in_api:
                    self.log_finding("Consultant cannot see either DENİZ OTEL or BELO - possible assignment issue")
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        logger.info("\n" + "="*80)
        logger.info("5. INVESTIGATION SUMMARY REPORT")
        logger.info("="*80)
        
        logger.info("\n🔍 KEY FINDINGS:")
        for i, finding in enumerate(self.investigation_results["findings"], 1):
            logger.info(f"  {i}. {finding}")
        
        # Specific analysis for the review request
        logger.info("\n📋 REVIEW REQUEST ANALYSIS:")
        
        db_clients = self.investigation_results.get("database_clients", [])
        api_clients_consultant = self.investigation_results.get("api_clients_consultant", [])
        
        # Question 1: Which clients are assigned to consultants?
        logger.info("\n  Q1: Which clients are assigned to consultants?")
        assigned_clients = [c for c in db_clients if c.get("consultant_id")]
        unassigned_clients = [c for c in db_clients if not c.get("consultant_id")]
        
        logger.info(f"    - {len(assigned_clients)} clients have consultant assignments")
        logger.info(f"    - {len(unassigned_clients)} clients have NO consultant assignment")
        
        for client in assigned_clients:
            logger.info(f"      * {client.get('name', 'Unknown')} → Consultant: {client.get('consultant_id')}")
        
        # Question 2: Are DENİZ OTEL and BELO assigned to same consultant?
        logger.info("\n  Q2: Are DENİZ OTEL and BELO assigned to same consultant?")
        deniz_consultant = None
        belo_consultant = None
        
        for client in db_clients:
            name = client.get("name", "").upper()
            if "DENİZ" in name or "DENIZ" in name:
                deniz_consultant = client.get("consultant_id")
                logger.info(f"    - DENİZ OTEL consultant_id: {deniz_consultant}")
            if "BELO" in name:
                belo_consultant = client.get("consultant_id")
                logger.info(f"    - BELO consultant_id: {belo_consultant}")
        
        if deniz_consultant and belo_consultant:
            if deniz_consultant == belo_consultant:
                logger.info(f"    ✅ SAME consultant: {deniz_consultant}")
            else:
                logger.info(f"    ❌ DIFFERENT consultants: {deniz_consultant} vs {belo_consultant}")
        else:
            logger.info(f"    ⚠️ Missing assignments - DENİZ: {deniz_consultant}, BELO: {belo_consultant}")
        
        # Question 3: Backend stats logic for consultant users
        logger.info("\n  Q3: Backend stats logic for consultant users")
        admin_stats = self.investigation_results.get("api_stats_admin")
        consultant_stats = self.investigation_results.get("api_stats_consultant")
        
        if admin_stats and consultant_stats:
            admin_clients = admin_stats.get("total_clients", 0)
            consultant_clients = consultant_stats.get("total_clients", 0)
            
            logger.info(f"    - Admin sees: {admin_clients} clients")
            logger.info(f"    - Consultant sees: {consultant_clients} clients")
            
            if consultant_clients == admin_clients:
                logger.info("    ❌ Consultant sees ALL clients (no filtering)")
            elif consultant_clients < admin_clients:
                logger.info("    ✅ Consultant sees FILTERED clients (working correctly)")
            else:
                logger.info("    ⚠️ Unexpected: Consultant sees more than admin")
        else:
            logger.info("    ⚠️ Could not compare - API responses not available")
        
        # Question 4: Backend clients logic for consultant users
        logger.info("\n  Q4: Backend clients logic for consultant users")
        if api_clients_consultant is not None:
            consultant_client_count = len(api_clients_consultant)
            logger.info(f"    - Consultant API returns: {consultant_client_count} clients")
            
            if consultant_client_count == 1:
                logger.info("    ✅ Consultant sees 1 client (matches frontend)")
            elif consultant_client_count == 2:
                logger.info("    ❌ Consultant sees 2 clients (more than frontend shows)")
            else:
                logger.info(f"    ⚠️ Consultant sees {consultant_client_count} clients")
        else:
            logger.info("    ⚠️ Could not test - API not accessible")
        
        # Root cause analysis
        logger.info("\n🎯 ROOT CAUSE ANALYSIS:")
        
        if len(db_clients) == 2 and api_clients_consultant and len(api_clients_consultant) == 1:
            logger.info("  ✅ Database has 2 clients, consultant API returns 1 - filtering is working")
            logger.info("  🔍 Issue likely: BELO is not assigned to the consultant or assignment is incorrect")
        elif len(db_clients) == 2 and api_clients_consultant and len(api_clients_consultant) == 2:
            logger.info("  ❌ Database has 2 clients, consultant API returns 2 - no filtering applied")
            logger.info("  🔍 Issue: Backend filtering logic not working for consultant role")
        elif len(db_clients) == 2 and not api_clients_consultant:
            logger.info("  ⚠️ Database has 2 clients, but consultant API not accessible")
            logger.info("  🔍 Issue: Authentication or endpoint accessibility problem")
        
        logger.info("\n📝 RECOMMENDATIONS:")
        logger.info("  1. Verify consultant_id assignments in clients collection")
        logger.info("  2. Check consultant user's consultant_id in users collection")
        logger.info("  3. Test backend filtering logic with valid authentication tokens")
        logger.info("  4. Ensure BELO client has correct consultant_id if it should be visible")
        logger.info("  5. Verify frontend is using correct API endpoints and handling responses properly")

def main():
    """Main investigation function"""
    logger.info("🚀 STARTING CONSULTANT CLIENT ASSIGNMENT INVESTIGATION")
    logger.info("="*80)
    
    investigation = ConsultantAssignmentInvestigation()
    
    # Run all investigation steps
    investigation.investigate_database_assignments()
    investigation.test_api_clients_endpoint()
    investigation.test_api_stats_endpoint()
    investigation.analyze_filtering_logic()
    investigation.generate_summary_report()
    
    logger.info("\n🏁 INVESTIGATION COMPLETED")
    logger.info("="*80)

if __name__ == "__main__":
    main()