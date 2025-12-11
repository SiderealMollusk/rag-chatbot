import sys
import json
import argparse
from celery import Celery
from core.common import setup_logging, get_redis_url, logger, require_context
from core.schema import ManifestEntry
from core.work_order import WorkOrder
from core.execution_logger import ExecutionLogger
import redis

# Setup Celery Client
app = Celery('movie_bible', 
             broker=get_redis_url(),
             backend=get_redis_url())

def dispatch_work_order(work_order_path: str, dry_run: bool = False):
    """
    Dispatch tasks from a work order.
    Reads the work order, loads the manifest, and queues tasks to the backlog.
    """
    # Load work order
    wo = WorkOrder.from_yaml(work_order_path)
    
    # Setup execution logger
    exec_log = ExecutionLogger(wo.get_execution_log_path())
    
    # Connect to Redis
    r = redis.from_url(get_redis_url())
    
    # Read manifest
    manifest_path = wo.get_manifest_path()
    logger.info(f"Loading manifest: {manifest_path}")
    
    tasks = []
    with open(manifest_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            tasks.append(data)
    
    logger.info(f"Loaded {len(tasks)} tasks from manifest")
    
    if dry_run:
        logger.info("[DRY RUN] Would dispatch to backlog")
        return
    
    # Log job start
    exec_log.job_started(wo.job_id, wo.backlog_key, len(tasks))
    
    # Push tasks to backlog
    count = 0
    for task_data in tasks:
        # Push raw JSON to backlog
        r.rpush(wo.backlog_key, json.dumps(task_data))
        count += 1
    
    logger.success(f"Dispatched {count} tasks to {wo.backlog_key}")
    
    # Update work order
    wo.status = "pending"
    wo.execution.tasks_dispatched = count
    wo.to_yaml(work_order_path)
    
    logger.info(f"Job {wo.job_id} ready for execution")
    logger.info(f"Next step: python /scripts/jobs/core/conductor.py {work_order_path}")

def main():
    setup_logging()
    require_context('shell')
    parser = argparse.ArgumentParser(description="Dispatch jobs from work order")
    parser.add_argument("work_order", help="Path to work_order.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually dispatch")
    args = parser.parse_args()

    dispatch_work_order(args.work_order, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
