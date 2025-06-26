#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta
import os
import sys
import time
import random

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

# Test consumption data for current year
current_year = datetime.now().year
previous_year = current_year - 1

# Generate realistic consumption data for a Turkish hotel
def generate_consumption_data(year, month, is_high_season=False):
    # High season in Turkey is typically June-September
    high_season = month >= 6 and month <= 9
    season_multiplier = 1.5 if high_season else 1.0
    
    # Base values for a medium-sized hotel
    base_electricity = 75000  # kWh
    base_water = 2500        # m³
    base_natural_gas = 1500  # m³
    base_coal = 500          # kg
    
    # Accommodation count varies by season
    base_accommodation = 2000 if high_season else 800
    
    # Add some randomness
    random_factor = random.uniform(0.9, 1.1)
    
    return {
        "year": year,
        "month": month,
        "electricity": round(base_electricity * season_multiplier * random_factor, 2),
        "water": round(base_water * season_multiplier * random_factor, 2),
        "natural_gas": round(base_natural_gas * season_multiplier * random_factor, 2),
        "coal": round(base_coal * season_multiplier * random_factor, 2),
        "accommodation_count": int(base_accommodation * season_multiplier * random_factor)
    }

class ConsumptionTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.client_id = None
        self.consumption_ids = []
        # For testing purposes, we'll bypass authentication
        self.headers = {}
        self.test_results = {
            "client_creation": {"status": "Not tested", "details": []},
            "consumption_creation": {"status": "Not tested", "details": []},
            "consumption_retrieval": {"status": "Not tested", "details": []},
            "consumption_update": {"status": "Not tested", "details": []},
            "consumption_deletion": {"status": "Not tested", "details": []},
            "consumption_analytics": {"status": "Not tested", "details": []},
            "duplicate_prevention": {"status": "Not tested", "details": []}
        }
        
    def run_all_tests(self):
        """Run all consumption management API tests in sequence"""
        print("Starting consumption management API tests...")
        
        # Create a test client first
        self.create_test_client()
        
        if self.client_id:
            # Test consumption CRUD operations
            self.test_consumption_creation()
            self.test_consumption_retrieval()
            self.test_consumption_update()
            self.test_duplicate_prevention()
            self.test_consumption_analytics()
            self.test_consumption_deletion()
        
        # Print summary
        self.print_summary()
        
    def create_test_client(self):
        """Create a test client for consumption data"""
        print("\n=== Creating Test Client ===")
        
        try:
            response = requests.post(f"{self.base_url}/clients", json=test_client, headers=self.headers)
            if response.status_code == 200:
                client_data = response.json()
                self.client_id = client_data["id"]
                print(f"✅ Successfully created client with ID: {self.client_id}")
                self.test_results["client_creation"]["status"] = "Success"
                self.test_results["client_creation"]["details"].append({
                    "endpoint": "POST /api/clients",
                    "status": "Success",
                    "response": client_data
                })
            else:
                print(f"❌ Failed to create client: {response.status_code} - {response.text}")
                self.test_results["client_creation"]["status"] = "Failed"
                self.test_results["client_creation"]["details"].append({
                    "endpoint": "POST /api/clients",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when creating client: {str(e)}")
            self.test_results["client_creation"]["status"] = "Error"
            self.test_results["client_creation"]["details"].append({
                "endpoint": "POST /api/clients",
                "status": "Error",
                "error": str(e)
            })
    
    def test_consumption_creation(self):
        """Test creating consumption records for different months"""
        print("\n=== Testing Consumption Creation ===")
        
        # Create consumption data for current year (6 months)
        for month in range(1, 7):
            consumption_data = generate_consumption_data(current_year, month)
            self._create_consumption_record(consumption_data)
            
        # Create consumption data for previous year (all 12 months)
        for month in range(1, 13):
            consumption_data = generate_consumption_data(previous_year, month)
            self._create_consumption_record(consumption_data)
        
        # Set overall status
        success_count = sum(1 for detail in self.test_results["consumption_creation"]["details"] if detail["status"] == "Success")
        total_count = len(self.test_results["consumption_creation"]["details"])
        
        if total_count == 0:
            self.test_results["consumption_creation"]["status"] = "Not tested"
        elif success_count == total_count:
            self.test_results["consumption_creation"]["status"] = "Success"
        elif success_count > 0:
            self.test_results["consumption_creation"]["status"] = "Partial Success"
        else:
            self.test_results["consumption_creation"]["status"] = "Failed"
    
    def _create_consumption_record(self, consumption_data):
        """Helper method to create a single consumption record"""
        try:
            print(f"\nCreating consumption record for {consumption_data['year']}-{consumption_data['month']}")
            response = requests.post(f"{self.base_url}/consumptions", json=consumption_data, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                consumption_id = result.get("consumption_id")
                if consumption_id:
                    self.consumption_ids.append(consumption_id)
                
                print(f"✅ Successfully created consumption record for {consumption_data['year']}-{consumption_data['month']}")
                self.test_results["consumption_creation"]["details"].append({
                    "endpoint": "POST /api/consumptions",
                    "status": "Success",
                    "year": consumption_data['year'],
                    "month": consumption_data['month'],
                    "response": result
                })
                return True
            else:
                print(f"❌ Failed to create consumption record: {response.status_code} - {response.text}")
                self.test_results["consumption_creation"]["details"].append({
                    "endpoint": "POST /api/consumptions",
                    "status": "Failed",
                    "year": consumption_data['year'],
                    "month": consumption_data['month'],
                    "error": f"{response.status_code} - {response.text}"
                })
                return False
        except Exception as e:
            print(f"❌ Exception when creating consumption record: {str(e)}")
            self.test_results["consumption_creation"]["details"].append({
                "endpoint": "POST /api/consumptions",
                "status": "Error",
                "year": consumption_data['year'],
                "month": consumption_data['month'],
                "error": str(e)
            })
            return False
    
    def test_consumption_retrieval(self):
        """Test retrieving consumption records with year filtering"""
        print("\n=== Testing Consumption Retrieval ===")
        
        # Test getting all consumption records
        print("\nTesting GET /api/consumptions (all records)")
        try:
            response = requests.get(f"{self.base_url}/consumptions", headers=self.headers)
            if response.status_code == 200:
                consumptions = response.json()
                print(f"✅ Successfully retrieved {len(consumptions)} consumption records")
                self.test_results["consumption_retrieval"]["details"].append({
                    "endpoint": "GET /api/consumptions",
                    "status": "Success",
                    "count": len(consumptions)
                })
            else:
                print(f"❌ Failed to get consumption records: {response.status_code} - {response.text}")
                self.test_results["consumption_retrieval"]["details"].append({
                    "endpoint": "GET /api/consumptions",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when getting consumption records: {str(e)}")
            self.test_results["consumption_retrieval"]["details"].append({
                "endpoint": "GET /api/consumptions",
                "status": "Error",
                "error": str(e)
            })
        
        # Test getting consumption records for current year
        print(f"\nTesting GET /api/consumptions?year={current_year}")
        try:
            response = requests.get(f"{self.base_url}/consumptions?year={current_year}", headers=self.headers)
            if response.status_code == 200:
                consumptions = response.json()
                print(f"✅ Successfully retrieved {len(consumptions)} consumption records for {current_year}")
                self.test_results["consumption_retrieval"]["details"].append({
                    "endpoint": f"GET /api/consumptions?year={current_year}",
                    "status": "Success",
                    "count": len(consumptions),
                    "year": current_year
                })
            else:
                print(f"❌ Failed to get consumption records for {current_year}: {response.status_code} - {response.text}")
                self.test_results["consumption_retrieval"]["details"].append({
                    "endpoint": f"GET /api/consumptions?year={current_year}",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when getting consumption records for {current_year}: {str(e)}")
            self.test_results["consumption_retrieval"]["details"].append({
                "endpoint": f"GET /api/consumptions?year={current_year}",
                "status": "Error",
                "error": str(e)
            })
        
        # Test getting consumption records for previous year
        print(f"\nTesting GET /api/consumptions?year={previous_year}")
        try:
            response = requests.get(f"{self.base_url}/consumptions?year={previous_year}", headers=self.headers)
            if response.status_code == 200:
                consumptions = response.json()
                print(f"✅ Successfully retrieved {len(consumptions)} consumption records for {previous_year}")
                self.test_results["consumption_retrieval"]["details"].append({
                    "endpoint": f"GET /api/consumptions?year={previous_year}",
                    "status": "Success",
                    "count": len(consumptions),
                    "year": previous_year
                })
            else:
                print(f"❌ Failed to get consumption records for {previous_year}: {response.status_code} - {response.text}")
                self.test_results["consumption_retrieval"]["details"].append({
                    "endpoint": f"GET /api/consumptions?year={previous_year}",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when getting consumption records for {previous_year}: {str(e)}")
            self.test_results["consumption_retrieval"]["details"].append({
                "endpoint": f"GET /api/consumptions?year={previous_year}",
                "status": "Error",
                "error": str(e)
            })
        
        # Set overall status
        success_count = sum(1 for detail in self.test_results["consumption_retrieval"]["details"] if detail["status"] == "Success")
        total_count = len(self.test_results["consumption_retrieval"]["details"])
        
        if total_count == 0:
            self.test_results["consumption_retrieval"]["status"] = "Not tested"
        elif success_count == total_count:
            self.test_results["consumption_retrieval"]["status"] = "Success"
        elif success_count > 0:
            self.test_results["consumption_retrieval"]["status"] = "Partial Success"
        else:
            self.test_results["consumption_retrieval"]["status"] = "Failed"
    
    def test_consumption_update(self):
        """Test updating existing consumption records"""
        print("\n=== Testing Consumption Update ===")
        
        # Get a consumption ID to update
        if not self.consumption_ids:
            print("❌ No consumption IDs available for update test")
            self.test_results["consumption_update"]["status"] = "Not tested"
            return
        
        consumption_id = self.consumption_ids[0]
        
        # Update data with increased values
        update_data = {
            "year": current_year,
            "month": 1,
            "electricity": 85000,
            "water": 3000,
            "natural_gas": 1800,
            "coal": 600,
            "accommodation_count": 2200
        }
        
        print(f"\nTesting PUT /api/consumptions/{consumption_id}")
        try:
            response = requests.put(f"{self.base_url}/consumptions/{consumption_id}", json=update_data, headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully updated consumption record: {result['message']}")
                self.test_results["consumption_update"]["details"].append({
                    "endpoint": f"PUT /api/consumptions/{consumption_id}",
                    "status": "Success",
                    "response": result
                })
                self.test_results["consumption_update"]["status"] = "Success"
            else:
                print(f"❌ Failed to update consumption record: {response.status_code} - {response.text}")
                self.test_results["consumption_update"]["details"].append({
                    "endpoint": f"PUT /api/consumptions/{consumption_id}",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
                self.test_results["consumption_update"]["status"] = "Failed"
        except Exception as e:
            print(f"❌ Exception when updating consumption record: {str(e)}")
            self.test_results["consumption_update"]["details"].append({
                "endpoint": f"PUT /api/consumptions/{consumption_id}",
                "status": "Error",
                "error": str(e)
            })
            self.test_results["consumption_update"]["status"] = "Error"
    
    def test_consumption_deletion(self):
        """Test deleting consumption records (admin permission)"""
        print("\n=== Testing Consumption Deletion ===")
        
        # Get a consumption ID to delete
        if not self.consumption_ids:
            print("❌ No consumption IDs available for deletion test")
            self.test_results["consumption_deletion"]["status"] = "Not tested"
            return
        
        consumption_id = self.consumption_ids[-1]
        
        print(f"\nTesting DELETE /api/consumptions/{consumption_id}")
        try:
            response = requests.delete(f"{self.base_url}/consumptions/{consumption_id}", headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully deleted consumption record: {result['message']}")
                self.test_results["consumption_deletion"]["details"].append({
                    "endpoint": f"DELETE /api/consumptions/{consumption_id}",
                    "status": "Success",
                    "response": result
                })
                self.test_results["consumption_deletion"]["status"] = "Success"
            else:
                print(f"❌ Failed to delete consumption record: {response.status_code} - {response.text}")
                self.test_results["consumption_deletion"]["details"].append({
                    "endpoint": f"DELETE /api/consumptions/{consumption_id}",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
                self.test_results["consumption_deletion"]["status"] = "Failed"
        except Exception as e:
            print(f"❌ Exception when deleting consumption record: {str(e)}")
            self.test_results["consumption_deletion"]["details"].append({
                "endpoint": f"DELETE /api/consumptions/{consumption_id}",
                "status": "Error",
                "error": str(e)
            })
            self.test_results["consumption_deletion"]["status"] = "Error"
    
    def test_consumption_analytics(self):
        """Test analytics endpoint with year-over-year comparison"""
        print("\n=== Testing Consumption Analytics ===")
        
        # Test analytics for current year
        print(f"\nTesting GET /api/consumptions/analytics?year={current_year}")
        try:
            response = requests.get(f"{self.base_url}/consumptions/analytics?year={current_year}", headers=self.headers)
            if response.status_code == 200:
                analytics = response.json()
                print(f"✅ Successfully retrieved consumption analytics for {current_year}")
                
                # Verify the structure of the analytics response
                if "monthly_comparison" in analytics and "yearly_totals" in analytics and "yearly_per_person" in analytics:
                    print("✅ Analytics response contains all required sections")
                    
                    # Check if we have monthly data
                    if len(analytics["monthly_comparison"]) > 0:
                        print(f"✅ Analytics contains {len(analytics['monthly_comparison'])} months of data")
                        
                        # Check if per-person calculations are working
                        if "current_year_per_person" in analytics["monthly_comparison"][0]:
                            print("✅ Per-person consumption calculations are working")
                        else:
                            print("❌ Per-person consumption calculations are missing")
                    
                    self.test_results["consumption_analytics"]["details"].append({
                        "endpoint": f"GET /api/consumptions/analytics?year={current_year}",
                        "status": "Success",
                        "year": current_year,
                        "has_monthly_data": len(analytics["monthly_comparison"]) > 0,
                        "has_yearly_totals": "yearly_totals" in analytics,
                        "has_per_person_data": "yearly_per_person" in analytics
                    })
                else:
                    print("❌ Analytics response is missing required sections")
                    self.test_results["consumption_analytics"]["details"].append({
                        "endpoint": f"GET /api/consumptions/analytics?year={current_year}",
                        "status": "Partial Success",
                        "year": current_year,
                        "error": "Response missing required sections"
                    })
            else:
                print(f"❌ Failed to get consumption analytics: {response.status_code} - {response.text}")
                self.test_results["consumption_analytics"]["details"].append({
                    "endpoint": f"GET /api/consumptions/analytics?year={current_year}",
                    "status": "Failed",
                    "error": f"{response.status_code} - {response.text}"
                })
        except Exception as e:
            print(f"❌ Exception when getting consumption analytics: {str(e)}")
            self.test_results["consumption_analytics"]["details"].append({
                "endpoint": f"GET /api/consumptions/analytics?year={current_year}",
                "status": "Error",
                "error": str(e)
            })
        
        # Set overall status
        success_count = sum(1 for detail in self.test_results["consumption_analytics"]["details"] if detail["status"] == "Success")
        partial_count = sum(1 for detail in self.test_results["consumption_analytics"]["details"] if detail["status"] == "Partial Success")
        total_count = len(self.test_results["consumption_analytics"]["details"])
        
        if total_count == 0:
            self.test_results["consumption_analytics"]["status"] = "Not tested"
        elif success_count == total_count:
            self.test_results["consumption_analytics"]["status"] = "Success"
        elif success_count + partial_count > 0:
            self.test_results["consumption_analytics"]["status"] = "Partial Success"
        else:
            self.test_results["consumption_analytics"]["status"] = "Failed"
    
    def test_duplicate_prevention(self):
        """Test duplicate prevention (same month/year)"""
        print("\n=== Testing Duplicate Prevention ===")
        
        # Try to create a duplicate record for the same month/year
        duplicate_data = generate_consumption_data(current_year, 1)  # We already created this in test_consumption_creation
        
        print(f"\nTesting duplicate prevention for {duplicate_data['year']}-{duplicate_data['month']}")
        try:
            response = requests.post(f"{self.base_url}/consumptions", json=duplicate_data, headers=self.headers)
            
            # We expect a 400 Bad Request for duplicate
            if response.status_code == 400:
                print("✅ Duplicate prevention working correctly - server rejected duplicate record")
                self.test_results["duplicate_prevention"]["details"].append({
                    "endpoint": "POST /api/consumptions (duplicate)",
                    "status": "Success",
                    "year": duplicate_data['year'],
                    "month": duplicate_data['month'],
                    "response": response.text
                })
                self.test_results["duplicate_prevention"]["status"] = "Success"
            else:
                print(f"❌ Duplicate prevention failed - server accepted duplicate record: {response.status_code} - {response.text}")
                self.test_results["duplicate_prevention"]["details"].append({
                    "endpoint": "POST /api/consumptions (duplicate)",
                    "status": "Failed",
                    "year": duplicate_data['year'],
                    "month": duplicate_data['month'],
                    "error": f"Expected 400, got {response.status_code}"
                })
                self.test_results["duplicate_prevention"]["status"] = "Failed"
        except Exception as e:
            print(f"❌ Exception when testing duplicate prevention: {str(e)}")
            self.test_results["duplicate_prevention"]["details"].append({
                "endpoint": "POST /api/consumptions (duplicate)",
                "status": "Error",
                "year": duplicate_data['year'],
                "month": duplicate_data['month'],
                "error": str(e)
            })
            self.test_results["duplicate_prevention"]["status"] = "Error"
    
    def print_summary(self):
        """Print a summary of all test results"""
        print("\n=== TEST SUMMARY ===")
        for category, result in self.test_results.items():
            status_symbol = "✅" if result["status"] == "Success" else "⚠️" if result["status"] == "Partial Success" else "❌"
            print(f"{status_symbol} {category.replace('_', ' ').title()}: {result['status']}")

if __name__ == "__main__":
    tester = ConsumptionTester(BACKEND_URL)
    tester.run_all_tests()