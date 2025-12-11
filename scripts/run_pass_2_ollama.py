import json
import os
import requests
import argparse
import time
import sys
from typing import List, Dict

# Configuration
DEFAULT_MODEL = "llama3"
OLLAMA_URL = "http://localhost:11434/api/chat"
INPUT_FILE = "data/passes/02_deep_profiling/corpus.02.jsonl"
OUTPUT_FILE = "data/passes/02_deep_profiling/corpus.02.annotated.jsonl"
PROMPT_FILE = "data/passes/02_deep_profiling/prompt.md"
BATCH_SIZE = 5

def load_processed_ids(output_path: str) -> set:
    if not os.path.exists(output_path):
        return set()
    
    ids = set()
    with open(output_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                data = json.loads(line)
                ids.add(data['id'])
            except:
                pass
    return ids

def get_system_prompt() -> str:
    with open(PROMPT_FILE, 'r') as f:
        return f.read()

def call_ollama(model: str, system_prompt: str, user_content: str) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for deterministic styling
            "num_ctx": 4096      # Ensure enough context for batches
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()['message']['content']
    except Exception as e:
        print(f"Error calling Ollama: {e}", file=sys.stderr)
        return None

def parse_llm_response(response_text: str, expected_ids: List[str]) -> List[Dict]:
    # 1. Clean Markdown
    clean_text = response_text
    if "```json" in clean_text:
        clean_text = clean_text.split("```json")[1].split("```")[0]
    elif "```" in clean_text:
        clean_text = clean_text.split("```")[1].split("```")[0]
        
    clean_text = clean_text.strip()
    
    results = []
    
    # Strategy A: Try parsing as a JSON Array
    try:
        data = json.loads(clean_text)
        if isinstance(data, list):
            results = data
        elif isinstance(data, dict):
            results = [data]
    except json.JSONDecodeError:
        # Strategy B: Try parsing line by line (NDJSON)
        lines = clean_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line: continue
            try:
                # Remove trailing commas if present (common LLM error in block mode)
                if line.endswith(','):
                    line = line[:-1]
                obj = json.loads(line)
                results.append(obj)
            except:
                continue
                
    # Validation
    valid_results = []
    processed_id_map = {r.get('id'): r for r in results}
    
    for eid in expected_ids:
        if eid in processed_id_map:
            valid_results.append(processed_id_map[eid])
        else:
            print(f"Warning: Batch response missing ID {eid}", file=sys.stderr)
            
    return valid_results

def main():
    parser = argparse.ArgumentParser(description="Run Pass 2 extraction with Ollama")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name")
    parser.add_argument("--batch", type=int, default=BATCH_SIZE, help="Batch size")
    args = parser.parse_args()

    # check ollama
    try:
        requests.get(OLLAMA_URL.replace("/api/chat", ""), timeout=2)
    except:
        print(f"Error: Could not connect to Ollama at {OLLAMA_URL}. Is it running?")
        sys.exit(1)

    processed_ids = load_processed_ids(OUTPUT_FILE)
    system_prompt = get_system_prompt()
    
    print(f"Model: {args.model}")
    print(f"Processed: {len(processed_ids)} records")
    print(f"Input: {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print("-" * 40)

    # Read Input
    pending_records = []
    with open(INPUT_FILE, 'r') as f:
        for line in f:
            if not line.strip(): continue
            record = json.loads(line)
            if record['id'] not in processed_ids:
                pending_records.append(record)
    
    print(f"Pending: {len(pending_records)} records")
    
    # Process
    with open(OUTPUT_FILE, 'a') as fout:
        for i in range(0, len(pending_records), args.batch):
            batch = pending_records[i : i + args.batch]
            batch_ids = [r['id'] for r in batch]
            
            # Prepare Input JSONs
            # We explicitly format them as lines for the prompt
            batch_str = "\n".join([json.dumps(r) for r in batch])
            
            print(f"Processing batch {i//args.batch + 1}/{(len(pending_records)//args.batch)+1} (IDs: {batch_ids[0]}...{batch_ids[-1]})")
            
            response_text = call_ollama(args.model, system_prompt, batch_str)
            
            if response_text:
                results = parse_llm_response(response_text, batch_ids)
                
                for res in results:
                    fout.write(json.dumps(res) + "\n")
                fout.flush()
                
                success_count = len(results)
                if success_count < len(batch):
                    print(f"  Warning: Only got {success_count}/{len(batch)} valid records back.")
            else:
                print("  Error: No response from Ollama.")
            
            # Rate limit politeness (even local needs a breath sometimes)
            time.sleep(0.1)

    print("Done.")

if __name__ == "__main__":
    main()
