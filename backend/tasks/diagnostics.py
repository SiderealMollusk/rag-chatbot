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
    from datetime import datetime, timedelta
    
    start_time = datetime.now()
    predicted_end = start_time + timedelta(seconds=seconds)
    
    logger.bind(task_id=self.request.id).info(f"Job Started: {seconds}s duration.")
    logger.bind(task_id=self.request.id).info(f" >> Started : {start_time.strftime('%H:%M:%S')}")
    logger.bind(task_id=self.request.id).info(f" >> Predict : {predicted_end.strftime('%H:%M:%S')}")
    
    time.sleep(seconds)
    
    actual_end = datetime.now()
    logger.bind(task_id=self.request.id).success(f"Job Finished: Woke up at {actual_end.strftime('%H:%M:%S')}!")
    return {
        "status": "slept", 
        "duration": seconds,
        "started": start_time.isoformat(),
        "predicted": predicted_end.isoformat(),
        "finished": actual_end.isoformat()
    }
