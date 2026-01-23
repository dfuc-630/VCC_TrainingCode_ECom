from celery import Celery
from app import create_app

flask_app = create_app()

celery = Celery(
    "worker", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0"
)

celery.conf.update(flask_app.config)


class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask
