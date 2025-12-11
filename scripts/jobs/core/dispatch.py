import sys
import json
import argparse
from celery import Celery
from core.common import setup_logging, get_redis_url, logger
from core.schema import ManifestEntry

# Setup Celery Client
app = Celery('movie_bible', 
             broker=get_redis_url(),
             backend=get_redis_url())

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Dispatch jobs from a manifest")
    parser.add_argument("manifest", help="Path to manifest.jsonl")
    parser.add_argument("--dry-run", action="store_true", help="Do not actually enqueue")
    args = parser.parse_args()

    logger.info(f"Reading manifest: {args.manifest}")

    count = 0
    with open(args.manifest, 'r') as f:
        for line in f:
            if not line.strip(): continue
            try:
                data = json.loads(line)
                entry = ManifestEntry(**data)
                
                if args.dry_run:
                    logger.info(f"[Dry Run] Would dispatch: {entry.task} args={entry.args}")
                else:
                    # Enqueue
                    res = app.send_task(entry.task, args=entry.args, kwargs=entry.kwargs)
                    # Emit structured log for piping
                    print(json.dumps({"task": entry.task, "id": res.id, "status": "dispatched"}))
                    # Also log to stderr for human
                    logger.debug(f"Dispatched {entry.task}: {res.id}")
                
                count += 1
            except Exception as e:
                logger.error(f"Failed to process line: {line.strip()} | Error: {e}")

    logger.success(f"Dispatched {count} tasks.")

if __name__ == "__main__":
    main()
