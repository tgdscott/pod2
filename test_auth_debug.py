"""
Test auth endpoints with proper data to see the actual errors
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_auth():
    print("Testing auth endpoints with data...")
    
    # Test user registration
    register_data = {
        "email": "newuser@example.com",
        "password": "password123",
        "username": "newuser"
    }
    
    print("\n1. Testing registration:")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test user login
    login_data = {
        "email": "newuser@example.com",
        "password": "password123"
    }
    
    print("\n2. Testing login:")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_auth()
