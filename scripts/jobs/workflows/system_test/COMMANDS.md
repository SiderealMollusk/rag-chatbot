# System Test Workflow

This document describes the steps to run the `system_test` workflow.

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

## 2. Plan (Generate Manifest)
Create the job manifest file.

```bash
# Example: Generate 10 stress tasks
python /scripts/jobs/workflows/system_test/plan.py --mode stress_supervisor --count 10
```
*   **Result:** Creates a file at `/data/system_test_stress_supervisor_XX.jsonl`.
*   **Check:** Verify the file exists (Human: Check IDE `data/shell/`; Agent: `cat` the file).

## 3. Dispatch (Queue Jobs)
Send the jobs from the manifest to the Redis backlog.
*Replace `<FILE>` with the actual filename generated in Step 2.*

```bash
python /scripts/jobs/core/dispatch.py <FILE_PATH> --backlog backlog:stress
```
*   **Example:** `python /scripts/jobs/core/dispatch.py /data/system_test_stress_supervisor_01.jsonl --backlog backlog:stress`

## 4. Execute (Start Conductor)
Start the conductor to route tasks to workers. This process runs indefinitely until stopped.

```bash
python /scripts/jobs/core/conductor.py
```

## 5. View Logs
Monitor the execution.

*   **Dozzle (Logs):** [http://localhost:8080/container/movie_bible_shell](http://localhost:8080/container/movie_bible_shell)
*   **Flower (Tasks):** [http://localhost:5555](http://localhost:5555)
