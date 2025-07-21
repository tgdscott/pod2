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
from src.database.models_dev import Episode, Podcast, Template, Job, UserFile, User, File
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
            episode_number=data.get('episode_number'),
            season_number=data.get('season_number', 1),
            status='draft',
            episode_metadata=data.get('template_config', {}),  # Save template_config as episode_metadata
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


@episodes_bp.route('<episode_id>', methods=['GET'])
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


@episodes_bp.route('<episode_id>', methods=['PUT'])
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
        updatable_fields = ['title', 'description', 'episode_number', 'season_number', 'episode_metadata', 'audio_files', 'template_id']
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


@episodes_bp.route('<episode_id>/process', methods=['POST'])
@episodes_bp.route('<episode_id>/process/', methods=['POST'])
@jwt_required()
def process_episode(episode_id):
    import sys
    print(f"[TRACE] process_episode called for episode_id={episode_id}", file=sys.stderr)
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        data = request.get_json() or {}

        print(f"[TRACE] user_id={user_id}, episode_id={episode_id}", file=sys.stderr)
        # DEBUG: Print user_id and episode_id
        print(f"[DEBUG] process_episode: user_id={user_id}, episode_id={episode_id}")

        # Get episode with ownership check
        episode = db.query(Episode).join(Podcast).filter(
            Episode.id == episode_id,
            Podcast.user_id == user_id
        ).first()

        # DEBUG: Print if episode was found
        print(f"[DEBUG] process_episode: episode found? {bool(episode)}")

        if not episode:
            print(f"[DEBUG] process_episode: Episode not found for user {user_id}")
            return {'error': 'Episode not found'}, 404

        print("[DEBUG] process_episode: Passed episode check")

        if episode.status == 'processing':
            print("[DEBUG] process_episode: Episode already processing")
            return {'error': 'Episode is already being processed'}, 400

        # Get user for API keys
        user = db.query(User).get(user_id)
        print(f"[DEBUG] process_episode: user found? {bool(user)}")
        if not user:
            print(f"[DEBUG] process_episode: User not found: {user_id}")
            return {'error': 'User not found'}, 404

        # Get template if specified
        template = None
        if episode.template_id:
            template = db.query(Template).filter_by(
                id=episode.template_id,
                user_id=user_id
            ).first()
            print(f"[DEBUG] process_episode: template found? {bool(template)}")
            if not template:
                print(f"[DEBUG] process_episode: Template not found: {episode.template_id}")
                return {'error': 'Template not found'}, 404

        # Validate audio files exist
        audio_files = []
        for file_id in episode.audio_files:
            # Try UserFile first (legacy)
            user_file = db.query(UserFile).filter_by(
                id=file_id,
                user_id=user_id,
                file_type='audio'
            ).first()
            if user_file:
                upload_path = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
                file_path = upload_path / user_file.file_path
                if not file_path.exists():
                    print(f"[DEBUG] process_episode: Audio file {file_id} not found on disk (UserFile)")
                    return {'error': f'Audio file {file_id} not found on disk'}, 404
                audio_files.append(str(file_path))
                continue
            # Try File table (new)
            file = db.query(File).filter_by(
                id=file_id,
                user_id=user_id
            ).first()
            if file:
                upload_path = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
                file_path = upload_path / file.file_path
                if not file_path.exists():
                    print(f"[DEBUG] process_episode: Audio file {file_id} not found on disk (File)")
                    return {'error': f'Audio file {file_id} not found on disk'}, 404
                audio_files.append(str(file_path))
                continue
            print(f"[DEBUG] process_episode: Audio file {file_id} not found in UserFile or File table")
            return {'error': f'Audio file {file_id} not found'}, 404

        print(f"[DEBUG] process_episode: audio_files list: {audio_files}")
        if not audio_files:
            print("[DEBUG] process_episode: No valid audio files found")
            return {'error': 'No valid audio files found'}, 400

        # Create processing job
        print("[DEBUG] process_episode: Creating job")
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
        print("[DEBUG] process_episode: Job created and committed")

        # Start background processing with Celery
        try:
            db = get_db_session()
            from src.core.tasks import process_episode_task
            print(f"[TRACE] About to send task to celery for episode_id={episode_id}", file=sys.stderr)
            task = process_episode_task.apply_async(
                args=[episode_id, user_id, job.id],
                queue='episode_processing'
            )
            print(f"[TRACE] Task sent to celery with id {task.id}", file=sys.stderr)
            job.task_id = task.id
            db.commit()
            print(f"[TRACE] Job committed with celery task id {task.id}", file=sys.stderr)
        except Exception as queue_error:
            print(f"[TRACE] Celery queue error: {queue_error}", file=sys.stderr)
            job.status = 'failed'
            job.error_message = f"Failed to start processing: {str(queue_error)}"
            job.completed_at = datetime.now(timezone.utc)
            episode.status = 'failed'
            episode.updated_at = datetime.now(timezone.utc)
            db.commit()
            return {'error': f'Failed to start processing: {str(queue_error)}'}, 500

        print("[DEBUG] process_episode: Returning success response")
        return {
            'message': 'Episode processing started',
            'job_id': job.id,
            'task_id': job.task_id,
            'episode': episode.to_dict()
        }

    except Exception as e:
        print(f"[DEBUG] process_episode: Exception: {e}")
        import traceback
        print(f"[DEBUG] process_episode: Full traceback: {traceback.format_exc()}")
        return {'error': f'Failed to start processing: {str(e)}'}, 500


@episodes_bp.route('<episode_id>/download', methods=['GET'])
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


@episodes_bp.route('<episode_id>', methods=['DELETE'])
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


@episodes_bp.route('<episode_id>/generate-show-notes', methods=['POST'])
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


@episodes_bp.route('<episode_id>/transcribe', methods=['POST'])
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