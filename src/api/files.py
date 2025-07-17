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


def get_upload_path():
    """Get the upload directory path"""
    upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def save_file(file, user_id, file_type=None):
    """Save uploaded file and create database record"""
    # Generate unique filename
    file_id = str(uuid.uuid4())
    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    safe_filename = f"{file_id}.{extension}" if extension else file_id
    
    # Create user-specific directory
    upload_path = get_upload_path()
    user_dir = upload_path / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = user_dir / safe_filename
    file.save(str(file_path))
    
    # Get file size
    file_size = file_path.stat().st_size
    
    # Create database record
    db = get_db_session()
    try:
        user_file = UserFile(
            id=file_id,
            user_id=user_id,
            original_filename=original_filename,
            stored_filename=safe_filename,
            file_path=str(file_path.relative_to(upload_path)),
            file_size=file_size,
            file_type=file_type or extension,
            mime_type=file.content_type
        )
        
        db.add(user_file)
        db.commit()
        return user_file
    except Exception as e:
        db.rollback()
        # Clean up file if database save failed
        if file_path.exists():
            file_path.unlink()
        raise e


@files_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Upload file (audio, image, etc.)"""
    try:
        user_id = get_jwt_identity()
        
        # Check if file is in request
        if 'file' not in request.files:
            return {'error': 'No file provided'}, 400
        
        file = request.files['file']
        
        if file.filename == '':
            return {'error': 'No file selected'}, 400
        
        # Get file type from form data
        file_type = request.form.get('type', '').lower()
        
        # Validate file extension
        if not allowed_file(file.filename, file_type):
            return {'error': 'File type not allowed'}, 400
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_type == 'audio' and file_size > MAX_AUDIO_SIZE:
            return {'error': f'Audio file too large. Max size: {MAX_AUDIO_SIZE // (1024*1024)}MB'}, 413
        elif file_type == 'image' and file_size > MAX_IMAGE_SIZE:
            return {'error': f'Image file too large. Max size: {MAX_IMAGE_SIZE // (1024*1024)}MB'}, 413
        
        # Save file
        user_file = save_file(file, user_id, file_type)
        
        return {
            'message': 'File uploaded successfully',
            'file': user_file.to_dict()
        }, 201
        
    except RequestEntityTooLarge:
        return {'error': 'File too large'}, 413
    except Exception as e:
        current_app.logger.error(f"File upload error: {str(e)}")
        return {'error': 'Upload failed'}, 500


@files_bp.route('/<file_id>', methods=['GET'])
@jwt_required()
def get_file(file_id):
    """Get file information or download"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        # Get file record
        user_file = db.query(UserFile).filter_by(
            id=file_id,
            user_id=user_id
        ).first()
        
        if not user_file:
            return {'error': 'File not found'}, 404
        
        # Check if download is requested
        if request.args.get('download') == 'true':
            # Return file for download
            upload_path = get_upload_path()
            file_path = upload_path / user_file.file_path
            
            if not file_path.exists():
                return {'error': 'File not found on disk'}, 404
            
            return send_file(
                str(file_path),
                as_attachment=True,
                download_name=user_file.original_filename,
                mimetype=user_file.mime_type
            )
        else:
            # Return file information
            return {'file': user_file.to_dict()}
            
    except Exception as e:
        current_app.logger.error(f"File access error: {str(e)}")
        return {'error': 'File access failed'}, 500


@files_bp.route('/', methods=['GET'])
@jwt_required()
def list_files():
    """List user's uploaded files"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        # Get query parameters
        file_type = request.args.get('type')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Build query
        query = db.query(UserFile).filter_by(user_id=user_id)
        
        if file_type:
            query = query.filter(UserFile.file_type == file_type)
        
        # Get files with pagination
        files = query.order_by(UserFile.created_at.desc())\
                    .offset(offset)\
                    .limit(per_page)\
                    .all()
        
        # Get total count
        total_query = db.query(UserFile).filter_by(user_id=user_id)
        if file_type:
            total_query = total_query.filter(UserFile.file_type == file_type)
        total = total_query.count()
        pages = (total + per_page - 1) // per_page
        
        return {
            'files': [f.to_dict() for f in files],
            'pagination': {
                'page': page,
                'pages': pages,
                'per_page': per_page,
                'total': total
            }
        }
        
    except Exception as e:
        current_app.logger.error(f"File listing error: {str(e)}")
        return {'error': 'Failed to list files'}, 500


@files_bp.route('/<file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    """Delete uploaded file"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        # Get file record
        user_file = db.query(UserFile).filter_by(
            id=file_id,
            user_id=user_id
        ).first()
        
        if not user_file:
            return {'error': 'File not found'}, 404
        
        # Delete file from disk
        upload_path = get_upload_path()
        file_path = upload_path / user_file.file_path
        
        if file_path.exists():
            file_path.unlink()
        
        # Delete database record
        db.delete(user_file)
        db.commit()
        
        return {'message': 'File deleted successfully'}
        
    except Exception as e:
        current_app.logger.error(f"File deletion error: {str(e)}")
        return {'error': 'File deletion failed'}, 500
