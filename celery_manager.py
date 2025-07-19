from src.api.app import create_app, celery

app = create_app()

if __name__ == '__main__':
    # Example: Launch a test task or manage Celery from here
    print('Celery manager loaded. Use this script to manage tasks or inspect the worker.')
