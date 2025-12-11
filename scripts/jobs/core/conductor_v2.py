import sys
import json
import argparse
import time
import redis
from celery import Celery
from core.common import setup_logging, get_redis_url, logger, require_context
from core.schema import ManifestEntry
from core.work_order import WorkOrder
from core.execution_logger import ExecutionLogger
from core.config import GEMINI_RATE_LIMIT_RPM, METAL_QUEUE_DEPTH

# Setup
setup_logging()
require_context('shell')
app = Celery('movie_bible', 
             broker=get_redis_url(),
             backend=get_redis_url())
r = redis.from_url(get_redis_url())

# Constants
QUEUE_METAL = 'queue_metal'
QUEUE_CLOUD = 'queue_cloud'
LIMIT_METAL_DEPTH = METAL_QUEUE_DEPTH
LIMIT_CLOUD_DEPTH = 10

# Cloud Rate Limit Token Bucket
CLOUD_TOKENS_PER_MIN = GEMINI_RATE_LIMIT_RPM
CLOUD_BUCKET_CAPACITY = 2
cloud_tokens = CLOUD_BUCKET_CAPACITY
last_refill = time.time()

def refill_bucket():
    global cloud_tokens, last_refill
    now = time.time()
    elapsed = now - last_refill
    refill = elapsed * (CLOUD_TOKENS_PER_MIN / 60.0)
    if refill > 0:
        cloud_tokens = min(CLOUD_BUCKET_CAPACITY, cloud_tokens + refill)
        last_refill = now

def run_conductor_v2(work_order_path: str):
    global cloud_tokens
    
    # Load work order
    wo = WorkOrder.from_yaml(work_order_path)
    exec_log = ExecutionLogger(wo.get_execution_log_path())
    
    backlog_key = wo.backlog_key
    strategy = wo.routing_strategy
    
    logger.info(f"Starting Conductor for Job: {wo.job_id}")
    logger.info(f"Strategy: {strategy}")
    logger.info(f"Backlog: {backlog_key}")
    exec_log.conductor_decision(f"Conductor started with strategy: {strategy}")
    
    # Update work order status
    wo.status = "running"
    import datetime
    wo.execution.started_at = datetime.datetime.now()
    wo.to_yaml(work_order_path)
    
    # Strategy-specific routing
    if strategy == "force_metal":
        target_queue = QUEUE_METAL
    elif strategy == "force_cloud":
        target_queue = QUEUE_CLOUD
    else:
        target_queue = None  # Dynamic routing
    
    while True:
        refill_bucket()
        
        # Check backlog
        backlog_len = r.llen(backlog_key)
        if backlog_len == 0:
            logger.info("Backlog empty. Job complete.")
            exec_log.conductor_decision("Backlog drained. Job complete.")
            break
        
        # Get queue depths
        metal_len = r.llen(QUEUE_METAL)
        cloud_len = r.llen(QUEUE_CLOUD)
        
        action_taken = False
        
        # Strategy: Force specific queue
        if target_queue:
            raw = r.lpop(backlog_key)
            if raw:
                try:
                    data = json.loads(raw)
                    entry = ManifestEntry(**data)
                    task_id = entry.meta.get('id', 'Unknown')
                    
                    # Log: Pulled from backlog
                    exec_log.task_pulled(task_id, backlog_key)
                    
                    # Dispatch
                    app.send_task(entry.task, args=entry.args, kwargs=entry.kwargs, queue=target_queue)
                    
                    # Log: Routed to queue
                    exec_log.task_routed(task_id, target_queue, f"Strategy: {strategy}")
                    logger.info(f"Job {task_id} -> {target_queue}")
                    
                    action_taken = True
                except Exception as e:
                    logger.error(f"Dispatch error: {e}")
        
        # Strategy: Hybrid Supervisor (Metal first, Cloud spillover)
        else:
            # Rule 1: Feed Metal
            if metal_len < LIMIT_METAL_DEPTH:
                raw = r.lpop(backlog_key)
                if raw:
                    try:
                        data = json.loads(raw)
                        entry = ManifestEntry(**data)
                        task_id = entry.meta.get('id', 'Unknown')
                        
                        exec_log.task_pulled(task_id, backlog_key)
                        
                        task_name = entry.task
                        if task_name == 'tasks.rag.process_batch':
                            task_name = 'tasks.rag.process_batch_ollama'
                        
                        app.send_task(task_name, args=entry.args, kwargs=entry.kwargs, queue=QUEUE_METAL)
                        
                        exec_log.task_routed(task_id, QUEUE_METAL, "Hybrid: Metal available")
                        logger.info(f"Job {task_id} assigned to Metal (Queue: {metal_len})")
                        
                        action_taken = True
                        continue
                    except Exception as e:
                        logger.error(f"Failed to dispatch: {e}")
            
            # Rule 2: Feed Cloud (if Metal full)
            if cloud_len < LIMIT_CLOUD_DEPTH:
                if cloud_tokens >= 1.0:
                    raw = r.lpop(backlog_key)
                    if raw:
                        try:
                            data = json.loads(raw)
                            entry = ManifestEntry(**data)
                            task_id = entry.meta.get('id', 'Unknown')
                            
                            exec_log.task_pulled(task_id, backlog_key)
                            
                            task_name = entry.task
                            if task_name == 'tasks.rag.process_batch':
                                task_name = 'tasks.rag.process_batch_gemini'
                            
                            app.send_task(task_name, args=entry.args, kwargs=entry.kwargs, queue=QUEUE_CLOUD)
                            
                            cloud_tokens -= 1.0
                            
                            exec_log.task_routed(task_id, QUEUE_CLOUD, f"Hybrid: Metal full, Budget: {cloud_tokens:.1f}/{CLOUD_BUCKET_CAPACITY}")
                            logger.info(f"Job {task_id} assigned to Gemma (Budget: {cloud_tokens:.1f}/{CLOUD_BUCKET_CAPACITY})")
                            
                            action_taken = True
                        except:
                            logger.error("Failed dispatch cloud")
        
        if not action_taken:
            time.sleep(0.5)
    
    # Job complete - update work order
    wo.status = "completed"
    wo.execution.completed_at = datetime.datetime.now()
    wo.to_yaml(work_order_path)
    
    exec_log.job_completed(wo.job_id, wo.execution.tasks_dispatched, 
                          wo.execution.tasks_completed, wo.execution.tasks_failed)
    
    logger.success(f"Job {wo.job_id} completed!")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("work_order", help="Path to work_order.yaml")
    args = parser.parse_args()
    
    try:
        run_conductor_v2(args.work_order)
    except KeyboardInterrupt:
        logger.warning("Conductor stopping...")

if __name__ == "__main__":
    main()
