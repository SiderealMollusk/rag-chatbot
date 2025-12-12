from celery import Celery
import os
import sys
from loguru import logger

# Configure Loguru to intercept standard logging if needed, or just be standalone
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>")

# Configure Celery
app = Celery('movie_bible', 
             broker=os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
             backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'))

# Register routes
app.conf.task_routes = {
    'tasks.rag.process_batch_gemini': {'queue': 'queue_cloud'},
    'tasks.rag.process_batch_ollama': {'queue': 'queue_metal'},
}

# Import sub-modules to register tasks
import tasks.diagnostics
import tasks.crud
import tasks.rag
import tasks.compute
