# Test Has Results Workflow Commands

This document describes the steps to run the `test_has_results` workflow.

## 0. Execution Context
**All commands below must be run inside the `movie_bible_shell` container.**

*   **Human Operator:**
    1.  Enter the shell: `docker exec -it movie_bible_shell /bin/bash`
    2.  Run the commands as listed below directly.
*   **AI Agent / CI:**
    *   Wrap commands using `docker exec movie_bible_shell bash -c "<COMMAND>"`.
    *   Ensure `PYTHONPATH` is set for every command (e.g., `export PYTHONPATH=/scripts/jobs && <COMMAND>`).

---

## 1. Setup
Initialize the environment path.

```bash
export PYTHONPATH=/scripts/jobs
```

## 2. Plan (Generate Job Package)
Create a job package with manifest and work order.

```bash
# TODO: Adjust --count as needed
python /scripts/jobs/workflows/test_has_results/plan.py --count 10
```
*   **Result:** Creates a job package at `/data/jobs/test_has_results_YYYYMMDD_HHMMSS/`.
*   **Check:** Note the job directory path from the output.

## 3. Dispatch (Queue Jobs)
Send the jobs from the work order to the Redis backlog.
*Replace `<JOB_DIR>` with the directory from Step 2.*

```bash
python /scripts/jobs/core/dispatch_v2.py <JOB_DIR>/work_order.yaml
```
*   **Example:** `python /scripts/jobs/core/dispatch_v2.py /data/jobs/test_has_results_20251211_150000/work_order.yaml`

## 4. Execute (Start Conductor)
Start the conductor to route tasks to workers. This process runs until the backlog is empty.

```bash
python /scripts/jobs/core/conductor_v2.py <JOB_DIR>/work_order.yaml
```

## 5. Check Status
Monitor job progress.

```bash
python /scripts/jobs/core/status.py <JOB_DIR>/work_order.yaml
```

## 6. View Execution Log
Review the detailed audit trail.

```bash
cat <JOB_DIR>/execution.log
```

## 7. View Results (Optional)
If result collection is implemented:

```bash
cat <JOB_DIR>/results.jsonl
```

## 8. Monitoring Tools
*   **Dashboard:** [http://localhost:3000/jobs](http://localhost:3000/jobs)
*   **Dozzle (Logs):** [http://localhost:8080](http://localhost:8080)
*   **Flower (Tasks):** [http://localhost:5555](http://localhost:5555)
