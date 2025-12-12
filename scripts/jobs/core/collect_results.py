"""
Result Collector - Automatically collects task results to results.jsonl

This script runs as a background process alongside the conductor,
listening for task completion and writing results to the job's results.jsonl file.
"""
import sys
import json
import argparse
import time
import redis
from celery import Celery
from celery.result import AsyncResult
from core.common import setup_logging, get_redis_url, logger, require_context
from core.work_order import WorkOrder
import os

def collect_results(work_order_path: str, poll_interval: int = 2):
    """
    Poll for completed tasks and write results to results.jsonl.
    
    Args:
        work_order_path: Path to work order YAML
        poll_interval: How often to check for results (seconds)
    """
    wo = WorkOrder.from_yaml(work_order_path)
    results_path = wo.get_results_path()
    
    # Ensure results file exists
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    
    # Track which task IDs we've already collected
    collected_ids = set()
    
    # Load any existing results
    if os.path.exists(results_path):
        with open(results_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if 'task_id' in data:
                        collected_ids.add(data['task_id'])
                except:
                    pass
    
    app = Celery('movie_bible', 
                 broker=get_redis_url(),
                 backend=get_redis_url())
    
    r = redis.from_url(get_redis_url())
    
    logger.info(f"Starting result collector for job: {wo.job_id}")
    logger.info(f"Results will be written to: {results_path}")
    logger.info(f"Poll interval: {poll_interval}s")
    
    total_tasks = wo.manifest.count
    last_count = len(collected_ids)
    
    while True:
        # Scan for celery task results
        # Pattern: celery-task-meta-*
        task_keys = r.keys("celery-task-meta-*")
        
        new_results = 0
        for key in task_keys:
            task_id = key.decode('utf-8').replace('celery-task-meta-', '')
            
            if task_id in collected_ids:
                continue
            
            # Get result
            res = AsyncResult(task_id, app=app)
            
            if res.state in ['SUCCESS', 'FAILURE']:
                # Collect it
                result_data = {
                    'task_id': task_id,
                    'state': res.state,
                    'result': res.result if res.state == 'SUCCESS' else None,
                    'error': str(res.result) if res.state == 'FAILURE' else None,
                    'traceback': res.traceback if res.state == 'FAILURE' else None,
                    'date_done': res.date_done.isoformat() if res.date_done else None
                }
                
                # Write to results file
                with open(results_path, 'a') as f:
                    f.write(json.dumps(result_data) + "\n")
                
                collected_ids.add(task_id)
                new_results += 1
                
                if res.state == 'SUCCESS':
                    logger.success(f"Collected result for {task_id[:8]}...")
                else:
                    logger.error(f"Collected FAILURE for {task_id[:8]}...")
        
        if new_results > 0:
            current_count = len(collected_ids)
            logger.info(f"Progress: {current_count}/{total_tasks} results collected")
            
            # Update work order
            wo.execution.tasks_completed = sum(1 for tid in collected_ids if tid)  # Count successes
            wo.to_yaml(work_order_path)
            
            # Check if done
            if current_count >= total_tasks:
                logger.success(f"All {total_tasks} results collected!")
                break
        
        time.sleep(poll_interval)

def main():
    setup_logging()
    require_context('shell')
    
    parser = argparse.ArgumentParser(description="Collect task results to results.jsonl")
    parser.add_argument("work_order", help="Path to work_order.yaml")
    parser.add_argument("--interval", type=int, default=2, help="Poll interval in seconds")
    args = parser.parse_args()
    
    try:
        collect_results(args.work_order, args.interval)
    except KeyboardInterrupt:
        logger.warning("Result collector stopping...")

if __name__ == "__main__":
    main()
