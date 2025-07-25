from api.app import create_app
from core.celery_config import make_celery
from core.tasks import process_episode_task

app = create_app()
celery = make_celery(app) 