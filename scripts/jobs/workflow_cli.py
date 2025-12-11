#!/usr/bin/env python3
"""
Workflow CLI - Manage job system workflows

Commands:
  create <name>    Create a new workflow with proper structure
  list             List all existing workflows
  info <name>      Show workflow details
"""
import sys
import os
import argparse
from pathlib import Path

WORKFLOWS_DIR = "/scripts/jobs/workflows"

def create_workflow(name: str):
    """Create a new workflow with proper file structure and stubs."""
    # Validate name
    if not name.replace('_', '').isalnum():
        print(f"❌ Error: Workflow name must be alphanumeric (underscores allowed)")
        sys.exit(1)
    
    workflow_dir = Path(WORKFLOWS_DIR) / name
    
    if workflow_dir.exists():
        print(f"❌ Error: Workflow '{name}' already exists at {workflow_dir}")
        sys.exit(1)
    
    # Create directory
    workflow_dir.mkdir(parents=True, exist_ok=True)
    
    # Create plan.py stub
    plan_template = f'''import sys
import json
import argparse
import random
from core.common import setup_logging, logger, require_context
from core.work_order import WorkOrder, WorkOrderManifest
from datetime import datetime
import os

def generate_{name}_tasks(count: int):
    """
    Generate tasks for {name} workflow.
    
    TODO: Implement your task generation logic here.
    """
    rows = []
    logger.info(f"Generating {{count}} {name} tasks...")
    
    for i in range(1, count + 1):
        # TODO: Replace this with your actual task structure
        rows.append({{
            "task": "tasks.your_task_name",  # Update this
            "kwargs": {{}},
            "meta": {{
                "description": f"{name} Task {{i}}/{{count}}",
                "id": f"Task-{{i:02d}}"
            }}
        }})
    
    return rows

def main():
    setup_logging()
    require_context('shell')
    
    parser = argparse.ArgumentParser(description="Generate {name.replace('_', ' ').title()} Job Packages")
    parser.add_argument("--count", type=int, default=5, help="Number of tasks to generate")
    parser.add_argument("--strategy", 
                       choices=["hybrid_supervisor", "force_metal", "force_cloud"], 
                       default="hybrid_supervisor",
                       help="Routing strategy")
    args = parser.parse_args()

    logger.info(f"Generating {name} job package with {{args.count}} tasks...")
    
    # Generate task data
    data = generate_{name}_tasks(args.count)
    
    # Create job package directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_id = f"{name}_{{timestamp}}"
    job_dir = f"/data/jobs/{{job_id}}"
    os.makedirs(job_dir, exist_ok=True)
    
    # Write manifest
    manifest_path = f"{{job_dir}}/manifest.jsonl"
    with open(manifest_path, 'w') as f:
        for row in data:
            f.write(json.dumps(row) + "\\n")
    
    # Create work order
    work_order = WorkOrder(
        job_id=job_id,
        name=f"{name.replace('_', ' ').title()} - {{args.count}} tasks",
        manifest=WorkOrderManifest(
            path="manifest.jsonl",
            count=len(data)
        ),
        routing_strategy=args.strategy,
        backlog_key=f"job:{{job_id}}:backlog"
    )
    
    # Write work order
    work_order_path = f"{{job_dir}}/work_order.yaml"
    work_order.to_yaml(work_order_path)
    
    logger.success(f"Created job package: {{job_dir}}/")
    logger.info(f"  - work_order.yaml")
    logger.info(f"  - manifest.jsonl ({{len(data)}} tasks)")
    logger.info(f"  Strategy: {{args.strategy}}")
    logger.info(f"  Backlog: {{work_order.backlog_key}}")

if __name__ == "__main__":
    main()
'''
    
    # Create README.md stub
    readme_template = f'''# {name.replace('_', ' ').title()} Workflow

## Purpose
TODO: Describe what this workflow does.

## Usage

### 1. Plan
Generate a job package:
```bash
python /scripts/jobs/workflows/{name}/plan.py --count 10
```

### 2. Dispatch
Queue the tasks:
```bash
python /scripts/jobs/core/dispatch_v2.py /data/jobs/{name}_YYYYMMDD_HHMMSS/work_order.yaml
```

### 3. Execute
Run the conductor:
```bash
python /scripts/jobs/core/conductor_v2.py /data/jobs/{name}_YYYYMMDD_HHMMSS/work_order.yaml
```

### 4. Check Status
Monitor progress:
```bash
python /scripts/jobs/core/status.py /data/jobs/{name}_YYYYMMDD_HHMMSS/work_order.yaml
```

## Task Definition
TODO: Document the structure of tasks this workflow generates.

## Dependencies
TODO: List any required Celery tasks, external services, etc.
'''
    
    # Write files
    (workflow_dir / "plan.py").write_text(plan_template)
    (workflow_dir / "README.md").write_text(readme_template)
    
    # Make plan.py executable
    os.chmod(workflow_dir / "plan.py", 0o755)
    
    print(f"✅ Created workflow: {name}")
    print(f"📁 Location: {workflow_dir}/")
    print(f"")
    print(f"Files created:")
    print(f"  - plan.py      (Task generator)")
    print(f"  - README.md    (Documentation)")
    print(f"")
    print(f"Next steps:")
    print(f"  1. Edit {workflow_dir}/plan.py")
    print(f"  2. Implement generate_{name}_tasks() logic")
    print(f"  3. Create your Celery task in backend/tasks/")
    print(f"  4. Update README.md with workflow details")

