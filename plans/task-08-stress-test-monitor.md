# Task 08: Stress Test & Conductor Verification

This task implements a specific stress test to validate the Hybrid Supervisor logic, as requested by the user.

## Goal
Verify that the `conductor` correctly prioritizes the local M1 worker (Metal) and spills over to the Cloud worker (Gemini) only when necessary, while strictly adhering to rate limits and queue depths.

## Specifications
1.  **Job Profile**: 10 total jobs. Each takes 1.5 - 2.5 minutes (90s - 150s).
2.  **Workers**:
    *   **Metal (M1)**: Concurrency 1. Conductor attempts to keep queue depth at 2.
    *   **Cloud (Gemini)**: Rate limit **max 2 jobs/minute**.
3.  **Logging**: Specific debug logs for:
    *   Start of script.
    *   "M1 is full, trying Gemini".
    *   "Gemini near rate limit".
    *   "No compute available holding".

## Implementation Plan

### 1. Refactor `scripts/jobs/core/conductor.py`
We will enhance the supervisor loop to support dynamic task names and specific feedback logs.

*   **Configurable Rate Limits**: Allow `CLOUD_TOKENS_PER_MIN` to be set via CLI (defaulting to 2.0 for this test).
*   **Intelligent Routing**:
    *   Check Metal Queue.
    *   If full -> Log "M1 is full, trying Gemini".
    *   Check Cloud Queue + Tokens.
    *   If Tokens low -> Log "Gemini near rate limit".
    *   If both full/limited -> Log "No compute available holding".
    *   *Correction*: To support the logs correctly without losing data, we must PEEK or rely on the `if/else` logic carefully without popping until we are sure we can send. (Actually, popping and holding in memory for a split second is fine, but checking lengths *before* popping is safer to avoid data loss if we crash).
*   **Task Dispatch**:
    *   Remove hardcoded `rag.process_batch_...` task names.
    *   Use the `task` field from the manifest JSON if available.
    *   Allow specific routing overrides (e.g., all "sleep" tasks go to both Metal/Cloud queues depending on capacity, but we need to ensure the *worker* listening on `queue_metal` can physically run the code. since it's the same codebase, it can).

### 2. Create Test Plan Generator: `scripts/jobs/workflows/system_test/plan_stress.py`
A new script to generate the specific 10-job manifest.

*   **Inputs**: None (hardcoded for this spec).
*   **Output**: `scripts/jobs/manifests/stress_test_v1.jsonl`.
*   **Content**:
    *   10 Entries.
    *   Task: `tasks.sleep_task`.
    *   Args: Random int between 90 and 150.
    *   Metadata: `{"id": "Job X"}`.

### 3. Execution
The user will run:
```bash
# 1. Generate
python scripts/jobs/workflows/system_test/plan_stress.py

# 2. Open Log Viewer (Dozzle)
# http://localhost:8080

# 3. Load Backlog
python scripts/jobs/core/dispatch.py scripts/jobs/manifests/stress_test_v1.jsonl --target backlog:stress

# 4. Start Conductor
python scripts/jobs/core/conductor.py --backlog backlog:stress --rate-limit 2.0
```

## Verification
We expect to see:
*   M1 immediately picks up 1 job (running) + 1 queued.
*   Conductor waits.
*   M1 gets a 2nd job in queue? (Limit is 2).
*   Spillover to Cloud starts.
*   Cloud accepts 2 jobs rapidly.
*   Conductor pauses Cloud dispatch ("Gemini near rate limit").
*   M1 churns slowly (1 job every ~2 mins).
*   Cloud churns steadily (2 jobs every minute).
