# System Test Workflow: Predictable Demo (30s Spillover)

This workflow demonstrates the Hybrid Job System's ability to prioritize "Metal" (Local) workers and spill over to "Cloud" (Gemini) when capacity is reached.

**Scenario:** 
- **5 Tasks** of **30 seconds** duration each.
- **Metal Capacity:** 1 Active + 2 Queued = 3 Max.
- **Expected Behavior:** 
    - Jobs 1-3 fill Metal.
    - Jobs 4-5 spill to Cloud.
    - Cloud jobs finish first (30s).
    - Metal jobs finish sequentially (30s, 60s, 90s).

---

## 0. Prerequisite: Observability
Open these in separate windows/tabs:

1.  **Dashboard:** [http://localhost:3000/jobs](http://localhost:3000/jobs)
2.  **Terminal Log Stream:**
    ```bash
    docker compose logs -f | grep --line-buffered "\[job-system\]"
    ```

---

## 1. Execution (Inside Shell)

Enter the shell if not already there:
```bash
docker exec -it movie_bible_shell /bin/bash
```

Run the following sequence:

### Step A: Setup & Flush
Clean the slate.
```bash
export PYTHONPATH=/scripts/jobs
python /scripts/jobs/core/flush.py --force
```

### Step B: Plan
Generate the demo manifest.
```bash
python /scripts/jobs/workflows/system_test/plan.py --mode demo --count 5
```
*Take note of the filename output (e.g., `/data/system_test_demo_01.jsonl`)*

### Step C: Dispatch
Start the race! (Replace filename as needed).
```bash
python /scripts/jobs/core/dispatch.py /data/system_test_demo_01.jsonl --backlog backlog:stress
```

---

## 2. Validation

**Watch the Dashboard:**
*   [ ] **T+0s:** Backlog -> 0. Metal Queue -> 2. Cloud Queue -> 2.
*   [ ] **T+30s:** Cloud Queue -> 0 (Done). Metal Queue -> 2 (Job 1 done, Job 2 starts).
*   [ ] **T+90s:** All queues empty. Completed -> 5.

**Watch the Logs:**
*   Look for `[job-system] | INFO | Job Job-04 assigned to Gemma` in the Conductor logs.
*   Look for `t.d:sleep_task - >> Predict : HH:MM:SS` in the Worker logs.
