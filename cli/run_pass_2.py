import os
import glob
import time
import json
import google.generativeai as genai
from tqdm import tqdm

# Configuration
INPUT_DIR = "kindle-ai-export/out/B000FBJAGO/chapters"
OUTPUT_DIR = "data/passes/02_deep_profiling"
PROMPT_FILE = "data/passes/02_deep_profiling/prompt.md"
MODEL_NAME = "gemini-2.0-flash"  # Or gemini-1.5-flash for speed

def setup_gemini():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(MODEL_NAME)

def load_prompt():
    with open(PROMPT_FILE, "r") as f:
        return f.read()

def process_chapter(model, prompt_template, chapter_path):
    chapter_filename = os.path.basename(chapter_path)
    output_filename = chapter_filename.replace(".txt", ".json")
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Skip if exists
    if os.path.exists(output_path) and os.path.getsize(output_path) > 10:
        print(f"Skipping {chapter_filename} (already exists)")
        return

    print(f"Processing {chapter_filename}...")
    
    with open(chapter_path, "r") as f:
        chapter_text = f.read()
    
    # Construct Message
    full_prompt = f"{prompt_template}\n\n# CHAPTER CONTENT:\n{chapter_text}"
    
    max_retries = 10
    retry_delay = 30
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                full_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Save Result
            with open(output_path, "w") as f:
                f.write(response.text)
                
            print(f"Saved {output_filename}")
            time.sleep(10) # Base rate limit buffer
            return
            
        except Exception as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                print(f"Rate limit hit for {chapter_filename} (Attempt {attempt+1}/{max_retries}). Sleeping {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 120) # Backoff cap at 120s
            else:
                print(f"ERROR processing {chapter_filename}: {e}")
                return # Don't retry other errors

def main():
    # Ensure raw output dir exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        model = setup_gemini()
        prompt = load_prompt()
        
        chapter_files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.txt")))
        
        for ch_file in chapter_files:
            process_chapter(model, prompt, ch_file)
            
    except Exception as e:
        print(f"Fatal Error: {e}")

if __name__ == "__main__":
    main()
