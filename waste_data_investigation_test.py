#!/usr/bin/env python3
"""
GreenWave CRM - Waste Data Investigation Test
Deep dive into waste_management collection and data availability
"""

import requests
import json
import sys
from datetime import datetime

class WasteDataInvestigator:
    def __init__(self):
        self.base_url = "https://rota-crm-production.up.railway.app"
        self.api_base = f"{self.base_url}/api"
        
        print("🔍 GreenWave CRM - Waste Data Investigation")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 80)
    
    def test_waste_endpoints_detailed(self):
        """Test all waste-related endpoints in detail"""
        print("🗑️ TESTING WASTE ENDPOINTS:")
        print()
        
        waste_endpoints = [
            "/waste/bulk",
            "/consumptions/waste-data", 
            "/consumptions/waste",
            "/consumptions/waste/analytics",
            "/environment",
            "/analytics/carbon-footprint"
        ]
        
        for endpoint in waste_endpoints:
            try:
                response = requests.get(f"{self.api_base}{endpoint}", timeout=5)
                print(f"📍 {endpoint}")
                print(f"   Status: HTTP {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✅ Accessible without auth")
                elif response.status_code in [401, 403]:
                    print("   🔒 Secured (requires authentication)")
                elif response.status_code == 404:
                    print("   ❌ Not found")
                elif response.status_code == 405:
                    print("   ⚠️  Method not allowed (try POST)")
                else:
                    print(f"   ❓ Unexpected: {response.status_code}")
                
                # Check headers
                if 'Access-Control-Allow-Origin' in response.headers:
                    print("   🌐 CORS enabled")
                
                print()
                
            except Exception as e:
                print(f"📍 {endpoint}")
                print(f"   ❌ Error: {str(e)}")
                print()
    
    def test_carbon_footprint_with_sample_clients(self):
        """Test carbon footprint endpoint with known sample clients"""
        print("🧪 TESTING CARBON FOOTPRINT WITH SAMPLE CLIENTS:")
        print()
        
        # Known client IDs from previous tests
        sample_clients = [
            "94927a77-edc3-45ec-8329-795feae35771",  # CANO OTEL
            "test-client-id",
            "demo-client-1",
            "sample-client"
        ]
        
        for client_id in sample_clients:
            print(f"👤 Testing client: {client_id}")
            
            for year in [2024, 2023]:
                try:
                    params = {
                        "client_id": client_id,
                        "year": year
                    }
                    
                    response = requests.get(
                        f"{self.api_base}/analytics/carbon-footprint",
                        params=params,
                        timeout=10
                    )
                    
                    print(f"   📅 Year {year}: HTTP {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            total_waste_co2 = data.get("total_waste_co2", "Not found")
                            total_hotel_co2 = data.get("total_hotel_co2", "Not found") 
                            methodology = data.get("methodology", "Not found")
                            
                            print(f"      🗑️ total_waste_co2: {total_waste_co2}")
                            print(f"      🏨 total_hotel_co2: {total_hotel_co2}")
                            print(f"      📋 methodology: {methodology}")
                            
                            if "monthly_carbon_data" in data:
                                monthly_data = data["monthly_carbon_data"]
                                print(f"      📊 Monthly data: {len(monthly_data)} months")
                                
                                # Check first month for waste/hotel data
                                if monthly_data:
                                    first_month = monthly_data[0]
                                    month_waste = first_month.get("total_waste_co2", "Not found")
                                    month_hotel = first_month.get("total_hotel_co2", "Not found")
                                    print(f"      📅 First month waste CO2: {month_waste}")
                                    print(f"      📅 First month hotel CO2: {month_hotel}")
                            
                        except json.JSONDecodeError:
                            print("      ❌ Invalid JSON response")
                    
                    elif response.status_code in [401, 403]:
                        print("      🔒 Authentication required")
                    elif response.status_code == 404:
                        print("      ❌ Endpoint not found")
                    else:
                        print(f"      ❓ Unexpected: {response.status_code}")
                        
                except Exception as e:
                    print(f"      ❌ Error: {str(e)}")
            
            print()
    
    def test_waste_data_endpoints_methods(self):
        """Test different HTTP methods on waste endpoints"""
        print("🔧 TESTING WASTE ENDPOINTS WITH DIFFERENT METHODS:")
        print()
        
        waste_endpoints = [
            "/consumptions/waste-data",
            "/consumptions/waste", 
            "/waste/bulk"
        ]
        
        methods = ["GET", "POST", "PUT", "DELETE"]
        
        for endpoint in waste_endpoints:
            print(f"📍 {endpoint}")
            
            for method in methods:
                try:
                    if method == "GET":
                        response = requests.get(f"{self.api_base}{endpoint}", timeout=5)
                    elif method == "POST":
                        response = requests.post(f"{self.api_base}{endpoint}", json={}, timeout=5)
                    elif method == "PUT":
                        response = requests.put(f"{self.api_base}{endpoint}", json={}, timeout=5)
                    elif method == "DELETE":
                        response = requests.delete(f"{self.api_base}{endpoint}", timeout=5)
                    
                    print(f"   {method}: HTTP {response.status_code}")
                    
                except Exception as e:
                    print(f"   {method}: Error - {str(e)}")
            
            print()
    
    def test_environment_endpoint_detailed(self):
        """Test environment endpoint in detail"""
        print("🌍 TESTING ENVIRONMENT ENDPOINT (WASTE DATA SOURCE):")
        print()
        
        try:
            response = requests.get(f"{self.api_base}/environment", timeout=10)
            
            print(f"📍 /api/environment")
            print(f"   Status: HTTP {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   📊 Response type: {type(data)}")
                    
                    if isinstance(data, list):
                        print(f"   📋 Records count: {len(data)}")
                        if data:
                            first_record = data[0]
                            print(f"   🔍 First record keys: {list(first_record.keys())}")
                            
                            # Check for waste fields
                            waste_fields = [
                                "organic_waste", "plastic_waste", "glass_waste",
                                "paper_waste", "metal_waste", "electronic_waste",
                                "oil_waste", "mixed_waste"
                            ]
                            
                            found_waste_fields = [field for field in waste_fields if field in first_record]
                            print(f"   🗑️ Waste fields found: {found_waste_fields}")
                    
                    elif isinstance(data, dict):
                        print(f"   🔍 Response keys: {list(data.keys())}")
                        
                except json.JSONDecodeError:
                    print("   ❌ Invalid JSON response")
                    print(f"   📄 Raw response: {response.text[:200]}...")
            
            elif response.status_code in [401, 403]:
                print("   🔒 Authentication required (expected)")
            elif response.status_code == 404:
                print("   ❌ Endpoint not found")
            else:
                print(f"   ❓ Unexpected status: {response.status_code}")
                print(f"   📄 Response: {response.text[:200]}...")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        print()
    
    def run_investigation(self):
        """Run complete waste data investigation"""
        print("🚀 Starting Waste Data Investigation...")
        print()
        
        # Test all waste endpoints
        self.test_waste_endpoints_detailed()
        
        # Test environment endpoint in detail
        self.test_environment_endpoint_detailed()
        
        # Test different HTTP methods
        self.test_waste_data_endpoints_methods()
        
        # Test carbon footprint with sample clients
        self.test_carbon_footprint_with_sample_clients()
        
        print("=" * 80)
        print("🎯 WASTE DATA INVESTIGATION SUMMARY")
        print("=" * 80)
        print()
        print("🔍 KEY FINDINGS:")
        print("   1. Waste endpoints accessibility status")
        print("   2. Environment data collection status") 
        print("   3. Carbon footprint API response structure")
        print("   4. Sample client waste data availability")
        print()
        print("💡 RECOMMENDATIONS:")
        print("   - Check if waste_management collection has actual data")
        print("   - Verify DEFRA waste calculation is receiving data")
        print("   - Test with authenticated requests to get real data")
        print("   - Check backend logs for waste calculation messages")

def main():
    """Main investigation execution"""
    investigator = WasteDataInvestigator()
    investigator.run_investigation()

if __name__ == "__main__":
    main()