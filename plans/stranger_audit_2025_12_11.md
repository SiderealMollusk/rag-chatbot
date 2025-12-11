# Project Audit: A Stranger's Perspective
**Date:** 2025-12-11
**Auditor:** Agent (Simulating a new contributor)

## First Impressions

Scanning the repository for the first time, I'm struck by the ambitious scope—building a "Movie Bible" from raw text is a cool concept. However, navigating the actual implementation was a bit of a treasure hunt. Here are my raw notes on the onboarding experience.

### 1. The "Junkyard" Paradox
**Observation:** The core operational scripts (OCR, Segmentation, Analysis) seem to live in `scripts/junkyard`.
**Reaction:** This is the most confusing part. 
- *Is this code deprecated?*
- *Do I run `scripts/junkyard/ocr_book.py` only if I'm desperate?*
- *Where is the "real" pipeline?*

It turns out the `junkyard` *is* the pipeline. Renaming this to `scripts/pipeline` or just `scripts/core` would instantly build more trust. If I'm a new dev, I'm terrified to touch anything in a folder named "trash", but that seems to be where the magic happens.

### 2. The TypeScript / Python Chasm
**Observation:** There is a polished looking `kindle-ai-export` tool (TypeScript/Playwright) and a backend analysis stack (Python).
**Reaction:** I can see *how* to extract images, and I can see *how* to OCR them, but the handshake is missing.
- Does the TS script dump to a folder the Python script watches?
- Do I need to manually move files?
- A top-level `Makefile` or `run.sh` that maps `npm run export -> python ocr.py` is missing. I feel like I need to hold the system's hand to get from "screen capture" to "text".

### 3. Truth Source Dissonance
**Observation:**
- `KG_STATUS.md` claims: **Scene Segmentation: 100% Complete**
- `docs/knowledge_graph_construction/README.md` claims: **Pass 3: Scene Segmentation (Pending)**
**Reaction:** As a stranger, I don't know if the feature works or not. I'd probably assume the docs are stale, but it makes me hesitant to rely on the "100%" claim without verifying the code myself.

### 4. Application vs. Script Collection
**Observation:** There is a `backend/` (FastAPI) and `frontend/` (Next.js), but also a heavy reliance on standalone scripts.
**Reaction:** It feels like the project is mid-metamorphosis. It's evolving from a "bunch of python scripts run by `virgil`" into a "deployed web application".
- Use `docker-compose` implies a localized app.
- But the heavy lifting seems to still be in those manual/junkyard scripts.
- I'm unsure if the Web UI is just a viewer, or if it controls the pipeline.

## Recommendations
If I were to contribute, my first PRs would be:
1.  **Move the Cheese:** `mv scripts/junkyard scripts/ops` (or similar).
2.  **Bridge the Gap:** Add a `make pipeline` target that runs the Extraction -> OCR -> Ingest flow.
3.  **Sync the Docs:** Delete the "Pending" lines in the README if the status is truly Green.
4.  **Adopt the Pattern:** I found `scripts/jobs/workflows`... see below.

## 5. The Hidden Order (Update)
**Observation:** I initially missed `scripts/jobs/workflows`. This directory changes my assessment significantly. 
- It implements a sophisticated **Hybrid Job System** (Metal vs. Cloud).
- It follows a strict **Plan -> Dispatch -> Execute** lifecycle.
- It uses Redis for backlogs and Celery for execution.

**Reaction:** THIS is the metamorphosis!
- **Junkyard** = The Caterpillar. Ad-hoc, direct script execution, messy.
- **Jobs/Workflows** = The Butterfly. Orchestrated, scalable, distributed.

The project isn't just "cleaning up scripts"; it's moving from *scripting* to *platform engineering*. The `system_test` workflow acts as a proof-of-concept for this new engine.


**New Recommendation:**
Refactor the "June Scripts" (OCR, Segmentation) to become **Workflows**.
- `junkyard/ocr_book.py` -> `workflows/ingestion/plan.py`
- `junkyard/segment_scenes.py` -> `workflows/segmentation/plan.py`

This would unify the repository under the new Architecture.

## 6. Phase 2 Observations: The Hybrid Engine ("Take 2")
**Date:** 2025-12-11 (Post-Discovery)

I dug deeper into `backend/tasks` and `scripts/jobs/core`. The sophistication here is surprisingly high for a "work in progress".

### A. The "Conductor" Pattern
**Observation:** `scripts/jobs/core/conductor.py` is an intelligent router.
- It doesn't just run tasks; it balances them.
- **Rule 1:** Feed Metal (Ollama) first to keep the M1 chip saturated.
- **Rule 2:** Spill over to Cloud (Gemini) if Metal is full, but respect a Token Bucket rate limit.
- This is wildly more advanced than the sequential for-loops in `junkyard`.

### B. Task Alignment
**Observation:**
- `backend/tasks/rag.py` has distinct entries for `process_batch_gemini` and `process_batch_ollama`.
- The Conductor dynamically rewrites the generic `process_batch` task name to the specific runtime version based on where it sends the job.

**Reaction:** This confirms the architectural intent. The "Workflows" generate generic intent ("Analyze this"), and the "Conductor" decides the execution strategy ("Do it on Metal or Cloud").

### C. The Missing Link: Kindle Export
**Observation:** `kindle-ai-export` is still an island. It's a client-side (Playwright) tool that generates artifacts.
**Gap:** The Job System currently lives inside the Docker network (Shell/Redis/Celery). The Kindle Export runs on the Host (GUI required).
- **Migration Challenge:** You can't easily containerize the Playwright GUI part if it needs to see a real Kindle App (though it seems to use Cloud/Web Reader?).
- **Bridge Idea:** A "Watcher" Workflow.
    - `workflows/ingestion/plan.py` could scan the *output directory* of the Kindle Export tool.
    - When it sees new files, it generates Manifests to ingest them.
    - This keeps the GUI tool loose, but hooks its *output* into the rigorous pipeline.

### D. Final Verdict
The repository is split between "The Old World" (Junkyard scripts, manual execution) and "The New World" (Conductor, Redis, Celery).
- **The Old World** works but is fragile.
- **The New World** is robust but currently only fully implemented for `system_test`.
- **The Mission:** Port the `junkyard` logic into `backend/tasks` and `workflows/`.


