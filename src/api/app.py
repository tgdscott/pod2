"""
Flask Application Factory
"""

import os
from datetime import datetime
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

from src.database import init_database
from src.core.celery_config import make_celery

# Global Celery instance
celery = None

def create_app(config_name: str = 'development') -> Flask:
    """Create and configure Flask application"""
    
    # Load environment variables
    load_dotenv()
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.update({
        'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-secret-key'),
        'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY', 'jwt-secret-key'),
        'JWT_ACCESS_TOKEN_EXPIRES': int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)),
        'JWT_REFRESH_TOKEN_EXPIRES': int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000)),
        
        'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///podcastpro_dev.db'),
        'DATABASE_POOL_SIZE': int(os.getenv('DATABASE_POOL_SIZE', 10)),
        'DATABASE_POOL_TIMEOUT': int(os.getenv('DATABASE_POOL_TIMEOUT', 30)),
        
        'REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        
        'UPLOAD_FOLDER': os.getenv('UPLOAD_FOLDER', 'uploads'),
        'OUTPUT_FOLDER': os.getenv('OUTPUT_FOLDER', 'outputs'),
        'MAX_CONTENT_LENGTH': int(os.getenv('MAX_CONTENT_LENGTH', 2147483648)),  # 2GB
        
        'GOOGLE_CLOUD_PROJECT': os.getenv('GOOGLE_CLOUD_PROJECT'),
        'GOOGLE_CLOUD_STORAGE_BUCKET': os.getenv('GOOGLE_CLOUD_STORAGE_BUCKET'),
        
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'ELEVENLABS_API_KEY': os.getenv('ELEVENLABS_API_KEY'),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
        
        'APP_NAME': os.getenv('APP_NAME', 'PodcastPro'),
        'APP_VERSION': os.getenv('APP_VERSION', '2.0.0'),
        'DEFAULT_PAGINATION_SIZE': int(os.getenv('DEFAULT_PAGINATION_SIZE', 20)),
        'MAX_PAGINATION_SIZE': int(os.getenv('MAX_PAGINATION_SIZE', 100)),
        
        'SQLALCHEMY_ECHO': os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true',
    })
    
    # Initialize extensions
    CORS(app, origins=["http://localhost:3000", "http://localhost:5000"])  # Add your frontend URLs
    
    # Initialize JWT manager
    jwt = JWTManager(app)
    
    # Create upload and output directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    # Initialize database
    init_database(app)
    
    # Register blueprints
    from src.api.auth import auth_bp
    from src.api.podcasts import podcasts_bp
    from src.api.episodes import episodes_bp
    from src.api.templates import templates_bp
    from src.api.jobs import jobs_bp
    from src.api.files import files_bp
    from src.api.voices import voices_bp
    from src.api.settings import settings_bp
    from src.web import web_bp
    
    # API routes with versioning
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(podcasts_bp, url_prefix='/api/v1/podcasts')
    app.register_blueprint(episodes_bp, url_prefix='/api/v1/episodes')
    app.register_blueprint(templates_bp, url_prefix='/api/v1/templates')
    app.register_blueprint(jobs_bp, url_prefix='/api/v1/jobs')
    app.register_blueprint(files_bp, url_prefix='/api/v1/files')
    app.register_blueprint(voices_bp, url_prefix='/api/v1/voices')
    app.register_blueprint(settings_bp, url_prefix='/api/v1/settings')
    
    # Web interface routes
    app.register_blueprint(web_bp)
    
    # Health check endpoint
    @app.route('/api/v1/health')
    def health_check():
        """Health check endpoint"""
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'version': app.config.get('APP_VERSION', '2.0.0'),
            'services': {
                'database': 'connected',
                'storage': 'available'
            }
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        return {'error': 'File too large'}, 413
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'error': 'Token has expired'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'error': 'Invalid token'}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'error': 'Token required'}, 401
    
    # Initialize Celery
    global celery
    celery = make_celery(app)
    
    # Register Celery tasks
    from src.core.tasks import register_tasks
    register_tasks(celery)

    @app.route('/api/v1/debug/routes')
    def debug_routes():
        output = []
        for rule in app.url_map.iter_rules():
            output.append(f"{sorted(rule.methods)} {rule.rule}")
        return "<br>".join(sorted(output))
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
