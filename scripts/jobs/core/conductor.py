import sys
import json
import argparse
import time
import redis
import math
from celery import Celery
from core.common import setup_logging, get_redis_url, logger
from core.schema import ManifestEntry
from core.config import GEMINI_RATE_LIMIT_RPM, METAL_QUEUE_DEPTH

# Setup
setup_logging()
app = Celery('movie_bible', 
             broker=get_redis_url(),
             backend=get_redis_url())
r = redis.from_url(get_redis_url())

# Constants (Rules)
QUEUE_METAL = 'queue_metal'
QUEUE_CLOUD = 'queue_cloud'

LIMIT_METAL_DEPTH = METAL_QUEUE_DEPTH  # Keep M1 fed with just enough
LIMIT_CLOUD_DEPTH = 10 # Cloud has higher concurrency

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

def run_conductor(backlog_key: str):
    global cloud_tokens
    
    logger.info(f"Starting Conductor (Supervisor). Watching {backlog_key}...")
    logger.info(f"Rules: Metal<{LIMIT_METAL_DEPTH}, Cloud<{LIMIT_CLOUD_DEPTH} @ {CLOUD_TOKENS_PER_MIN} rpm")

    while True:
        # Refill tokens
        refill_bucket()
        
        # Check Backlog
        backlog_len = r.llen(backlog_key)
        if backlog_len == 0:
             time.sleep(1) # Idle wait
             continue

        # Check Capabilities
        metal_len = r.llen(QUEUE_METAL)
        cloud_len = r.llen(QUEUE_CLOUD)
        
        action_taken = False
        
        # --- RULE 1: FEED METAL (Priority: Keep Local Busy) ---
        if metal_len < LIMIT_METAL_DEPTH:
            raw = r.lpop(backlog_key)
            if raw:
                try:
                    # Parse
                    data = json.loads(raw)
                    entry = ManifestEntry(**data)
                    
                    # Routing Logic
                    task_name = entry.task
                    if task_name == 'tasks.rag.process_batch':
                        task_name = 'tasks.rag.process_batch_ollama'
                    
                    # Dispatch
                    res = app.send_task(task_name, args=entry.args, kwargs=entry.kwargs, queue=QUEUE_METAL)
                    
                    # Log Format: "Job {id} assigned to Metal (Queue: {len})"
                    job_id = entry.meta.get('id', 'Unknown')
                    logger.info(f"Job {job_id} assigned to Metal (Queue: {metal_len})")
                    
                    action_taken = True
                    continue # Loop fast to refill metal if needed
                except Exception as e:
                    logger.error(f"Failed to dispatch: {e}")

        # --- RULE 2: FEED CLOUD (If Metal Full) ---
        if cloud_len < LIMIT_CLOUD_DEPTH:
            if cloud_tokens >= 1.0:
                raw = r.lpop(backlog_key)
                if raw:
                     try:
                        data = json.loads(raw)
                        entry = ManifestEntry(**data)
                        
                        task_name = entry.task
                        if task_name == 'tasks.rag.process_batch':
                             task_name = 'tasks.rag.process_batch_gemini'
                        
                        res = app.send_task(task_name, args=entry.args, kwargs=entry.kwargs, queue=QUEUE_CLOUD)
                        
                        cloud_tokens -= 1.0
                        
                        # Log Format: "Job {id} assigned to Gemma (Budget: {tokens}/{cap})"
                        job_id = entry.meta.get('id', 'Unknown')
                        logger.info(f"Job {job_id} assigned to Gemma (Budget: {cloud_tokens:.1f}/{CLOUD_BUCKET_CAPACITY})")
                        
                        action_taken = True
                     except:
                        logger.error("Failed dispatch cloud")
        
        if not action_taken:
            # We have work, but workers are busy/limited.
            time.sleep(0.5)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backlog", required=True, help="Redis List Key to consume")
    args = parser.parse_args()
    
    try:
        run_conductor(args.backlog)
    except KeyboardInterrupt:
        logger.warning("Conductor stopping...")

if __name__ == "__main__":
    main()
