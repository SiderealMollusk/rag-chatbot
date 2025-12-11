# Pass 3: Scene Segmentation

**Goal:** Break down linear Chapter text into discreet **Scenes**.
A Scene is defined as a continuous block of action occurring in a specific **Location** and **Timeframe**.

## Strategy
Since visual markers (`***`) are unreliable or absent in the OCR, we use **Semantic Segmentation** via LLM.

### Algorithm
1.  **Input:** Text from `named_chapters/*.txt`.
2.  **Windowing:** 
    - Text is potentially too long for precise LLM attention (10k+ tokens).
    - We process text in **Chunks** (e.g., 2000 words / 8k chars) with **Overlap** (500 chars).
    - **Calibration:** We verify the optimal chunk size to ensure the LLM catches breaks without losing context.
3.  **LLM Task:**
    - Prompt: "Identify the *Start Sentence* of any new scene within this text. A new scene occurs when Location, Time, or POV changes."
    - Output: JSON list of "Start Sentences" or "Paragraph Indices".
4.  **Reconstruction:**
    - Map quotes back to source text indices.
    - Split the source text at these indices.
    - Merge accidental splits if needed (optional logic).
5.  **Metadata Extraction (Pass 3.5?):**
    - Once split, each Scene is treated as a mini-document.
    - We (later) extract `Location`, `Characters Present`, `Time`, and `Summary` for the Knowledge Graph.

## Calibration Mode
The script `segment_scenes.py` includes a `--calibrate` or `--dry-run` mode.
- Allows testing on a single chapter.
- Outputs the detected "Break Sentences" to console for manual verification.
- User can adjust `--chunk-size` to find the sweet spot.

## Artifacts
- `scenes.json`: Master list of scenes `[{id: "scene_001", chapter: "001", text: "...", location: "..."}]`
- `scenes/`: Directory containing individual scene text files (useful for RAG indexing).
