"""
Templates API Blueprint
Handles podcast episode templates and configurations
"""

import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.database import get_db_session
from src.database.models_dev import Template, User

templates_bp = Blueprint('templates', __name__)


@templates_bp.route('/', methods=['GET'])
@jwt_required()
def get_templates():
    """Get user's templates"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        try:
            # Get query parameters
            page = int(request.args.get('page', 1))
            per_page = min(int(request.args.get('per_page', 20)), 100)
            template_type = request.args.get('type')
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Build query
            query = db.query(Template).filter(Template.user_id == user_id)
            
            if template_type:
                query = query.filter(Template.template_type == template_type)
            
            # Get templates with pagination
            templates = query.order_by(Template.created_at.desc())\
                           .offset(offset)\
                           .limit(per_page)\
                           .all()
            
            # Get total count
            total_query = db.query(Template).filter(Template.user_id == user_id)
            if template_type:
                total_query = total_query.filter(Template.template_type == template_type)
            total = total_query.count()
            
            return {
                'templates': [template.to_dict() for template in templates],
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
        current_app.logger.error(f"Get templates error: {str(e)}")
        return {'error': 'Failed to get templates'}, 500


@templates_bp.route('/', methods=['POST'])
@jwt_required()
def create_template():
    """Create a new template"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        name = data.get('name', '').strip()
        template_type = data.get('type', '').strip()
        content = data.get('content', {})
        
        if not name:
            return {'error': 'Template name is required'}, 400
        
        if not template_type:
            return {'error': 'Template type is required'}, 400
        
        if not content:
            return {'error': 'Template content is required'}, 400
        
        db = get_db_session()
        try:
            # Check if template with same name exists for user
            existing_template = db.query(Template).filter(
                Template.user_id == user_id,
                Template.name == name
            ).first()
            
            if existing_template:
                return {'error': 'Template with this name already exists'}, 400
            
            # Create new template
            template = Template(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=name,
                template_type=template_type,
                content=content,
                description=data.get('description', ''),
                is_public=data.get('is_public', False),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            db.add(template)
            db.commit()
            
            return {
                'message': 'Template created successfully',
                'template': template.to_dict()
            }, 201
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Create template error: {str(e)}")
        return {'error': 'Failed to create template'}, 500


@templates_bp.route('/<template_id>', methods=['GET'])
@jwt_required()
def get_template(template_id):
    """Get a specific template"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        try:
            template = db.query(Template).filter(
                Template.id == template_id,
                Template.user_id == user_id
            ).first()
            
            if not template:
                return {'error': 'Template not found'}, 404
            
            return {
                'template': template.to_dict()
            }
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Get template error: {str(e)}")
        return {'error': 'Failed to get template'}, 500


@templates_bp.route('/<template_id>', methods=['PUT'])
@jwt_required()
def update_template(template_id):
    """Update a template"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        db = get_db_session()
        try:
            template = db.query(Template).filter(
                Template.id == template_id,
                Template.user_id == user_id
            ).first()
            
            if not template:
                return {'error': 'Template not found'}, 404
            
            # Update fields
            if 'name' in data:
                name = data['name'].strip()
                if not name:
                    return {'error': 'Template name cannot be empty'}, 400
                template.name = name
            
            if 'content' in data:
                if not data['content']:
                    return {'error': 'Template content cannot be empty'}, 400
                template.content = data['content']
            
            if 'description' in data:
                template.description = data['description']
            
            if 'is_public' in data:
                template.is_public = data['is_public']
            
            template.updated_at = datetime.now(timezone.utc)
            db.commit()
            
            return {
                'message': 'Template updated successfully',
                'template': template.to_dict()
            }
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Update template error: {str(e)}")
        return {'error': 'Failed to update template'}, 500


@templates_bp.route('/<template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    """Delete a template"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        try:
            template = db.query(Template).filter(
                Template.id == template_id,
                Template.user_id == user_id
            ).first()
            
            if not template:
                return {'error': 'Template not found'}, 404
            
            db.delete(template)
            db.commit()
            
            return {
                'message': 'Template deleted successfully'
            }
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Delete template error: {str(e)}")
        return {'error': 'Failed to delete template'}, 500
