# Workflow CLI

Quick tool to manage job system workflows.

## Commands

### Create a New Workflow
```bash
python /scripts/jobs/workflow_cli.py create my_workflow_name
```

**What it does:**
- Creates `/scripts/jobs/workflows/my_workflow_name/`
- Generates `plan.py` stub with proper structure
- Generates `README.md` template
- Makes `plan.py` executable

**Next steps after creation:**
1. Edit `plan.py` and implement your `generate_*_tasks()` logic
2. Create the corresponding Celery task in `backend/tasks/`
3. Update `README.md` with workflow documentation

### List All Workflows
```bash
python /scripts/jobs/workflow_cli.py list
```

Shows all workflows with status indicators:
- ✅ = Has plan.py (ready to use)
- ⚠️  = Missing plan.py (incomplete)

### Show Workflow Info
```bash
python /scripts/jobs/workflow_cli.py info system_test
```

Displays:
- File structure
- README contents
- File sizes

## Example Usage

```bash
# Create a new workflow for OCR processing
python /scripts/jobs/workflow_cli.py create ocr_batch

# Edit the generated plan.py
vi /scripts/jobs/workflows/ocr_batch/plan.py

# List to verify
python /scripts/jobs/workflow_cli.py list

# Get details
python /scripts/jobs/workflow_cli.py info ocr_batch
```

## Workflow Naming Conventions

- Use lowercase with underscores: `gap_fill`, `ocr_batch`, `entity_extraction`
- Be descriptive but concise
- Avoid special characters
