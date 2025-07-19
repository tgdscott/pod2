"""
User Settings Management API
"""

import requests
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.database import get_db_session
from src.database.models import User

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/', methods=['GET'])
@jwt_required()
def get_settings():
    """Get all user settings"""
    try:
        current_user_id = get_jwt_identity()
        db = get_db_session()
        user = db.query(User).filter(User.id == current_user_id).first()
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Return all settings
        return jsonify({
            'success': True,
            'settings': {
                'api_keys': {
                    'elevenlabs': user.elevenlabs_api_key is not None,
                    'gemini': user.gemini_api_key is not None,
                    'openai': user.openai_api_key is not None,
                    'spreaker': user.spreaker_api_key is not None
                },
                'preferences': {
                    'default_voice': getattr(user, 'default_voice_id', None),
                    'default_stability': getattr(user, 'default_voice_stability', 0.5),
                    'default_quality': getattr(user, 'default_audio_quality', 192),
                    'auto_save_interval': getattr(user, 'auto_save_interval', 60),
                    'email_notifications': getattr(user, 'email_notifications', False),
                    'auto_publish': getattr(user, 'auto_publish', False)
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error loading settings: {str(e)}'
        }), 500

@settings_bp.route('/api-keys', methods=['POST'])
@jwt_required()
def save_api_keys():
    """Save user API keys"""
    try:
        current_user_id = get_jwt_identity()
        db = get_db_session()
        user = db.query(User).filter(User.id == current_user_id).first()
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        data = request.get_json()
        api_keys = data.get('api_keys', {})
        
        # Update user's API keys
        if 'elevenlabs' in api_keys:
            user.elevenlabs_api_key = api_keys['elevenlabs']
        if 'gemini' in api_keys:
            user.gemini_api_key = api_keys['gemini']
        if 'openai' in api_keys:
            user.openai_api_key = api_keys['openai']
        if 'spreaker' in api_keys:
            user.spreaker_api_key = api_keys['spreaker']
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'API keys saved successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error saving API keys: {str(e)}'
        }), 500

@settings_bp.route('/test-connections', methods=['POST'])
@jwt_required()
def test_api_connections():
    """Test API connections"""
    try:
        current_user_id = get_jwt_identity()
        db = get_db_session()
        user = db.query(User).filter(User.id == current_user_id).first()
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        results = {}
        
        # Test ElevenLabs
        if user.elevenlabs_api_key:
            try:
                headers = {'xi-api-key': user.elevenlabs_api_key}
                response = requests.get('https://api.elevenlabs.io/v1/voices', headers=headers)
                results['elevenlabs'] = {
                    'success': response.status_code == 200,
                    'message': 'Connected successfully' if response.status_code == 200 else f'Error: {response.status_code}'
                }
            except Exception as e:
                results['elevenlabs'] = {
                    'success': False,
                    'message': f'Connection failed: {str(e)}'
                }
        else:
            results['elevenlabs'] = {
                'success': False,
                'message': 'API key not configured'
            }
        
        # Test Gemini
        if user.gemini_api_key:
            try:
                headers = {'Authorization': f'Bearer {user.gemini_api_key}'}
                response = requests.get('https://generativelanguage.googleapis.com/v1beta/models', headers=headers)
                results['gemini'] = {
                    'success': response.status_code == 200,
                    'message': 'Connected successfully' if response.status_code == 200 else f'Error: {response.status_code}'
                }
            except Exception as e:
                results['gemini'] = {
                    'success': False,
                    'message': f'Connection failed: {str(e)}'
                }
        else:
            results['gemini'] = {
                'success': False,
                'message': 'API key not configured'
            }
        
        # Test OpenAI
        if user.openai_api_key:
            try:
                headers = {'Authorization': f'Bearer {user.openai_api_key}'}
                response = requests.get('https://api.openai.com/v1/models', headers=headers)
                results['openai'] = {
                    'success': response.status_code == 200,
                    'message': 'Connected successfully' if response.status_code == 200 else f'Error: {response.status_code}'
                }
            except Exception as e:
                results['openai'] = {
                    'success': False,
                    'message': f'Connection failed: {str(e)}'
                }
        else:
            results['openai'] = {
                'success': False,
                'message': 'API key not configured'
            }
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error testing connections: {str(e)}'
        }), 500

@settings_bp.route('/default-voice', methods=['GET', 'POST'])
@jwt_required()
def default_voice_settings():
    """Get or save default voice settings"""
    try:
        current_user_id = get_jwt_identity()
        db = get_db_session()
        user = db.query(User).filter(User.id == current_user_id).first()
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        if request.method == 'GET':
            # Return current default voice settings
            return jsonify({
                'success': True,
                'settings': {
                    'voice_id': getattr(user, 'default_voice_id', None),
                    'stability': getattr(user, 'default_voice_stability', 0.5)
                }
            })
        
        elif request.method == 'POST':
            # Save default voice settings
            data = request.get_json()
            voice_id = data.get('voice_id')
            stability = data.get('stability', 0.5)
            
            user.default_voice_id = voice_id
            user.default_voice_stability = stability
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'Default voice settings saved successfully'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error managing default voice settings: {str(e)}'
        }), 500

@settings_bp.route('/storage', methods=['GET'])
@jwt_required()
def get_storage_info():
    """Get storage usage information"""
    try:
        current_user_id = get_jwt_identity()
        db = get_db_session()
        
        # Get user's files
        from src.database.models import File
        user_files = db.query(File).filter(File.user_id == current_user_id).all()
        
        # Calculate total size
        total_size = sum(file.file_size for file in user_files if file.file_size)
        file_count = len(user_files)
        
        # Convert to GB (assuming sizes are in bytes)
        total_size_gb = total_size / (1024**3)
        
        # For now, assume 10GB limit (this could be made configurable)
        storage_limit_gb = 10
        usage_percentage = min((total_size_gb / storage_limit_gb) * 100, 100)
        
        return jsonify({
            'success': True,
            'storage': {
                'used_gb': round(total_size_gb, 2),
                'limit_gb': storage_limit_gb,
                'usage_percentage': round(usage_percentage, 1),
                'file_count': file_count
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting storage info: {str(e)}'
        }), 500 