# Test Has Results Workflow

## Purpose
TODO: Describe what this workflow does.

## Usage

### 1. Plan
Generate a job package:
```bash
python /scripts/jobs/workflows/test_has_results/plan.py --count 10
```

### 2. Dispatch
Queue the tasks:
```bash
python /scripts/jobs/core/dispatch_v2.py /data/jobs/test_has_results_YYYYMMDD_HHMMSS/work_order.yaml
```

### 3. Execute
Run the conductor:
```bash
python /scripts/jobs/core/conductor_v2.py /data/jobs/test_has_results_YYYYMMDD_HHMMSS/work_order.yaml
```

### 4. Check Status
Monitor progress:
```bash
python /scripts/jobs/core/status.py /data/jobs/test_has_results_YYYYMMDD_HHMMSS/work_order.yaml
```

## Task Definition
TODO: Document the structure of tasks this workflow generates.

## Dependencies
TODO: List any required Celery tasks, external services, etc.
