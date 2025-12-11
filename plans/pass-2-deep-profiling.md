# Plan: Deep Profiling (Pass 2)

**Status:** Proposed
**Goal:** Generate a detailed JSON profile for every character, location, and faction in `entities_manual.yaml`.

## Problem Statement
We have a list of names ("Ravna", "Pham Nuwen"). We have a book. We need structured data ("Appearance: Dark hair", "Role: Protagonist") to power the Knowledge Graph.

## Methodology: "The Windowing Search"

We will avoid expensive whole-book context windows. Instead, we perform a deterministic **Search & Synthesize** loop.

### Step 1: Tooling Setup (The Profiler)
Create `scripts/generate_profiles.py` that:
1.  **Iterates** through each entity in `entities_manual.yaml`.
2.  **Searches** `content.json` for all occurrences of the Name and its Aliases.
3.  **Extracts** 1000-character windows around each match.
4.  **Ranks** windows by "Descriptive Density" (heuristics checking for words like *eyes, hair, wore, said, felt, tall, imposing*).
5.  **Batches** the Top 15 chunks into an LLM Prompt.

### Step 2: Prompt Engineering
Develop `prompts/profile_extraction.txt` to enforce a strict JSON schema:
-   **Appearance:** Physical traits (eyes, hair, build, cybernetics).
-   **Gear:** Items typically carried (weapons, tools).
-   **Personality:** Traits, speech patterns, motivations.
-   **Role:** Job/Function in the plot.
-   **Relationships:** Known connections to other entities (e.g. `{"target": "Pham Nuwen", "relation": "Ally"}`).
-   **First Appearance:** Which page first mentions them?

### Step 3: Execution & Review
1.  Run the Profiler on a **Pilot Batch** (Top 10 Characters) to verify quality.
2.  **Validation:** Check if hallucinations occur (e.g. inventing details not in the chunks).
3.  **Full Run:** Execute for all 368 entities.
4.  **Output:** Store in `kindle-ai-export/out/[ASIN]/profiles/{EntityName}.json`.

## Deliverables
- [ ] `scripts/generate_profiles.py`
- [ ] `prompts/profile_extraction.txt` (or functional equivalent in code)
- [ ] `profiles/` directory populated with JSON files.
- [ ] `Pass 2 Complete` checkpoint in README.

## Dependencies
- LLM Provider (OpenAI/Anthropic/Deepseek) via `llama-index` or direct API.
- Need to confirm **Ranking Heuristic** (Simple keyword count vs Embedding similarity). *Proposal: Start with Keyword Count for speed.*
