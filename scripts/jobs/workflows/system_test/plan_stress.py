
import json
import random
import os
import argparse

# Constants
OUTPUT_FILE = "scripts/jobs/manifests/stress_test_v1.jsonl"
TOTAL_JOBS = 10

def generate_plan():
    print(f"Generating {TOTAL_JOBS} Sleep Jobs for Stress Test...")
    
    with open(OUTPUT_FILE, 'w') as f:
        for i in range(1, TOTAL_JOBS + 1):
            # Duration: 1.5 to 2.5 minutes (90 to 150 seconds)
            duration = random.randint(90, 150)
            
            job = {
                "id": f"Job-{i:02d}",
                "task": "tasks.sleep_task",
                "args": [duration],
                "kwargs": {},
                "meta": {
                    "description": f"Sleeper Job {i}/{TOTAL_JOBS}",
                    "expected_duration": duration
                }
            }
            f.write(json.dumps(job) + "\n")
            
    print(f"Plan written to {OUTPUT_FILE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    generate_plan()
