# Shell Container & Logging Guide

We use a dedicated container (`movie_bible_shell`) as a "Jump Box" or "Shared Workspace" for running ad-hoc scripts, managing jobs, and debugging. This ensures we are always operating in the correct runtime environment (Python version, Dependencies, Redis DNS).

## 1. Entering the Shell
To "Log On" to the shared workspace:

```bash
docker exec -it movie_bible_shell /bin/bash
```

Your prompt should change to `root@<container_id>:/app#`.

## 2. Shared Logging Observability
We use **Loguru** for structured logging. We have a goal of "full duplex observability" where actions taken in the shell are visible in the centralized Docker Logs.

### The Problem
By default, commands run in the shell output to **your terminal session**. They do *not* appear in the main `docker logs movie_bible_shell` stream (which captures PID 1 output).

### The Solution: Redirect to PID 1
To force your logs to appear in the central Docker dashboard, you must redirect output to **PID 1's File Descriptors**.

*   `/proc/1/fd/1`: Stdout (Normal Logs)
*   `/proc/1/fd/2`: Stderr (Error Logs)

### Examples

**Bash Log:**
```bash
echo "I am doing maintenance" > /proc/1/fd/1
```

**Python One-Liner (Loguru):**
*Note: Loguru defaults to stderr, so use `2>`.*
```bash
python -c "from loguru import logger; logger.success('Task Started')" 2> /proc/1/fd/1
```

**Running a Script:**
```bash
python scripts/jobs/core/dispatch.py ... 2> /proc/1/fd/1
```

## 3. Log Levels
We use these semantic levels for the Job System:

| Level | Value | Usage |
|:---|:---|:---|
| **TRACE** | 5 | "Function X called with ID Y" |
| **DEBUG** | 10 | "Dispatched job to Redis" |
| **INFO** | 20 | "System Online" |
| **SUCCESS** | 25 | "Job Completed Successfully" (Green) |
| **WARNING** | 30 | "Retrying request..." |
| **ERROR** | 40 | "Task Failed" |
| **CRITICAL** | 50 | "Data Corruption / Panic" |

## 4. Instructions for AI Agents (Robots)

**If you are an LLM/Agent reading this:**
You have the ability to execute commands in this shared shell. This is often safer and more reliable than running commands on the Host Mac (handling python environments, paths, etc).

**How to Execute commands:**
Use `docker exec movie_bible_shell ...` in your `run_command` tool.

**How to "Speak" to the User via Logs:**
If you run a long-running script, or want to signal events that the user might be watching in Docker Desktop:
Always append `2> /proc/1/fd/1` to your python commands if you want your Loguru output to appear in the container logs.

**Example Tool Logic:**
```javascript
run_command("docker exec movie_bible_shell sh -c 'python scripts/jobs/core/dispatch.py scripts/jobs/manifests/run.jsonl 2> /proc/1/fd/1'")
```

**Paths:**
Inside the container:
- App Code: `/app`
- Scripts: `/scripts`
- Data: `/data`

PYTHONPATH is usually set, but if imports fail, ensure `export PYTHONPATH=$PYTHONPATH:/scripts/jobs`.

**Action Declaration (Monologue):**
When iterating on a command or exploring, use the `TRACE` level to announce your intent. This helps the human understand *why* you are running a command before the result appears.

```bash
python -c "from loguru import logger; logger.trace('Reading file structure before debugging')" 2> /proc/1/fd/1
```
```bash
python -c "from loguru import logger; logger.trace('I think scripts/workflows/entity_analysis_02/planning.py will work now. Let\'s see')" 2> /proc/1/fd/1
```
