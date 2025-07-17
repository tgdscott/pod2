"""
Database initialization and session management for PodcastPro v2
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

from .models import Base

# Global variables for database connection
engine = None
SessionLocal = None


def init_database(app):
    """Initialize database connection and create tables"""
    global engine, SessionLocal
    
    # Get database URL from config
    database_url = app.config.get('DATABASE_URL', 'sqlite:///podcastpro_dev.db')
    
    # For SQLite, we need special configuration
    if database_url.startswith('sqlite'):
        engine = create_engine(
            database_url,
            poolclass=StaticPool,
            connect_args={
                "check_same_thread": False,
            },
            echo=app.config.get('DEBUG', False)
        )
    else:
        # PostgreSQL configuration
        engine = create_engine(
            database_url,
            pool_size=app.config.get('DATABASE_POOL_SIZE', 10),
            pool_timeout=app.config.get('DATABASE_POOL_TIMEOUT', 30),
            echo=app.config.get('DEBUG', False)
        )
    
    # Create session factory
    SessionLocal = scoped_session(sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    ))
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Store in app context for cleanup
    app.teardown_appcontext(shutdown_session)


def get_db_session():
    """Get a database session"""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return SessionLocal()


def shutdown_session(exception=None):
    """Clean up database session on app teardown"""
    if SessionLocal is not None:
        SessionLocal.remove()
