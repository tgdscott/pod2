#!/usr/bin/env python3
"""
Quick 500 Error Debug Test
Uses working credentials to test the specific 500 errors
"""

import requests
import tempfile
import json
from datetime import datetime

API_BASE_URL = 'http://localhost:5000/api'

def test_500_errors():
    print("🔧 QUICK 500 ERROR DEBUG")
    print("=" * 50)
    
    # Step 1: Get auth token with working credentials
    print("\n1. Getting auth token...")
    
    # Try to register a new user first
    register_data = {
        "email": f"test500_{datetime.now().strftime('%H%M%S')}@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            data = response.json()
            token = data['access_token']
            print("✅ Registration successful")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Step 2: Test podcast creation with detailed error info
    print("\n2. Testing podcast creation...")
    
    podcast_data = {
        "name": "Test Debug Podcast",
        "description": "A test podcast for debugging 500 errors",
        "author": "Test User",
        "category": "Technology",
        "language": "en"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/podcasts", json=podcast_data, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text}")
        
        if response.status_code == 500:
            print("❌ Podcast creation has 500 error")
        elif response.status_code == 201:
            print("✅ Podcast creation working!")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request error: {e}")
    
    # Step 3: Test file upload with detailed error info
    print("\n3. Testing file upload...")
    
    # Create a small test audio file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # Write minimal WAV header and some data
        wav_data = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
        f.write(wav_data)
        test_file_path = f.name
    
    try:
        with open(test_file_path, 'rb') as audio_file:
            files = {'file': ('test.wav', audio_file, 'audio/wav')}
            data = {'type': 'audio'}
            
            response = requests.post(f"{API_BASE_URL}/files/upload", 
                                   files=files, 
                                   data=data,
                                   headers={'Authorization': f'Bearer {token}'})
            
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Response: {response.text}")
            
            if response.status_code == 500:
                print("❌ File upload has 500 error")
            elif response.status_code == 201:
                print("✅ File upload working!")
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Request error: {e}")
    
    print("\n" + "=" * 50)
    print("🔧 Quick debug complete!")

if __name__ == "__main__":
    test_500_errors()
