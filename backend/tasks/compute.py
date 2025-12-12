import time
import random
from tasks import app
from loguru import logger

@app.task(name="tasks.compute_multiply", bind=True)
def compute_multiply(self, a: int, b: int, sleep_duration: int = 0):
    """
    Multiply two numbers with optional sleep to simulate longer work.
    Returns the result plus metadata.
    """
    from datetime import datetime
    
    start_time = datetime.now()
    task_id = self.request.id
    
    # Log start
    logger.bind(task_id=task_id).info(f"Computing {a} × {b} (will sleep {sleep_duration}s)")
    
    # Do the "work"
    result = a * b
    
    # Sleep to make it observable
    if sleep_duration > 0:
        time.sleep(sleep_duration)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Log completion
    logger.bind(task_id=task_id).success(f"Result: {a} × {b} = {result} (took {duration:.1f}s)")
    
    return {
        "operation": "multiply",
        "input_a": a,
        "input_b": b,
        "result": result,
        "sleep_duration": sleep_duration,
        "actual_duration": duration,
        "started": start_time.isoformat(),
        "finished": end_time.isoformat()
    }
