"""
PodcastPro v2 Database Models
Multi-tenant podcast creation platform models
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, DateTime, 
    ForeignKey, BigInteger, JSON, CheckConstraint,
    UniqueConstraint
)
# Use string for UUID in SQLite, UUID in PostgreSQL
# For development with SQLite, always use String(36) for UUIDs
UUID = String(36)  # UUID as string
ARRAY = lambda x: Text  # Arrays as JSON strings
USING_POSTGRESQL = False
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class User(Base, TimestampMixin):
    """User accounts and authentication"""
    __tablename__ = 'users'
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True))
    
    # User preferences and settings
    settings = Column(JSON, default=dict)
    
    # Encrypted API keys
    elevenlabs_key = Column(Text)
    gemini_key = Column(Text)
    hosting_keys = Column(JSON, default=dict)
    
    # Relationships
    podcasts = relationship("Podcast", back_populates="user", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="user", cascade="all, delete-orphan")
    user_files = relationship("UserFile", back_populates="user", cascade="all, delete-orphan")
    template_segments = relationship("TemplateSegment", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password: str) -> None:
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format"""
        if '@' not in email:
            raise ValueError("Invalid email address")
        return email.lower()
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        parts = [self.first_name, self.last_name]
        return ' '.join(part for part in parts if part)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat(),
            'settings': self.settings
        }


