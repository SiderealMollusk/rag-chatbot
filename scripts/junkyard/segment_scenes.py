import os
import argparse
import json
import glob
import requests
import re
from tqdm import tqdm

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1"

def get_scene_breaks(chunk_text, overlap_context=""):
    """
    Asks LLM to identify scene breaks in the text.
    overlap_context: Text from previous chunk to help continuity (optional)
    """
    
    prompt = f"""You are an expert novel editor. Analyze the text below for SCENE BREAKS.
    A Scene Break occurs when there is a significant change in:
    1. LOCATION (Characters move to a new place)
    2. TIME (Hours or days pass, e.g. "The next morning", "Later that day")
    3. POV (Narrative focus shifts to a different character)
    
    IGNORE simple paragraph breaks. Look for clear transitions.
    
    TEXT TO ANALYZE:
    \"\"\"
    {chunk_text}
    \"\"\"
    
    INSTRUCTIONS:
    Identify the STARTING SENTENCE (first 5-10 words) of every new scene found in the text.
    Return a JSON Object with a key "breaks" containing a list of strings.
    If no breaks are found, return "breaks": [].
    
    Example JSON:
    {{
      "breaks": ["It was after 02.30 when", "The Skroderiders dwindled beneath"]
    }}
    
    OUTPUT JSON ONLY.
    """
    
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        res_json = response.json()['response']
        return json.loads(res_json).get("breaks", [])
    except Exception as e:
        print(f"LLM Error: {e}")
        return []

def find_indices_of_breaks(text, breaks):
    indices = []
    normalized_text = " ".join(text.split()) # Simple normalization for fuzzy search?
    # Actually, exact search in raw text is risky due to whitespace.
    # We'll search simply.
    
    for b in breaks:
        # We search for the phrase.
        # We might need to be loose.
        # Let's clean the break string (remove quotes, etc)
        clean_break = b.strip().strip('"').strip("'")
        
        idx = text.find(clean_break)
        if idx != -1:
            indices.append(idx)
        else:
            # Fallback: Try searching specifically near newlines?
            # Or just warn
            # print(f"Warning: Could not locate break paragraph: '{clean_break}'")
            pass
            
    return sorted(list(set(indices)))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--asin", required=True)
    parser.add_argument("--target", help="Specific chapter filename (e.g. 015_eight.txt)")
    parser.add_argument("--chunk-size", type=int, default=8000, help="Characters per chunk")
    parser.add_argument("--overlap", type=int, default=500)
    parser.add_argument("--dry-run", action="store_true", help="Do not save, just print breaks")
    args = parser.parse_args()
    
    base_dir = os.path.join("kindle-ai-export", "out", args.asin)
    input_dir = os.path.join(base_dir, "named_chapters")
    output_dir = os.path.join(base_dir, "scenes")
    os.makedirs(output_dir, exist_ok=True)
    
    # Get Files
    if args.target:
        files = [os.path.join(input_dir, args.target)]
        if not os.path.exists(files[0]):
             # Try matching partial
             all_files = glob.glob(os.path.join(input_dir, "*.txt"))
             matched = [f for f in all_files if args.target in f]
             if matched:
                 files = [matched[0]]
             else:
                 print(f"File {args.target} not found in {input_dir}")
                 return
    else:
        files = sorted(glob.glob(os.path.join(input_dir, "*.txt")))
        
    print(f"Processing {len(files)} files for Scene Segmentation...")
    
    for file_path in files:
        fname = os.path.basename(file_path)
        with open(file_path, 'r') as f:
            text = f.read()
            
        print(f"\nAnalyzing {fname} ({len(text)} chars)...")
        
        # Chunking Logic (Simplified: Just sliding window)
        # We only really care about finding breaks.
        # If text < chunk_size, Just run once.
        
        all_break_indices = [0] # Scene 1 starts at 0
        
        # We will iterate chunks
        cursor = 0
        
        while cursor < len(text):
            chunk_end = min(cursor + args.chunk_size, len(text))
            chunk = text[cursor:chunk_end]
            
            # If chunk is too small (e.g. end of file), unlikely to have scenes unless short?
            # Just run it.
            
            breaks_found = get_scene_breaks(chunk)
            
            if args.dry_run:
                print(f"  [Chunk {cursor}-{chunk_end}] Found breaks: {breaks_found}")
            
            # Map back to global indices
            indices = find_indices_of_breaks(chunk, breaks_found)
            
            for local_idx in indices:
                global_idx = cursor + local_idx
                # Avoid duplicates or very close breaks
                if global_idx > 0 and global_idx not in all_break_indices:
                    all_break_indices.append(global_idx)
            
            # Move cursor
            if chunk_end == len(text):
                break
                
            cursor += (args.chunk_size - args.overlap)
            
        all_break_indices.sort()
        
        # Dedupe (if overlap found same break twice)
        # Filter indices within N chars of each other?
        unique_indices = [0]
        for idx in all_break_indices[1:]:
            if idx - unique_indices[-1] > 100: # Minimum scene length 100 chars?
                unique_indices.append(idx)
        
        # Split text
        scenes = []
        for i in range(len(unique_indices)):
            start = unique_indices[i]
            end = unique_indices[i+1] if i+1 < len(unique_indices) else len(text)
            scene_text = text[start:end].strip()
            
            # Only ignore empty
            if len(scene_text) > 20: 
                scenes.append(scene_text)
            
        if args.dry_run:
            print(f"-> Detected {len(scenes)} Scenes in {fname}")
            for i, s in enumerate(scenes):
                print(f"   Scene {i+1} Start: {s[:50]}...")
        else:
            # Save
            chapter_name = fname.replace(".txt", "")
            chap_dir = os.path.join(output_dir, chapter_name)
            os.makedirs(chap_dir, exist_ok=True)
            
            for i, s in enumerate(scenes):
                s_name = f"scene_{i+1:02d}.txt"
                with open(os.path.join(chap_dir, s_name), 'w') as f:
                    f.write(s)
            
            # Create metadata JSON for chapter?
            # Maybe unnecessary now.

if __name__ == "__main__":
    main()
