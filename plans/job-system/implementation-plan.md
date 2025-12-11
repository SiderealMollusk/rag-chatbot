# Job System Implementation Plan

## Objective
Establish a robust, "Manifest-Driven" job execution system for managing long-running background tasks (like LLM processing) using Celery, Redis, and Loguru.

## Core Philosophy: The Manifest Pattern
1.  **Plan:** We authorize work by generating a `manifest.jsonl` (The Work Order).
2.  **Dispatch:** We execute the work order by feeding it to the Dispatcher.
3.  **Verify:** We confirm success by auditing the **Execution Receipts** returned by the workers.

## Components

### 1. Infrastructure (Docker)
- **Service:** `shell` (Already active) - Shared workspace.
- **Service:** `redis` (Already active) - Broker & Result Store.
- **Service:** `worker` (Already active) - Executes the tasks.
- **Service:** `flower` (Already active) - Dashboard.

### 2. The Job Lifecycle Scripts (`scripts/jobs/`)
We will use a "Workflow Plugin" structure to separate concerns. Each workflow type (System Test vs Production) has its own planning/verification logic, sharing a generic dispatcher.

```
scripts/jobs/
├── core/
│   ├── dispatch.py       # Generic: Reads ANY manifest -> Redis
│   ├── common.py         # Shared utils (Loguru setup, Paths)
│   └── schema.py         # Pydantic models for Manifest Entry
│
├── workflows/            # Domain-Specific Logic
│   ├── system_test/      # Workflow 1: Infrastructure Validation
│   │   ├── plan.py       # Generates debug/crud/sleep manifests
│   │   └── verify.py     # Checks task receipts
│   │
│   └── gap_fill/         # Workflow 2: Corpus Repair
│       ├── plan.py       # Scans DB/Corpus for gaps -> manifest
│       └── verify.py     # Checks final DB row counts
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

## Implementation Steps

### Step 1: Foundation
- [ ] Requirements: Add `loguru` to `backend/requirements.txt`.
- [ ] Directory: Create directory tree (`scripts/jobs/core`, `scripts/jobs/workflows`, etc.).
- [ ] Directory: Create `backend/tasks/`.

### Step 2: Code Refactor
- [ ] **Refactor Tasks**: Move `tasks.py` logic into `backend/tasks/` modules.
- [ ] **Instrument**: Add `logger.bind(task_id=...)` to all tasks.
- [ ] **Rebuild**: Update Docker container with new structure.

### Step 3: Tooling Logic (Core)
- [ ] **`core/dispatch.py`**: Implement generic manifest reader.
- [ ] **`core/schema.py`**: Define `ManifestEntry` model.

### Step 4: Tooling Logic (Workflows)
- [ ] **`workflows/system_test`**: Implement `plan.py` for mock generation.
- [ ] **`workflows/gap_fill`**: Port the gap-fill logic to `plan.py`.

## Protocol: How to Run
1.  **Enter Shell:** `docker exec -it movie_bible_shell /bin/bash`
2.  **Generate Plan:** `python scripts/jobs/workflows/system_test/plan.py --mode crud_stress`
3.  **Inspect:** `cat scripts/jobs/manifests/crud_stress_test.jsonl`
4.  **Dispatch:** `python scripts/jobs/core/dispatch.py scripts/jobs/manifests/crud_stress_test.jsonl`
5.  **Watch:** (Flower Dashboard)
6.  **Verify:** `python scripts/jobs/workflows/system_test/verify.py scripts/jobs/manifests/crud_stress_test.jsonl`
