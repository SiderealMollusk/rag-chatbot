import sys
import json
import argparse
import random
from core.common import setup_logging, logger, require_context
from core.work_order import WorkOrder, WorkOrderManifest
from datetime import datetime
import os

def generate_test_has_results_tasks(count: int):
    """
    Generate tasks for test_has_results workflow.
    
    TODO: Implement your task generation logic here.
    """
    rows = []
    logger.info(f"Generating {count} test_has_results tasks...")
    
    for i in range(1, count + 1):
        # TODO: Replace this with your actual task structure
        rows.append({
            "task": "tasks.your_task_name",  # Update this
            "kwargs": {},
            "meta": {
                "description": f"test_has_results Task {i}/{count}",
                "id": f"Task-{i:02d}"
            }
        })
    
    return rows

def main():
    setup_logging()
    require_context('shell')
    
    parser = argparse.ArgumentParser(description="Generate Test Has Results Job Packages")
    parser.add_argument("--count", type=int, default=5, help="Number of tasks to generate")
    parser.add_argument("--strategy", 
                       choices=["hybrid_supervisor", "force_metal", "force_cloud"], 
                       default="hybrid_supervisor",
                       help="Routing strategy")
    args = parser.parse_args()

    logger.info(f"Generating test_has_results job package with {args.count} tasks...")
    
    # Generate task data
    data = generate_test_has_results_tasks(args.count)
    
    # Create job package directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_id = f"test_has_results_{timestamp}"
    job_dir = f"/data/jobs/{job_id}"
    os.makedirs(job_dir, exist_ok=True)
    
    # Write manifest
    manifest_path = f"{job_dir}/manifest.jsonl"
    with open(manifest_path, 'w') as f:
        for row in data:
            f.write(json.dumps(row) + "\n")
    
    # Create work order
    work_order = WorkOrder(
        job_id=job_id,
        name=f"Test Has Results - {args.count} tasks",
        manifest=WorkOrderManifest(
            path="manifest.jsonl",
            count=len(data)
        ),
        routing_strategy=args.strategy,
        backlog_key=f"job:{job_id}:backlog"
    )
    
    # Write work order
    work_order_path = f"{job_dir}/work_order.yaml"
    work_order.to_yaml(work_order_path)
    
    logger.success(f"Created job package: {job_dir}/")
    logger.info(f"  - work_order.yaml")
    logger.info(f"  - manifest.jsonl ({len(data)} tasks)")
    logger.info(f"  Strategy: {args.strategy}")
    logger.info(f"  Backlog: {work_order.backlog_key}")

if __name__ == "__main__":
    main()
