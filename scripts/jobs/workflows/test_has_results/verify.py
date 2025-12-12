import sys
import json
import argparse
import time
from celery import Celery
from celery.result import AsyncResult
from core.common import setup_logging, get_redis_url, logger, require_context

app = Celery('movie_bible', 
             broker=get_redis_url(),
             backend=get_redis_url())

def verify_task(task_name, result):
    """
    Validation logic for compute_multiply tasks.
    Verifies that the multiplication result is correct.
    """
    if task_name == "tasks.compute_multiply":
        # Extract values
        a = result.get("input_a")
        b = result.get("input_b")
        actual_result = result.get("result")
        expected_result = a * b if (a is not None and b is not None) else None
        
        # Verify
        if actual_result == expected_result:
            return True
        else:
            logger.error(f"Multiplication error: {a} × {b} = {actual_result}, expected {expected_result}")
            return False
    
    return True  # Default: assume success

def main():
    setup_logging()
    require_context('shell')
    
    parser = argparse.ArgumentParser(description="Verify Test Has Results Task Results")
    parser.add_argument("--ids", nargs='+', help="List of Task IDs to verify")
    parser.add_argument("--file", help="File containing task IDs (one per line or JSON)")
    args = parser.parse_args()
    
    ids = []
    if args.ids:
        ids = args.ids
    if args.file:
        with open(args.file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                # Handle raw ID or JSON log from dispatch
                if '{' in line:
                    try:
                        data = json.loads(line)
                        if 'id' in data: ids.append(data['id'])
                    except: pass
                else:
                    ids.append(line)
                    
    if not ids:
        logger.error("No Task IDs provided to verify. Usage: python verify.py --ids ID1 ID2 ...")
        sys.exit(1)

    logger.info(f"Verifying {len(ids)} tasks...")
    
    success_count = 0
    pending_count = 0
    
    for task_id in ids:
        res = AsyncResult(task_id, app=app)
        state = res.state
        
        if state == 'SUCCESS':
            val = res.get()
            logger.info(f"Task {task_id}: SUCCESS | Result: {val}")
            
            # TODO: Add your custom validation logic here
            if isinstance(val, dict):
                # Example: Check if specific field exists
                # if verify_task("your_task_name", val):
                #     success_count += 1
                # else:
                #     logger.error(f"Task {task_id} Failed Validation")
                success_count += 1
            else:
                 success_count += 1
                 
        elif state in ['PENDING', 'STARTED', 'RETRY']:
            logger.warning(f"Task {task_id}: {state}")
            pending_count += 1
        else:
            logger.error(f"Task {task_id}: {state} | {res.traceback}")

    logger.success(f"Verified: {success_count}/{len(ids)} Success. ({pending_count} Pending)")

if __name__ == "__main__":
    main()
