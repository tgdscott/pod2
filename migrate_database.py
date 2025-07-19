#!/usr/bin/env python3
"""
Database Migration Script
Adds new API key and voice settings columns to User table
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_database():
    """Run database migrations"""
    print("🔄 Starting database migration...")
    
    # Create database engine
    database_url = os.getenv('DATABASE_URL', 'sqlite:///podcastpro_dev.db')
    engine = create_engine(database_url)
    
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if columns already exist
        inspector = inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('users')]
        
        print(f"📋 Existing columns: {existing_columns}")
        
        # Add missing columns
        new_columns = [
            ('elevenlabs_api_key', 'TEXT'),
            ('gemini_api_key', 'TEXT'),
            ('openai_api_key', 'TEXT'),
            ('spreaker_api_key', 'TEXT'),
            ('default_voice_id', 'VARCHAR(100)'),
            ('default_voice_stability', 'INTEGER DEFAULT 50')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                print(f"➕ Adding column: {column_name}")
                if database_url.startswith('sqlite'):
                    # SQLite syntax
                    session.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
                else:
                    # PostgreSQL syntax
                    session.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
                session.commit()
                print(f"✅ Added column: {column_name}")
            else:
                print(f"⏭️  Column already exists: {column_name}")
        
        # Rename old columns if they exist
        old_to_new = {
            'elevenlabs_key': 'elevenlabs_api_key',
            'gemini_key': 'gemini_api_key'
        }
        
        for old_name, new_name in old_to_new.items():
            if old_name in existing_columns and new_name not in existing_columns:
                print(f"🔄 Renaming column: {old_name} -> {new_name}")
                if database_url.startswith('sqlite'):
                    # SQLite doesn't support RENAME COLUMN directly, so we'll skip this
                    print(f"⚠️  SQLite doesn't support column renaming. Please manually rename {old_name} to {new_name}")
                else:
                    session.execute(text(f"ALTER TABLE users RENAME COLUMN {old_name} TO {new_name}"))
                    session.commit()
                print(f"✅ Renamed column: {old_name} -> {new_name}")
        
        print("🎉 Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == '__main__':
    migrate_database() 