import sys
import redis
import argparse
from core.common import get_redis_url, setup_logging, logger, require_context

def main():
    setup_logging()
    require_context('shell')
    
    parser = argparse.ArgumentParser(description="Flush Job History (Redis)")
    parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    parser.add_argument("--dry-run", action="store_true", help="List keys but do not delete")
    args = parser.parse_args()

    r_url = get_redis_url()
    try:
        r = redis.from_url(r_url)
    except Exception as e:
        logger.error(f"Could not connect to Redis at {r_url}: {e}")
        sys.exit(1)

    keys = r.keys("*")
    key_count = len(keys)
    
    logger.info(f"Connected to Redis. Found {key_count} keys.")
    
    if key_count == 0:
        logger.success("Database is already empty.")
        return

    # Categorize for info
    queues = [k for k in keys if b'celery' in k or b'queue' in k or b'backlog' in k]
    results = [k for k in keys if b'celery-task-meta' in k]
    others = [k for k in keys if k not in queues and k not in results]

    logger.info(f"Summary: {len(queues)} Queue/Backlog keys, {len(results)} Result keys, {len(others)} Other keys")

    if args.dry_run:
        logger.info("[Dry Run] Would flush database.")
        return

    if not args.force:
        val = input(f"WARNING: This will delete ALL {key_count} keys in the Redis DB. Continue? [y/N] ")
        if val.lower() != 'y':
            logger.info("Aborted.")
            sys.exit(0)

    # Flush
    r.flushdb()
    logger.success("Redis Database Flushed. Job history and queues cleared.")

if __name__ == "__main__":
    main()
