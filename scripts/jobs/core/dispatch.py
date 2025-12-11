import sys
import json
import argparse
from celery import Celery
from core.common import setup_logging, get_redis_url, logger, require_context
from core.schema import ManifestEntry

# Setup Celery Client
app = Celery('movie_bible', 
             broker=get_redis_url(),
             backend=get_redis_url())

def main():
    setup_logging()
    require_context('shell')
    parser = argparse.ArgumentParser(description="Dispatch jobs from a manifest")
    parser.add_argument("manifest", help="Path to manifest.jsonl")
    parser.add_argument("--backlog", help="Push to Redis List (Backlog) instead of executing immediately", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Do not actually enqueue")
    args = parser.parse_args()

    # Redis Client (Lazy load if needed)
    redis_client = None
    if args.backlog:
        import redis
        redis_client = redis.from_url(get_redis_url())

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
                elif args.backlog:
                    # Push to Backlog List
                    redis_client.rpush(args.backlog, line.strip()) # Push raw JSON
                    logger.debug(f"Queued to Backlog {args.backlog}: {entry.task}")
                else:
                    # Enqueue immediately
                    res = app.send_task(entry.task, args=entry.args, kwargs=entry.kwargs)
                    print(json.dumps({"task": entry.task, "id": res.id, "status": "dispatched"}))
                    logger.debug(f"Dispatched {entry.task}: {res.id}")
                
                count += 1
            except Exception as e:
                logger.error(f"Failed to process line: {line.strip()} | Error: {e}")

    logger.success(f"Processed {count} items.")

if __name__ == "__main__":
    main()
