import sys
import json
import argparse
import time
import redis
import math
from celery import Celery
from core.common import setup_logging, get_redis_url, logger
from core.schema import ManifestEntry

# Setup
setup_logging()
app = Celery('movie_bible', 
             broker=get_redis_url(),
             backend=get_redis_url())
r = redis.from_url(get_redis_url())

# Constants (Rules)
QUEUE_METAL = 'queue_metal'
QUEUE_CLOUD = 'queue_cloud'

LIMIT_METAL_DEPTH = 2  # Keep M1 fed with just enough
LIMIT_CLOUD_DEPTH = 10 # Cloud has higher concurrency

# Cloud Rate Limit Token Bucket
CLOUD_TOKENS_PER_MIN = 5 # Very Conservative (Free Tier is ~2-15 depending heavily on bursts)
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
        # We peek first? No, LPOP is atomic. We only pop if we intend to send.
        # But we need to know if there is work.
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
                    # Parse to ensure validity, but re-dispatch as task
                    data = json.loads(raw)
                    entry = ManifestEntry(**data)
                    
                    # Force Task Name to Metal Route
                    # Note: We assume the Manifest generated generic 'process_batch' 
                    # OR specific. 
                    # Ideally, we Dynamically Rewrite the task here.
                    
                    # Heuristic: If task is generic 'tasks.process_batch', we upgrade it
                    task_name = 'tasks.rag.process_batch_ollama'
                    
                    # Dispatch
                    res = app.send_task(task_name, args=entry.args, kwargs=entry.kwargs, queue=QUEUE_METAL)
                    
                    logger.info(f"Fed Metal [Q:{metal_len}]: {res.id}")
                    action_taken = True
                    continue # Loop fast to refill metal if needed
                except Exception as e:
                    logger.error(f"Failed to dispatch: {e}")
                    # Push back? Or DLQ? For now, we log and drop to avoid infinite loops on bad data.

        # --- RULE 2: FEED CLOUD (If Metal Full) ---
        # Only if we have tokens
        if cloud_len < LIMIT_CLOUD_DEPTH and cloud_tokens >= 1.0:
            raw = r.lpop(backlog_key)
            if raw:
                 try:
                    data = json.loads(raw)
                    entry = ManifestEntry(**data)
                    
                    task_name = 'tasks.rag.process_batch_gemini'
                    
                    res = app.send_task(task_name, args=entry.args, kwargs=entry.kwargs, queue=QUEUE_CLOUD)
                    
                    cloud_tokens -= 1.0
                    logger.info(f"Fed Cloud [Q:{cloud_len}][Tokens:{cloud_tokens:.1f}]: {res.id}")
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
