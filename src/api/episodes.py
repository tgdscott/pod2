"""
Episodes API Blueprint
Handles episode creation, management, and processing
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.database import get_db_session
from src.database.models_dev import Episode, Podcast, Template, Job, UserFile, User
from ..core import PodcastProcessor

episodes_bp = Blueprint('episodes', __name__)


@episodes_bp.route('/', methods=['GET'])
@jwt_required()
def get_episodes():
    """Get user's episodes"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()

        # Get query parameters
        podcast_id = request.args.get('podcast_id')
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        # Calculate offset
        offset = (page - 1) * per_page

        # Build query
        query = db.query(Episode).join(Podcast).filter(Podcast.user_id == user_id)

        if podcast_id:
            query = query.filter(Episode.podcast_id == podcast_id)

        if status:
            query = query.filter(Episode.status == status)

        # Get episodes with pagination
        episodes = query.order_by(Episode.created_at.desc())\
                         .offset(offset)\
                         .limit(per_page)\
                         .all()

        # Get total count
        total_query = db.query(Episode).join(Podcast).filter(Podcast.user_id == user_id)
        if podcast_id:
            total_query = total_query.filter(Episode.podcast_id == podcast_id)
        if status:
            total_query = total_query.filter(Episode.status == status)
        total = total_query.count()
        pages = (total + per_page - 1) // per_page

        return {
            'episodes': [ep.to_dict() for ep in episodes],
            'pagination': {
                'page': page,
                'pages': pages,
                'per_page': per_page,
                'total': total
            }
        }

    except Exception as e:
        current_app.logger.error(f"Episodes listing error: {str(e)}")
        return {'error': 'Failed to list episodes'}, 500


@episodes_bp.route('/', methods=['POST'])
@jwt_required()
def create_episode():
    """Create new episode"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        data = request.get_json()

        # Validate required fields
        required_fields = ['title', 'podcast_id']
        for field in required_fields:
            if field not in data:
                return {'error': f'Missing required field: {field}'}, 400

        # Verify podcast ownership
        podcast = db.query(Podcast).filter_by(
            id=data['podcast_id'],
            user_id=user_id
        ).first()

        if not podcast:
            return {'error': 'Podcast not found'}, 404

        # Create episode
        episode = Episode(
            id=str(uuid.uuid4()),
            podcast_id=data['podcast_id'],
            title=data['title'],
            description=data.get('description', ''),
            status='draft',
            episode_metadata=data.get('metadata', {}),
            audio_files=data.get('audio_files', []),
            template_id=data.get('template_id')
        )

        db.add(episode)
        db.commit()

        return {
            'message': 'Episode created successfully',
            'episode': episode.to_dict()
        }, 201

    except Exception as e:
        current_app.logger.error(f"Episode creation error: {str(e)}")
        return {'error': 'Failed to create episode'}, 500


@episodes_bp.route('/<episode_id>', methods=['GET'])
@jwt_required()
def get_episode(episode_id):
    """Get specific episode"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()

        # Get episode with ownership check
        episode = db.query(Episode).join(Podcast).filter(
            Episode.id == episode_id,
            Podcast.user_id == user_id
        ).first()

        if not episode:
            return {'error': 'Episode not found'}, 404

        return {'episode': episode.to_dict()}

    except Exception as e:
        current_app.logger.error(f"Episode retrieval error: {str(e)}")
        return {'error': 'Failed to get episode'}, 500