def list_workflows():
    """List all existing workflows."""
    workflows_path = Path(WORKFLOWS_DIR)
    
    if not workflows_path.exists():
        print(f"❌ Workflows directory not found: {WORKFLOWS_DIR}")
        sys.exit(1)
    
    workflows = [d.name for d in workflows_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    if not workflows:
        print("No workflows found.")
        return
    
    print(f"\\n{'='*60}")
    print(f"AVAILABLE WORKFLOWS")
    print(f"{'='*60}")
    for wf in sorted(workflows):
        readme_path = workflows_path / wf / "README.md"
        plan_path = workflows_path / wf / "plan.py"
        
        status = "✅" if plan_path.exists() else "⚠️ "
        print(f"{status} {wf}")
        
        if readme_path.exists():
            # Try to extract first line of purpose section
            try:
                content = readme_path.read_text()
                if "## Purpose" in content:
                    purpose_line = content.split("## Purpose")[1].split("\\n")[1].strip()
                    if purpose_line and not purpose_line.startswith("TODO"):
                        print(f"    {purpose_line}")
            except:
                pass
    print(f"{'='*60}\\n")

def show_workflow_info(name: str):
    """Show detailed info about a workflow."""
    workflow_dir = Path(WORKFLOWS_DIR) / name
    
    if not workflow_dir.exists():
        print(f"❌ Workflow '{name}' not found")
        sys.exit(1)
    
    print(f"\\n{'='*60}")
    print(f"WORKFLOW: {name}")
    print(f"{'='*60}")
    print(f"Location: {workflow_dir}")
    print(f"\\nFiles:")
    
    for file in sorted(workflow_dir.iterdir()):
        if file.is_file():
            size = file.stat().st_size
            print(f"  - {file.name: <20} ({size} bytes)")
    
    readme_path = workflow_dir / "README.md"
    if readme_path.exists():
        print(f"\\n{'-'*60}")
        print(f"README:")
        print(f"{'-'*60}")
        print(readme_path.read_text())
    
    print(f"{'='*60}\\n")

def main():
    parser = argparse.ArgumentParser(
        description="Workflow CLI - Manage job system workflows",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new workflow')
    create_parser.add_argument('name', help='Workflow name (e.g., gap_fill, ocr_batch)')
    
    # List command
    subparsers.add_parser('list', help='List all workflows')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show workflow details')
    info_parser.add_argument('name', help='Workflow name')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'create':
        create_workflow(args.name)
    elif args.command == 'list':
        list_workflows()
    elif args.command == 'info':
        show_workflow_info(args.name)

if __name__ == "__main__":
    main()
