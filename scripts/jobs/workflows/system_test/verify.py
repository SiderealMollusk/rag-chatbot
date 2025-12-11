import sys
import json
import argparse
import time
from celery import Celery
from celery.result import AsyncResult
from core.common import setup_logging, get_redis_url, logger

app = Celery('movie_bible', 
             broker=get_redis_url(),
             backend=get_redis_url())

def verify_task(task_name, result):
    """
    Validation logic specific to task type.
    """
    if task_name == "tasks.debug_task":
        if result.get("status") == "ok": return True
        return False
        
    elif task_name == "tasks.sleep_task":
        if result.get("status") == "slept": return True
        return False
        
    elif "crud_task" in task_name:
        # Check Receipt
        lc = result.get("lifecycle", [])
        required = ["created", "verified", "deleted"] # We can be loose or strict
        if all(x in lc for x in required):
            return True
        logger.warning(f"CRUD Receipt Incomplete: {lc}")
        return False
        
    return True

def main():
    setup_logging()
    # Note: This verifier is mostly illustrative because we don't have the Task IDs linked to the manifest 
    # unless we logged them during dispatch.
    # In a real system, 'dispatch.py' would output a 'run_log.jsonl' linking Manifest Entry -> Job ID.
    # For this demo, we will inspect the *Celery Backend* for recent tasks matching the signature.
    # OR simpler: The user runs dispatch, which outputs IDs.
    
    # IMPROVEMENT: Let's assume the user pipes the dispatch output or we just scan generally?
    # Actually, for "verify", the best pattern is usually:
    # 1. Dispatch writes 'run_id.jsonl'
    # 2. Verify reads 'run_id.jsonl'.
    
    # But since we didn't implement that in dispatch.py yet, let's make this verify script
    # inspect the Last N tasks from the backend (if possible) or just say 
    # "To verify, use Flower".
    
    # WAIT! Standard pattern: The user provides the list of IDs to verify.
    # But that's tedious.
    
    # Let's verify by just inspecting random recent tasks? No.
    # Let's verify by side-effects?
    # Debug/Sleep have no side effects.
    # CRUD deletes its data.
    
    # OK, the only way to verify programmatically is if we know the Task IDs.
    # I will stick to the plan: "Check Receipts". 
    # But I need IDs.
    
    # PROPOSAL: Update dispatch.py to print JSON lines to stdout: `{"task": "...", "id": "..."}`
    # Then verify.py reads stdin.
    
    parser = argparse.ArgumentParser()
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
            # We don't know the task name easily from AsyncResult (sometimes), 
            # so we infer or generic check.
            # Actually AsyncResult doesn't easily give task name unless we store it.
            # We will just log the result.
            logger.info(f"Task {task_id}: SUCCESS | Result: {val}")
            
            # Simple heuristic check
            if isinstance(val, dict):
                if val.get("lifecycle"): # It's a CRUD task
                    if verify_task("tasks.fast_crud_task", val):
                        success_count += 1
                    else:
                        logger.error(f"Task {task_id} Failed Validation")
                else:
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
