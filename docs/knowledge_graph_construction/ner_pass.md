# Pass 1: Named Entity Recognition (NER)

**Goal:** Create a canonical list of all Proper Nouns (Entities) in the book.

## Methodology

We employ a "Greedy + Filter" approach rather than relying solely on standard ML models, as Sci-Fi names often confuse standard trained models.

### Algorithm
1.  **Ingest:** Read full book text from `content.json`.
2.  **SpaCy NLP:** Run standard `en_core_web_sm` to identify standard `PROPN` tokens (PERSON, ORG, LOC).
3.  **Greedy Heuristic:** Scan for capitalized N-grams (e.g., "Out of Band", "High Lab") that appear frequently but might be missed by SpaCy.
4.  **Frequency Analysis:** Count occurrences of every candidate. Low-frequency candidates are likely OCR errors or noise.
5.  **Stopword Filtering:** Remove common capitalized words (Start of sentence, standard English proper nouns like 'Monday').

## Artifacts

*   **Script:** `scripts/extract_entities.py`
*   **Input:** `kindle-ai-export/out/[ASIN]/content.json`
*   **Output:** `kindle-ai-export/out/[ASIN]/entities_candidates.yaml`

## Human In The Loop

The output `entities_candidates.yaml` is **not** final. It is a staging file.
The user must:
1.  **Review** the list.
2.  **Delete** junk entries (OCR noise, common words).
3.  **Merge** aliases (e.g., list "Pham" and "Nuwen" under "Pham Nuwen").
4.  **Categorize** unknowns (Move "Tines World" from `UNCATEGORIZED` to `LOCATION`).
5.  **Save** as `entities_manual.yaml`.

This `entities_manual.yaml` becomes the **Source of Truth** for Pass 2.
