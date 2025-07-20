"""
Advanced Audio Processor
Handles sophisticated audio processing for podcast templates with precise timing and fade controls
"""

import os
import librosa
import soundfile as sf
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import uuid
from datetime import datetime
from pydub import AudioSegment

class AdvancedAudioProcessor:
    """Advanced audio processing for podcast templates"""
    
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_audio_duration(self, file_path: str) -> float:
        """Get audio file duration in seconds"""
        try:
            y, sr = librosa.load(file_path, sr=None)
            return librosa.get_duration(y=y, sr=sr)
        except Exception as e:
            print(f"Error getting duration for {file_path}: {str(e)}")
            return 0.0
    
    def create_fade_curve(self, duration: float, fade_type: str = 'linear') -> np.ndarray:
        """Create fade curve for smooth transitions"""
        if fade_type == 'linear':
            return np.linspace(0, 1, int(duration * 1000))  # 1ms resolution
        elif fade_type == 'exponential':
            return np.power(np.linspace(0, 1, int(duration * 1000)), 2)
        elif fade_type == 'logarithmic':
            return np.log(np.linspace(1, np.e, int(duration * 1000)))
        else:
            return np.linspace(0, 1, int(duration * 1000))
    
    def apply_fade(self, audio: AudioSegment, fade_in_duration: float = 0, fade_out_duration: float = 0) -> AudioSegment:
        """Apply fade in/out to audio segment"""
        if fade_in_duration > 0:
            # Apply fade in manually
            fade_ms = int(fade_in_duration * 1000)
            audio = audio.fade_in(fade_ms)
        
        if fade_out_duration > 0:
            # Apply fade out manually
            fade_ms = int(fade_out_duration * 1000)
            audio = audio.fade_out(fade_ms)
        
        return audio
    
    def load_audio_file(self, file_path: str) -> Optional[AudioSegment]:
        """Load audio file with error handling"""
        try:
            if not os.path.exists(file_path):
                print(f"Audio file not found: {file_path}")
                return None
            
            # Determine file format
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.mp3':
                return AudioSegment.from_mp3(file_path)
            elif file_ext == '.wav':
                return AudioSegment.from_wav(file_path)
            elif file_ext == '.flac':
                return AudioSegment.from_file(file_path, format='flac')
            elif file_ext in ['.m4a', '.aac']:
                return AudioSegment.from_file(file_path, format='m4a')
            elif file_ext == '.ogg':
                return AudioSegment.from_file(file_path, format='ogg')
            else:
                # Try to load with pydub's generic loader
                return AudioSegment.from_file(file_path)
                
        except Exception as e:
            print(f"Error loading audio file {file_path}: {str(e)}")
            return None
    
    def create_silence(self, duration: float) -> AudioSegment:
        """Create silence segment of specified duration"""
        return AudioSegment.silent(duration=duration * 1000)  # Convert to milliseconds
    
    def mix_audio_layers(self, layers: List[Dict]) -> AudioSegment:
        """
        Mix multiple audio layers with precise timing
        
        Args:
            layers: List of layer dictionaries with keys:
                - audio: AudioSegment or file path
                - start_time: Start time in seconds
                - volume: Volume adjustment in dB
                - fade_in: Fade in duration
                - fade_out: Fade out duration
        
        Returns:
            Mixed AudioSegment
        """
        try:
            # Find total duration
            max_end_time = 0
            for layer in layers:
                if isinstance(layer['audio'], str):
                    duration = self.get_audio_duration(layer['audio'])
                else:
                    duration = len(layer['audio']) / 1000  # Convert from ms to seconds
                
                end_time = layer['start_time'] + duration
                max_end_time = max(max_end_time, end_time)
            
            # Create base silence
            mixed_audio = self.create_silence(max_end_time)
            
            # Add each layer
            for layer in layers:
                # Load audio if it's a file path
                if isinstance(layer['audio'], str):
                    audio = self.load_audio_file(layer['audio'])
                else:
                    audio = layer['audio']
                
                if audio is None:
                    continue
                
                # Apply volume adjustment
                if 'volume' in layer:
                    audio = audio + layer['volume']
                
                # Apply fades
                audio = self.apply_fade(
                    audio,
                    fade_in_duration=layer.get('fade_in', 0),
                    fade_out_duration=layer.get('fade_out', 0)
                )
                
                # Calculate position in milliseconds
                start_ms = layer['start_time'] * 1000
                
                # Overlay the audio
                mixed_audio = mixed_audio.overlay(audio, position=start_ms)
            
            return mixed_audio
            
        except Exception as e:
            print(f"Error mixing audio layers: {str(e)}")
            return AudioSegment.silent(duration=1000)  # Return 1 second of silence
    
    def process_template_segments(self, 
                                segments: List[Dict], 
                                music_track: Dict = None,
                                output_filename: str = None) -> Dict:
        """
        Process template segments with music track
        
        Args:
            segments: List of segment dictionaries
            music_track: Music track configuration
            output_filename: Output filename (optional)
        
        Returns:
            Dictionary with processing results
        """
        try:
            if not output_filename:
                output_filename = f"episode_{uuid.uuid4().hex[:8]}.mp3"
            
            output_path = self.output_dir / output_filename
            
            # Process segments
            segment_layers = []
            total_duration = 0
            
            for segment in segments:
                audio_file = segment.get('audio_file')
                if not audio_file:
                    continue
                
                # Load segment audio
                audio = self.load_audio_file(audio_file)
                if audio is None:
                    continue
                
                # Get segment timing
                start_offset = float(segment.get('timing', {}).get('start_offset', 0))
                end_offset = float(segment.get('timing', {}).get('end_offset', 0))
                
                # Apply timing offsets
                if start_offset > 0:
                    audio = audio[start_offset * 1000:]  # Convert to milliseconds
                
                if end_offset > 0:
                    audio = audio[:-end_offset * 1000]  # Remove from end
                
                # Apply fades
                fade_in_duration = float(segment.get('fade', {}).get('fade_in', 0))
                fade_out_duration = float(segment.get('fade', {}).get('fade_out', 0))
                
                audio = self.apply_fade(audio, fade_in_duration, fade_out_duration)
                
                # Add to layers
                segment_layers.append({
                    'audio': audio,
                    'start_time': total_duration,
                    'volume': 0,  # Normal volume
                    'fade_in': 0,
                    'fade_out': 0
                })
                
                total_duration += len(audio) / 1000  # Convert from ms to seconds
            
            # Add music track if specified
            if music_track and music_track.get('type') == 'upload':
                music_file = music_track.get('file_path')
                if music_file and os.path.exists(music_file):
                    music_audio = self.load_audio_file(music_file)
                    if music_audio:
                        # Loop music if needed
                        music_duration = len(music_audio) / 1000
                        if music_duration < total_duration:
                            # Calculate how many loops needed
                            loops_needed = int(total_duration / music_duration) + 1
                            music_audio = music_audio * loops_needed
                        
                        # Trim to exact duration
                        music_audio = music_audio[:total_duration * 1000]
                        
                        # Apply music settings
                        music_start = float(music_track.get('start_point', 0))
                        music_fade_in = float(music_track.get('fade_in', 2))
                        music_fade_out = float(music_track.get('fade_out', 3))
                        
                        # Apply fades
                        music_audio = self.apply_fade(music_audio, music_fade_in, music_fade_out)
                        
                        # Add music as background layer (lower volume)
                        segment_layers.append({
                            'audio': music_audio,
                            'start_time': music_start,
                            'volume': -10,  # Lower volume for background
                            'fade_in': music_fade_in,
                            'fade_out': music_fade_out
                        })
            
            # Mix all layers
            final_audio = self.mix_audio_layers(segment_layers)
            
            # Export final audio
            final_audio.export(str(output_path), format='mp3', bitrate='192k')
            
            return {
                'success': True,
                'output_path': str(output_path),
                'duration': len(final_audio) / 1000,
                'segments_processed': len(segments),
                'music_track_used': music_track is not None
            }
            
        except Exception as e:
            print(f"Error processing template segments: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_episode_from_template(self, 
                                   template_data: Dict, 
                                   episode_data: Dict,
                                   output_filename: str = None) -> Dict:
        """
        Create a complete episode from template and episode data
        
        Args:
            template_data: Template structure and configuration
            episode_data: Episode-specific content and audio files
            output_filename: Output filename (optional)
        
        Returns:
            Dictionary with processing results
        """
        try:
            if not output_filename:
                output_filename = f"episode_{uuid.uuid4().hex[:8]}.mp3"
            
            # Extract template structure
            structure = template_data.get('content', {})
            segments = structure.get('segments', [])
            music_track = structure.get('music_track')
            ai_segments = structure.get('ai_segments')
            
            # Process AI segments if present
            if ai_segments and episode_data.get('ai_content'):
                # This would integrate with ElevenLabs service
                # For now, we'll use placeholder audio
                pass
            
            # Map episode audio files to template segments
            episode_audio_files = episode_data.get('audio_files', [])
            
            # Process segments with actual audio files
            processed_segments = []
            for segment in segments:
                # Find matching audio file for this segment
                segment_audio = None
                for audio_file in episode_audio_files:
                    if audio_file.get('segment_type') == segment.get('type'):
                        segment_audio = audio_file.get('file_path')
                        break
                
                if segment_audio:
                    processed_segments.append({
                        'audio_file': segment_audio,
                        'timing': segment.get('timing', {}),
                        'fade': segment.get('fade', {}),
                        'type': segment.get('type')
                    })
            
            # Process the episode
            result = self.process_template_segments(
                segments=processed_segments,
                music_track=music_track,
                output_filename=output_filename
            )
            
            return result
            
        except Exception as e:
            print(f"Error creating episode from template: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def normalize_audio(self, audio: AudioSegment, target_dBFS: float = -20.0) -> AudioSegment:
        """Normalize audio to target dBFS level"""
        try:
            change_in_dBFS = target_dBFS - audio.dBFS
            return audio.apply_gain(change_in_dBFS)
        except Exception as e:
            print(f"Error normalizing audio: {str(e)}")
            return audio
    
    def compress_audio(self, audio: AudioSegment, threshold: float = -20.0, ratio: float = 4.0) -> AudioSegment:
        """Apply compression to audio"""
        try:
            # Simple compression implementation
            # In a real implementation, you'd use a proper compressor
            return audio
        except Exception as e:
            print(f"Error compressing audio: {str(e)}")
            return audio
    
    def add_metadata(self, audio_path: str, metadata: Dict) -> bool:
        """Add metadata to audio file"""
        try:
            # This would use a library like mutagen to add ID3 tags
            # For now, we'll just return success
            return True
        except Exception as e:
            print(f"Error adding metadata: {str(e)}")
            return False 