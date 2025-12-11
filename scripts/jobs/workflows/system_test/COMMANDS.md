# Quick Start Log

```bash
# 0. Access Shell
docker exec -it movie_bible_shell /bin/bash

# 1. Setup Environment (Inside Container)
export PYTHONPATH=/scripts/jobs

# 2. Generate Plan
python /scripts/jobs/workflows/system_test/plan.py --mode stress_supervisor --count 10

# 3. Dispatch
python /scripts/jobs/core/dispatch.py \
  /data/system_test_stress_supervisor_01.jsonl \
  --backlog backlog:stress
```

# 3. Watch Logs
# http://localhost:8080/container/movie_bible_shell

*Note: System stops after jobs complete. Auto-verify WIP.*
