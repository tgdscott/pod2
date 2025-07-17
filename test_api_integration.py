"""
Test API Integration with Audio Processing
Tests the complete workflow from file upload to episode processing
"""

import os
import requests
import json
from pathlib import Path
import tempfile
import wave
import numpy as np

# Test configuration
API_BASE = "http://localhost:5000/api"

def get_test_user():
    """Get a unique test user for this run"""
    import time
    timestamp = int(time.time())
    return {
        "email": f"test{timestamp}@example.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User"
    }

def create_test_audio_file():
    """Create a simple test audio file"""
    # Create a simple sine wave audio file for testing
    sample_rate = 44100
    duration = 5  # 5 seconds
    frequency = 440  # A4 note
    
    # Generate sine wave
    t = np.linspace(0, duration, sample_rate * duration, False)
    audio_data = np.sin(2 * np.pi * frequency * t)
    
    # Convert to 16-bit integers
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Create temporary WAV file
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    
    with wave.open(temp_file.name, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    return temp_file.name

def test_workflow():
    """Test the complete workflow"""
    print("🎙️ Testing PodcastPro API Integration")
    print("=" * 50)
    
    # Get unique test user
    TEST_USER = get_test_user()
    
    # Step 1: Register user
    print("1. Registering test user...")
    register_response = requests.post(f"{API_BASE}/auth/register", json=TEST_USER)
    
    if register_response.status_code != 201:
        print(f"⚠️ Registration failed: {register_response.json()}")
        print("   Trying to login with known test user...")
        
        # Try with known credentials
        test_login = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        login_response = requests.post(f"{API_BASE}/auth/login", json=test_login)
        
        if login_response.status_code != 200:
            print(f"❌ Login also failed: {login_response.json()}")
            return False
            
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Logged in with existing user")
    else:
        print("✅ User registered successfully")
        
        # Step 2: Login with new user
        print("\n2. Logging in...")
        login_response = requests.post(f"{API_BASE}/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.json()}")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful")
    
    # Step 3: Create a podcast
    print("\n3. Creating test podcast...")
    podcast_data = {
        "name": "Test Podcast",
        "description": "A test podcast for API integration",
        "author": "Test User",
        "category": "Technology"
    }
    
    podcast_response = requests.post(f"{API_BASE}/podcasts", json=podcast_data, headers=headers)
    
    if podcast_response.status_code != 201:
        print(f"❌ Podcast creation failed: {podcast_response.json()}")
        return False
    
    podcast_id = podcast_response.json()["podcast"]["id"]
    print("✅ Podcast created successfully")
    
    # Step 4: Create test audio file
    print("\n4. Creating test audio file...")
    audio_file_path = create_test_audio_file()
    print(f"✅ Test audio file created: {audio_file_path}")
    
    # Step 5: Upload audio file
    print("\n5. Uploading audio file...")
    try:
        with open(audio_file_path, 'rb') as audio_file:
            files = {'file': audio_file}
            data = {'type': 'audio'}
            upload_response = requests.post(f"{API_BASE}/files/upload", 
                                          files=files, data=data, headers=headers)
        
        if upload_response.status_code != 201:
            print(f"❌ File upload failed: {upload_response.json()}")
            return False
        
        file_id = upload_response.json()["file"]["id"]
        print("✅ Audio file uploaded successfully")
        
    finally:
        # Clean up test file
        os.unlink(audio_file_path)
    
    # Step 6: Create episode
    print("\n6. Creating episode...")
    episode_data = {
        "title": "Test Episode 1",
        "description": "A test episode for API integration",
        "podcast_id": podcast_id,
        "audio_files": [file_id]
    }
    
    episode_response = requests.post(f"{API_BASE}/episodes", json=episode_data, headers=headers)
    
    if episode_response.status_code != 201:
        print(f"❌ Episode creation failed: {episode_response.json()}")
        return False
    
    episode_id = episode_response.json()["episode"]["id"]
    print("✅ Episode created successfully")
    
    # Step 7: Process episode
    print("\n7. Starting episode processing...")
    process_response = requests.post(f"{API_BASE}/episodes/{episode_id}/process", 
                                   json={}, headers=headers)
    
    if process_response.status_code != 200:
        print(f"❌ Episode processing failed: {process_response.json()}")
        return False
    
    job_id = process_response.json()["job_id"]
    print("✅ Episode processing started")
    
    # Step 8: Check job status
    print("\n8. Checking job status...")
    status_response = requests.get(f"{API_BASE}/jobs/{job_id}/status", headers=headers)
    
    if status_response.status_code == 200:
        job = status_response.json()["job"]
        print(f"✅ Job status: {job['status']}")
        if job.get('error_message'):
            print(f"⚠️ Error: {job['error_message']}")
    else:
        print(f"❌ Failed to get job status: {status_response.json()}")
        return False
    
    # Step 9: Check episode status
    print("\n9. Checking final episode status...")
    episode_status_response = requests.get(f"{API_BASE}/episodes/{episode_id}", headers=headers)
    
    if episode_status_response.status_code == 200:
        episode = episode_status_response.json()["episode"]
        print(f"✅ Episode status: {episode['status']}")
        if episode.get('output_file'):
            print(f"✅ Output file: {episode['output_file']}")
        if episode.get('show_notes'):
            print(f"✅ Show notes generated: {len(episode['show_notes'])} characters")
    else:
        print(f"❌ Failed to get episode status: {episode_status_response.json()}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 API Integration test completed successfully!")
    return True

if __name__ == "__main__":
    try:
        success = test_workflow()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        exit(1)
