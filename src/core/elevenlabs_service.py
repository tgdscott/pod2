"""
ElevenLabs Integration Service
Handles AI voice generation and text-to-speech functionality
"""

import os
import requests
import json
from typing import Dict, List, Optional
from pathlib import Path
import uuid
from datetime import datetime

class ElevenLabsService:
    """Service for interacting with ElevenLabs API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required")
    
    def get_voices(self) -> List[Dict]:
        """Get available voices from ElevenLabs"""
        try:
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key
            }
            
            response = requests.get(f"{self.base_url}/voices", headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get('voices', [])
            
        except Exception as e:
            print(f"Error getting voices: {str(e)}")
            return []
    
    def get_voice(self, voice_id: str) -> Optional[Dict]:
        """Get specific voice details"""
        try:
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key
            }
            
            response = requests.get(f"{self.base_url}/voices/{voice_id}", headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Error getting voice {voice_id}: {str(e)}")
            return None
    
    def text_to_speech(self, 
                      text: str, 
                      voice_id: str, 
                      output_path: str,
                      stability: float = 0.5,
                      similarity_boost: float = 0.75,
                      style: float = 0.0,
                      use_speaker_boost: bool = True) -> Optional[str]:
        """
        Convert text to speech using ElevenLabs
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            output_path: Path to save the audio file
            stability: Voice stability (0-1)
            similarity_boost: Voice similarity boost (0-1)
            style: Voice style (0-1)
            use_speaker_boost: Whether to use speaker boost
            
        Returns:
            Path to generated audio file or None if failed
        """
        try:
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": style,
                    "use_speaker_boost": use_speaker_boost
                }
            }
            
            response = requests.post(
                f"{self.base_url}/text-to-speech/{voice_id}",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            # Save audio file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return output_path
            
        except Exception as e:
            print(f"Error in text-to-speech: {str(e)}")
            return None
    
    def text_to_speech_stream(self, 
                            text: str, 
                            voice_id: str,
                            stability: float = 0.5,
                            similarity_boost: float = 0.75,
                            style: float = 0.0,
                            use_speaker_boost: bool = True) -> Optional[bytes]:
        """
        Convert text to speech and return audio data as bytes
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            stability: Voice stability (0-1)
            similarity_boost: Voice similarity boost (0-1)
            style: Voice style (0-1)
            use_speaker_boost: Whether to use speaker boost
            
        Returns:
            Audio data as bytes or None if failed
        """
        try:
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": style,
                    "use_speaker_boost": use_speaker_boost
                }
            }
            
            response = requests.post(
                f"{self.base_url}/text-to-speech/{voice_id}",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            print(f"Error in text-to-speech stream: {str(e)}")
            return None
    
    def clone_voice(self, 
                   name: str, 
                   description: str, 
                   files: List[str]) -> Optional[str]:
        """
        Clone a voice using audio files
        
        Args:
            name: Name for the cloned voice
            description: Description of the voice
            files: List of audio file paths
            
        Returns:
            Voice ID of the cloned voice or None if failed
        """
        try:
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "name": name,
                "description": description
            }
            
            files_data = []
            for file_path in files:
                with open(file_path, 'rb') as f:
                    files_data.append(('files', (os.path.basename(file_path), f, 'audio/mpeg')))
            
            response = requests.post(
                f"{self.base_url}/voices/add",
                headers=headers,
                data=data,
                files=files_data
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('voice_id')
            
        except Exception as e:
            print(f"Error cloning voice: {str(e)}")
            return None
    
    def delete_voice(self, voice_id: str) -> bool:
        """Delete a cloned voice"""
        try:
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key
            }
            
            response = requests.delete(f"{self.base_url}/voices/{voice_id}", headers=headers)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            print(f"Error deleting voice {voice_id}: {str(e)}")
            return False
    
    def get_usage(self) -> Optional[Dict]:
        """Get API usage information"""
        try:
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key
            }
            
            response = requests.get(f"{self.base_url}/user/subscription", headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Error getting usage: {str(e)}")
            return None
    
    def generate_episode_segment(self, 
                               prompt: str, 
                               voice_id: str, 
                               output_dir: str,
                               segment_name: str = None,
                               stability: float = 0.5) -> Optional[str]:
        """
        Generate an episode segment using AI voice
        
        Args:
            prompt: Text prompt for the segment
            voice_id: ElevenLabs voice ID
            output_dir: Directory to save the audio file
            segment_name: Name for the segment file
            stability: Voice stability setting
            
        Returns:
            Path to generated audio file or None if failed
        """
        try:
            if not segment_name:
                segment_name = f"segment_{uuid.uuid4().hex[:8]}"
            
            output_path = Path(output_dir) / f"{segment_name}.mp3"
            
            # Generate the audio
            result = self.text_to_speech(
                text=prompt,
                voice_id=voice_id,
                output_path=str(output_path),
                stability=stability
            )
            
            return result
            
        except Exception as e:
            print(f"Error generating episode segment: {str(e)}")
            return None
    
    def process_template_segments(self, 
                                template_data: Dict, 
                                output_dir: str) -> List[Dict]:
        """
        Process AI segments from a template
        
        Args:
            template_data: Template data with AI segments
            output_dir: Directory to save generated audio files
            
        Returns:
            List of generated segment information
        """
        try:
            generated_segments = []
            
            if 'ai_segments' not in template_data:
                return generated_segments
            
            ai_config = template_data['ai_segments']
            voice_id = ai_config.get('voice_model')
            stability = float(ai_config.get('stability', 0.5))
            prompts = ai_config.get('prompts', [])
            
            if not voice_id or not prompts:
                return generated_segments
            
            # Create output directory
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Generate audio for each prompt
            for i, prompt in enumerate(prompts):
                if not prompt.strip():
                    continue
                
                segment_name = f"ai_segment_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                audio_path = self.generate_episode_segment(
                    prompt=prompt,
                    voice_id=voice_id,
                    output_dir=output_dir,
                    segment_name=segment_name,
                    stability=stability
                )
                
                if audio_path:
                    generated_segments.append({
                        'prompt': prompt,
                        'audio_path': audio_path,
                        'segment_name': segment_name,
                        'voice_id': voice_id,
                        'stability': stability
                    })
            
            return generated_segments
            
        except Exception as e:
            print(f"Error processing template segments: {str(e)}")
            return []


# Default voice models for quick access
DEFAULT_VOICES = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",
    "domi": "AZnzlk1XvdvUeBnXmlld", 
    "bella": "EXAVITQu4vr4xnSDxMaL",
    "josh": "21j0vfeTClDxlSDvGRl",
    "arnold": "VR6AewLTigWG4xSOukaG",
    "sam": "yoZ06aMxZJJ28mfd3POQ"
} 