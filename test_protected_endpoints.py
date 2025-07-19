"""
Test protected endpoints with valid JWT token
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_protected_endpoints():
    print("Testing protected endpoints with auth token...")
    
    # First login to get a token
    login_data = {
        "email": "newuser@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔐 Testing with valid token:")
    
    # Test protected endpoints
    endpoints = [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/podcasts"),
        ("GET", "/api/v1/episodes"),
        ("GET", "/api/v1/templates"),
        ("GET", "/api/v1/jobs"),
    ]
    
    for method, endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            print(f"{method} {endpoint}: {response.status_code}")
            if response.status_code not in [200, 201]:
                print(f"  Response: {response.text[:200]}...")
        except Exception as e:
            print(f"{method} {endpoint}: ERROR - {str(e)}")
    
    print("\n✅ Protected endpoints test complete!")

if __name__ == "__main__":
    test_protected_endpoints()
