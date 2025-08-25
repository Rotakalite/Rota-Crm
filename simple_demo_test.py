#!/usr/bin/env python3
"""
Simple Demo System Test - Direct Database Check
"""

import asyncio
import aiohttp
import json
import uuid
from datetime import datetime

class SimpleDemoTest:
    def __init__(self):
        self.base_url = "https://survey-module.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        
    async def test_basic_endpoints(self):
        """Test basic endpoint accessibility"""
        print("🔍 TESTING BASIC ENDPOINTS")
        print("=" * 50)
        
        endpoints = [
            ("GET", "/health", "Health Check"),
            ("POST", "/auth/self-signup", "Self-Signup"),
            ("GET", "/admin/pending-approvals", "Admin Pending Approvals"),
            ("POST", "/admin/approve-user/test", "Admin Approve User"),
            ("GET", "/clients", "Clients"),
            ("GET", "/users", "Users"),
            ("GET", "/documents", "Documents")
        ]
        
        async with aiohttp.ClientSession() as session:
            for method, endpoint, name in endpoints:
                try:
                    url = f"{self.api_url}{endpoint}"
                    
                    if method == "GET":
                        async with session.get(url) as response:
                            status = response.status
                            try:
                                data = await response.json()
                            except:
                                data = await response.text()
                    else:  # POST
                        test_data = {"test": "data"}
                        async with session.post(url, json=test_data) as response:
                            status = response.status
                            try:
                                data = await response.json()
                            except:
                                data = await response.text()
                    
                    print(f"📍 {name}: {method} {endpoint} -> Status: {status}")
                    if status == 404:
                        print(f"   ❌ Endpoint not found")
                    elif status == 405:
                        print(f"   ⚠️ Method not allowed")
                    elif status in [401, 403]:
                        print(f"   🔒 Authentication required")
                    elif status == 200:
                        print(f"   ✅ Working")
                    else:
                        print(f"   ℹ️ Status: {status}")
                        
                except Exception as e:
                    print(f"📍 {name}: ERROR - {str(e)}")
                
                print()
    
    async def test_route_registration(self):
        """Test if routes are properly registered"""
        print("🛣️ TESTING ROUTE REGISTRATION")
        print("=" * 50)
        
        # Test if we can get route information
        try:
            async with aiohttp.ClientSession() as session:
                # Test a known working endpoint
                async with session.get(f"{self.api_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Health endpoint working: {data.get('service', 'Unknown')}")
                        print(f"   API Router Mounted: {data.get('api_router_mounted', 'Unknown')}")
                    else:
                        print(f"❌ Health endpoint failed: {response.status}")
                
                # Test the problematic self-signup endpoint with different methods
                methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
                for method in methods:
                    try:
                        if method == "GET":
                            async with session.get(f"{self.api_url}/auth/self-signup") as response:
                                status = response.status
                        elif method == "POST":
                            async with session.post(f"{self.api_url}/auth/self-signup", json={}) as response:
                                status = response.status
                        elif method == "PUT":
                            async with session.put(f"{self.api_url}/auth/self-signup", json={}) as response:
                                status = response.status
                        elif method == "DELETE":
                            async with session.delete(f"{self.api_url}/auth/self-signup") as response:
                                status = response.status
                        elif method == "OPTIONS":
                            async with session.options(f"{self.api_url}/auth/self-signup") as response:
                                status = response.status
                        
                        print(f"   {method} /auth/self-signup -> {status}")
                        
                    except Exception as e:
                        print(f"   {method} /auth/self-signup -> ERROR: {str(e)}")
                        
        except Exception as e:
            print(f"❌ Route registration test failed: {str(e)}")
    
    async def run_tests(self):
        """Run all tests"""
        print("🚀 SIMPLE DEMO SYSTEM TEST")
        print("🎯 Testing against:", self.base_url)
        print("=" * 80)
        
        await self.test_basic_endpoints()
        await self.test_route_registration()
        
        print("=" * 80)
        print("✅ Test completed!")

async def main():
    tester = SimpleDemoTest()
    await tester.run_tests()

if __name__ == "__main__":
    asyncio.run(main())