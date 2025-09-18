#!/usr/bin/env python3
"""
Test script to check if available-rooms endpoint is registered
"""

import sys
import os
sys.path.append('/app/backend')

try:
    from server import app, api_router
    
    print("🔍 Checking registered routes...")
    print("=" * 50)
    
    # Check API router routes
    print("📋 API Router Routes:")
    for route in api_router.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"  {list(route.methods)[0] if route.methods else 'N/A'} {route.path}")
            if 'available-rooms' in route.path:
                print(f"    ✅ FOUND: available-rooms endpoint!")
    
    print("\n📋 App Routes:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"  {list(route.methods)[0] if route.methods else 'N/A'} {route.path}")
            if 'available-rooms' in route.path:
                print(f"    ✅ FOUND: available-rooms endpoint in app!")
    
    # Check if the route exists in the full path
    print("\n🔍 Searching for available-rooms in all routes...")
    found = False
    for route in app.routes:
        if hasattr(route, 'path'):
            if 'available-rooms' in route.path:
                print(f"✅ Found available-rooms route: {route.path}")
                found = True
        # Check if it's a mounted router
        if hasattr(route, 'app') and hasattr(route.app, 'routes'):
            for subroute in route.app.routes:
                if hasattr(subroute, 'path') and 'available-rooms' in subroute.path:
                    print(f"✅ Found available-rooms in mounted router: {route.path}{subroute.path}")
                    found = True
    
    if not found:
        print("❌ available-rooms endpoint not found in registered routes!")
        
        # Let's check what front-office routes exist
        print("\n🏨 Front Office routes found:")
        for route in api_router.routes:
            if hasattr(route, 'path') and 'front-office' in route.path:
                print(f"  ✅ {list(route.methods)[0] if route.methods else 'N/A'} {route.path}")
    
except Exception as e:
    print(f"❌ Error checking routes: {e}")
    import traceback
    traceback.print_exc()