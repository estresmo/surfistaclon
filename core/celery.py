import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('surfista')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.redis_backend_health_check_interval = 30
app.conf.broker_transport_options = {
    'global_keyprefix': 'surfista_',
    'visibility_timeout': 3600,  
    'fanout_prefix': True,
    'fanout_patterns': True
}



app.autodiscover_tasks()
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1