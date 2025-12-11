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
TEMPLATES_DIR = "/scripts/jobs/templates/workflow"

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
    
    # Template substitutions
    substitutions = {
        '{{WORKFLOW_NAME}}': name,
        '{{WORKFLOW_TITLE}}': name.replace('_', ' ').title()
    }
    
    # Copy and process templates
    templates_path = Path(TEMPLATES_DIR)
    
    for template_file in templates_path.glob('*.template'):
        # Read template
        template_content = template_file.read_text()
        
        # Apply substitutions
        for placeholder, value in substitutions.items():
            template_content = template_content.replace(placeholder, value)
        
        # Determine output filename (remove .template suffix)
        output_filename = template_file.stem  # Removes .template
        output_path = workflow_dir / output_filename
        
        # Write processed template
        output_path.write_text(template_content)
        
        # Make Python files executable
        if output_filename.endswith('.py'):
            os.chmod(output_path, 0o755)
    
    print(f"✅ Created workflow: {name}")
    print(f"📁 Location: {workflow_dir}/")
    print(f"")
    print(f"Files created:")
    print(f"  - plan.py       (Task generator)")
    print(f"  - verify.py     (Result validator)")
    print(f"  - README.md     (Workflow documentation)")
    print(f"  - COMMANDS.md   (Execution steps)")
    print(f"")
    print(f"Next steps:")
    print(f"  1. Edit {workflow_dir}/plan.py")
    print(f"  2. Implement generate_{name}_tasks() logic")
    print(f"  3. Create your Celery task in backend/tasks/")
    print(f"  4. Update README.md and COMMANDS.md with workflow details")

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
