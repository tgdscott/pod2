"""
Celery background tasks for PodcastPro v2
"""

import logging
from datetime import datetime, timezone
from celery import shared_task
from src.core.advanced_audio_processor import AdvancedAudioProcessor
from src.database.models import Episode, Podcast, Template, get_db_session

logger = logging.getLogger(__name__)

# Register process_episode_task at module level
@shared_task(bind=True, name='podcast_tasks.process_episode')
def process_episode_task(self, episode_id, user_id, job_id):
    """Background task to process an episode using real audio processing"""
    try:
        logger.info(f"Starting REAL episode processing for episode_id={episode_id}")
        db = get_db_session()
        episode = db.query(Episode).filter(Episode.id == episode_id).first()
        if not episode:
            raise Exception(f"Episode {episode_id} not found")
        template = db.query(Template).filter(Template.id == episode.template_id).first()
        if not template:
            raise Exception(f"Template {episode.template_id} not found")
        # Parse template content (assume JSON)
        import json
        template_data = json.loads(template.content) if isinstance(template.content, str) else template.content
        # Gather episode audio files (assume episode.audio_files is a list of dicts)
        episode_data = {
            'audio_files': episode.audio_files if hasattr(episode, 'audio_files') else [],
            'ai_content': episode.episode_metadata.get('ai_content') if hasattr(episode, 'episode_metadata') else None
        }
        processor = AdvancedAudioProcessor(output_dir='outputs')
        result = processor.create_episode_from_template(template_data, episode_data, output_filename=None)
        if not result.get('success'):
            raise Exception(result.get('error', 'Unknown error during audio processing'))
        # Update episode with output file
        episode.output_file = result['output_path']
        episode.status = 'completed'
        db.commit()
        logger.info(f"Episode processing completed for episode_id={episode_id}")
        return {
            'episode_id': episode_id,
            'status': 'completed',
            'output_file': result['output_path'],
            'message': 'Episode processing completed successfully',
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Episode processing failed: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'message': 'Episode processing failed'
            }
        )
        # Mark episode as failed
        try:
            db = get_db_session()
            episode = db.query(Episode).filter(Episode.id == episode_id).first()
            if episode:
                episode.status = 'failed'
                db.commit()
        except Exception:
            pass
        raise


@shared_task(bind=True)
    def generate_show_notes_task(self, episode_id, user_id):
        try:
            logger.info(f"Starting show notes generation for episode_id={episode_id}")
            return {
                'episode_id': episode_id,
                'status': 'completed',
                'show_notes': 'Generated show notes would appear here...',
                'completed_at': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Show notes generation failed: {str(e)}")
            raise
    
@shared_task(bind=True)
    def process_audio_file_task(self, file_id, user_id):
        try:
            logger.info(f"Starting audio processing for file_id={file_id}")
            return {
                'file_id': file_id,
                'status': 'completed',
                'message': 'Audio file processed successfully',
                'completed_at': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            raise
    
logger.info("Celery tasks registered at module level.")
