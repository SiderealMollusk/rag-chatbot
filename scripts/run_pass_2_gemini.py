import json
import os
import sys
import time
import argparse
from typing import List, Dict
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Config
INPUT_FILE = "data/passes/02_deep_profiling/corpus.02.jsonl"
OUTPUT_FILE = "data/passes/02_deep_profiling/corpus.02.annotated.jsonl"
PROMPT_FILE = "data/passes/02_deep_profiling/prompt.md"

# Safety: We want to block nothing, since we are analyzing fiction.
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# --- Rate Limiter Implementation ---
class AdaptiveRateLimiter:
    def __init__(self, rpm_limit=15):
        self.rpm_limit = rpm_limit
        self.interval = 60.0 / rpm_limit
        self.last_call_time = 0
        self.backoff_multiplier = 20.0 # Start conservative (max slow)

    def wait(self):
        # Calculate time since last call
        now = time.time()
        elapsed = now - self.last_call_time
        
        # Enforce basic interval (Token Bucket Style)
        sleep_needed = max(0, self.interval * self.backoff_multiplier - elapsed)
        if sleep_needed > 0:
            time.sleep(sleep_needed)
            
        self.last_call_time = time.time()

    def report_success(self):
        # Recover speed (Accelerate)
        if self.backoff_multiplier > 1.0:
            self.backoff_multiplier = max(1.0, self.backoff_multiplier - 0.5)

    def report_throttled(self):
        # Exponential Backoff
        print(f"  [RateLimiter] Hit 429! Increasing delay (Current multiplier: {self.backoff_multiplier:.1f}x)")
        self.backoff_multiplier *= 2.0
        # Cap max sway (30 * 20 = 600s = 10 mins)
        if self.backoff_multiplier > 20.0:
            self.backoff_multiplier = 20.0
        # Force a hard sleep immediately
        wait_time = 30 * self.backoff_multiplier
        print(f" [Sleeping {wait_time:.0f}s]", end="")
        time.sleep(wait_time)


def get_system_prompt() -> str:
    with open(PROMPT_FILE, 'r') as f:
        return f.read()

def load_processed_ids(output_path: str) -> set:
    if not os.path.exists(output_path):
        return set()
    ids = set()
    with open(output_path, 'r') as f:
        for line in f:
            if not line.strip(): continue
            try:
                data = json.loads(line)
                ids.add(data['id'])
            except:
                pass
    return ids

def parse_response(text: str, expected_ids: List[str]) -> List[Dict]:
    # Strip markdown syntax
    clean = text.replace('```json', '').replace('```', '').strip()
    
    results = []
    # Attempt 1: Line-by-line NDJSON
    lines = clean.split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        try:
            # Handle trailing commas
            if line.endswith(','): line = line[:-1]
            obj = json.loads(line)
            results.append(obj)
        except:
            pass
            
    # Attempt 2: Valid JSON List
    if not results:
        try:
            data = json.loads(clean)
            if isinstance(data, list):
                results = data
            elif isinstance(data, dict):
                results = [data]
        except:
            pass

    # Validate IDs
    valid = []
    res_map = {r.get('id'): r for r in results}
    for eid in expected_ids:
        if eid in res_map:
            valid.append(res_map[eid])
        else:
            print(f"    Missing ID in response: {eid}")
            
    return valid

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True, help="Gemini API Key")
    parser.add_argument("--batch", type=int, default=10, help="Batch size (Try 10-20 for Gemini 2.0)")
    args = parser.parse_args()

    # Init Gemini
    genai.configure(api_key=args.key)
    model = genai.GenerativeModel("gemini-2.0-flash", safety_settings=SAFETY_SETTINGS)
    
    # Init Rate Limiter (Conservative start)
    limiter = AdaptiveRateLimiter(rpm_limit=10) 

    # Prepare Data
    processed_ids = load_processed_ids(OUTPUT_FILE)
    system_prompt = get_system_prompt()
    
    pending = []
    with open(INPUT_FILE, 'r') as f:
        for line in f:
            if not line.strip(): continue
            rec = json.loads(line)
            if rec['id'] not in processed_ids:
                pending.append(rec)
                
    print(f"Starting Gemini 2.0 Flash Pass.")
    print(f"Total Pending: {len(pending)}")
    print(f"Batch Size: {args.batch}")
    
    with open(OUTPUT_FILE, 'a') as fout:
        for i in range(0, len(pending), args.batch):
            batch = pending[i : i + args.batch]
            batch_ids = [r['id'] for r in batch]
            
            # Format input
            batch_text = "\n".join([json.dumps(r) for r in batch])
            prompt = f"{system_prompt}\n\nINPUT DATA:\n{batch_text}"
            
            print(f"Processing Batch {i//args.batch + 1} ({len(batch)} items)...", end="", flush=True)
            
            # Retry Loop
            max_retries = 5
            for attempt in range(max_retries):
                limiter.wait()
                try:
                    resp = model.generate_content(prompt)
                    
                    # Check for 429 in API (Library sometimes throws, sometimes returns empty)
                    if not resp.parts and resp.prompt_feedback:
                         # Blocked prompt?
                         print(" [Blocked]", end="")
                         break
                         
                    results = parse_response(resp.text, batch_ids)
                    
                    if len(results) > 0:
                        # Success
                        for r in results:
                            fout.write(json.dumps(r) + "\n")
                        fout.flush()
                        limiter.report_success()
                        print(f" Done. ({len(results)}/{len(batch)})")
                        break
                    else:
                        print(f" [Empty/Parse Fail]", end="")
                        
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "Quota" in err_str:
                        limiter.report_throttled()
                        print(f" [429 Error - Retrying]", end="")
                    elif "500" in err_str or "503" in err_str:
                        time.sleep(5)
                        print(f" [Server Error - Retrying]", end="")
                    else:
                        print(f" [Error: {e}]")
                        break
            
            if attempt == max_retries - 1:
                print(" -> FAILED BATCH after retries.")

if __name__ == "__main__":
    main()
