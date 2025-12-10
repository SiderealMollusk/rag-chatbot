# Pass 2: Deep Profiling

**Goal:** Generate a rich, structured profile for every entity in `entities_manual.yaml`.

## Concept: The Windowing Search

Unlike vector search which is fuzzy, we use **deterministic windowing** to find facts.
1.  **Search:** Find every occurrence of the Entity Name (and aliases) in the text.
2.  **Window:** Grab the surrounding paragraph (+/- 500 chars).
3.  **Synthesize:** Feed the top 20 most "descriptive" chunks into an LLM to generate the JSON profile.

## Output Structure (`profiles/Name.json`)

```json
{
  "name": "Ravna Bergsndot",
  "aliases": ["Ravna", "Ms. Bergsndot"],
  "category": "CHARACTER",
  "description": {
    "appearance": "...",
    "gear": ["Commsset", "Datagoggles"],
    "personality_traits": ["Curious", "Competent", "Lonely"],
    "key_relationships": [
       {"target": "Pham Nuwen", "type": "Ally"},
       {"target": "Blueshell", "type": "Colleague"}
    ]
  },
  "narrative_role": "Protagonist",
  "first_appearance": "Page 12",
  "citations": [
     {"text": "Ravna adjusted her goggles...", "page": 14}
  ]
}
```

## Algorithm

1.  **Input:** `entities_manual.yaml`
2.  **For each Entity:**
    *   Find all text chunks containing `name` or `aliases`.
    *   Rank chunks by "Descriptive Density" (Keywords like: *looked, wore, said, felt, tall, eyes*).
    *   Select Top N chunks.
    *   **LLM Call:** "Based on these excerpts, generate the Profile JSON."
3.  **Output:** Save to `profiles/{Safe_Name}.json`.

## Artifacts

*   **Script:** `scripts/generate_profiles.py`
*   **Prompt:** `prompts/profile_extraction.txt`
