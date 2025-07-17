#!/usr/bin/env python3
"""
Database Recreation Script
Safely recreates the database with the correct schema
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def recreate_database():
    """Recreate the database with correct schema"""
    
    print("🔧 DATABASE RECREATION")
    print("=" * 50)
    
    # Check if database exists
    db_path = "podcastpro_dev.db"
    
    if os.path.exists(db_path):
        print(f"📁 Found existing database: {db_path}")
        
        # Try to remove it
        try:
            os.remove(db_path)
            print("✅ Old database removed")
        except PermissionError:
            print("❌ Cannot remove database - server may still be running")
            print("📋 Please stop the Flask server first:")
            print("   1. Press Ctrl+C in the server terminal")
            print("   2. Or close the terminal running 'python run.py'")
            print("   3. Then run this script again")
            return False
        except Exception as e:
            print(f"❌ Error removing database: {e}")
            return False
    else:
        print("📁 No existing database found")
    
    # Import database modules
    try:
        from src.database import init_database
        from src.database.models_dev import Base
        print("✅ Database modules imported")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Create new database
    try:
        print("🔨 Creating new database...")
        
        # Create a Flask app for database initialization
        from src.api.app import create_app
        app = create_app('development')
        
        with app.app_context():
            init_database(app)
        
        print("✅ Database created successfully")
        
        # Verify database was created
        if os.path.exists(db_path):
            print(f"✅ Database file exists: {db_path}")
            
            # Get file size
            size = os.path.getsize(db_path)
            print(f"📊 Database size: {size:,} bytes")
            
            return True
        else:
            print("❌ Database file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def test_database():
    """Test basic database operations"""
    print("\n🧪 TESTING DATABASE")
    print("=" * 50)
    
    try:
        from src.database import get_db_session
        from src.database.models_dev import User, Podcast, Episode
        
        # Test database connection
        db = get_db_session()
        print("✅ Database connection successful")
        
        # Test user creation
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        user.set_password("testpassword")
        
        db.add(user)
        db.commit()
        print("✅ User creation successful")
        
        # Test podcast creation
        podcast = Podcast(
            user_id=user.id,
            name="Test Podcast",
            description="A test podcast",
            author="Test User",
            category="Technology",
            language="en"
        )
        
        db.add(podcast)
        db.commit()
        print("✅ Podcast creation successful")
        
        # Test episode creation
        episode = Episode(
            podcast_id=podcast.id,
            title="Test Episode",
            description="A test episode"
        )
        
        db.add(episode)
        db.commit()
        print("✅ Episode creation successful")
        
        print(f"📊 Test data created:")
        print(f"   User ID: {user.id}")
        print(f"   Podcast ID: {podcast.id}")
        print(f"   Episode ID: {episode.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting database recreation process...")
    
    if recreate_database():
        print("\n🎉 Database recreation successful!")
        
        if test_database():
            print("\n🎉 Database tests passed!")
            print("\n📋 Next steps:")
            print("   1. Start the Flask server: python run.py")
            print("   2. Test the APIs with: python debug_final.py")
            print("   3. Try the setup wizard at: http://localhost:5000/setup")
        else:
            print("\n⚠️ Database tests failed - check for schema issues")
    else:
        print("\n❌ Database recreation failed")
        print("Make sure the Flask server is stopped and try again")