@episodes_bp.route('/<episode_id>', methods=['PUT'])
@jwt_required()
def update_episode(episode_id):
    """Update episode"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        data = request.get_json()

        # Get episode with ownership check
        episode = db.query(Episode).join(Podcast).filter(
            Episode.id == episode_id,
            Podcast.user_id == user_id
        ).first()

        if not episode:
            return {'error': 'Episode not found'}, 404

        # Update allowed fields
        updatable_fields = ['title', 'description', 'episode_metadata', 'audio_files', 'template_id']
        for field in updatable_fields:
            if field in data:
                setattr(episode, field, data[field])

        episode.updated_at = datetime.now(timezone.utc)
        db.commit()

        return {
            'message': 'Episode updated successfully',
            'episode': episode.to_dict()
        }

    except Exception as e:
        current_app.logger.error(f"Episode update error: {str(e)}")
        return {'error': 'Failed to update episode'}, 500


@episodes_bp.route('/<episode_id>/process', methods=['POST'])
@jwt_required()
def process_episode(episode_id):
    """Start processing episode"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        data = request.get_json() or {}

        # Get episode with ownership check
        episode = db.query(Episode).join(Podcast).filter(
            Episode.id == episode_id,
            Podcast.user_id == user_id
        ).first()

        if not episode:
            return {'error': 'Episode not found'}, 404

        if episode.status == 'processing':
            return {'error': 'Episode is already being processed'}, 400

        # Get user for API keys
        user = db.query(User).get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        # Get template if specified
        template = None
        if episode.template_id:
            template = db.query(Template).filter_by(
                id=episode.template_id,
                user_id=user_id
            ).first()

            if not template:
                return {'error': 'Template not found'}, 404

        # Validate audio files exist
        audio_files = []
        for file_id in episode.audio_files:
            user_file = db.query(UserFile).filter_by(
                id=file_id,
                user_id=user_id,
                file_type='audio'
            ).first()

            if not user_file:
                return {'error': f'Audio file {file_id} not found'}, 404

            # Get full file path
            upload_path = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
            file_path = upload_path / user_file.file_path

            if not file_path.exists():
                return {'error': f'Audio file {file_id} not found on disk'}, 404

            audio_files.append(str(file_path))

        if not audio_files:
            return {'error': 'No valid audio files found'}, 400

        # Create processing job
        job = Job(
            id=str(uuid.uuid4()),
            user_id=user_id,
            episode_id=episode_id,
            job_type='episode_processing',
            status='queued',
            input_data={
                'episode_id': episode_id,
                'audio_files': audio_files,
                'template_id': episode.template_id,
                'options': data.get('options', {})
            }
        )

        db.add(job)

        # Update episode status
        episode.status = 'processing'
        episode.updated_at = datetime.now(timezone.utc)

        db.commit()

        # Start background processing with Celery
        try:
            # Re-get the db session to ensure it's fresh for the Celery task context if needed
            # This line might not be strictly necessary if get_db_session always returns a new session
            # or manages session lifecycle correctly for background tasks.
            # However, for demonstration, keeping it here as it was in the original.
            db = get_db_session() 
            from src.api.app import celery

            # Queue episode processing task
            task = celery.send_task(
                'podcast_tasks.process_episode',
                args=[episode_id, user_id, job.id],
                queue='episode_processing'
            )

            # Store task ID in job
            job.task_id = task.id
            db.commit()

            current_app.logger.info(f"Queued episode processing task {task.id} for episode {episode_id}")

        except Exception as queue_error:
            current_app.logger.error(f"Failed to queue episode processing: {str(queue_error)}")

            # Update job with error
            job.status = 'failed'
            job.error_message = f"Failed to start processing: {str(queue_error)}"
            job.completed_at = datetime.now(timezone.utc)

            # Update episode
            episode.status = 'failed'
            episode.updated_at = datetime.now(timezone.utc)

            db.commit()

            return {'error': f'Failed to start processing: {str(queue_error)}'}, 500

        return {
            'message': 'Episode processing started',
            'job_id': job.id,
            'task_id': job.task_id,
            'episode': episode.to_dict()
        }

    except Exception as e:
        current_app.logger.error(f"Episode processing start error: {str(e)}")
        import traceback
        current_app.logger.error(f"Full traceback: {traceback.format_exc()}")
        return {'error': f'Failed to start processing: {str(e)}'}, 500


