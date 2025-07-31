#!/usr/bin/env python3
"""
Minimal test to check if API router mounting works
"""

from fastapi import FastAPI, APIRouter
import uvicorn

app = FastAPI()
api_router = APIRouter()

@api_router.get("/test")
async def test_endpoint():
    return {"message": "API router test working"}

@app.get("/direct-test")
async def direct_test():
    return {"message": "Direct app test working"}

app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    print("Starting minimal test server...")
    print("Test endpoints:")
    print("  http://localhost:8002/direct-test")
    print("  http://localhost:8002/api/test")
    uvicorn.run(app, host="0.0.0.0", port=8002)