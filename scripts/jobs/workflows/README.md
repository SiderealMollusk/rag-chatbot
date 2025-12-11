# Job Workflows

This directory manages the operational workflows for the **Hybrid Job Execution System**. A "Workflow" is a standardized process to Plan (Generate Manifest), Dispatch (Queue), and Execute (Process) a specific type of work.

## 1. Using a Generic Workflow
The system is designed so that all workflows follow the same lifecycle:

| Stage | Action | Trigger | Inputs | Outputs | Context |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Plan** | Generate specific tasks | `python scripts/jobs/workflows/<WORKFLOW>/plan.py` | CLI Args | `manifest.jsonl` | **Shell Container** |
| **2. Dispatch** | Queue tasks | `python scripts/jobs/core/dispatch.py` | `manifest.jsonl` | Redis List | **Shell Container** |
| **3. Execute** | Route & Run | `python scripts/jobs/core/conductor.py` | Redis Backlog | Workers | **Shell Container** |
| **4. Verify** | Validate results | `python scripts/jobs/workflows/<WORKFLOW>/verify.py` | Completion State | Logs | **Shell Container** |

---

## 2. List of Workflows

### A. `system_test` (Infrastructure Validation)
Validates system stability, supervisor logic, and rate limiting.

*   **Logic:** `scripts/jobs/workflows/system_test/plan.py`
*   **Modes:**
    *   `--mode stress_supervisor`: Generates 10 long-running "sleeper" tasks (90-150s) to test queue pressure and cloud spillover.
    *   `--mode debug`: Simple echo tasks.
    *   `--mode crud`: Database write/read/delete tests.
*   **Target Backlog:** `backlog:stress` (Convention)
*   **Example:**
    ```bash
    # Plan (Run in Shell)
    docker exec movie_bible_shell \
      python scripts/jobs/workflows/system_test/plan.py --mode stress_supervisor --count 10
    
    # Dispatch (Run in Shell)
    docker exec -e PYTHONPATH=/scripts/jobs movie_bible_shell \
      python /scripts/jobs/core/dispatch.py \
      /scripts/jobs/manifests/system_test_stress_supervisor_01.jsonl \
      --backlog backlog:stress
    ```

### B. `gap_fill` (Content Repair)
*(Planned)* Scans the `bible.db` for missing nodes or disconnected edges and generates jobs to fix them.

---

## 3. Making a New Workflow
To add a new capability (e.g., "Image Analysis"):

1.  **Create Directory:**
    `mkdir scripts/jobs/workflows/image_analysis`

2.  **Create Planner (`plan.py`):**
    *   Must output a JSONL file to `scripts/jobs/manifests/`.
    *   Must use `core.common.get_next_filename` for versioning.
    *   Entries must match the Schema: `{"task": "...", "args": [], "meta": {...}}`.

3.  **Define Tasks (Backend):**
    *   Add your Celery task logic in `backend/tasks/<category>.py`.
    *   Ensure the task name in the manifest matches the Celery task name.

4.  **Update Conductor (Optional):**
    *   If you need special routing logic (e.g., "Always send Image tasks to Cloud"), add a rule in `scripts/jobs/core/conductor.py`.
    *   Otherwise, standard routing (Metal First -> Cloud Spillover) applies.
