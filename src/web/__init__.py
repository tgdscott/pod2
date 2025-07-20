"""
Web interface blueprint for PodcastPro v2
Serves the frontend and static files
"""

import os
import requests
from flask import Blueprint, render_template, send_from_directory, request, redirect, url_for, session, flash

web_bp = Blueprint('web', __name__, template_folder='templates')

# API base URL
API_BASE = "http://localhost:5000/api/v1"

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


@web_bp.route('/dashboard')
def dashboard():
    """Serve the dashboard page with real data"""
    stats = {}
    recent_episodes = []
    processing_jobs = []
    
    # Check if user is logged in
    if 'token' not in session:
        return redirect(url_for('web.login'))
    
    try:
        headers = {'Authorization': f'Bearer {session["token"]}'}
        
        # Get podcasts count
        response = requests.get(f"{API_BASE}/podcasts", headers=headers)
        if response.status_code == 200:
            podcasts_data = response.json()
            stats['podcasts'] = len(podcasts_data.get('podcasts', []))
        
        # Get episodes count and recent episodes
        response = requests.get(f"{API_BASE}/episodes", headers=headers)
        if response.status_code == 200:
            episodes_data = response.json()
            episodes = episodes_data.get('episodes', [])
            stats['episodes'] = len(episodes)
            stats['completed'] = len([e for e in episodes if e.get('status') == 'completed'])
            stats['processing'] = len([e for e in episodes if e.get('status') == 'processing'])
            
            # Get recent episodes (last 5)
            recent_episodes = episodes[:5]
        
        # Get processing jobs
        response = requests.get(f"{API_BASE}/jobs", headers=headers)
        if response.status_code == 200:
            jobs_data = response.json()
            processing_jobs = [job for job in jobs_data.get('jobs', []) if job.get('status') in ['queued', 'processing']]
            
    except Exception as e:
        # If API calls fail, use default values
        stats = {'podcasts': 0, 'episodes': 0, 'processing': 0, 'completed': 0}
        recent_episodes = []
        processing_jobs = []
    
    return render_template('dashboard.html', stats=stats, recent_episodes=recent_episodes, processing_jobs=processing_jobs)


@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                'email': email,
                'password': password
            })
            
            if response.status_code == 200:
                data = response.json()
                session['token'] = data['access_token']
                session['user'] = data['user']
                return redirect(url_for('web.dashboard'))
            else:
                error_data = response.json()
                return render_template('auth.html', error=error_data.get('error', 'Login failed'))
                
        except Exception as e:
            return render_template('auth.html', error='Connection error. Please try again.')
    
    return render_template('auth.html')


