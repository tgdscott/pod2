#!/usr/bin/env python3
"""
PodcastPro v2 Development Server
Quick start script for development
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after path setup
from src.api.app import create_app

if __name__ == '__main__':
    print("🎙️  Starting PodcastPro v2 Development Server")
    print("=" * 50)
    
    # Check if .env exists
    env_file = project_root / '.env'
    if not env_file.exists():
        print("⚠️  Warning: .env file not found!")
        print("   Copy .env.example to .env and configure your settings")
        print()
    
    try:
        app = create_app()
        print("✅ Flask app created successfully")
        print("🌐 Server will start at: http://localhost:5000")
        print("📋 API Documentation: See docs/API_SPEC.md")
        print("🏥 Health Check: http://localhost:5000/health")
        print()
        print("Registered routes:")
        for rule in app.url_map.iter_rules():
            print(f"{sorted(rule.methods)} {rule.rule}")
        print()
        print("Press Ctrl+C to stop the server")
        print("-" * 50)
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )
        
    except Exception as e:
        print(f"❌ Failed to start server: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your .env configuration")
        print("2. Ensure PostgreSQL is running")
        print("3. Verify database exists and is accessible")
        print("4. Check that all requirements are installed")
        sys.exit(1)
