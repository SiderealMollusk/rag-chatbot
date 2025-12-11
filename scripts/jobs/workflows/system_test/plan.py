import sys
import json
import argparse
import random
from core.common import setup_logging, logger, get_next_filename, require_context

OUTPUT_DIR = "/data"

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

def generate_stress_supervisor(count):
    rows = []
    logger.info(f"Generating {count} Long-Running Supervisor Stress Tasks (90-150s)...")
    for i in range(1, count + 1):
        # Duration: 1.5 to 2.5 minutes (90 to 150 seconds)
        duration = random.randint(90, 150)
        
        rows.append({
            "id": f"Job-{i:02d}", # Explicit ID for logging
            "task": "tasks.sleep_task",
            "kwargs": {}, # Oops, diagnostics.py expects 'seconds' as arg or kwarg? 
                          # Checking diagnostics.py: def sleep_task(self, seconds: int). 
                          # Celery usually maps args/kwargs. 
                          # Previous plan used "args": [duration]. 
                          # The schema in conductor.py supports args/kwargs.
                          # Let's align with plan.py's kwargs style if possible, or support args.
            "args": [duration], 
            "meta": { # ManifestEntry supports meta
                "description": f"Sleeper Job {i}/{count} ({duration}s)",
                "id": f"Job-{i:02d}"
            }
        })
    return rows

def main():
    setup_logging()
    require_context('shell')
    parser = argparse.ArgumentParser(description="Generate System Test Manifests")
    parser.add_argument("--mode", choices=["debug", "sleep", "crud", "crud_latency", "stress_supervisor"], required=True)
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
    elif args.mode == "stress_supervisor":
        data = generate_stress_supervisor(args.count)
        
    outfile = get_next_filename(OUTPUT_DIR, f"system_test_{args.mode}")
    with open(outfile, 'w') as f:
        for row in data:
            f.write(json.dumps(row) + "\n")
            
    logger.success(f"Generated {len(data)} items to {outfile}")

if __name__ == "__main__":
    main()
