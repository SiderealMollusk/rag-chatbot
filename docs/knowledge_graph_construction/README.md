# Knowledge Graph Construction Pipeline

This pipeline transforms raw book text into a structured "Movie Bible" Knowledge Graph, capable of supporting high-fidelity queries about characters, scenes, and narrative arcs.

## Workflow Overview

| Pass | Name | Technique | Input | Output | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **0** | **Quality Check** | Spell Check + Statistical Anomaly | `content.json` | `qc_report.json` | Verify OCR health without ground truth by checking dictionary hit-rates and garbage-string density. |
| **1** | **Entity Extraction** | Greedy NER + Human Review | `content.json` (Raw Text) | `entities_manual.yaml` | Build the canonical dictionary of Characters, Places, and Factions. |
| **1.5**| **Alias Resolution** | Substring Clustering | `entities_manual.yaml` | `entities_manual.yaml` | Merge "Ravna" into "Ravna Bergsndot" to prevent duplicate profiles. |
| **2** | **Deep Profiling** | LLM-based RAG Extraction | `entities_manual.yaml` + Raw Text | `profiles/*.json` | Generate detailed descriptions (Appearance, Gear, Personality) for every entity. |
| **3** | **Scene Segmentation** | Heuristic + LLM Boundary Detection | Raw Text | `scenes.json` | Slice the book into discrete Scenes based on time/location shifts. |
| **4** | **Event Extraction** | LLM Analysis per Scene | `scenes.json` + `entities_manual.yaml` | `timeline.json` | Identify "What Happened" in each scene, tagging visible entities and emotional beats. |
| **5** | **Graph Synthesis** | Relational Mapping | All of the above | `knowledge_graph.json` | The final queryable artifact linking Entities, Events, and Descriptions. |
| **6** | **Vector Indexing** | Embedding | `knowledge_graph.json` | `vector_store` | Create semantic entry points for fuzzy queries (e.g. "the sad scene") to find Graph Nodes. |

## Documentation

## Documentation

*   [**Pass 0: Quality Check**](./qc_pass.md) - *Statistical health check on OCR output.*
*   [**Pass 1: Named Entity Recognition (NER)**](./ner_pass.md) - *Details on heuristic extraction and dictionary curation.*
*   [**Pass 2: Deep Profiling**](./profiling_pass.md) - *Windowing search & LLM Extraction.*
*   **(Pending)** Pass 3: Scene Segmentation
*   **(Pending)** Pass 4: Event Timeline
*   **(Pending)** Pass 6: Vector Indexing
