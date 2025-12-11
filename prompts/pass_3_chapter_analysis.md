# Knowledge Graph Extraction Prompt (Chapter Level)

**Role:** Expert Literary Analyst and Knowledge Graph Architect.
**Task:** Analyze the provided specific Novel Chapter. Deeply understand the narrative flow, characters, and setting.
**Goal:** Segment the chapter into distinct **Scenes** and extract rich metadata for each scene to build a Knowledge Graph.

## Definitions
- **Scene:** A continuous block of action occurring in a specific **Location** and **Timeframe**. If the characters move to a new place, time jumps forward, or the POV character changes significantly, that is a new scene.
- **Characters:** List ONLY characters physically present or actively participating in the scene (not just mentioned).
- **Entities:** Key objects, ships, or concepts central to the scene.

## Output Format (JSON)

```json
{
  "chapter_title": "Derived Title or Number",
  "chapter_summary": "A high-level summary of the entire chapter's narrative arc.",
  "scenes": [
    {
      "scene_index": 1,
      "start_sentence": "The exact first sentence of the scene text.",
      "end_sentence": "The exact last sentence of the scene text.",
      "location": {
        "name": "Specific Location (e.g. 'Ravna's Apartment - Balcony')",
        "region": "Broader Region (e.g. 'Sjandra Kei', 'High Beyond')",
        "description": "Brief visual description of the setting in this scene."
      },
      "characters_present": [
        "Ravna Bergsndot",
        "Pham Nuwen",
        "Blueshell"
      ],
      "timeframe": "relative time (e.g. 'Late Night', 'Moments later', 'Three days ago')",
      "summary": "Detailed summary of the action in this specific scene.",
      "key_events": [
        "Event 1",
        "Event 2"
      ],
      "mood": "The emotional atmosphere (e.g. 'Tense', 'Melancholic', 'Chaotic')",
      "significance": "Why does this scene matter to the plot? (e.g. 'Reveals the traitor', 'Introduction of the Blight')"
    }
  ]
}
```

## Instructions
1. **Read** the full chapter text provided below.
2. **Segment** it into scenes based on breaks in time, place, or POV.
3. **Extract** the details for the JSON structure above.
4. **Quote** the `start_sentence` and `end_sentence` VERBATIM from the text so they can be mapped back programmatically.
5. **Be Thorough:** Do not skip short scenes. Capture every shift in the narrative.

## Chapter Text
[PASTE CHAPTER TEXT HERE]
