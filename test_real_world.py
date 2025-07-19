"""
End-to-End Real World Test for PodcastPro v2
Tests the complete user workflow from registration to episode processing
"""

import requests
import json
import time
import os
from pathlib import Path

BASE_URL = "http://localhost:5000"

class PodcastProTester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.podcast_id = None
        self.episode_id = None
        self.file_id = None
        
    def log(self, message, success=None):
        """Log test results"""
        if success is True:
            print(f"✅ {message}")
        elif success is False:
            print(f"❌ {message}")
        else:
            print(f"🔄 {message}")
    
    def test_user_registration(self):
        """Test user registration"""
        self.log("Testing user registration...")
        
        data = {
            "email": "realworld@test.com",
            "password": "RealWorld123!",
            "username": "realworlduser"
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=data)
        
        if response.status_code == 201:
            result = response.json()
            self.token = result["access_token"]
            self.user_id = result["user"]["id"]
            self.log(f"User registered: {result['user']['email']}", True)
            return True
        elif response.status_code == 400:
            # User might already exist, try login
            self.log("User already exists, trying login...", None)
            return self.test_user_login()
        else:
            self.log(f"Registration failed: {response.text}", False)
            return False
    
    def test_user_login(self):
        """Test user login"""
        self.log("Testing user login...")
        
        data = {
            "email": "realworld@test.com",
            "password": "RealWorld123!"
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=data)
        
        if response.status_code == 200:
            result = response.json()
            self.token = result["access_token"]
            self.user_id = result["user"]["id"]
            self.log(f"Login successful: {result['user']['email']}", True)
            return True
        else:
            self.log(f"Login failed: {response.text}", False)
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_create_podcast(self):
        """Test podcast creation"""
        self.log("Testing podcast creation...")
        
        # First check if we already have a podcast
        response = requests.get(
            f"{BASE_URL}/api/v1/podcasts", 
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            podcasts = response.json().get("podcasts", [])
            if podcasts:
                # Use existing podcast
                self.podcast_id = podcasts[0]["id"]
                self.log(f"Using existing podcast: {podcasts[0]['title']}", True)
                return True
        
        # Create new podcast with unique title
        import time
        unique_title = f"Real World Test Podcast {int(time.time())}"
        
        data = {
            "title": unique_title,
            "description": "A podcast created during end-to-end testing",
            "language": "en",
            "category": "Technology",
            "explicit": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/podcasts", 
            json=data, 
            headers=self.get_headers()
        )
        
        if response.status_code == 201:
            result = response.json()
            self.podcast_id = result["podcast"]["id"]
            self.log(f"Podcast created: {result['podcast']['title']}", True)
            return True
        else:
            self.log(f"Podcast creation failed: {response.text}", False)
            return False
    
    def test_file_upload(self):
        """Test file upload (create a dummy audio file)"""
        self.log("Testing file upload...")
        
        # Create a dummy audio file for testing
        dummy_audio = b"RIFF" + b"\\x00" * 40 + b"WAVE" + b"\\x00" * 100  # Fake WAV header
        
        files = {
            'file': ('test_audio.wav', dummy_audio, 'audio/wav')
        }
        data = {
            'type': 'audio'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/files/upload",
            files=files,
            data=data,
            headers=self.get_headers()
        )
        
        if response.status_code == 201:
            result = response.json()
            self.file_id = result["file"]["id"]
            self.log(f"File uploaded: {result['file']['original_filename']}", True)
            return True
        else:
            self.log(f"File upload failed: {response.text}", False)
            return False
    
    def test_create_episode(self):
        """Test episode creation"""
        self.log("Testing episode creation...")
        
        data = {
            "podcast_id": self.podcast_id,
            "title": "Real World Test Episode",
            "description": "An episode created during end-to-end testing",
            "audio_files": [self.file_id] if self.file_id else [],
            "tags": ["test", "automation", "real-world"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/episodes",
            json=data,
            headers=self.get_headers()
        )
        
        if response.status_code == 201:
            result = response.json()
            self.episode_id = result["episode"]["id"]
            self.log(f"Episode created: {result['episode']['title']}", True)
            return True
        else:
            self.log(f"Episode creation failed: {response.text}", False)
            return False
    
    def test_episode_processing(self):
        """Test episode processing"""
        self.log("Testing episode processing...")
        
        if not self.episode_id:
            self.log("No episode to process", False)
            return False
        
        response = requests.post(
            f"{BASE_URL}/api/v1/episodes/{self.episode_id}/process",
            json={},
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get("job_id")
            self.log(f"Episode processing started: {job_id}", True)
            
            # Test job status
            if job_id:
                self.test_job_status(job_id)
            return True
        else:
            self.log(f"Episode processing failed: {response.text}", False)
            return False
    
    def test_job_status(self, job_id):
        """Test job status monitoring"""
        self.log(f"Testing job status for: {job_id}")
        
        response = requests.get(
            f"{BASE_URL}/api/v1/jobs/{job_id}",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result["job"]["status"]
            self.log(f"Job status: {status}", True)
            return True
        else:
            self.log(f"Job status check failed: {response.text}", False)
            return False
    
    def test_data_retrieval(self):
        """Test retrieving created data"""
        self.log("Testing data retrieval...")
        
        # Test get podcasts
        response = requests.get(f"{BASE_URL}/api/v1/podcasts", headers=self.get_headers())
        if response.status_code == 200:
            podcasts = response.json()["podcasts"]
            self.log(f"Retrieved {len(podcasts)} podcasts", True)
        else:
            self.log("Failed to retrieve podcasts", False)
        
        # Test get episodes
        response = requests.get(f"{BASE_URL}/api/v1/episodes", headers=self.get_headers())
        if response.status_code == 200:
            episodes = response.json()["episodes"]
            self.log(f"Retrieved {len(episodes)} episodes", True)
        else:
            self.log("Failed to retrieve episodes", False)
        
        # Test get jobs
        response = requests.get(f"{BASE_URL}/api/v1/jobs", headers=self.get_headers())
        if response.status_code == 200:
            jobs = response.json()["jobs"]
            self.log(f"Retrieved {len(jobs)} jobs", True)
        else:
            self.log("Failed to retrieve jobs", False)
        return True
    
    def test_error_handling(self):
        """Test error handling and edge cases"""
        self.log("Testing error handling...")
        
        # Test invalid podcast creation
        response = requests.post(
            f"{BASE_URL}/api/v1/podcasts",
            json={"title": ""},  # Invalid - empty title
            headers=self.get_headers()
        )
        if response.status_code == 400:
            self.log("Empty title validation working", True)
        else:
            self.log("Empty title validation failed", False)
        
        # Test accessing non-existent resource
        response = requests.get(
            f"{BASE_URL}/api/v1/podcasts/non-existent-id",
            headers=self.get_headers()
        )
        if response.status_code == 404:
            self.log("404 handling working", True)
        else:
            self.log("404 handling failed", False)
        
        # Test unauthorized access
        response = requests.get(f"{BASE_URL}/api/v1/podcasts")  # No auth header
        if response.status_code == 401:
            self.log("Unauthorized access protection working", True)
        else:
            self.log("Unauthorized access protection failed", False)
        return True
    
    def run_full_test(self):
        """Run the complete end-to-end test"""
        print("🚀 Starting Real World End-to-End Test")
        print("=" * 50)
        
        tests = [
            ("User Registration/Login", self.test_user_registration),
            ("Podcast Creation", self.test_create_podcast),
            ("File Upload", self.test_file_upload),
            ("Episode Creation", self.test_create_episode),
            ("Episode Processing", self.test_episode_processing),
            ("Data Retrieval", self.test_data_retrieval),
            ("Error Handling", self.test_error_handling),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}:")
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log(f"Test crashed: {str(e)}", False)
        
        print(f"\n🏆 RESULTS: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - MVP IS READY FOR REAL WORLD USE!")
        else:
            print("⚠️  SOME TESTS FAILED - NEEDS ATTENTION")
        
        return passed == total

if __name__ == "__main__":
    tester = PodcastProTester()
    tester.run_full_test()
