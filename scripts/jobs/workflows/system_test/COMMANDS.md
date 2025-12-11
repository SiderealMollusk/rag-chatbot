# Quick Start Log

```bash
# 1. Generate Plan
python scripts/jobs/workflows/system_test/plan.py --mode stress_supervisor --count 10
# (Needs to run inside container: docker exec movie_bible_shell python scripts/jobs/workflows/system_test/plan.py ...)

# 2. Dispatch (Update filename!)
docker exec -e PYTHONPATH=/scripts/jobs movie_bible_shell \
  python /scripts/jobs/core/dispatch.py \
  /scripts/jobs/manifests/system_test_stress_supervisor_01.jsonl \
  --backlog backlog:stress

# 3. Watch Logs
# http://localhost:8080/container/movie_bible_shell
```

*Note: System stops after jobs complete. Auto-verify WIP.*
