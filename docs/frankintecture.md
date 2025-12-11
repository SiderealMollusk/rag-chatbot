# Frankintecture: Kindle Extraction & RAG Pipeline

A hybrid system stitching together a Node.js scraper and a Python RAG/OCR chatbot.

## Components

1.  **Scraper (Node.js/Playwright)**
    *   **Location:** `./kindle-ai-export`
    *   **Purpose:** Logs into Amazon Kindle Web Reader, screenshotting every page of a book.
    *   **Output:** Images in `./kindle-ai-export/out/[ASIN]/pages/` and metadata in `metadata.json`.

2.  **OCR & RAG (Python/EasyOCR/LlamaIndex)**
    *   **Location:** `./` (Root)
    *   **Purpose:**
        *   **OCR:** Converts screenshots to text using EasyOCR (GPU/CPU) via `scripts/ocr_book.py`.
        *   **Chatbot:** Ingests the text and runs a RAG pipeline (`rag_chatbot`).

## Workflow

### 1. Extract Images (Node.js)
Before running, set `AMAZON_EMAIL`, `AMAZON_PASSWORD`, `ASIN` in `./kindle-ai-export/.env`.

```bash
cd kindle-ai-export
npx tsx src/extract-kindle-book.ts
# Follow prompts for 2FA if needed.
# Result: Screenshots in out/[ASIN]/pages/
```

### 2. OCR Images (Python)
Uses EasyOCR to read the screenshots and generate the content JSON expected by the rest of the pipeline.

```bash
# From root
uv run python scripts/ocr_book.py --asin [ASIN]
# Result: content.json in kindle-ai-export/out/[ASIN]/
```

### 3. Run RAG Chatbot
Point the chatbot to the extracted data or ingest it.

```bash
uv run python -m rag_chatbot --host localhost
```

## Data Paths

*   **Extraction Root:** `./kindle-ai-export/out/[ASIN]/`
    *   **Pages:** `./pages/*.png`
    *   **Metadata:** `./metadata.json`
    *   **Extracted Text:** `./content.json`
