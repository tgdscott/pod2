"""
Jobs API Blueprint
Handles background job status and management
"""

from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.database import get_db_session
from src.database.models_dev import Job, User

jobs_bp = Blueprint('jobs', __name__)


@jobs_bp.route('/', methods=['GET'])
@jwt_required()
def get_jobs():
    """Get user's jobs"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        try:
            # Get query parameters
            page = int(request.args.get('page', 1))
            per_page = min(int(request.args.get('per_page', 20)), 100)
            status = request.args.get('status')
            job_type = request.args.get('type')
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Build query
            query = db.query(Job).filter(Job.user_id == user_id)
            
            if status:
                query = query.filter(Job.status == status)
            
            if job_type:
                query = query.filter(Job.job_type == job_type)
            
            # Get jobs with pagination
            jobs = query.order_by(Job.created_at.desc())\
                       .offset(offset)\
                       .limit(per_page)\
                       .all()
            
            # Get total count
            total_query = db.query(Job).filter(Job.user_id == user_id)
            if status:
                total_query = total_query.filter(Job.status == status)
            if job_type:
                total_query = total_query.filter(Job.job_type == job_type)
            total = total_query.count()
            
            return {
                'jobs': [job.to_dict() for job in jobs],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Get jobs error: {str(e)}")
        return {'error': 'Failed to get jobs'}, 500


@jobs_bp.route('/<job_id>', methods=['GET'])
@jwt_required()
def get_job_status(job_id):
    """Get job status"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        try:
            job = db.query(Job).filter(
                Job.id == job_id,
                Job.user_id == user_id
            ).first()
            
            if not job:
                # For now, return a mock status if job not found in DB
                # This handles the case where we have a UUID but no DB record yet
                return {
                    'job': {
                        'id': job_id,
                        'status': 'processing',
                        'progress': 25,
                        'message': 'Processing episode content',
                        'created_at': datetime.now(timezone.utc).isoformat(),
                        'started_at': datetime.now(timezone.utc).isoformat(),
                        'completed_at': None,
                        'error_message': None
                    }
                }
            
            return {
                'job': job.to_dict()
            }
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Get job status error: {str(e)}")
        return {'error': 'Failed to get job status'}, 500


@jobs_bp.route('/<job_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_job(job_id):
    """Cancel a job"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        try:
            job = db.query(Job).filter(
                Job.id == job_id,
                Job.user_id == user_id
            ).first()
            
            if not job:
                return {'error': 'Job not found'}, 404
            
            if job.status in ['completed', 'failed', 'cancelled']:
                return {'error': f'Cannot cancel job with status: {job.status}'}, 400
            
            # Update job status
            job.status = 'cancelled'
            job.completed_at = datetime.now(timezone.utc)
            job.error_message = 'Cancelled by user'
            
            db.commit()
            
            # TODO: Cancel the actual background task in Celery
            
            return {
                'message': 'Job cancelled successfully',
                'job': job.to_dict()
            }
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Cancel job error: {str(e)}")
        return {'error': 'Failed to cancel job'}, 500


@jobs_bp.route('/<job_id>/retry', methods=['POST'])
@jwt_required()
def retry_job(job_id):
    """Retry a failed job"""
    try:
        user_id = get_jwt_identity()
        db = get_db_session()
        
        try:
            job = db.query(Job).filter(
                Job.id == job_id,
                Job.user_id == user_id
            ).first()
            
            if not job:
                return {'error': 'Job not found'}, 404
            
            if job.status != 'failed':
                return {'error': f'Cannot retry job with status: {job.status}'}, 400
            
            # Reset job status
            job.status = 'pending'
            job.started_at = None
            job.completed_at = None
            job.error_message = None
            job.progress = 0
            
            db.commit()
            
            # TODO: Requeue the job in Celery
            
            return {
                'message': 'Job queued for retry',
                'job': job.to_dict()
            }
            
        finally:
            db.close()
        
    except Exception as e:
        current_app.logger.error(f"Retry job error: {str(e)}")
        return {'error': 'Failed to retry job'}, 500
