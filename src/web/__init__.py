"""
Web interface blueprint for PodcastPro v2
Serves the frontend and static files
"""

from flask import Blueprint, render_template, send_from_directory
import os

web_bp = Blueprint('web', __name__)


@web_bp.route('/')
def index():
    """Serve the main application page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>PodcastPro v2</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 40px; }
            .status { background: #e8f5e8; padding: 20px; border-radius: 8px; }
            .endpoints { background: #f5f5f5; padding: 20px; border-radius: 8px; margin-top: 20px; }
            code { background: #f0f0f0; padding: 2px 4px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎙️ PodcastPro v2</h1>
                <p>AI-Powered Podcast Creation Platform</p>
            </div>
            
            <div class="status">
                <h2>✅ Server Status: Running</h2>
                <p>The PodcastPro v2 API server is up and running successfully!</p>
            </div>
            
            <div class="endpoints">
                <h3>API Endpoints</h3>
                <ul>
                    <li><code>POST /api/v1/auth/register</code> - Register new user</li>
                    <li><code>POST /api/v1/auth/login</code> - User login</li>
                    <li><code>GET /api/v1/auth/me</code> - Get current user</li>
                    <li><code>GET /api/v1/podcasts</code> - List podcasts</li>
                    <li><code>POST /api/v1/podcasts</code> - Create podcast</li>
                    <li><code>GET /api/v1/episodes</code> - List episodes</li>
                    <li><code>POST /api/v1/episodes</code> - Create episode</li>
                    <li><code>POST /api/v1/files/upload</code> - Upload files</li>
                    <li><code>GET /api/v1/templates</code> - List templates</li>
                    <li><code>GET /api/v1/jobs</code> - List background jobs</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    '''


@web_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'PodcastPro v2',
        'version': '2.0.0'
    }
