import sys
import argparse
import redis
from core.common import setup_logging, get_redis_url, logger, require_context
from core.work_order import WorkOrder

def show_status(work_order_path: str):
    """Show status of a job."""
    # Load work order
    wo = WorkOrder.from_yaml(work_order_path)
    
    # Connect to Redis
    r = redis.from_url(get_redis_url())
    
    # Get queue depths
    backlog_len = r.llen(wo.backlog_key)
    
    # Print status
    print(f"\n{'='*60}")
    print(f"JOB STATUS: {wo.job_id}")
    print(f"{'='*60}")
    print(f"Name:      {wo.name}")
    print(f"Status:    {wo.status.upper()}")
    print(f"Strategy:  {wo.routing_strategy}")
    print(f"\n{'-'*60}")
    print(f"PROGRESS")
    print(f"{'-'*60}")
    print(f"Dispatched:  {wo.execution.tasks_dispatched}")
    print(f"Backlog:     {backlog_len}")
    print(f"Completed:   {wo.execution.tasks_completed}")
    print(f"Failed:      {wo.execution.tasks_failed}")
    
    if wo.execution.tasks_dispatched > 0:
        progress_pct = (wo.execution.tasks_completed / wo.execution.tasks_dispatched) * 100
        print(f"Progress:    {progress_pct:.1f}%")
    
    print(f"\n{'-'*60}")
    print(f"FILES")
    print(f"{'-'*60}")
    print(f"Manifest:    {wo.get_manifest_path()}")
    print(f"Results:     {wo.get_results_path()}")
    print(f"Exec Log:    {wo.get_execution_log_path()}")
    print(f"{'='*60}\n")

def main():
    setup_logging()
    require_context('shell')
    parser = argparse.ArgumentParser(description="Check job status")
    parser.add_argument("work_order", help="Path to work_order.yaml")
    args = parser.parse_args()

    show_status(args.work_order)

if __name__ == "__main__":
    main()
