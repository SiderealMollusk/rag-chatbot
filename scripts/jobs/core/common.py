import sys
from loguru import logger
import os

# Configure standard logging format
def setup_logging():
    logger.remove()
    logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")

def get_redis_url():
    return os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
