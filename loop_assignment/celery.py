import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loop_assignment.settings')

app = Celery('loop_assignment')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.broker_url = 'redis://localhost:6379/0'