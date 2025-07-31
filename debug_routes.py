#!/usr/bin/env python3
"""
Debug script to check FastAPI routes registration
"""

import sys
sys.path.append('/app/backend')

import server

def check_routes():
    print("=== FASTAPI APP ROUTES ===")
    app_routes = []
    for route in server.app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            app_routes.append({
                'path': route.path,
                'methods': list(route.methods) if route.methods else [],
                'name': getattr(route, 'name', 'unknown')
            })
    
    print(f"Total app routes: {len(app_routes)}")
    
    # Look for report routes
    report_routes = [r for r in app_routes if 'report' in r['path']]
    print(f"\nReport routes in main app: {len(report_routes)}")
    for route in report_routes:
        print(f"  {route['path']} - {route['methods']}")
    
    print("\n=== API ROUTER ROUTES ===")
    api_routes = []
    for route in server.api_router.routes:
        if hasattr(route, 'path'):
            api_routes.append({
                'path': route.path,
                'methods': list(route.methods) if hasattr(route, 'methods') and route.methods else [],
                'name': getattr(route, 'name', 'unknown')
            })
    
    print(f"Total API router routes: {len(api_routes)}")
    
    # Look for report routes
    api_report_routes = [r for r in api_routes if 'report' in r['path']]
    print(f"\nReport routes in API router: {len(api_report_routes)}")
    for route in api_report_routes:
        print(f"  {route['path']} - {route['methods']}")
    
    # Check if API router is mounted
    print(f"\n=== ROUTER MOUNTING CHECK ===")
    mounted_routes = [r for r in app_routes if r['path'].startswith('/api/')]
    print(f"Routes with /api/ prefix in main app: {len(mounted_routes)}")
    
    # Look for the specific report routes we expect
    expected_routes = [
        '/api/reports/comprehensive',
        '/api/reports/training', 
        '/api/reports/consumption',
        '/api/test-reports'
    ]
    
    print(f"\n=== EXPECTED ROUTES CHECK ===")
    for expected in expected_routes:
        found_in_app = any(r['path'] == expected for r in app_routes)
        found_in_api = any(r['path'] == expected.replace('/api', '') for r in api_routes)
        print(f"  {expected}: App={found_in_app}, API Router={found_in_api}")

if __name__ == "__main__":
    check_routes()