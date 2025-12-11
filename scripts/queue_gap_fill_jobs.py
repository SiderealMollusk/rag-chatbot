import json
import os
import sys
import argparse
from celery import Celery

# Setup Celery Client
# We must match the app name and broker
app = Celery('movie_bible', 
             broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
             backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'))

INPUT_FILE = "data/passes/02_deep_profiling/corpus.02.jsonl"
ANNOTATED_FILE = "data/passes/02_deep_profiling/corpus.02.annotated.jsonl"
BATCH_SIZE = 10

def load_processed_ids():
    if not os.path.exists(ANNOTATED_FILE):
        return set()
    ids = set()
    with open(ANNOTATED_FILE, 'r') as f:
        for line in f:
            if not line.strip(): continue
            try:
                data = json.loads(line)
                ids.add(data['id'])
            except:
                pass
    return ids

def queue_jobs(dry_run=False):
    processed = load_processed_ids()
    print(f"Found {len(processed)} already processed records.")
    
    pending = []
    with open(INPUT_FILE, 'r') as f:
        for line in f:
            if not line.strip(): continue
            rec = json.loads(line)
            if rec['id'] not in processed:
                pending.append(rec)
                
    print(f"Found {len(pending)} pending records (Gaps).")
    
    if not pending:
        print("Everything is up to date!")
        return

    print(f"Queuing {len(pending)} records in batches of {BATCH_SIZE}...")
    
    queued_count = 0
    for i in range(0, len(pending), BATCH_SIZE):
        batch = pending[i : i + BATCH_SIZE]
        batch_ids = [r['id'] for r in batch]
        
        if not dry_run:
            # Send to Celery
            # Signature: process_batch(batch_ids, batch_data)
            app.send_task("tasks.process_batch", args=[batch_ids, batch])
            queued_count += 1
        
    if dry_run:
        print(f"[Dry Run] Would have queued {queued_count} tasks.")
    else:
        print(f"Successfully queued {queued_count} tasks to Redis.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen")
    args = parser.parse_args()
    
    queue_jobs(dry_run=args.dry_run)