class Podcast(Base, TimestampMixin):
    """Podcast-level configuration and metadata"""
    __tablename__ = 'podcasts'
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='unique_user_podcast_name'),
    )
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Basic metadata
    name = Column(String(200), nullable=False)
    description = Column(Text)
    author = Column(String(200))
    category = Column(String(100))
    language = Column(String(10), default='en')
    explicit = Column(Boolean, default=False)
    
    # Default settings
    default_template_id = Column(UUID, ForeignKey('templates.id', ondelete='SET NULL'))
    
    # Publishing settings
    auto_publish = Column(Boolean, default=False)
    hosting_platform = Column(String(50))  # 'spreaker', 'anchor', etc.
    hosting_config = Column(JSON, default=dict)
    
    # Metadata
    cover_art_url = Column(Text)
    website_url = Column(Text)
    rss_url = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="podcasts")
    episodes = relationship("Episode", back_populates="podcast", cascade="all, delete-orphan")
    default_template = relationship("Template", foreign_keys=[default_template_id])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'title': self.name,  # API expects 'title' but model uses 'name'
            'name': self.name,
            'description': self.description,
            'author': self.author,
            'category': self.category,
            'language': self.language,
            'explicit': self.explicit,
            'auto_publish': self.auto_publish,
            'hosting_platform': self.hosting_platform,
            'cover_art_url': self.cover_art_url,
            'website_url': self.website_url,
            'rss_url': self.rss_url,
            'episode_count': len(self.episodes) if self.episodes else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Template(Base, TimestampMixin):
    """Reusable podcast episode structures"""
    __tablename__ = 'templates'
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='unique_user_template_name'),
    )
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Template structure as JSON
    structure = Column(JSON, nullable=False)
    
    # Template sharing
    is_public = Column(Boolean, default=False, index=True)
    is_system_default = Column(Boolean, default=False, index=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="templates")
    episodes = relationship("Episode", back_populates="template")
    podcasts_using_as_default = relationship("Podcast", foreign_keys=[Podcast.default_template_id])
    
    @validates('structure')
    def validate_structure(self, key, structure):
        """Validate template structure"""
        if not isinstance(structure, dict):
            raise ValueError("Template structure must be a dictionary")
        
        required_keys = ['version', 'segments']
        for req_key in required_keys:
            if req_key not in structure:
                raise ValueError(f"Template structure missing required key: {req_key}")
        
        return structure
    
    def increment_usage(self) -> None:
        """Increment usage counter"""
        self.usage_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'structure': self.structure,
            'is_public': self.is_public,
            'is_system_default': self.is_system_default,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Episode(Base, TimestampMixin):
    """Individual podcast episodes and their metadata"""
    __tablename__ = 'episodes'
    __table_args__ = (
        UniqueConstraint('podcast_id', 'episode_number', name='unique_podcast_episode_number'),
        CheckConstraint('duration >= 0', name='check_positive_duration'),
        CheckConstraint('file_size_bytes >= 0', name='check_positive_file_size'),
    )
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    podcast_id = Column(UUID, ForeignKey('podcasts.id', ondelete='CASCADE'), nullable=False, index=True)
    template_id = Column(UUID, ForeignKey('templates.id', ondelete='SET NULL'))
    
    # Content and processing
    audio_files = Column(JSON, default=list)  # List of UserFile IDs
    output_file = Column(Text)  # Path to processed audio
    episode_metadata = Column(JSON, default=dict)
    
    # Episode metadata
    title = Column(String(300), nullable=False)
    description = Column(Text)
    episode_number = Column(Integer)
    season_number = Column(Integer, default=1)
    
    # Content URLs  
    show_notes = Column(Text)
    transcript = Column(Text)
    
    # Publishing
    status = Column(String(20), default='draft', index=True)  # draft, processing, ready, completed, failed, published
    published_at = Column(DateTime(timezone=True), index=True)
    scheduled_publish_at = Column(DateTime(timezone=True), index=True)
    
    # Processing results
    duration = Column(Integer)  # Duration in seconds
    file_size_bytes = Column(BigInteger)
    
    # Relationships
    podcast = relationship("Podcast", back_populates="episodes")
    template = relationship("Template", back_populates="episodes")
    jobs = relationship("Job", back_populates="episode", cascade="all, delete-orphan")
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate episode status"""
        valid_statuses = ['draft', 'processing', 'ready', 'completed', 'failed', 'published']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return status
    
    @property
    def is_published(self) -> bool:
        """Check if episode is published"""
        return self.status == 'published' and self.published_at is not None
    
    @property
    def duration_formatted(self) -> Optional[str]:
        """Get duration in HH:MM:SS format"""
        if not self.duration:
            return None
        
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'podcast_id': str(self.podcast_id),
            'template_id': str(self.template_id) if self.template_id else None,
            'title': self.title,
            'description': self.description,
            'episode_number': self.episode_number,
            'season_number': self.season_number,
            'status': self.status,
            'audio_files': self.audio_files or [],
            'output_file': self.output_file,
            'episode_metadata': self.episode_metadata or {},
            'show_notes': self.show_notes,
            'transcript': self.transcript,
            'duration': self.duration,
            'duration_formatted': self.duration_formatted,
            'file_size_bytes': self.file_size_bytes,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'scheduled_publish_at': self.scheduled_publish_at.isoformat() if self.scheduled_publish_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Job(Base, TimestampMixin):
    """Processing job queue and status tracking"""
    __tablename__ = 'jobs'
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    episode_id = Column(UUID, ForeignKey('episodes.id', ondelete='CASCADE'), nullable=True, index=True)
    
    # Job details
    job_type = Column(String(50), nullable=False)
    status = Column(String(20), default='queued', index=True)  # queued, processing, completed, failed, cancelled
    priority = Column(Integer, default=0)
    task_id = Column(String(255), nullable=True, index=True)  # Celery task ID
    
    # Job data
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    
    # Progress tracking
    progress_percent = Column(Integer, default=0)
    current_step = Column(String(100))
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Relationships
    user = relationship("User")
    episode = relationship("Episode", back_populates="jobs")
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate job status"""
        valid_statuses = ['queued', 'processing', 'completed', 'failed', 'cancelled']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return status
    
    @validates('progress_percent')
    def validate_progress(self, key, progress):
        """Validate progress percentage"""
        if not (0 <= progress <= 100):
            raise ValueError("Progress must be between 0 and 100")
        return progress
    
    @property
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return self.status == 'failed' and self.retry_count < self.max_retries
    
    @property
    def is_active(self) -> bool:
        """Check if job is currently active"""
        return self.status in ['queued', 'processing']
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'episode_id': str(self.episode_id) if self.episode_id else None,
            'job_type': self.job_type,
            'status': self.status,
            'priority': self.priority,
            'progress_percent': self.progress_percent,
            'current_step': self.current_step,
            'input_data': self.input_data or {},
            'output_data': self.output_data or {},
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'can_retry': self.can_retry,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class UserFile(Base, TimestampMixin):
    """File management and tracking"""
    __tablename__ = 'user_files'
    __table_args__ = (
        CheckConstraint('file_size > 0', name='check_positive_file_size'),
    )
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # File details
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)  # Relative path from upload root
    file_type = Column(String(50), nullable=False)  # 'audio', 'image', 'document'
    mime_type = Column(String(100))
    file_size = Column(BigInteger, nullable=False)
    
    # Usage tracking
    reference_type = Column(String(50))  # 'episode_audio', 'cover_art', 'intro_audio', etc.
    reference_id = Column(UUID)
    
    # Relationships
    user = relationship("User", back_populates="user_files")
    
    @validates('file_type')
    def validate_file_type(self, key, file_type):
        """Validate file type"""
        valid_types = ['audio', 'image', 'document']
        if file_type not in valid_types:
            raise ValueError(f"Invalid file type. Must be one of: {valid_types}")
        return file_type
    
    @property
    def size_formatted(self) -> str:
        """Get file size in human-readable format"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'file_type': self.file_type,
            'mime_type': self.mime_type,
            'file_size': self.file_size,
            'size_formatted': self.size_formatted,
            'reference_type': self.reference_type,
            'reference_id': str(self.reference_id) if self.reference_id else None,
            'created_at': self.created_at.isoformat()
        }


class TemplateSegment(Base, TimestampMixin):
    """Reusable audio segments for templates"""
    __tablename__ = 'template_segments'
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='unique_user_segment_name'),
    )
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Segment details
    name = Column(String(200), nullable=False)
    segment_type = Column(String(50), nullable=False, index=True)  # 'intro', 'outro', 'commercial', 'transition'
    description = Column(Text)
    
    # Audio content
    audio_file_id = Column(UUID, ForeignKey('user_files.id', ondelete='SET NULL'))
    
    # Dynamic content settings
    has_dynamic_content = Column(Boolean, default=False)
    dynamic_content_config = Column(JSON, default=dict)
    
    # Usage and sharing
    is_public = Column(Boolean, default=False, index=True)
    usage_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="template_segments")
    audio_file = relationship("UserFile", foreign_keys=[audio_file_id])
    
    @validates('segment_type')
    def validate_segment_type(self, key, segment_type):
        """Validate segment type"""
        valid_types = ['intro', 'outro', 'commercial', 'transition', 'custom']
        if segment_type not in valid_types:
            raise ValueError(f"Invalid segment type. Must be one of: {valid_types}")
        return segment_type
    
    def increment_usage(self) -> None:
        """Increment usage counter"""
        self.usage_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'name': self.name,
            'segment_type': self.segment_type,
            'description': self.description,
            'audio_file_id': str(self.audio_file_id) if self.audio_file_id else None,
            'has_dynamic_content': self.has_dynamic_content,
            'dynamic_content_config': self.dynamic_content_config,
            'is_public': self.is_public,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