@episodes_bp.route('/<episode_id>/download', methods=['GET'])
@jwt_required()
def download_episode(episode_id):
    """Download processed episode"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()

        # Get episode with ownership check
        episode = db.query(Episode).join(Podcast).filter(
            Episode.id == episode_id,
            Podcast.user_id == user_id
        ).first()

        if not episode:
            return {'error': 'Episode not found'}, 404

        if episode.status != 'completed' or not episode.output_file:
            return {'error': 'Episode not ready for download'}, 400

        # Check if file exists
        output_file = Path(episode.output_file)
        if not output_file.exists():
            return {'error': 'Output file not found'}, 404

        return send_file(
            str(output_file),
            as_attachment=True,
            download_name=f"{episode.title}.mp3",
            mimetype='audio/mpeg'
        )

    except Exception as e:
        current_app.logger.error(f"Episode download error: {str(e)}")
        return {'error': 'Failed to download episode'}, 500


@episodes_bp.route('/<episode_id>', methods=['DELETE'])
@jwt_required()
def delete_episode(episode_id):
    """Delete episode"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()

        # Get episode with ownership check
        episode = db.query(Episode).join(Podcast).filter(
            Episode.id == episode_id,
            Podcast.user_id == user_id
        ).first()

        if not episode:
            return {'error': 'Episode not found'}, 404

        # Delete output file if it exists
        if episode.output_file:
            output_file = Path(episode.output_file)
            if output_file.exists():
                output_file.unlink()

        # Delete related jobs
        db.query(Job).filter_by(episode_id=episode_id).delete()

        # Delete episode
        db.delete(episode)
        db.commit()

        return {'message': 'Episode deleted successfully'}

    except Exception as e:
        current_app.logger.error(f"Episode deletion error: {str(e)}")
        return {'error': 'Failed to delete episode'}, 500


@episodes_bp.route('/<episode_id>/generate-show-notes', methods=['POST'])
@jwt_required()
def generate_show_notes(episode_id):
    """Generate show notes for episode using AI"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()

        # Get episode with ownership check
        episode = db.query(Episode).join(Podcast).filter(
            Episode.id == episode_id,
            Podcast.user_id == user_id
        ).first()

        if not episode:
            return {'error': 'Episode not found'}, 404

        # Create processing job
        job = Job(
            id=str(uuid.uuid4()),
            user_id=user_id,
            episode_id=episode_id,
            job_type='show_notes_generation',
            status='queued'
        )

        db.add(job)
        db.commit()

        # Queue show notes generation task
        try:
            from src.api.app import celery

            task = celery.send_task(
                'podcast_tasks.generate_show_notes',
                args=[episode_id, user_id, job.id],
                queue='ai_processing'
            )

            job.task_id = task.id
            db.commit()

            return {
                'message': 'Show notes generation started',
                'job_id': job.id,
                'task_id': job.task_id
            }

        except Exception as queue_error:
            current_app.logger.error(f"Failed to queue show notes generation: {str(queue_error)}")

            job.status = 'failed'
            job.error_message = f"Failed to start generation: {str(queue_error)}"
            db.commit()

            return {'error': f'Failed to start generation: {str(queue_error)}'}, 500

    except Exception as e:
        current_app.logger.error(f"Show notes generation error: {str(e)}")
        return {'error': str(e)}, 500


@episodes_bp.route('/<episode_id>/transcribe', methods=['POST'])
@jwt_required()
def transcribe_episode(episode_id):
    """Transcribe episode audio using AI"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()

        # Get episode with ownership check
        episode = db.query(Episode).join(Podcast).filter(
            Episode.id == episode_id,
            Podcast.user_id == user_id
        ).first()

        if not episode:
            return {'error': 'Episode not found'}, 404

        if not episode.output_file:
            return {'error': 'Episode must be processed before transcription'}, 400

        # Create processing job
        job = Job(
            id=str(uuid.uuid4()),
            user_id=user_id,
            episode_id=episode_id,
            job_type='transcription',
            status='queued'
        )

        db.add(job)
        db.commit()

        # Queue transcription task
        try:
            from src.api.app import celery

            task = celery.send_task(
                'podcast_tasks.transcribe_audio',
                args=[episode_id, user_id, job.id],
                queue='ai_processing'
            )

            job.task_id = task.id
            db.commit()

            return {
                'message': 'Transcription started',
                'job_id': job.id,
                'task_id': job.task_id
            }

        except Exception as queue_error:
            current_app.logger.error(f"Failed to queue transcription: {str(queue_error)}")

            job.status = 'failed'
            job.error_message = f"Failed to start transcription: {str(queue_error)}"
            db.commit()

            return {'error': f'Failed to start transcription: {str(queue_error)}'}, 500

    except Exception as e:
        current_app.logger.error(f"Transcription error: {str(e)}")
        return {'error': str(e)}, 500