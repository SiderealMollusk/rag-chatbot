# Pass 0: Quality Check (OCR Health)

**Goal:** Assess the quality of the OCR output without ground truth by analyzing statistical properties of the text.

## Methodology

Since we don't have the original text to compare against, we use "Naturalness Metrics" to determine if the output looks like valid English prose.

### Metrics

1.  **Dictionary Hit Rate:** The percentage of words in the text that appear in a standard English dictionary.
    *   **> 95%:** Excellent
    *   **85% - 95%:** Good (Typical for Sci-Fi with made-up names)
    *   **< 70%:** Garbage / Failed OCR
2.  **Junk String Density:** The percentage of "words" that contain illegal character combinations (e.g., `^&*%`, `th1s`).
3.  **Triviality Check:** Is the file empty or just whitespace?

## Artifacts

*   **Script:** `scripts/check_quality.py`
*   **Input:** `kindle-ai-export/out/[ASIN]/content.json`
*   **Output:** Console Output (Pass/Fail)

## Execution

```bash
uv run python scripts/check_quality.py --asin [ASIN]
```
