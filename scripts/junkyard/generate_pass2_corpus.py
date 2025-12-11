import json
import os

INPUT_FILE = "data/corpus.jsonl"
OUTPUT_FILE = "data/passes/02_deep_profiling/corpus.02.jsonl"
OS_DIR = os.path.dirname(OUTPUT_FILE)

def main():
    if not os.path.exists(OS_DIR):
        os.makedirs(OS_DIR)

    print(f"Reading from {INPUT_FILE}...")
    
    with open(INPUT_FILE, 'r') as fin, open(OUTPUT_FILE, 'w') as fout:
        ordinal = 0
        for line in fin:
            if not line.strip():
                continue
                
            data = json.loads(line)
            meta = data.get("metadata", {})
            
            # Handle Location: It might be a dict or a string in the source
            loc_raw = meta.get("location")
            location_str = "Unknown"
            if isinstance(loc_raw, dict):
                location_str = loc_raw.get("name", "Unknown")
            elif isinstance(loc_raw, str):
                location_str = loc_raw
            elif loc_raw is None:
                location_str = ""

            # Construct the new enriched skeleton object
            new_obj = {
                "id": data.get("id"),
                "text": data.get("text"),
                "ordinal": ordinal,
                "metadata": {
                    "source": meta.get("source", ""),
                    "chapter_title": meta.get("chapter_title", ""),
                    "scene_index": meta.get("scene_index", 0),
                    "location": location_str,
                    "timeframe": meta.get("timeframe", "")
                },
                "tags_characters": [],
                "tags_locations": [],
                "tags_events": [],
                "tags_factions": [],
                "tags_technologies": [],
                "tags_concepts": []
            }
            
            fout.write(json.dumps(new_obj) + "\n")
            ordinal += 1
            
    print(f"Successfully generated {OUTPUT_FILE} with {ordinal} records.")

if __name__ == "__main__":
    main()
