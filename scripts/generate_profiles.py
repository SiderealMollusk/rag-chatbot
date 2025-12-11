import os
import json
import yaml
import argparse
import re
import requests
from tqdm import tqdm

# --- Configuration ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1"
WINDOW_SIZE = 1000 # Chars padding
TOP_K_CHUNKS = 10

# Heuristic Keywords for physicality/description
KEYWORDS = [
    "hair", "eyes", "face", "skin", "tall", "short", "wore", "wearing", "dressed",
    "voice", "looked", "seemed", "appearance", "body", "hands", "arms", "legs",
    "carried", "holding", "weapon", "gun", "sword", "uniform", "suit", "jacket",
    "imposing", "beautiful", "ugly", "scar", "cybernetic", "implant", "goggles",
    "creature", "fur", "scales", "alien", "human", "man", "woman", "child"
]

def load_data(asin):
    base_dir = os.path.join(os.getcwd(), "kindle-ai-export", "out", asin)
    
    # 1. Content
    with open(os.path.join(base_dir, "content.json"), 'r') as f:
        chunks = json.load(f)
    full_text = "\n\n".join([c['text'] for c in chunks])
    
    # 2. Entities
    with open(os.path.join(base_dir, "entities_manual.yaml"), 'r') as f:
        data = yaml.safe_load(f)
    
    entities = []
    # Flatten
    for cat, items in data.items():
        if cat == 'meta': continue
        for item in items:
            item['category'] = cat
            entities.append(item)
            
    return base_dir, full_text, entities

def extract_windows(text, entity_name, aliases):
    # Find all occurrences
    names_to_find = [entity_name] + aliases
    
    matches = []
    
    # We use a simple finding approach to avoid regex explosion
    # For a real graph, we might want precise offsets, but for RAG context, approximate is fine.
    
    text_len = len(text)
    
    # Collect all indices of all aliases
    indices = []
    for name in names_to_find:
        start = 0
        while True:
            idx = text.find(name, start)
            if idx == -1: break
            indices.append(idx)
            start = idx + len(name)
    
    indices = sorted(list(set(indices)))
    
    # Create Windows
    windows = []
    processed_ranges = []
    
    for idx in indices:
        # Define window
        start = max(0, idx - WINDOW_SIZE)
        end = min(text_len, idx + WINDOW_SIZE)
        
        # Check overlap with previous windows to avoid duplicates
        is_overlap = False
        for p_start, p_end in processed_ranges:
            if start < p_end and end > p_start:
                # Significant overlap?
                is_overlap = True
                break
        
        if is_overlap: continue
        
        chunk = text[start:end]
        processed_ranges.append((start, end))
        
        # Score it
        score = 0
        lower_chunk = chunk.lower()
        for kw in KEYWORDS:
            if kw in lower_chunk:
                score += 1
        
        windows.append({
            "text": chunk,
            "score": score,
            "center_idx": idx
        })
        
    # Sort by Score Descending
    windows.sort(key=lambda x: x['score'], reverse=True)
    return windows[:TOP_K_CHUNKS]

def generate_profile(entity, windows, dry_run=False):
    name = entity['name']
    
    context_text = "\n---\n".join([w['text'] for w in windows])
    
    prompt = f"""
    You are an expert Data Profiler for a Wiki Database.
    Target Entity: "{name}"
    Category: {entity['category']}
    
    Read the following text excerpts from the book. They mentions the target entity.
    Extract key details into a structured JSON format.
    
    Focus on:
    1. Appearance: Physical traits, biology, clothes, hair, eyes.
    2. Gear: Equipment, tools, weapons they carry.
    3. Personality: Traits, mannerisms, beliefs.
    4. Narrative Role: What do they do? (e.g. Captain, Pilot, Hacker).
    
    Excerpts:
    {context_text}
    
    Output JSON ONLY. Format:
    {{
      "name": "{name}",
      "appearance": "string summary...",
      "gear": ["item1", "item2"],
      "personality": ["trait1", "trait2"],
      "role": "string",
      "description": "A comprehensive paragraph summarizing them suitable for an image generation prompt."
    }}
    """
    
    if dry_run:
        return {"dry_run_context": context_text, "prompt_preview": prompt}

    try:
        payload = {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        
        # Parse result and inject citations
        llm_result = response.json()['response']
        final_data = json.loads(llm_result)
        
        # Inject exact source windows
        final_data["citations"] = [
            {"text": w['text'], "score": w['score']} for w in windows
        ]
        
        return final_data
        
    except Exception as e:
        return f"Error: {e}" 

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--asin", required=True)
    parser.add_argument("--target", help="Specific entity name to process (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Do not call LLM, just dump windows")
    parser.add_argument("--limit", type=int, help="Limit number of entities to process")
    args = parser.parse_args()
    
    base_dir, text, entities = load_data(args.asin)
    
    # Filter target
    if args.target:
        entities = [e for e in entities if args.target.lower() in e['name'].lower()]
        if not entities:
            print(f"Target {args.target} not found.")
            return

    # Limit
    if args.limit:
        entities = entities[:args.limit]


    profiles_dir = os.path.join(base_dir, "profiles")
    os.makedirs(profiles_dir, exist_ok=True)
    
    if args.dry_run:
        debug_dir = os.path.join(base_dir, "debug_extracts")
        os.makedirs(debug_dir, exist_ok=True)
    
    print(f"Processing {len(entities)} entities...")
    
    for ent in tqdm(entities):
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', ent['name'])

        if args.dry_run:
            out_file = os.path.join(debug_dir, f"{safe_name}.txt")
        else:
            out_file = os.path.join(profiles_dir, f"{safe_name}.json")
            if os.path.exists(out_file):
                # print(f"Skipping {ent['name']} (Exists)")
                continue

        windows = extract_windows(text, ent['name'], ent['aliases'])
        
        if not windows:
            print(f"No text found for {ent['name']}")
            continue
            
        result = generate_profile(ent, windows, dry_run=args.dry_run)
        
        if args.dry_run:
            with open(out_file, 'w') as f:
                f.write(result['dry_run_context'])
            print(f"Saved debug windows to {out_file}")
        else:
            # out_file is already set
            try:
                # result should be dict now
                if isinstance(result, dict):
                    with open(out_file, 'w') as f:
                        json.dump(result, f, indent=2)
                else:
                    # Error string
                    print(result)
            except Exception as e:
                print(f"Failed to save JSON for {ent['name']}: {e}")
                # Save raw
                with open(out_file.replace('.json', '.txt'), 'w') as f:
                    f.write(str(result))
                    
if __name__ == "__main__":
    main()