@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle registration"""
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            response = requests.post(f"{API_BASE}/auth/register", json={
                'email': email,
                'username': username,
                'password': password
            })
            
            if response.status_code == 201:
                data = response.json()
                session['token'] = data['access_token']
                session['user'] = data['user']
                return redirect(url_for('web.dashboard'))
            else:
                error_data = response.json()
                return render_template('register.html', error=error_data.get('error', 'Registration failed'))
                
        except Exception as e:
            return render_template('register.html', error='Connection error. Please try again.')
    
    return render_template('register.html')


@web_bp.route('/logout')
def logout():
    """Handle logout"""
    session.clear()
    return redirect(url_for('web.login'))

@web_bp.route('/episodes')
def episodes():
    """Serve the episodes list page"""
    # Check if user is logged in
    if 'token' not in session:
        return redirect(url_for('web.login'))
    
    episodes = []
    podcasts = []
    pagination = None
    
    try:
        headers = {'Authorization': f'Bearer {session["token"]}'}
        
        # Get episodes
        response = requests.get(f"{API_BASE}/episodes", headers=headers)
        if response.status_code == 200:
            episodes_data = response.json()
            episodes = episodes_data.get('episodes', [])
        
        # Get podcasts for filter dropdown
        response = requests.get(f"{API_BASE}/podcasts", headers=headers)
        if response.status_code == 200:
            podcasts_data = response.json()
            podcasts = podcasts_data.get('podcasts', [])
            
    except Exception as e:
        episodes = []
        podcasts = []
    
    return render_template('episodes.html', episodes=episodes, podcasts=podcasts, pagination=pagination)

@web_bp.route('/episodes/new')
def new_episode():
    """Serve the new episode creation page"""
    # Check if user is logged in
    if 'token' not in session:
        return redirect(url_for('web.login'))
    
    podcasts = []
    templates = []
    
    try:
        headers = {'Authorization': f'Bearer {session["token"]}'}
        
        # Get podcasts
        response = requests.get(f"{API_BASE}/podcasts", headers=headers)
        if response.status_code == 200:
            podcasts_data = response.json()
            podcasts = podcasts_data.get('podcasts', [])
        
        # Get templates
        response = requests.get(f"{API_BASE}/templates", headers=headers)
        if response.status_code == 200:
            templates_data = response.json()
            templates = templates_data.get('templates', [])
    except Exception as e:
        podcasts = []
        templates = []
    
    return render_template('new_episode.html', podcasts=podcasts, templates=templates, token=session.get('token'))

@web_bp.route('/episodes/<episode_id>')
def episode_detail(episode_id):
    """Serve the episode detail page"""
    # Check if user is logged in
    if 'token' not in session:
        return redirect(url_for('web.login'))
    
    episode = None
    
    try:
        headers = {'Authorization': f'Bearer {session["token"]}'}
        response = requests.get(f"{API_BASE}/episodes/{episode_id}", headers=headers)
        if response.status_code == 200:
            episode_data = response.json()
            episode = episode_data.get('episode', episode_data)
    except Exception as e:
        episode = None
    
    if not episode:
        return redirect(url_for('web.episodes'))
    
    return render_template('episode_detail.html', episode=episode)

@web_bp.route('/admin')
def admin():
    """Serve the admin panel page"""
    # Check if user is logged in
    if 'token' not in session:
        return redirect(url_for('web.login'))
    
    stats = {}
    podcasts = []
    audio_files = []
    templates = []
    
    try:
        headers = {'Authorization': f'Bearer {session["token"]}'}
        
        # Get podcasts
        response = requests.get(f"{API_BASE}/podcasts", headers=headers)
        if response.status_code == 200:
            podcasts_data = response.json()
            podcasts = podcasts_data.get('podcasts', [])
        
        # Get episodes for stats
        response = requests.get(f"{API_BASE}/episodes", headers=headers)
        if response.status_code == 200:
            episodes_data = response.json()
            episodes = episodes_data.get('episodes', [])
            stats['total_episodes'] = len(episodes)
            stats['completed_episodes'] = len([e for e in episodes if e.get('status') == 'completed'])
            stats['processing_episodes'] = len([e for e in episodes if e.get('status') == 'processing'])
        
        # Get audio files
        response = requests.get(f"{API_BASE}/files", headers=headers)
        if response.status_code == 200:
            files_data = response.json()
            audio_files = files_data.get('files', [])
            stats['total_files'] = len(audio_files)
        
        # Get templates (if API exists)
        try:
            response = requests.get(f"{API_BASE}/templates", headers=headers)
            if response.status_code == 200:
                templates_data = response.json()
                templates = templates_data.get('templates', [])
        except:
            templates = []
            
    except Exception as e:
        stats = {'total_episodes': 0, 'completed_episodes': 0, 'processing_episodes': 0, 'total_files': 0}
        podcasts = []
        audio_files = []
        templates = []
    
    return render_template('admin.html', stats=stats, podcasts=podcasts, audio_files=audio_files, templates=templates, token=session.get('token'))

@web_bp.route('/admin/podcasts')
def admin_podcasts():
    """Serve the podcast management page"""
    # Check if user is logged in
    if 'token' not in session:
        return redirect(url_for('web.login'))
    
    podcasts = []
    
    try:
        headers = {'Authorization': f'Bearer {session["token"]}'}
        response = requests.get(f"{API_BASE}/podcasts", headers=headers)
        if response.status_code == 200:
            podcasts_data = response.json()
            podcasts = podcasts_data.get('podcasts', [])
    except Exception as e:
        podcasts = []
    
    return render_template('admin_podcasts.html', podcasts=podcasts, token=session.get('token'))

@web_bp.route('/admin/podcasts/new')
def admin_new_podcast():
    """Serve the new podcast creation page"""
    # Check if user is logged in
    if 'token' not in session:
        return redirect(url_for('web.login'))
    
    return render_template('admin_new_podcast.html', token=session.get('token'))

@web_bp.route('/admin/podcasts/<podcast_id>')
def admin_podcast_detail(podcast_id):
    """Serve the podcast detail/management page"""
    # Check if user is logged in
    if 'token' not in session:
        return redirect(url_for('web.login'))
    
    podcast = None
    
    try:
        headers = {'Authorization': f'Bearer {session["token"]}'}
        response = requests.get(f"{API_BASE}/podcasts/{podcast_id}", headers=headers)
        if response.status_code == 200:
            podcast = response.json()
    except Exception as e:
        podcast = None
    
    if not podcast:
        return redirect(url_for('web.admin_podcasts'))
    
    return render_template('admin_podcast_detail.html', podcast=podcast, token=session.get('token'))

@web_bp.route('/admin/templates')
def admin_templates():
    """Serve the template management page"""
    # Check if user is logged in
    if 'token' not in session:
        return redirect(url_for('web.login'))
    
    templates = []
    
    try:
        headers = {'Authorization': f'Bearer {session["token"]}'}
        response = requests.get(f"{API_BASE}/templates", headers=headers)
        if response.status_code == 200:
            templates_data = response.json()
            templates = templates_data.get('templates', [])
    except Exception as e:
        templates = []
    
    return render_template('admin_templates.html', templates=templates, token=session.get('token'))

@web_bp.route('/admin/templates/new')
def admin_new_template():
    """Serve the new template creation page"""
    # Check if user is logged in
    if 'token' not in session:
        return redirect(url_for('web.login'))
    
    podcasts = []
    
    try:
        headers = {'Authorization': f'Bearer {session["token"]}'}
        response = requests.get(f"{API_BASE}/podcasts", headers=headers)
        if response.status_code == 200:
            podcasts_data = response.json()
            podcasts = podcasts_data.get('podcasts', [])
    except Exception as e:
        podcasts = []
    
    return render_template('admin_new_template.html', podcasts=podcasts, token=session.get('token'))

@web_bp.route('/admin/templates/<template_id>')
def admin_template_detail(template_id):
    """Serve the template detail/management page"""
    # Check if user is logged in
    if 'token' not in session:
        return redirect(url_for('web.login'))
    
    template = None
    
    try:
        headers = {'Authorization': f'Bearer {session["token"]}'}
        response = requests.get(f"{API_BASE}/templates/{template_id}", headers=headers)
        if response.status_code == 200:
            template_data = response.json()
            template = template_data.get('template', template_data)
    except Exception as e:
        template = None
    
    if not template:
        return redirect(url_for('web.admin_templates'))
    
    return render_template('admin_template_detail.html', template=template, token=session.get('token'))

@web_bp.route('/admin/templates/<template_id>/edit')
def admin_template_edit(template_id):
    """Serve the template edit page"""
    # Check if user is logged in
    if 'token' not in session:
        return redirect(url_for('web.login'))
    
    template = None
    podcasts = []
    
    try:
        headers = {'Authorization': f'Bearer {session["token"]}'}
        
        # Get template
        response = requests.get(f"{API_BASE}/templates/{template_id}", headers=headers)
        if response.status_code == 200:
            template_data = response.json()
            template = template_data.get('template', template_data)
        
        # Get podcasts for the form
        response = requests.get(f"{API_BASE}/podcasts", headers=headers)
        if response.status_code == 200:
            podcasts_data = response.json()
            podcasts = podcasts_data.get('podcasts', [])
    except Exception as e:
        template = None
        podcasts = []
    
    if not template:
        return redirect(url_for('web.admin_templates'))
    
    return render_template('admin_edit_template.html', template=template, podcasts=podcasts, token=session.get('token'))

@web_bp.route('/admin/files')
def admin_files():
    """File management admin page"""
    # Check if user is logged in
    if 'token' not in session:
        return redirect(url_for('web.login'))
    
    return render_template('admin_files.html', token=session.get('token'))

@web_bp.route('/admin/audio-files/upload')
def admin_audio_upload():
    """Audio file upload page"""
    # Check if user is logged in
    if 'token' not in session:
        return redirect(url_for('web.login'))
    
    return render_template('admin_audio_upload.html', token=session.get('token'))

@web_bp.route('/admin/settings')
def admin_settings():
    """Settings management page"""
    # Check if user is logged in
    if 'token' not in session:
        return redirect(url_for('web.login'))
    
    return render_template('admin_settings.html', token=session.get('token'))
