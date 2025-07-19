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

from src.database import get_db_session
from src.database.models_dev import UserFile, User

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
        
        # Save to database
        db = get_db_session()
        try:
            user_file = UserFile(
                id=str(uuid.uuid4()),
                user_id=user_id,
                original_filename=filename,
                stored_filename=stored_filename,
                file_path=str(file_path.relative_to(Path(current_app.config['UPLOAD_FOLDER']))),
                file_type='audio' if file_extension in ALLOWED_AUDIO_EXTENSIONS else 'image',
                mime_type=file.content_type,
                file_size=file_size
            )
            
            db.add(user_file)
            db.commit()
            
            return {
                'message': 'File uploaded successfully',
                'file': {
                    'id': str(user_file.id),
                    'name': filename,
                    'size': file_size,
                    'duration': duration,
                    'type': user_file.file_type
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


@files_bp.route('/', methods=['GET'])
@jwt_required()
def get_files():
    """Get user's files"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        try:
            # Get query parameters
            file_type = request.args.get('type')
            reference_type = request.args.get('reference_type')
            page = int(request.args.get('page', 1))
            per_page = min(int(request.args.get('per_page', 20)), 100)
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Build query
            query = db.query(UserFile).filter(UserFile.user_id == user_id)
            
            if file_type:
                query = query.filter(UserFile.file_type == file_type)
            
            if reference_type:
                query = query.filter(UserFile.reference_type == reference_type)
            
            # Get files with pagination
            files = query.order_by(UserFile.created_at.desc())\
                        .offset(offset)\
                        .limit(per_page)\
                        .all()
            
            # Get total count
            total_query = db.query(UserFile).filter(UserFile.user_id == user_id)
            if file_type:
                total_query = total_query.filter(UserFile.file_type == file_type)
            if reference_type:
                total_query = total_query.filter(UserFile.reference_type == reference_type)
            total = total_query.count()
            
            return {
                'files': [file.to_dict() for file in files],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Get files error: {str(e)}")
        return {'error': 'Failed to get files'}, 500


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
