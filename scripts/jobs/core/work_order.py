from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import yaml
import os

class WorkOrderManifest(BaseModel):
    path: str  # Relative to job directory
    count: int = 0  # Will be set after generation

class WorkOrderOutput(BaseModel):
    results_path: str = "results.jsonl"
    logs_path: str = "execution.log"

class WorkOrderExecution(BaseModel):
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tasks_dispatched: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0

class WorkOrder(BaseModel):
    job_id: str
    name: str
    created: datetime = Field(default_factory=datetime.now)
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    
    # Input
    manifest: WorkOrderManifest
    
    # Routing (Simple strategy selection)
    routing_strategy: Literal["hybrid_supervisor", "force_metal", "force_cloud"] = "hybrid_supervisor"
    backlog_key: str  # e.g., "job:demo_01:backlog"
    
    # Output
    output: WorkOrderOutput = Field(default_factory=WorkOrderOutput)
    
    # Execution tracking
    execution: WorkOrderExecution = Field(default_factory=WorkOrderExecution)
    
    @classmethod
    def from_yaml(cls, path: str) -> "WorkOrder":
        """Load work order from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    def to_yaml(self, path: str):
        """Save work order to YAML file."""
        with open(path, 'w') as f:
            # Convert to dict, handle datetime serialization
            data = self.model_dump(mode='json')
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
    
    def update_status(self, status: str, save_path: Optional[str] = None):
        """Update status and optionally save."""
        self.status = status
        if save_path:
            self.to_yaml(save_path)
    
    def get_job_dir(self) -> str:
        """Get the job directory path (convention: /data/jobs/{job_id})."""
        return f"/data/jobs/{self.job_id}"
    
    def get_manifest_path(self) -> str:
        """Get absolute path to manifest file."""
        return os.path.join(self.get_job_dir(), self.manifest.path)
    
    def get_results_path(self) -> str:
        """Get absolute path to results file."""
        return os.path.join(self.get_job_dir(), self.output.results_path)
    
    def get_execution_log_path(self) -> str:
        """Get absolute path to execution log."""
        return os.path.join(self.get_job_dir(), self.output.logs_path)
