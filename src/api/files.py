"""
Files API Blueprint
Handles file uploads, downloads, and storage management
"""

import os
import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import librosa
import soundfile as sf
import json
import shutil
from datetime import datetime

from src.database import get_db_session
from src.database.models_dev import UserFile, User
from src.database.models import File
from src.database import get_db_session
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.database import get_db_session
from src.database.models_dev import User

files_bp = Blueprint('files', __name__)

# Allowed file extensions
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'flac', 'm4a', 'aac', 'ogg'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_EXTENSIONS = ALLOWED_AUDIO_EXTENSIONS | ALLOWED_IMAGE_EXTENSIONS

# Max file sizes (in bytes)
MAX_AUDIO_SIZE = 500 * 1024 * 1024  # 500MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10MB


def allowed_file(filename, file_type=None):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    
    if file_type == 'audio':
        return extension in ALLOWED_AUDIO_EXTENSIONS
    elif file_type == 'image':
        return extension in ALLOWED_IMAGE_EXTENSIONS
    else:
        return extension in ALLOWED_EXTENSIONS


def get_audio_duration(file_path):
    """Get audio file duration using librosa"""
    try:
        # Load audio file
        y, sr = librosa.load(file_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        return round(duration, 2)
    except Exception as e:
        current_app.logger.error(f"Error getting audio duration: {str(e)}")
        return None


def get_file_info(file_path):
    """Get detailed file information including audio metadata"""
    try:
        if not os.path.exists(file_path):
            return None
            
        file_info = {
            'size': os.path.getsize(file_path),
            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            'created': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
        }
        
        # Get audio-specific metadata if it's an audio file
        audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg'}
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in audio_extensions:
            try:
                y, sr = librosa.load(file_path, sr=None)
                duration = librosa.get_duration(y=y, sr=sr)
                file_info.update({
                    'duration': round(duration, 2),
                    'sample_rate': sr,
                    'channels': y.shape[1] if len(y.shape) > 1 else 1,
                    'audio_type': 'audio'
                })
            except Exception as e:
                file_info['audio_type'] = 'audio (error reading metadata)'
                file_info['error'] = str(e)
        else:
            file_info['audio_type'] = 'other'
            
        return file_info
    except Exception as e:
        return {'error': str(e)}


@files_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Upload a file"""
    try:
        user_id = get_jwt_identity()
        
        # Check if file is present
        if 'file' not in request.files:
            return {'error': 'No file provided'}, 400
        
        file = request.files['file']
        if file.filename == '':
            return {'error': 'No file selected'}, 400
        
        # Validate file
        if not allowed_file(file.filename):
            return {'error': 'File type not allowed'}, 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_AUDIO_SIZE:
            return {'error': 'File too large'}, 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        stored_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Create user upload directory
        user_upload_dir = Path(current_app.config['UPLOAD_FOLDER']) / str(user_id)
        user_upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = user_upload_dir / stored_filename
        file.save(file_path)
        
        # Get file metadata
        duration = None
        if file_extension in ALLOWED_AUDIO_EXTENSIONS:
            duration = get_audio_duration(file_path)
        
        # Get form data
        category = request.form.get('category', 'uncategorized')
        description = request.form.get('description', '')
        auto_organize = request.form.get('auto_organize', 'false').lower() == 'true'
        extract_metadata = request.form.get('extract_metadata', 'true').lower() == 'true'
        
        # Save to database using new File model
        db = get_db_session()
        try:
            relative_path = str(file_path.relative_to(Path(current_app.config['UPLOAD_FOLDER'])))
            relative_path = relative_path.replace('\\', '/').replace('\x00', '')
            
            db_file = File(
                id=str(uuid.uuid4()),
                user_id=user_id,
                file_path=relative_path,
                name=filename,
                description=description,
                category=category,
                file_size=file_size,
                mime_type=file.content_type,
                duration=duration
            )
            
            db.add(db_file)
            db.commit()
            
            return {
                'message': 'File uploaded successfully',
                'file': {
                    'id': str(db_file.id),
                    'name': filename,
                    'size': file_size,
                    'duration': duration,
                    'type': 'audio' if file_extension in ALLOWED_AUDIO_EXTENSIONS else 'image',
                    'category': category,
                    'description': description
                }
            }, 201
            
        finally:
            db.close()
        
    except RequestEntityTooLarge:
        return {'error': 'File too large'}, 413
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return {'error': 'Failed to upload file'}, 500


@files_bp.route('/upload/audio', methods=['POST'])
@jwt_required()
def upload_audio_files():
    """Upload multiple audio files for templates"""
    try:
        user_id = get_jwt_identity()
        
        # Check if files are present
        if 'files' not in request.files:
            return {'error': 'No files provided'}, 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return {'error': 'No files selected'}, 400
        
        uploaded_files = []
        db = get_db_session()
        
        try:
            for file in files:
                if file.filename == '':
                    continue
                
                # Validate file
                if not allowed_file(file.filename, 'audio'):
                    continue
                
                # Check file size
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                if file_size > MAX_AUDIO_SIZE:
                    continue
                
                # Generate unique filename
                filename = secure_filename(file.filename)
                file_extension = filename.rsplit('.', 1)[1].lower()
                stored_filename = f"{uuid.uuid4()}.{file_extension}"
                
                # Create user upload directory
                user_upload_dir = Path(current_app.config['UPLOAD_FOLDER']) / str(user_id)
                user_upload_dir.mkdir(parents=True, exist_ok=True)
                
                # Save file
                file_path = user_upload_dir / stored_filename
                file.save(file_path)
                
                # Get audio duration
                duration = get_audio_duration(file_path)
                
                # Save to database
                user_file = UserFile(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    original_filename=filename,
                    stored_filename=stored_filename,
                    file_path=str(file_path.relative_to(Path(current_app.config['UPLOAD_FOLDER']))),
                    file_type='audio',
                    mime_type=file.content_type,
                    file_size=file_size,
                    reference_type='template_audio'
                )
                
                db.add(user_file)
                db.commit()
                
                uploaded_files.append({
                    'id': str(user_file.id),
                    'name': filename,
                    'size': file_size,
                    'duration': duration,
                    'type': 'audio'
                })
            
            return {
                'message': f'{len(uploaded_files)} files uploaded successfully',
                'files': uploaded_files
            }, 201
            
        finally:
            db.close()
        
    except RequestEntityTooLarge:
        return {'error': 'Files too large'}, 413
    except Exception as e:
        current_app.logger.error(f"Audio upload error: {str(e)}")
        return {'error': 'Failed to upload files'}, 500





@files_bp.route('/<file_id>', methods=['GET'])
@jwt_required()
def get_file(file_id):
    """Get a specific file"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        try:
            user_file = db.query(UserFile).filter(
                UserFile.id == file_id,
                UserFile.user_id == user_id
            ).first()
            
            if not user_file:
                return {'error': 'File not found'}, 404
            
            return {
                'file': user_file.to_dict()
            }
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Get file error: {str(e)}")
        return {'error': 'Failed to get file'}, 500


@files_bp.route('/<file_id>/download', methods=['GET'])
@jwt_required()
def download_file(file_id):
    """Download a file"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        try:
            user_file = db.query(UserFile).filter(
                UserFile.id == file_id,
                UserFile.user_id == user_id
            ).first()
            
            if not user_file:
                return {'error': 'File not found'}, 404
            
            file_path = Path(current_app.config['UPLOAD_FOLDER']) / user_file.file_path
            
            if not file_path.exists():
                return {'error': 'File not found on disk'}, 404
            
            return send_file(
                file_path,
                as_attachment=True,
                download_name=user_file.original_filename
            )
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Download file error: {str(e)}")
        return {'error': 'Failed to download file'}, 500


@files_bp.route('/<file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    """Delete a file"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        try:
            user_file = db.query(UserFile).filter(
                UserFile.id == file_id,
                UserFile.user_id == user_id
            ).first()
            
            if not user_file:
                return {'error': 'File not found'}, 404
            
            # Delete file from disk
            file_path = Path(current_app.config['UPLOAD_FOLDER']) / user_file.file_path
            if file_path.exists():
                file_path.unlink()
            
            # Delete from database
            db.delete(user_file)
            db.commit()
            
            return {
                'message': 'File deleted successfully'
            }
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Delete file error: {str(e)}")
        return {'error': 'Failed to delete file'}, 500


@files_bp.route('/', methods=['GET'])
@jwt_required()
def list_files():
    """List all uploaded files with metadata"""
    try:
        current_user_id = get_jwt_identity()
        session = get_db_session()
        current_user = session.query(User).filter(User.id == current_user_id).first()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        files = []
        
        # Get files from database first
        db_files = session.query(File).filter_by(user_id=current_user.id).all()
        db_file_paths = {f.file_path: f for f in db_files}
        
        # Scan upload directory for user's files
        user_upload_dir = os.path.join(upload_folder, str(current_user_id))
        if not os.path.exists(user_upload_dir):
            return jsonify({
                'success': True,
                'files': [],
                'total_count': 0,
                'total_size_mb': 0
            })
        
        for root, dirs, filenames in os.walk(user_upload_dir):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, upload_folder)
                
                # Ensure the path uses forward slashes and doesn't contain null bytes
                relative_path = relative_path.replace('\\', '/').replace('\x00', '')
                
                # Skip files that don't belong to this user
                if not relative_path.startswith(str(current_user_id) + '/'):
                    continue
                
                # Get file info
                file_info = get_file_info(file_path)
                if not file_info:
                    continue
                    
                # Get database record if exists
                db_file = db_file_paths.get(relative_path)
                
                file_data = {
                    'filename': filename,
                    'path': relative_path,
                    'full_path': file_path,
                    'size': file_info['size'],
                    'size_mb': round(file_info['size'] / (1024 * 1024), 2),
                    'modified': file_info['modified'],
                    'created': file_info['created'],
                    'audio_type': file_info.get('audio_type', 'other'),
                    'duration': file_info.get('duration'),
                    'sample_rate': file_info.get('sample_rate'),
                    'channels': file_info.get('channels'),
                    'db_id': db_file.id if db_file else None,
                    'db_name': db_file.name if db_file else None,
                    'db_description': db_file.description if db_file else None,
                    'db_category': db_file.category if db_file else None
                }
                
                files.append(file_data)
        
        # Sort by modified date (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': files,
            'total_count': len(files),
            'total_size_mb': round(sum(f['size'] for f in files) / (1024 * 1024), 2)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@files_bp.route('/<path:file_path>', methods=['GET'])
