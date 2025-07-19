"""
ElevenLabs Voice Management API
"""

import requests
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.database import get_db_session
from src.database.models import User

voices_bp = Blueprint('voices', __name__)

@voices_bp.route('/', methods=['GET'])
@jwt_required()
def get_voices():
    """Get available ElevenLabs voices"""
    try:
        current_user_id = get_jwt_identity()
        db = get_db_session()
        user = db.query(User).filter(User.id == current_user_id).first()
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get ElevenLabs API key from user settings or environment
        elevenlabs_key = user.elevenlabs_api_key or request.headers.get('X-ElevenLabs-Key')
        
        if not elevenlabs_key:
            return jsonify({
                'success': False, 
                'error': 'ElevenLabs API key not configured. Please set it in your profile settings.'
            }), 400
        
        # Fetch voices from ElevenLabs API
        headers = {
            'xi-api-key': elevenlabs_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.get('https://api.elevenlabs.io/v1/voices', headers=headers)
        
        if response.status_code == 200:
            voices_data = response.json()
            voices = []
            
            for voice in voices_data.get('voices', []):
                voices.append({
                    'voice_id': voice.get('voice_id'),
                    'name': voice.get('name'),
                    'category': voice.get('category', 'Unknown'),
                    'description': voice.get('description', ''),
                    'labels': voice.get('labels', {}),
                    'preview_url': voice.get('preview_url')
                })
            
            return jsonify({
                'success': True,
                'voices': voices
            })
        else:
            return jsonify({
                'success': False,
                'error': f'ElevenLabs API error: {response.status_code}'
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error fetching voices: {str(e)}'
        }), 500

@voices_bp.route('/test', methods=['POST'])
@jwt_required()
def test_voice():
    """Test voice generation with ElevenLabs"""
    try:
        current_user_id = get_jwt_identity()
        db = get_db_session()
        user = db.query(User).filter(User.id == current_user_id).first()
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        data = request.get_json()
        voice_id = data.get('voice_id')
        text = data.get('text', 'Hello! This is a test of the voice generation.')
        stability = data.get('stability', 0.5)
        
        if not voice_id:
            return jsonify({'success': False, 'error': 'Voice ID is required'}), 400
        
        # Get ElevenLabs API key
        elevenlabs_key = user.elevenlabs_api_key or request.headers.get('X-ElevenLabs-Key')
        
        if not elevenlabs_key:
            return jsonify({
                'success': False, 
                'error': 'ElevenLabs API key not configured'
            }), 400
        
        # Generate audio with ElevenLabs
        headers = {
            'xi-api-key': elevenlabs_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'text': text,
            'model_id': 'eleven_monolingual_v1',
            'voice_settings': {
                'stability': stability,
                'similarity_boost': 0.5
            }
        }
        
        response = requests.post(
            f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}',
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            # Save the generated audio file
            import os
            from datetime import datetime
            
            filename = f"voice_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            filepath = os.path.join('uploads', filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return jsonify({
                'success': True,
                'message': 'Voice test completed successfully',
                'file_path': filepath
            })
        else:
            return jsonify({
                'success': False,
                'error': f'ElevenLabs API error: {response.status_code}'
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error testing voice: {str(e)}'
        }), 500 