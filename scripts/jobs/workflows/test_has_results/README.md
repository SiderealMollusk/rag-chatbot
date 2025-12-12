# Test Has Results Workflow

## Purpose
Demonstrates job execution with **observable results** and **visible processing time**.

Each task:
- **Multiplies two random numbers** (1-100) - Actual computational work
- **Sleeps for 3-6 seconds** - Makes execution observable in real-time
- **Returns structured results** - Verifiable outputs with metadata

**Use Case:** Testing result collection, verification, and dashboard observation without external dependencies.

## Task Structure
Each generated task looks like:
```json
{
  "task": "tasks.compute_multiply",
  "kwargs": {"a": 42, "b": 17, "sleep_duration": 4},
  "meta": {
    "id": "Task-01",
    "description": "Compute 42 × 17 (sleep 4s)",
    "expected_result": 714
  }
}
```

## Result Format
Each task returns:
```json
{
  "operation": "multiply",
  "input_a": 42,
  "input_b": 17,
  "result": 714,
  "sleep_duration": 4,
  "actual_duration": 4.01,
  "started": "2025-12-11T16:00:00",
  "finished": "2025-12-11T16:00:04"
}
```

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
