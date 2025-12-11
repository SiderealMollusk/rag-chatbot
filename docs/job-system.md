# Job System Operations Manual

This document describes the **Hybrid Job Execution System** used to process long-running tasks (like LLM Annotation) using a combination of local hardware (Metal/M1) and cloud APIs (Gemini).

## Architecture Overview

The system uses the **Supervisor Pattern** to balance work between limited resources.

### The Supervisor (Conductor)
Instead of dumping all work into the queue at once, a smart script (`conductor.py`) drip-feeds work into the execution queues based on real-time capacity monitoring.

1.  **Backlog (Redis List):** The "Waiting Room". All planned jobs sit here first.
2.  **Supervisor Loop:** Checks the status of the Workers every second.
    *   **Rule A (Metal/M1):** If the Local Worker has < 2 jobs queued, send it a job immediately. (Ensures 100% utilization).
    *   **Rule B (Cloud/Gemini):** If the Cloud Worker has < 5 jobs queued **AND** we haven't hit the API rate limit recently, send it a job.

### Queues & Workers
| Worker | Queue Name | Concurrency | Purpose |
|:---|:---|:---|:---|
| `worker_metal` | `queue_metal` | 1 | CPU/GPU intensive local tasks (Ollama). Sequential processing to avoid system lag. |
| `worker_cloud` | `queue_cloud` | 10 | I/O bound tasks (Gemini API). Parallel processing up to quota limits. |

---

## Operational Guide

### 1. The Workflow
All operations happen inside the `movie_bible_shell` container.

**A. Plan (Generate the Manifest)**
Decide what work needs to be done.
```bash
# Example: Plan a system test gap fill
python scripts/jobs/workflows/system_test/plan.py --mode backlog --count 50
# Output: scripts/jobs/manifests/gap_fill_v1.jsonl
```

**B. Dispatch (Load the Backlog)**
Push the planned items into the Redis Backlog (Waiting Room).
```bash
python scripts/jobs/core/dispatch.py scripts/jobs/manifests/gap_fill_v1.jsonl --target backlog:gap_fill
```

**C. Execute (Start the Conductor)**
Start the supervisor to begin distributing work.
```bash
python scripts/jobs/core/conductor.py --backlog backlog:gap_fill
```
*Watch the logs! You will see the Conductor making decisions: "Fed Metal", "Fed Cloud", "Cloud Paused due to Rate Limit".*

**D. Verify**
Check that the work was actually completed.
```bash
python scripts/jobs/workflows/system_test/verify.py --file scripts/jobs/manifests/gap_fill_v1.jsonl
```

### 2. Monitoring
*   **Logs:** `docker logs -f movie_bible_shell` (if Redirected) or watch the terminal running the Conductor.
*   **Flower Dashboard:** `http://localhost:5555`. View active tasks and queue depths visually.

### 3. Troubleshooting
*   **"Cloud stuck on PENDING":** If the Conductor is running but Cloud queue is empty, check if `GEMINI_API_KEY` is valid or if the bucket logic is pausing it (Rate Limit protection).
*   **"Metal worker slow":** It's running locally. Standard performance applies. Check `top` or Activity Monitor on host.
kflow 1: Infrastructure Validation
│   │   ├── plan.py       # Generates debug/crud/sleep manifests
│   │   └── verify.py     # Checks task receipts
│   │
│   └── gap_fill/         # Workflow 2: Corpus Repair
│       ├── plan.py       # Scans DB/Corpus for gaps -> manifest
│
└── manifests/            # The Output Artifacts
    ├── system_test_01.jsonl
    └── gap_fill_run_05.jsonl
```

- **`core/dispatch.py`**:
    *   Iterates *any* valid manifest file.
    *   Sends tasks to Celery based on the `task` and `args` fields.
    *   Logs "Job Sent" events.

- **`workflows/system_test/plan.py`**:
    *   Generates manifests for `debug`, `sleep`, `crud`, and `crud_latency` tests.
    *   Allows mocking scale (e.g., "Create 50 sleep tasks").

### 3. Task Package (`backend/tasks/`)
We will refactor the single `tasks.py` into a nested package structure for clarity:

- **`backend/tasks/__init__.py`**: Celery App definition.
- **`backend/tasks/diagnostics.py`**:
    *   `debug_task(msg)`: Echoes input.
    *   `sleep_task(sec)`: Tests timeouts/concurrency.
- **`backend/tasks/crud.py`**:
    *   `fast_crud_task(data)`: Performs atomic Create-Read-Update-Delete cycle. Returns `{"lifecycle": ["created", "verified", "deleted"]}` logic receipt.
    *   `sleep_crud_task(sec, data)`: Same, but with connection pooling stress (sleep before write).
- **`backend/tasks/rag.py`**:
    *   `process_batch_task(ids, data)`: The Gemini LLM processor.

### 4. Logging Standard
- **Library:** `loguru` (Best-in-class structured logging for Python).
- **Format:** JSON lines for machine parsing, Colors for humans.

## Protocol: How to Run
1.  **Enter Shell:** `docker exec -it movie_bible_shell /bin/bash`
2.  **Generate Plan:** `python scripts/jobs/workflows/system_test/plan.py --mode crud_stress`
3.  **Inspect:** `cat scripts/jobs/manifests/crud_stress_test.jsonl`
4.  **Dispatch:** `python scripts/jobs/core/dispatch.py scripts/jobs/manifests/crud_stress_test.jsonl`
5.  **Watch:** (Flower Dashboard)
6.  **Verify:** `python scripts/jobs/workflows/system_test/verify.py scripts/jobs/manifests/crud_stress_test.jsonl`
