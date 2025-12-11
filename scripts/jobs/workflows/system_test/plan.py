import sys
import json
import argparse
import random
from core.common import setup_logging, logger

OUTPUT_DIR = "scripts/jobs/manifests"

def generate_debug(count):
    rows = []
    for i in range(count):
        rows.append({
            "task": "tasks.debug_task",
            "kwargs": {"msg": f"Hello Debug {i}"},
            "description": f"Debug echo {i}"
        })
    return rows

def generate_sleep(count):
    rows = []
    for i in range(count):
        sec = random.randint(1, 5)
        rows.append({
            "task": "tasks.sleep_task",
            "kwargs": {"seconds": sec},
            "description": f"Sleep for {sec}s"
        })
    return rows

def generate_crud(count, latency=False):
    rows = []
    task = "tasks.sleep_crud_task" if latency else "tasks.fast_crud_task"
    for i in range(count):
        payload = f"test_data_{i}_{random.randint(1000,9999)}"
        kwargs = {"data": payload}
        if latency:
            kwargs["seconds"] = random.randint(1, 3)
            
        rows.append({
            "task": task,
            "kwargs": kwargs,
            "description": f"CRUD Test {i} latency={latency}"
        })
    return rows

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Generate System Test Manifests")
    parser.add_argument("--mode", choices=["debug", "sleep", "crud", "crud_latency"], required=True)
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args()

    logger.info(f"Generating {args.mode} manifest with {args.count} tasks...")
    
    if args.mode == "debug":
        data = generate_debug(args.count)
    elif args.mode == "sleep":
        data = generate_sleep(args.count)
    elif args.mode == "crud":
        data = generate_crud(args.count, latency=False)
    elif args.mode == "crud_latency":
        data = generate_crud(args.count, latency=True)
        
    outfile = f"{OUTPUT_DIR}/system_test_{args.mode}.jsonl"
    with open(outfile, 'w') as f:
        for row in data:
            f.write(json.dumps(row) + "\n")
            
    logger.success(f"Generated {len(data)} items to {outfile}")

if __name__ == "__main__":
    main()
