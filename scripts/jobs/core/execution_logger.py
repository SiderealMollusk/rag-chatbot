"""
Execution Logger for Job System

Logs job lifecycle events to execution.log in a structured, human-readable format.
Critical events:
- Task pulled from backlog
- Task routed to queue
- Task completed
- Task failed
"""
import os
from datetime import datetime
from typing import Optional

class ExecutionLogger:
    def __init__(self, log_path: str):
        self.log_path = log_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
    def _log(self, event_type: str, message: str, task_id: Optional[str] = None):
        """Write a log entry."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task_prefix = f"[{task_id}]" if task_id else "[SYSTEM]"
        line = f"{timestamp} | {task_prefix} | {event_type: <15} | {message}\n"
        
        with open(self.log_path, 'a') as f:
            f.write(line)
    
    def job_started(self, job_id: str, backlog_key: str, task_count: int):
        """Log job start."""
        self._log("JOB_STARTED", f"Job {job_id} started. {task_count} tasks in backlog: {backlog_key}")
    
    def task_pulled(self, task_id: str, from_backlog: str):
        """Log when a task is pulled from the backlog."""
        self._log("PULLED", f"Pulled from {from_backlog}", task_id)
    
    def task_routed(self, task_id: str, to_queue: str, reason: str = ""):
        """Log when a task is routed to a worker queue."""
        msg = f"Routed to {to_queue}"
        if reason:
            msg += f" ({reason})"
        self._log("ROUTED", msg, task_id)
    
    def task_completed(self, task_id: str, duration_sec: float):
        """Log when a task completes."""
        self._log("COMPLETED", f"Finished in {duration_sec:.1f}s", task_id)
    
    def task_failed(self, task_id: str, error: str):
        """Log when a task fails."""
        self._log("FAILED", f"Error: {error}", task_id)
    
    def job_completed(self, job_id: str, total_tasks: int, successful: int, failed: int):
        """Log job completion."""
        self._log("JOB_COMPLETED", f"Job {job_id} finished. Success: {successful}/{total_tasks}, Failed: {failed}")
    
    def conductor_decision(self, decision: str):
        """Log conductor routing decisions."""
        self._log("DECISION", decision)
