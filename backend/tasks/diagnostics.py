import time
from tasks import app
from loguru import logger

@app.task(name="tasks.debug_task", bind=True)
def debug_task(self, msg: str):
    """
    Simple echo task to verify connectivity.
    """
    logger.bind(task_id=self.request.id).info(f"DEBUG: {msg}")
    return {"status": "ok", "echo": msg}

@app.task(name="tasks.sleep_task", bind=True)
def sleep_task(self, seconds: int):
    """
    Sleeps for N seconds to test concurrency/timeouts.
    """
    logger.bind(task_id=self.request.id).info(f"Job Started: Sleeping for {seconds}s...")
    time.sleep(seconds)
    logger.bind(task_id=self.request.id).success(f"Job Finished: Woke up after {seconds}s!")
    return {"status": "slept", "duration": seconds}