@jwt_required()
def get_file_by_path(file_path):
    current_user_id = get_jwt_identity()
    session = get_db_session()
    current_user = session.query(User).filter(User.id == current_user_id).first()
    if not current_user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    """Get detailed information about a specific file"""
    try:
        # URL decode the file path
        import urllib.parse
        file_path = urllib.parse.unquote(file_path)
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        full_path = os.path.join(upload_folder, file_path)
        
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
        file_info = get_file_info(full_path)
        if not file_info:
            return jsonify({'success': False, 'error': 'Error reading file'}), 500
            
        # Get database record
        session = get_db_session()
        db_file = session.query(File).filter_by(file_path=file_path, user_id=current_user.id).first()
        
        file_data = {
            'filename': os.path.basename(file_path),
            'path': file_path,
            'full_path': full_path,
            'size': file_info['size'],
            'size_mb': round(file_info['size'] / (1024 * 1024), 2),
            'modified': file_info['modified'],
            'created': file_info['created'],
            'audio_type': file_info.get('audio_type', 'other'),
            'duration': file_info.get('duration'),
            'sample_rate': file_info.get('sample_rate'),
            'channels': file_info.get('channels'),
            'db_id': db_file.id if db_file else None,
            'db_name': db_file.name if db_file else None,
            'db_description': db_file.description if db_file else None,
            'db_category': db_file.category if db_file else None
        }
        
        return jsonify({'success': True, 'file': file_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@files_bp.route('/<path:file_path>', methods=['DELETE'])
@jwt_required()
def delete_file_by_path(file_path):
    current_user_id = get_jwt_identity()
    session = get_db_session()
    current_user = session.query(User).filter(User.id == current_user_id).first()
    if not current_user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    """Delete a specific file"""
    try:
        # URL decode the file path
        import urllib.parse
        file_path = urllib.parse.unquote(file_path)
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        full_path = os.path.join(upload_folder, file_path)
        
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
        # Check if file is in user's uploads (normalize paths for comparison)
        normalized_full_path = os.path.abspath(full_path)
        normalized_upload_folder = os.path.abspath(upload_folder)
        if not normalized_full_path.startswith(normalized_upload_folder):
            return jsonify({'success': False, 'error': 'Access denied'}), 403
            
        # Get file size before deletion for response
        file_size = os.path.getsize(full_path)
        
        # Delete from database first
        session = get_db_session()
        db_file = session.query(File).filter_by(file_path=file_path, user_id=current_user.id).first()
        if db_file:
            session.delete(db_file)
            session.commit()
        
        # Delete file
        os.remove(full_path)
        
        # Clean up empty directories
        directory = os.path.dirname(full_path)
        while directory != upload_folder and os.path.exists(directory):
            try:
                if not os.listdir(directory):  # Directory is empty
                    os.rmdir(directory)
                    directory = os.path.dirname(directory)
                else:
                    break
            except OSError:
                break
        
        return jsonify({
            'success': True,
            'message': 'File deleted successfully',
            'deleted_file': file_path,
            'size_mb': round(file_size / (1024 * 1024), 2)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@files_bp.route('/bulk-delete', methods=['POST'])
@jwt_required()
def bulk_delete_files():
    current_user_id = get_jwt_identity()
    session = get_db_session()
    current_user = session.query(User).filter(User.id == current_user_id).first()
    if not current_user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    """Delete multiple files at once"""
    try:
        data = request.get_json()
        file_paths = data.get('file_paths', [])
        
        if not file_paths:
            return jsonify({'success': False, 'error': 'No files specified'}), 400
            
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        deleted_files = []
        failed_files = []
        total_size = 0
        
        for file_path in file_paths:
            try:
                # URL decode the file path
                import urllib.parse
                file_path = urllib.parse.unquote(file_path)
                
                full_path = os.path.join(upload_folder, file_path)
                
                if not os.path.exists(full_path):
                    failed_files.append({'path': file_path, 'error': 'File not found'})
                    continue
                    
                # Check if file is in user's uploads (normalize paths for comparison)
                normalized_full_path = os.path.abspath(full_path)
                normalized_upload_folder = os.path.abspath(upload_folder)
                if not normalized_full_path.startswith(normalized_upload_folder):
                    failed_files.append({'path': file_path, 'error': 'Access denied'})
                    continue
                    
                # Get file size
                file_size = os.path.getsize(full_path)
                total_size += file_size
                
                # Delete from database
                session = get_db_session()
                db_file = session.query(File).filter_by(file_path=file_path, user_id=current_user.id).first()
                if db_file:
                    session.delete(db_file)
                
                # Delete file
                os.remove(full_path)
                deleted_files.append({
                    'path': file_path,
                    'size_mb': round(file_size / (1024 * 1024), 2)
                })
                
            except Exception as e:
                failed_files.append({'path': file_path, 'error': str(e)})
        
        # Commit database changes
        session.commit()
        
        # Clean up empty directories
        directories_to_check = set()
        for file_path in file_paths:
            full_path = os.path.join(upload_folder, file_path)
            directory = os.path.dirname(full_path)
            directories_to_check.add(directory)
        
        for directory in directories_to_check:
            while directory != upload_folder and os.path.exists(directory):
                try:
                    if not os.listdir(directory):
                        os.rmdir(directory)
                        directory = os.path.dirname(directory)
                    else:
                        break
                except OSError:
                    break
        
        return jsonify({
            'success': True,
            'deleted_files': deleted_files,
            'failed_files': failed_files,
            'total_deleted': len(deleted_files),
            'total_failed': len(failed_files),
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@files_bp.route('/<path:file_path>/metadata', methods=['PUT'])
@jwt_required()
def update_file_metadata(file_path):
    current_user_id = get_jwt_identity()
    session = get_db_session()
    current_user = session.query(User).filter(User.id == current_user_id).first()
    if not current_user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    """Update file metadata in database"""
    try:
        # URL decode the file path
        import urllib.parse
        file_path = urllib.parse.unquote(file_path)
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        category = data.get('category')
        
        # Get or create database record
        session = get_db_session()
        db_file = session.query(File).filter_by(file_path=file_path, user_id=current_user.id).first()
        
        if not db_file:
            # Create new record
            db_file = File(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                file_path=file_path,
                name=name or os.path.basename(file_path),
                description=description or '',
                category=category or 'uncategorized'
            )
            session.add(db_file)
        else:
            # Update existing record
            if name is not None:
                db_file.name = name
            if description is not None:
                db_file.description = description
            if category is not None:
                db_file.category = category
        
        session.commit()
        
        return jsonify({
            'success': True,
            'message': 'File metadata updated successfully',
            'file': {
                'id': db_file.id,
                'name': db_file.name,
                'description': db_file.description,
                'category': db_file.category
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@files_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_file_categories():
    current_user_id = get_jwt_identity()
    session = get_db_session()
    current_user = session.query(User).filter(User.id == current_user_id).first()
    if not current_user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    """Get all file categories used by the user"""
    try:
        session = get_db_session()
        categories = session.query(File.category).filter_by(user_id=current_user.id).distinct().all()
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return jsonify({
            'success': True,
            'categories': category_list
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
