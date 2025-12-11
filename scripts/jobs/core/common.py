import sys
from loguru import logger
import os

# Configure standard logging format
def setup_logging():
    logger.remove()
    logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")

def get_redis_url():
    return os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')

def get_next_filename(base_dir: str, prefix: str, ext: str = "jsonl") -> str:
    """
    Finds the next available filename like {prefix}_01.{ext}.
    Example: prefix="job_run", returns "job_run_01.jsonl"
    """
    i = 1
    while True:
        filename = f"{prefix}_{i:02d}.{ext}"
        path = os.path.join(base_dir, filename)
        if not os.path.exists(path):
            return path
        i += 1

def require_context(expected: str):
    """
    Ensures script is running in the correct Docker container.
    """
    current = os.environ.get('EXECUTION_CONTEXT', 'host')
    if current != expected:
        logger.error(f"Context Error: Script must run in '{expected}' (Current: '{current}')")
        sys.exit(1)
