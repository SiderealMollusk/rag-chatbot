import os
import argparse
import json
import glob
import requests
import time
from tqdm import tqdm

# Provided Ephemeral Key
GEMINI_KEY = "AIzaSyBLg-amQ5CXIT7GOI4NpAEjkHXBKX9qpcI"
# Valid Model found in list: models/gemini-2.0-flash
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"

def get_scene_breaks_gemini(text):
    prompt_text = f"""Analyze the following novel chapter text. Identify the STARTING SENTENCE (first 5-10 words) of every new scene.
    A new scene occurs when there is a significant change in:
    1. LOCATION (Characters move to a new place)
    2. TIME (Hours or days pass, e.g. "The next morning", "Later that day")
    3. POV (Narrative focus shifts to a different character)
    
    IGNORE simple paragraph breaks. Look for clear transitions.
    
    Return a valid JSON object with a key "breaks" containing a list of strings (the start sentences).
    
    TEXT:
    {text}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(URL, json=payload, headers=headers)
        if response.status_code == 429 or response.status_code == 503:
             return None, response.status_code
        response.raise_for_status()
        result = response.json()
        content = result['candidates'][0]['content']['parts'][0]['text']
        return json.loads(content).get("breaks", []), 200
    except Exception as e:
        print(f"Error: {e}")
        return [], 500

def find_indices_of_breaks(text, breaks):
    indices = []
    normalized_text = " ".join(text.split())
    
    for b in breaks:
        clean_break = b.strip().strip('"').strip("'")
        idx = text.find(clean_break)
        if idx != -1:
            indices.append(idx)
    return sorted(list(set(indices)))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--asin", required=True)
    args = parser.parse_args()
    
    base_dir = os.path.join("kindle-ai-export", "out", args.asin)
    input_dir = os.path.join(base_dir, "named_chapters")
    output_dir = os.path.join(base_dir, "scenes")
    os.makedirs(output_dir, exist_ok=True)
    
    files = sorted(glob.glob(os.path.join(input_dir, "*.txt")))
    
    current_sleep = 5.0 # Initial Sleep
    min_sleep = 1.0
    max_sleep = 60.0
    
    print(f"Processing {len(files)} chapters with AIMD Rate Limiting...")
    
    bar = tqdm(files)
    for file_path in bar:
        fname = os.path.basename(file_path)
        with open(file_path, 'r') as f:
            text = f.read()
            
        if len(text) < 500: continue
        if os.path.exists(os.path.join(output_dir, fname.replace(".txt", ""), "scene_01.txt")):
             # Skip done
             continue

        # Retry Loop
        while True:
            bar.set_description(f"Wait: {current_sleep:.1f}s | {fname}")
            
            # Sleep first? Or sleep after?
            # Better to sleep before if we are hot.
            time.sleep(current_sleep)
            
            breaks, status = get_scene_breaks_gemini(text)
            
            if status == 200:
                # Success -> Decrease Sleep (Additive Increase in speed, Multiplicative Decrease in sleep)
                current_sleep = max(min_sleep, current_sleep * 0.8) # 20% faster
                break
            elif status == 429 or status == 503:
                # Fail -> Increase Sleep (Multiplicative Increase in sleep)
                current_sleep = min(max_sleep, current_sleep * 2.0 + 1.0)
                # print(f"Rate Limit hit. Blocking for {current_sleep}s")
            else:
                # Other error -> Skip or retry?
                print(f"Hard Error {status}. Skipping.")
                breaks = []
                break # breaks is empty
        
        # Process and Save
        indices = find_indices_of_breaks(text, breaks)
        all_indices = sorted([0] + [i for i in indices if i > 100])
        
        scenes = []
        for i in range(len(all_indices)):
            start = all_indices[i]
            end = all_indices[i+1] if i+1 < len(all_indices) else len(text)
            scene_text = text[start:end].strip()
            if len(scene_text) > 50:
                scenes.append(scene_text)
                
        chapter_name = fname.replace(".txt", "")
        chap_dir = os.path.join(output_dir, chapter_name)
        os.makedirs(chap_dir, exist_ok=True)
        
        for i, s in enumerate(scenes):
            s_name = f"scene_{i+1:02d}.txt"
            with open(os.path.join(chap_dir, s_name), 'w') as f:
                f.write(s)

if __name__ == "__main__":
    main()
