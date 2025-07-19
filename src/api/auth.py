"""
Authentication API Blueprint
Handles user registration, login, and JWT token management
"""

from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token, 
    create_refresh_token, get_jwt
)

from src.database import get_db_session
from src.database.models_dev import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        username = data.get('username', '').strip()
        
        if not all([email, password, username]):
            return {'error': 'Email, password, and username are required'}, 400
        
        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[1]:
            return {'error': 'Invalid email format'}, 400
        
        if len(password) < 6:
            return {'error': 'Password must be at least 6 characters'}, 400
        
        db = get_db_session()
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(
                (User.email == email) | (User.username == username)
            ).first()
            
            if existing_user:
                if existing_user.email == email:
                    return {'error': 'Email already registered'}, 400
                else:
                    return {'error': 'Username already taken'}, 400
            
            # Hash password using User model method
            user = User(
                email=email,
                username=username,
                created_at=datetime.now(timezone.utc)
            )
            user.set_password(password)
            
            db.add(user)
            db.commit()
            
            # Create tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            return {
                'message': 'User registered successfully',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username
                },
                'access_token': access_token,
                'refresh_token': refresh_token
            }, 201
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Registration error: {str(e)}")
        return {'error': 'Registration failed'}, 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return tokens"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return {'error': 'Email and password are required'}, 400
        
        db = get_db_session()
        try:
            # Find user by email
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                return {'error': 'Invalid email or password'}, 401
            
            # Check password using User model method
            if not user.check_password(password):
                return {'error': 'Invalid email or password'}, 401
            
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            db.commit()
            
            # Create tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            return {
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username
                },
                'access_token': access_token,
                'refresh_token': refresh_token
            }
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return {'error': 'Login failed'}, 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        new_token = create_access_token(identity=current_user_id)
        
        return {
            'access_token': new_token
        }
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return {'error': 'Token refresh failed'}, 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        user_id = get_jwt_identity()
        
        db = get_db_session()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return {'error': 'User not found'}, 404
            
            return {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
            }
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Get user error: {str(e)}")
        return {'error': 'Failed to get user information'}, 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client should discard tokens)"""
    # In a production app, you might want to blacklist the token
    return {'message': 'Logged out successfully'}
