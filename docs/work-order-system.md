# Work Order System v2

**Status:** ✅ Implemented (Coexists with v1)

The Work Order System formalizes job execution by separating **Intent** (what/how) from **Execution** (doing it).

## Core Concepts

### Job Package
A self-contained directory that holds everything for one execution run:

```
/data/jobs/demo_20251211_153000/
├── work_order.yaml      # The blueprint (metadata, config, tracking)
├── manifest.jsonl       # The tasks to run
├── results.jsonl        # Output (auto-collected, future feature)
└── execution.log        # Audit trail (CRITICAL)
```

### Work Order Structure

```yaml
job_id: demo_20251211_153000
name: "Demo - 5 tasks"
created: '2025-12-11T15:30:00'
status: pending  # pending | running | completed | failed

manifest:
  path: manifest.jsonl
  count: 5

routing_strategy: hybrid_supervisor  # force_metal | force_cloud | hybrid_supervisor
backlog_key: "job:demo_20251211_153000:backlog"

output:
  results_path: results.jsonl
  logs_path: execution.log

execution:
  started_at: null
  completed_at: null
  tasks_dispatched: 5
  tasks_completed: 0
  tasks_failed: 0
```

### Execution Log Format

**Critical Feature:** The `execution.log` tracks **EVERY** task movement:

```
2025-12-11 15:30:05 | [SYSTEM]  | JOB_STARTED     | Job demo_01 started. 5 tasks in backlog: job:demo_01:backlog
2025-12-11 15:30:06 | [SYSTEM]  | DECISION        | Conductor started with strategy: hybrid_supervisor
2025-12-11 15:30:07 | [Job-01]  | PULLED          | Pulled from job:demo_01:backlog
2025-12-11 15:30:07 | [Job-01]  | ROUTED          | Routed to queue_metal (Hybrid: Metal available)
2025-12-11 15:30:07 | [Job-02]  | PULLED          | Pulled from job:demo_01:backlog
2025-12-11 15:30:07 | [Job-02]  | ROUTED          | Routed to queue_cloud (Hybrid: Metal full, Budget: 1.0/2)
...
2025-12-11 15:30:37 | [Job-02]  | COMPLETED       | Finished in 30.1s
2025-12-11 15:31:07 | [Job-01]  | COMPLETED       | Finished in 60.0s
2025-12-11 15:31:37 | [SYSTEM]  | JOB_COMPLETED   | Job demo_01 finished. Success: 5/5, Failed: 0
```

**What You Get:**
- **When** each task was pulled from backlog
- **Where** it was routed (Metal or Cloud)
- **Why** (routing strategy decision)
- **When** it finished

---

## The New Workflow

### 1. Plan (Generate Job Package)
```bash
python /scripts/jobs/workflows/system_test/plan.py --mode demo --count 5 --strategy hybrid_supervisor
```

**Output:**
```
Created job package: /data/jobs/demo_20251211_153000/
  - work_order.yaml
  - manifest.jsonl (5 tasks)
  Strategy: hybrid_supervisor
  Backlog: job:demo_20251211_153000:backlog
```

### 2. Dispatch (Queue Tasks)
```bash
python /scripts/jobs/core/dispatch_v2.py /data/jobs/demo_20251211_153000/work_order.yaml
```

**Output:**
```
Dispatched 5 tasks to job:demo_20251211_153000:backlog
Job demo_20251211_153000 ready for execution
Next step: python /scripts/jobs/core/conductor_v2.py /data/jobs/demo_20251211_153000/work_order.yaml
```

### 3. Execute (Run Conductor)
```bash
python /scripts/jobs/core/conductor_v2.py /data/jobs/demo_20251211_153000/work_order.yaml
```

**Logs to stdout AND writes to `execution.log`**

### 4. Check Status (Anytime)
```bash
python /scripts/jobs/core/status.py /data/jobs/demo_20251211_153000/work_order.yaml
```

**Output:**
```
============================================================
JOB STATUS: demo_20251211_153000
============================================================
Name:      Demo - 5 tasks
Status:    RUNNING
Strategy:  hybrid_supervisor

------------------------------------------------------------
PROGRESS
------------------------------------------------------------
Dispatched:  5
Backlog:     0
Completed:   3
Failed:      0
Progress:    60.0%

------------------------------------------------------------
FILES
------------------------------------------------------------
Manifest:    /data/jobs/demo_20251211_153000/manifest.jsonl
Results:     /data/jobs/demo_20251211_153000/results.jsonl
Exec Log:    /data/jobs/demo_20251211_153000/execution.log
============================================================
```

### 5. Review Execution Log
```bash
cat /data/jobs/demo_20251211_153000/execution.log
```

---

## Routing Strategies

### `hybrid_supervisor` (Default)
- **Rule:** Fill Metal first (up to capacity)
- **Spillover:** If Metal full, send to Cloud (respects rate limits)
- **Use Case:** Cost-effective, prefers local compute

### `force_metal`
- **Rule:** All tasks go to Metal queue
- **Use Case:** Offline work, GPU-required tasks

### `force_cloud`
- **Rule:** All tasks go to Cloud queue
- **Use Case:** Speed-critical, burst workloads

---

## Migration from v1

The old workflow still works:
```bash
# Old way (still supported)
python plan.py --mode demo --count 5
python dispatch.py /data/system_test_demo_01.jsonl --backlog backlog:stress
python conductor.py --backlog backlog:stress
```

**New way (recommended):**
```bash
python plan.py --mode demo --count 5  # Creates job package
python dispatch_v2.py /data/jobs/demo_XX/work_order.yaml
python conductor_v2.py /data/jobs/demo_XX/work_order.yaml
```

---

## Benefits

1. **Auditability:** `execution.log` is a full audit trail
2. **Replay:** Re-run a job by re-dispatching the same work order
3. **Visibility:** `status.py` shows real-time progress
4. **Isolation:** Each job has its own directory
5. **Flexibility:** Change routing strategy without code changes

---

## Future Enhancements

- **Result Collection:** Auto-collect task results into `results.jsonl`
- **Failure Recovery:** Auto-retry failed tasks
- **Dashboard Integration:** Web UI to browse jobs
- **Cleanup:** Auto-archive old jobs
