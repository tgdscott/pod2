"""
Podcasts API Blueprint
Handles podcast creation, management, and configuration
"""

import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.database import get_db_session
from src.database.models import Podcast, User

podcasts_bp = Blueprint('podcasts', __name__)


@podcasts_bp.route('/', methods=['GET'])
@jwt_required()
def get_podcasts():
    """Get user's podcasts"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        try:
            # Get query parameters
            page = int(request.args.get('page', 1))
            per_page = min(int(request.args.get('per_page', 20)), 100)
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Get podcasts with pagination
            podcasts = db.query(Podcast).filter(Podcast.user_id == user_id)\
                        .order_by(Podcast.created_at.desc())\
                        .offset(offset)\
                        .limit(per_page)\
                        .all()
            
            # Get total count
            total = db.query(Podcast).filter(Podcast.user_id == user_id).count()
            
            return {
                'podcasts': [podcast.to_dict() for podcast in podcasts],
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
        current_app.logger.error(f"Get podcasts error: {str(e)}")
        return {'error': 'Failed to get podcasts'}, 500


@podcasts_bp.route('/', methods=['POST'])
@jwt_required()
def create_podcast():
    """Create a new podcast"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        
        if not title:
            return {'error': 'Title is required'}, 400
        
        if not description:
            return {'error': 'Description is required'}, 400
        
        db = get_db_session()
        try:
            # Check if podcast with same title exists for user
            existing_podcast = db.query(Podcast).filter(
                Podcast.user_id == user_id,
                Podcast.title == title
            ).first()
            
            if existing_podcast:
                return {'error': 'Podcast with this title already exists'}, 400
            
            # Create new podcast
            podcast = Podcast(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=title,
                description=description,
                language=data.get('language', 'en'),
                category=data.get('category', 'General'),
                explicit=data.get('explicit', False),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            db.add(podcast)
            db.commit()
            
            return {
                'message': 'Podcast created successfully',
                'podcast': podcast.to_dict()
            }, 201
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Create podcast error: {str(e)}")
        return {'error': 'Failed to create podcast'}, 500


@podcasts_bp.route('/<podcast_id>', methods=['GET'])
@jwt_required()
def get_podcast(podcast_id):
    """Get a specific podcast"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        try:
            podcast = db.query(Podcast).filter(
                Podcast.id == podcast_id,
                Podcast.user_id == user_id
            ).first()
            
            if not podcast:
                return {'error': 'Podcast not found'}, 404
            
            return {
                'podcast': podcast.to_dict()
            }
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Get podcast error: {str(e)}")
        return {'error': 'Failed to get podcast'}, 500


@podcasts_bp.route('/<podcast_id>', methods=['PUT'])
@jwt_required()
def update_podcast(podcast_id):
    """Update a podcast"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        db = get_db_session()
        try:
            podcast = db.query(Podcast).filter(
                Podcast.id == podcast_id,
                Podcast.user_id == user_id
            ).first()
            
            if not podcast:
                return {'error': 'Podcast not found'}, 404
            
            # Update fields
            if 'title' in data:
                title = data['title'].strip()
                if not title:
                    return {'error': 'Title cannot be empty'}, 400
                podcast.title = title
            
            if 'description' in data:
                description = data['description'].strip()
                if not description:
                    return {'error': 'Description cannot be empty'}, 400
                podcast.description = description
            
            if 'language' in data:
                podcast.language = data['language']
            
            if 'category' in data:
                podcast.category = data['category']
            
            if 'explicit' in data:
                podcast.explicit = data['explicit']
            
            podcast.updated_at = datetime.now(timezone.utc)
            db.commit()
            
            return {
                'message': 'Podcast updated successfully',
                'podcast': podcast.to_dict()
            }
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Update podcast error: {str(e)}")
        return {'error': 'Failed to update podcast'}, 500


@podcasts_bp.route('/<podcast_id>', methods=['DELETE'])
@jwt_required()
def delete_podcast(podcast_id):
    """Delete a podcast"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        try:
            podcast = db.query(Podcast).filter(
                Podcast.id == podcast_id,
                Podcast.user_id == user_id
            ).first()
            
            if not podcast:
                return {'error': 'Podcast not found'}, 404
            
            db.delete(podcast)
            db.commit()
            
            return {
                'message': 'Podcast deleted successfully'
            }
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Delete podcast error: {str(e)}")
        return {'error': 'Failed to delete podcast'}, 500
