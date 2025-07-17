#!/usr/bin/env python3
"""
Minimal 500 Error Isolation Test
Tests the exact endpoints that are failing with minimal data
"""

import requests
import json
from datetime import datetime

API_BASE_URL = 'http://localhost:5000/api'

def minimal_test():
    print("🔧 MINIMAL 500 ERROR ISOLATION")
    print("=" * 50)
    
    # Get auth token
    print("\n1. Getting auth token...")
    
    register_data = {
        "email": f"minimal_{datetime.now().strftime('%H%M%S')}@test.com",
        "password": "password123",
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/register", json=register_data, timeout=10)
        if response.status_code != 201:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
            return
        
        token = response.json()['access_token']
        print("✅ Got auth token")
        
    except Exception as e:
        print(f"❌ Auth error: {e}")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test minimal podcast creation
    print("\n2. Testing minimal podcast creation...")
    
    minimal_podcast = {
        "name": "Test Podcast"
    }
    
    try:
        print(f"🔍 Sending: {json.dumps(minimal_podcast, indent=2)}")
        response = requests.post(f"{API_BASE_URL}/podcasts", 
                               json=minimal_podcast, 
                               headers=headers, 
                               timeout=10)
        
        print(f"Status: {response.status_code}")
        if response.status_code != 201:
            print(f"Response: {response.text}")
            
            # Try with more fields
            print("\n🔍 Trying with required fields...")
            full_podcast = {
                "name": "Test Podcast",
                "description": "Test description",
                "author": "Test Author",
                "category": "Technology"
            }
            response2 = requests.post(f"{API_BASE_URL}/podcasts", 
                                    json=full_podcast, 
                                    headers=headers, 
                                    timeout=10)
            print(f"Full data status: {response2.status_code}")
            print(f"Full data response: {response2.text}")
        else:
            print("✅ Podcast creation successful!")
            
    except Exception as e:
        print(f"❌ Podcast creation error: {e}")
    
    # Test user info endpoint (should work)
    print("\n3. Testing user info endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/auth/me", headers=headers, timeout=10)
        print(f"User info status: {response.status_code}")
        if response.status_code == 200:
            print("✅ User info working")
        else:
            print(f"❌ User info failed: {response.text}")
    except Exception as e:
        print(f"❌ User info error: {e}")
    
    print("\n" + "=" * 50)
    print("🔧 Minimal test complete!")

if __name__ == "__main__":
    minimal_test()
