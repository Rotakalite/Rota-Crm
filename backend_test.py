#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta
import os
import sys
import time

# Get the backend URL from the frontend/.env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1] + '/api'
            break

print(f"Using backend URL: {BACKEND_URL}")

# Test data - Turkish hotel information
test_client = {
    "name": "Akdeniz Turizm A.Ş.",
    "hotel_name": "Grand Antalya Resort & Spa",
    "contact_person": "Mehmet Yılmaz",
    "email": "myilmaz@grandantalya.com",
    "phone": "+90 242 123 4567",
    "address": "Lara Caddesi No:123, Antalya, Türkiye"
}

test_carbon_footprint = {
    "energy_consumption": 1250000,  # kWh/year
    "water_consumption": 45000,     # m3/year
    "waste_generated": 75000,       # kg/year
    "transport_emissions": 35000    # kg CO2
}

# Carbon footprint report document
test_carbon_report = {
    "name": "Karbon Ayak İzi Raporu 2025",
    "document_type": "Karbon Ayak İzi Raporu",
    "stage": "II.Aşama",
    "file_path": "/documents/carbon_report_2025.pdf",
    "file_size": 3072
}

test_training = {
    "title": "Sürdürülebilir Turizm Eğitimi",
    "description": "Otel personeli için sürdürülebilir turizm uygulamaları eğitimi",
    "training_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
    "participants": 25
}

test_document = {
    "name": "Sürdürülebilir Turizm Kriterleri",
    "document_type": "Türkiye Sürdürülebilir Turizm Programı Kriterleri (TR-I)",
    "stage": "I.Aşama",
    "file_path": "/documents/criteria_tr1.pdf",
    "file_size": 2048
}

class BackendTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.client_id = None
        self.training_id = None
        self.document_id = None
        self.carbon_report_id = None
        self.headers = {"Authorization": "Bearer test-token"}
        self.test_results = {
            "client_management": {"status": "Not tested", "details": []},
            "carbon_footprint": {"status": "Not tested", "details": []},
            "training_management": {"status": "Not tested", "details": []},
            "document_management": {"status": "Not tested", "details": []},
            "carbon_report_flow": {"status": "Not tested", "details": []},
            "statistics": {"status": "Not tested", "details": []}
        }
        
    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("Starting backend API tests...")
        
        # Test client management APIs
        self.test_client_management()
        
        # Test carbon footprint APIs
        if self.client_id:
            self.test_carbon_footprint()
        
        # Test training management APIs
        if self.client_id:
            self.test_training_management()
        
        # Test document management APIs
        if self.client_id:
            self.test_document_management()
            
        # Test carbon report flow (admin upload to client retrieval)
        if self.client_id:
            self.test_carbon_report_flow()
        
        # Test statistics API
        self.test_statistics()
        
        # Print summary
        self.print_summary()
        
    def test_client_management(self):
        """Test client management APIs"""
        print("\n=== Testing Client Management APIs ===")
        
        # Test creating a new client
        print("\nTesting POST /api/clients")
        try:
            response = requests.post(f"{self.base_url}/clients", json=test_client, headers=self.headers)
            if response.status_code == 200:
                client_data = response.json()
                self.client_id = client_data["id"]
                print(f"✅ Successfully created client with ID: {self.client_id}")
                self.test_results["client_management"]["details"].append({
                    "endpoint": "POST /api/clients",
                    "status": "Success",
                    "response": client_data
                })
            else:
                print(f"❌ Failed to create client: {response.status_code} - {response.text}")
                self.test_results["client_management"]["details"].append({
                    "endpoint": "POST /api/clients",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when creating client: {str(e)}")
            self.test_results["client_management"]["details"].append({
                "endpoint": "POST /api/clients",
                "status": "Error",
                "error": str(e)
            })
        
        # Test getting all clients
        print("\nTesting GET /api/clients")
        try:
            response = requests.get(f"{self.base_url}/clients", headers=self.headers)
            if response.status_code == 200:
                clients = response.json()
                print(f"✅ Successfully retrieved {len(clients)} clients")
                self.test_results["client_management"]["details"].append({
                    "endpoint": "GET /api/clients",
                    "status": "Success",
                    "count": len(clients)
                })
            else:
                print(f"❌ Failed to get clients: {response.status_code} - {response.text}")
                self.test_results["client_management"]["details"].append({
                    "endpoint": "GET /api/clients",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when getting clients: {str(e)}")
            self.test_results["client_management"]["details"].append({
                "endpoint": "GET /api/clients",
                "status": "Error",
                "error": str(e)
            })
        
        # Test getting a specific client
        if self.client_id:
            print(f"\nTesting GET /api/clients/{self.client_id}")
            try:
                response = requests.get(f"{self.base_url}/clients/{self.client_id}", headers=self.headers)
                if response.status_code == 200:
                    client = response.json()
                    print(f"✅ Successfully retrieved client: {client['hotel_name']}")
                    self.test_results["client_management"]["details"].append({
                        "endpoint": f"GET /api/clients/{self.client_id}",
                        "status": "Success",
                        "response": client
                    })
                else:
                    print(f"❌ Failed to get client: {response.status_code} - {response.text}")
                    self.test_results["client_management"]["details"].append({
                        "endpoint": f"GET /api/clients/{self.client_id}",
                        "status": "Failed",
                        "error": f"{response.status_code} - {response.text}"
                    })
            except Exception as e:
                print(f"❌ Exception when getting client: {str(e)}")
                self.test_results["client_management"]["details"].append({
                    "endpoint": f"GET /api/clients/{self.client_id}",
                    "status": "Error",
                    "error": str(e)
                })
        
        # Test updating a client
        if self.client_id:
            print(f"\nTesting PUT /api/clients/{self.client_id}")
            update_data = {
                "current_stage": "II.Aşama",
                "services_completed": ["Mevcut durum analizi", "Çalışma ekibinin belirlenmesi"]
            }
            try:
                response = requests.put(f"{self.base_url}/clients/{self.client_id}", json=update_data, headers=self.headers)
                if response.status_code == 200:
                    updated_client = response.json()
                    print(f"✅ Successfully updated client to stage: {updated_client['current_stage']}")
                    self.test_results["client_management"]["details"].append({
                        "endpoint": f"PUT /api/clients/{self.client_id}",
                        "status": "Success",
                        "response": updated_client
                    })
                else:
                    print(f"❌ Failed to update client: {response.status_code} - {response.text}")
                    self.test_results["client_management"]["details"].append({
                        "endpoint": f"PUT /api/clients/{self.client_id}",
                        "status": "Failed",
                        "error": f"{response.status_code} - {response.text}"
                    })
            except Exception as e:
                print(f"❌ Exception when updating client: {str(e)}")
                self.test_results["client_management"]["details"].append({
                    "endpoint": f"PUT /api/clients/{self.client_id}",
                    "status": "Error",
                    "error": str(e)
                })
        
        # Set the overall status for client management
        success_count = sum(1 for detail in self.test_results["client_management"]["details"] if detail["status"] == "Success")
        total_count = len(self.test_results["client_management"]["details"])
        
        if success_count == total_count:
            self.test_results["client_management"]["status"] = "Success"
        elif success_count > 0:
            self.test_results["client_management"]["status"] = "Partial Success"
        else:
            self.test_results["client_management"]["status"] = "Failed"
    
    def test_carbon_footprint(self):
        """Test carbon footprint calculation APIs"""
        print("\n=== Testing Carbon Footprint APIs ===")
        
        # Test calculating carbon footprint
        print("\nTesting POST /api/carbon-footprint")
        carbon_data = test_carbon_footprint.copy()
        carbon_data["client_id"] = self.client_id
        
        try:
            response = requests.post(f"{self.base_url}/carbon-footprint", json=carbon_data, headers=self.headers)
            if response.status_code == 200:
                footprint = response.json()
                print(f"✅ Successfully calculated carbon footprint: {footprint['total_co2_emissions']} kg CO2/year")
                self.test_results["carbon_footprint"]["details"].append({
                    "endpoint": "POST /api/carbon-footprint",
                    "status": "Success",
                    "response": footprint
                })
            else:
                print(f"❌ Failed to calculate carbon footprint: {response.status_code} - {response.text}")
                self.test_results["carbon_footprint"]["details"].append({
                    "endpoint": "POST /api/carbon-footprint",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when calculating carbon footprint: {str(e)}")
            self.test_results["carbon_footprint"]["details"].append({
                "endpoint": "POST /api/carbon-footprint",
                "status": "Error",
                "error": str(e)
            })
        
        # Test getting client's carbon footprint history
        print(f"\nTesting GET /api/carbon-footprint/{self.client_id}")
        try:
            response = requests.get(f"{self.base_url}/carbon-footprint/{self.client_id}")
            if response.status_code == 200:
                footprints = response.json()
                print(f"✅ Successfully retrieved {len(footprints)} carbon footprint records")
                self.test_results["carbon_footprint"]["details"].append({
                    "endpoint": f"GET /api/carbon-footprint/{self.client_id}",
                    "status": "Success",
                    "count": len(footprints)
                })
            else:
                print(f"❌ Failed to get carbon footprint history: {response.status_code} - {response.text}")
                self.test_results["carbon_footprint"]["details"].append({
                    "endpoint": f"GET /api/carbon-footprint/{self.client_id}",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when getting carbon footprint history: {str(e)}")
            self.test_results["carbon_footprint"]["details"].append({
                "endpoint": f"GET /api/carbon-footprint/{self.client_id}",
                "status": "Error",
                "error": str(e)
            })
        
        # Set the overall status for carbon footprint
        success_count = sum(1 for detail in self.test_results["carbon_footprint"]["details"] if detail["status"] == "Success")
        total_count = len(self.test_results["carbon_footprint"]["details"])
        
        if success_count == total_count:
            self.test_results["carbon_footprint"]["status"] = "Success"
        elif success_count > 0:
            self.test_results["carbon_footprint"]["status"] = "Partial Success"
        else:
            self.test_results["carbon_footprint"]["status"] = "Failed"
    
    def test_training_management(self):
        """Test training management APIs"""
        print("\n=== Testing Training Management APIs ===")
        
        # Test creating a training session
        print("\nTesting POST /api/trainings")
        training_data = test_training.copy()
        training_data["client_id"] = self.client_id
        
        try:
            response = requests.post(f"{self.base_url}/trainings", json=training_data)
            if response.status_code == 200:
                training = response.json()
                self.training_id = training["id"]
                print(f"✅ Successfully created training session with ID: {self.training_id}")
                self.test_results["training_management"]["details"].append({
                    "endpoint": "POST /api/trainings",
                    "status": "Success",
                    "response": training
                })
            else:
                print(f"❌ Failed to create training session: {response.status_code} - {response.text}")
                self.test_results["training_management"]["details"].append({
                    "endpoint": "POST /api/trainings",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when creating training session: {str(e)}")
            self.test_results["training_management"]["details"].append({
                "endpoint": "POST /api/trainings",
                "status": "Error",
                "error": str(e)
            })
        
        # Test getting client's training sessions
        print(f"\nTesting GET /api/trainings/{self.client_id}")
        try:
            response = requests.get(f"{self.base_url}/trainings/{self.client_id}")
            if response.status_code == 200:
                trainings = response.json()
                print(f"✅ Successfully retrieved {len(trainings)} training sessions")
                self.test_results["training_management"]["details"].append({
                    "endpoint": f"GET /api/trainings/{self.client_id}",
                    "status": "Success",
                    "count": len(trainings)
                })
            else:
                print(f"❌ Failed to get training sessions: {response.status_code} - {response.text}")
                self.test_results["training_management"]["details"].append({
                    "endpoint": f"GET /api/trainings/{self.client_id}",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when getting training sessions: {str(e)}")
            self.test_results["training_management"]["details"].append({
                "endpoint": f"GET /api/trainings/{self.client_id}",
                "status": "Error",
                "error": str(e)
            })
        
        # Test updating training status
        if self.training_id:
            print(f"\nTesting PUT /api/trainings/{self.training_id}")
            try:
                response = requests.put(f"{self.base_url}/trainings/{self.training_id}?status=Completed")
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Successfully updated training status: {result['message']}")
                    self.test_results["training_management"]["details"].append({
                        "endpoint": f"PUT /api/trainings/{self.training_id}",
                        "status": "Success",
                        "response": result
                    })
                else:
                    print(f"❌ Failed to update training status: {response.status_code} - {response.text}")
                    self.test_results["training_management"]["details"].append({
                        "endpoint": f"PUT /api/trainings/{self.training_id}",
                        "status": "Failed",
                        "error": f"{response.status_code} - {response.text}"
                    })
            except Exception as e:
                print(f"❌ Exception when updating training status: {str(e)}")
                self.test_results["training_management"]["details"].append({
                    "endpoint": f"PUT /api/trainings/{self.training_id}",
                    "status": "Error",
                    "error": str(e)
                })
        
        # Set the overall status for training management
        success_count = sum(1 for detail in self.test_results["training_management"]["details"] if detail["status"] == "Success")
        total_count = len(self.test_results["training_management"]["details"])
        
        if success_count == total_count:
            self.test_results["training_management"]["status"] = "Success"
        elif success_count > 0:
            self.test_results["training_management"]["status"] = "Partial Success"
        else:
            self.test_results["training_management"]["status"] = "Failed"
    
    def test_document_management(self):
        """Test document management APIs"""
        print("\n=== Testing Document Management APIs ===")
        
        # Test creating a document record
        print("\nTesting POST /api/documents")
        document_data = test_document.copy()
        document_data["client_id"] = self.client_id
        
        try:
            response = requests.post(f"{self.base_url}/documents", json=document_data)
            if response.status_code == 200:
                document = response.json()
                print(f"✅ Successfully created document record with ID: {document['id']}")
                self.test_results["document_management"]["details"].append({
                    "endpoint": "POST /api/documents",
                    "status": "Success",
                    "response": document
                })
            else:
                print(f"❌ Failed to create document record: {response.status_code} - {response.text}")
                self.test_results["document_management"]["details"].append({
                    "endpoint": "POST /api/documents",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when creating document record: {str(e)}")
            self.test_results["document_management"]["details"].append({
                "endpoint": "POST /api/documents",
                "status": "Error",
                "error": str(e)
            })
        
        # Test getting client documents
        print(f"\nTesting GET /api/documents/{self.client_id}")
        try:
            response = requests.get(f"{self.base_url}/documents/{self.client_id}")
            if response.status_code == 200:
                documents = response.json()
                print(f"✅ Successfully retrieved {len(documents)} document records")
                self.test_results["document_management"]["details"].append({
                    "endpoint": f"GET /api/documents/{self.client_id}",
                    "status": "Success",
                    "count": len(documents)
                })
            else:
                print(f"❌ Failed to get document records: {response.status_code} - {response.text}")
                self.test_results["document_management"]["details"].append({
                    "endpoint": f"GET /api/documents/{self.client_id}",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when getting document records: {str(e)}")
            self.test_results["document_management"]["details"].append({
                "endpoint": f"GET /api/documents/{self.client_id}",
                "status": "Error",
                "error": str(e)
            })
        
        # Set the overall status for document management
        success_count = sum(1 for detail in self.test_results["document_management"]["details"] if detail["status"] == "Success")
        total_count = len(self.test_results["document_management"]["details"])
        
        if success_count == total_count:
            self.test_results["document_management"]["status"] = "Success"
        elif success_count > 0:
            self.test_results["document_management"]["status"] = "Partial Success"
        else:
            self.test_results["document_management"]["status"] = "Failed"
    
    def test_statistics(self):
        """Test statistics dashboard API"""
        print("\n=== Testing Statistics Dashboard API ===")
        
        # Test getting dashboard statistics
        print("\nTesting GET /api/stats")
        try:
            response = requests.get(f"{self.base_url}/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Successfully retrieved dashboard statistics")
                print(f"   Total clients: {stats['total_clients']}")
                print(f"   Stage distribution: {stats['stage_distribution']}")
                print(f"   Total documents: {stats['total_documents']}")
                print(f"   Total trainings: {stats['total_trainings']}")
                self.test_results["statistics"]["details"].append({
                    "endpoint": "GET /api/stats",
                    "status": "Success",
                    "response": stats
                })
                self.test_results["statistics"]["status"] = "Success"
            else:
                print(f"❌ Failed to get dashboard statistics: {response.status_code} - {response.text}")
                self.test_results["statistics"]["details"].append({
                    "endpoint": "GET /api/stats",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
                self.test_results["statistics"]["status"] = "Failed"
        except Exception as e:
            print(f"❌ Exception when getting dashboard statistics: {str(e)}")
            self.test_results["statistics"]["details"].append({
                "endpoint": "GET /api/stats",
                "status": "Error",
                "error": str(e)
            })
            self.test_results["statistics"]["status"] = "Failed"
            
    def test_carbon_report_flow(self):
        """Test carbon footprint report document flow from admin upload to client retrieval"""
        print("\n=== Testing Carbon Footprint Report Flow ===")
        
        # 1. Admin uploads carbon footprint report for client
        print("\nTesting POST /api/carbon-report (Admin uploads carbon report)")
        carbon_report_data = test_carbon_report.copy()
        carbon_report_data["client_id"] = self.client_id
        
        try:
            response = requests.post(f"{self.base_url}/carbon-report", json=carbon_report_data)
            if response.status_code == 200:
                report = response.json()
                self.carbon_report_id = report["id"]
                print(f"✅ Successfully uploaded carbon report with ID: {self.carbon_report_id}")
                self.test_results["carbon_report_flow"]["details"].append({
                    "endpoint": "POST /api/carbon-report",
                    "status": "Success",
                    "response": report
                })
            else:
                print(f"❌ Failed to upload carbon report: {response.status_code} - {response.text}")
                self.test_results["carbon_report_flow"]["details"].append({
                    "endpoint": "POST /api/carbon-report",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when uploading carbon report: {str(e)}")
            self.test_results["carbon_report_flow"]["details"].append({
                "endpoint": "POST /api/carbon-report",
                "status": "Error",
                "error": str(e)
            })
        
        # 2. Client retrieves their carbon footprint reports
        print(f"\nTesting GET /api/carbon-reports/{self.client_id} (Client retrieves carbon reports)")
        try:
            response = requests.get(f"{self.base_url}/carbon-reports/{self.client_id}")
            if response.status_code == 200:
                reports = response.json()
                print(f"✅ Successfully retrieved {len(reports)} carbon reports")
                
                # Verify the uploaded report is in the list
                report_found = False
                for report in reports:
                    if self.carbon_report_id and report["id"] == self.carbon_report_id:
                        report_found = True
                        print(f"✅ Found the uploaded carbon report in client's reports")
                        break
                
                if report_found or not self.carbon_report_id:
                    self.test_results["carbon_report_flow"]["details"].append({
                        "endpoint": f"GET /api/carbon-reports/{self.client_id}",
                        "status": "Success",
                        "count": len(reports),
                        "report_found": report_found
                    })
                else:
                    print(f"❌ Uploaded carbon report not found in client's reports")
                    self.test_results["carbon_report_flow"]["details"].append({
                        "endpoint": f"GET /api/carbon-reports/{self.client_id}",
                        "status": "Failed",
                        "error": "Uploaded carbon report not found in client's reports"
                    })
            else:
                print(f"❌ Failed to get carbon reports: {response.status_code} - {response.text}")
                self.test_results["carbon_report_flow"]["details"].append({
                    "endpoint": f"GET /api/carbon-reports/{self.client_id}",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when getting carbon reports: {str(e)}")
            self.test_results["carbon_report_flow"]["details"].append({
                "endpoint": f"GET /api/carbon-reports/{self.client_id}",
                "status": "Error",
                "error": str(e)
            })
        
        # Set the overall status for carbon report flow
        success_count = sum(1 for detail in self.test_results["carbon_report_flow"]["details"] if detail["status"] == "Success")
        total_count = len(self.test_results["carbon_report_flow"]["details"])
        
        if success_count == total_count:
            self.test_results["carbon_report_flow"]["status"] = "Success"
        elif success_count > 0:
            self.test_results["carbon_report_flow"]["status"] = "Partial Success"
        else:
            self.test_results["carbon_report_flow"]["status"] = "Failed"
    
    def test_delete_client(self):
        """Test client deletion API"""
        if not self.client_id:
            return
            
        print("\n=== Testing Client Deletion API ===")
        print(f"\nTesting DELETE /api/clients/{self.client_id}")
        
        try:
            response = requests.delete(f"{self.base_url}/clients/{self.client_id}")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully deleted client: {result['message']}")
                self.test_results["client_management"]["details"].append({
                    "endpoint": f"DELETE /api/clients/{self.client_id}",
                    "status": "Success",
                    "response": result
                })
            else:
                print(f"❌ Failed to delete client: {response.status_code} - {response.text}")
                self.test_results["client_management"]["details"].append({
                    "endpoint": f"DELETE /api/clients/{self.client_id}",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when deleting client: {str(e)}")
            self.test_results["client_management"]["details"].append({
                "endpoint": f"DELETE /api/clients/{self.client_id}",
                "status": "Error",
                "error": str(e)
            })
    
    def print_summary(self):
        """Print a summary of all test results"""
        print("\n=== TEST SUMMARY ===")
        for category, result in self.test_results.items():
            status_symbol = "✅" if result["status"] == "Success" else "⚠️" if result["status"] == "Partial Success" else "❌"
            print(f"{status_symbol} {category.replace('_', ' ').title()}: {result['status']}")
        
        # Test client deletion at the end
        if self.client_id:
            self.test_delete_client()

if __name__ == "__main__":
    tester = BackendTester(BACKEND_URL)
    tester.run_all_tests()