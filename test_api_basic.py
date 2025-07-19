"""
Quick API Test Script
Tests all the major endpoints to ensure they're working
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_endpoint(method, endpoint, data=None, headers=None, expected_status=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        
        print(f"{method} {endpoint}: {response.status_code}")
        
        if response.status_code != 200 and response.status_code != 201:
            print(f"  Response: {response.text}")
        
        return response
    
    except Exception as e:
        print(f"{method} {endpoint}: ERROR - {str(e)}")
        return None

def main():
    print("🎙️ Testing PodcastPro v2 API Endpoints")
    print("=" * 50)
    
    # Test basic connectivity
    print("\n1. Basic Connectivity:")
    test_endpoint("GET", "/")
    test_endpoint("GET", "/api/v1/health")
    
    # Test auth endpoints (should require data)
    print("\n2. Auth Endpoints:")
    test_endpoint("POST", "/api/v1/auth/register")  # Should fail - no data
    test_endpoint("POST", "/api/v1/auth/login")     # Should fail - no data
    
    # Test protected endpoints (should require auth)
    print("\n3. Protected Endpoints (should require auth):")
    test_endpoint("GET", "/api/v1/podcasts")
    test_endpoint("GET", "/api/v1/episodes")
    test_endpoint("GET", "/api/v1/templates")
    test_endpoint("GET", "/api/v1/jobs")
    test_endpoint("GET", "/api/v1/files")
    
    print("\n✅ Basic API connectivity test complete!")
    print("If you see mostly 401 (Unauthorized) errors above, that's good - it means auth is working.")
    print("If you see 404 or 500 errors, we need to investigate further.")

if __name__ == "__main__":
    main()
