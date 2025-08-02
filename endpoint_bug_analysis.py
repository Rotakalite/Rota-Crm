#!/usr/bin/env python3
"""
CRITICAL BUG FOUND: Sustainability Report Endpoint Not Accessible
"""

import asyncio
import httpx
from datetime import datetime

async def test_endpoint_registration_issue():
    """Test to confirm the endpoint registration issue"""
    
    print("🚨 CRITICAL BUG ANALYSIS: Sustainability Report Endpoint")
    print("=" * 60)
    
    backend_url = "https://d787e851-4fbb-4d90-a594-90394e6ba15e.preview.emergentagent.com"
    
    # Test 1: Health endpoint (should work)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{backend_url}/api/health")
            if response.status_code == 200:
                print("✅ /api/health endpoint: WORKING (200 OK)")
            else:
                print(f"❌ /api/health endpoint: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ /api/health endpoint: ERROR - {e}")
    
    # Test 2: Comprehensive report endpoint (currently broken)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{backend_url}/api/reports/comprehensive")
            if response.status_code == 404:
                print("❌ /api/reports/comprehensive endpoint: NOT FOUND (404) - CRITICAL BUG!")
            elif response.status_code in [401, 403]:
                print("✅ /api/reports/comprehensive endpoint: ACCESSIBLE (requires auth)")
            else:
                print(f"⚠️  /api/reports/comprehensive endpoint: UNEXPECTED ({response.status_code})")
    except Exception as e:
        print(f"❌ /api/reports/comprehensive endpoint: ERROR - {e}")
    
    # Test 3: Other report endpoints
    report_endpoints = ["/api/reports/training", "/api/reports/consumption"]
    for endpoint in report_endpoints:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{backend_url}{endpoint}")
                if response.status_code == 404:
                    print(f"❌ {endpoint} endpoint: NOT FOUND (404) - Same issue!")
                elif response.status_code in [401, 403]:
                    print(f"✅ {endpoint} endpoint: ACCESSIBLE (requires auth)")
                else:
                    print(f"⚠️  {endpoint} endpoint: UNEXPECTED ({response.status_code})")
        except Exception as e:
            print(f"❌ {endpoint} endpoint: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print("🔍 ROOT CAUSE ANALYSIS:")
    print("=" * 60)
    print("❌ PROBLEM: All /api/reports/* endpoints return 404 Not Found")
    print("🔍 CAUSE: Endpoints defined with @app.get('/api/reports/...') instead of @api_router.get('/reports/...')")
    print("🛠️  SOLUTION: Change endpoint decorators from @app.get to @api_router.get and remove /api prefix")
    print("\n📋 AFFECTED ENDPOINTS:")
    print("   - /api/reports/comprehensive (Sustainability Report)")
    print("   - /api/reports/training (Training Report)")  
    print("   - /api/reports/consumption (Consumption Report)")
    print("\n🚨 IMPACT: Users cannot generate any PDF reports!")
    print("⚡ PRIORITY: CRITICAL - Core functionality broken")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_endpoint_registration_issue())