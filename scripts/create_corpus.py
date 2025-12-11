import os
import json
import glob
import re
from typing import List, Dict, Any

# Paths
SCENE_SUMMARY_DIR = "data/passes/01_scene_summary"
CHAPTERS_DIR = "kindle-ai-export/out/B000FBJAGO/chapters"
OUTPUT_FILE = "data/corpus.jsonl"

def normalize_text(text: str) -> str:
    """Normalize text for matching (remove punctuation, lower case)."""
    return re.sub(r'\W+', '', text).lower()

def find_sentence_offset(search_text: str, full_text: str, start_search_idx: int = 0) -> int:
    """
    Finds the start index of search_text in full_text.
    Uses a normalized comparison for robustness.
    """
    norm_search = normalize_text(search_text)
    if not norm_search:
        return -1
        
    # Heuristic: search for the first 20 chars of normalized text matched in normalized full text
    # This is expensive if we do it for every char.
    # Alternative: Just find the literal string first.
    
    idx = full_text.find(search_text, start_search_idx)
    if idx != -1:
        return idx
        
    # Fallback: Try with just the first 30 chars
    short_search = search_text[:30]
    idx = full_text.find(short_search, start_search_idx)
    if idx != -1:
        return idx
        
    # Fallback: simple normalization (ignore whitespace)
    # This is hard to map back to original indices. 
    # For now, let's assume the text is reasonably close.
    return -1

def split_into_paragraphs(text: str) -> List[str]:
    """
    Splits text into paragraphs.
    Heuristics based on observing the raw text:
    - Double underscores '__' seem to be used as breaks.
    - Standard double newlines '\n\n'.
    - Newlines that look like breaks.
    """
    # Replace the weird double underscore with a standard break
    text = text.replace('__', '\n\n')
    
    # Split by double newline
    paras = text.split('\n\n')
    
    # Clean up
    paras = [p.strip() for p in paras if p.strip()]
    return paras

def main():
    print(f"Building corpus from {SCENE_SUMMARY_DIR} and {CHAPTERS_DIR}...")
    
    documents = []
    
    # Map scene files to chapter files
    # Scene summaries are named like '009_two.json'
    # Chapters are named like 'chapter_009.txt' ? No, list showed 'chapter_009.txt'
    
    scene_files = sorted(glob.glob(os.path.join(SCENE_SUMMARY_DIR, "*.json")))
    
    for scene_file in scene_files:
        basename = os.path.basename(scene_file)
        # 009_two.json -> chapter_009.txt
        # We need to extract the number.
        match = re.match(r'(\d+)_', basename)
        if not match:
            print(f"Skipping {basename} (no number found)")
            continue
            
        chapter_num_str = match.group(1)
        chapter_file_name = f"chapter_{chapter_num_str}.txt"
        chapter_path = os.path.join(CHAPTERS_DIR, chapter_file_name)
        
        if not os.path.exists(chapter_path):
            print(f"Warning: Chapter file {chapter_file_name} not found for {basename}")
            continue
            
        print(f"Processing {basename} -> {chapter_file_name}")
        
        # Load Content
        with open(scene_file, 'r') as f:
            scene_data = json.load(f)
            
        with open(chapter_path, 'r') as f:
            raw_text = f.read()
            
        # Extract Scenes
        scenes = scene_data.get('scenes', [])
        scene_boundaries = []
        
        last_idx = 0
        for i, scene in enumerate(scenes):
            start_sent = scene.get('start_sentence', '').strip()
            
            # Search
            idx = find_sentence_offset(start_sent, raw_text, last_idx)
            
            if idx == -1 and len(start_sent) > 50:
                 idx = find_sentence_offset(start_sent[:50], raw_text, last_idx)
            
            if idx == -1 and len(start_sent) > 20:
                 # Try an even smaller chunk
                 idx = find_sentence_offset(start_sent[:20], raw_text, last_idx)

            if idx == -1:
                print(f"  Warning: Could not find start of Scene {scene.get('scene_index')} in {basename}")
                # Fallback Strategy:
                # If this is the FIRST scene, assume it starts at 0.
                if i == 0:
                    print(f"    -> Defaulting Scene 1 to index 0")
                    idx = 0
                else:
                    # If we can't find it, we skip explicit boundary. 
                    # The text will remain part of the previous scene.
                    # Ideally, we'd estimate, but merging with previous is safer than dropping.
                    continue
            
            scene_boundaries.append((idx, scene))
            if idx != -1: # Only advance if we found a real spot
                last_idx = idx
        
        # SAFETY CHECK: If no boundaries were found at all (bad OCR match?), 
        # take the whole text as Scene 1 (or whatever the first scene is).
        if not scene_boundaries and scenes:
            print(f"  Fallback: No boundaries found. assigning entire text to Scene 1")
            scene_boundaries.append((0, scenes[0]))

        # Sort by index
        scene_boundaries.sort(key=lambda x: x[0])
        
        # Ensure we start at 0
        if scene_boundaries and scene_boundaries[0][0] > 0:
             # There is text before the first identified scene. 
             # It's likely Chapter Intro text or we missed the real Scene 1 start.
             # We should attach it to the first scene (Scene 1) to avoid dropping it?
             # Or create a "Scene 0" chunk?
             # Let's attach it to Scene 1.
             scene_boundaries[0] = (0, scene_boundaries[0][1])

        # Create Chunks

        for i, (start_idx, scene_meta) in enumerate(scene_boundaries):
            # End index is the start of the next scene, or end of file
            if i + 1 < len(scene_boundaries):
                end_idx = scene_boundaries[i+1][0]
            else:
                end_idx = len(raw_text)
                
            scene_text = raw_text[start_idx:end_idx]
            
            # Split Paragraphs
            paragraphs = split_into_paragraphs(scene_text)
            
            for p_idx, para in enumerate(paragraphs):
                doc_id = f"ch{chapter_num_str}_sc{scene_meta['scene_index']:02d}_p{p_idx:02d}"
                
                doc = {
                    "id": doc_id,
                    "text": para,
                    "metadata": {
                        "source": basename,
                        "chapter_title": scene_data.get('chapter_title'),
                        "scene_index": scene_meta.get('scene_index'),
                        "location": scene_meta.get('location'),
                        "timeframe": scene_meta.get('timeframe'),
                        "characters": scene_meta.get('characters_present'),
                        "summary": scene_meta.get('summary'),
                        "tags": scene_meta.get('mood', '').split(', ')
                    }
                }
                documents.append(doc)

    # Save
    with open(OUTPUT_FILE, 'w') as f:
        for doc in documents:
            f.write(json.dumps(doc) + "\n")
            
    print(f"Created corpus with {len(documents)} paragraphs in {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
