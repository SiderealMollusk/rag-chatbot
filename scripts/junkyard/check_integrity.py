import json
import re
import sys
from collections import defaultdict

INPUT_FILE = "data/passes/02_deep_profiling/corpus.02.annotated.jsonl"

def check_integrity():
    print(f"Checking integrity of {INPUT_FILE}...")
    
    # Store by hierarchy: Chapter -> Scene -> Paragraphs
    structure = defaultdict(lambda: defaultdict(list))
    all_ids = set()
    rows = []
    
    try:
        with open(INPUT_FILE, 'r') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                rows.append(data)
                
                # ID Format: chXXX_scYY_pZZ
                # Regex to parse safely
                match = re.match(r'ch(\d+)_sc(\d+)_p(\d+)', data['id'])
                if match:
                    ch = int(match.group(1))
                    sc = int(match.group(2))
                    p = int(match.group(3))
                    
                    structure[ch][sc].append(p)
                    all_ids.add(data['id'])
                else:
                    print(f" [!] Malformed ID: {data['id']}")
                    
    except FileNotFoundError:
        print("  Error: File not found.")
        return

    print(f"Loaded {len(rows)} records.")
    
    # 1. Total Count Check
    # We expected ~1240 from previous steps.
    msg = "OK" if len(rows) >= 1240 else "WARNING: Count low (Did deep profiling finish?)"
    print(f"Status: {len(rows)} records. ({msg})")

    # 2. Sequential Checks
    print("\n--- Sequential Gaps Check ---")
    
    sorted_chapters = sorted(structure.keys())
    
    # Check Chapter Gaps (We know 0-5 are missing prologue stuff, but 6+ should be contiguous)
    # Actually, file chapters might skip if not summarized.
    print(f"Chapters found: {min(sorted_chapters)} to {max(sorted_chapters)}")
    
    issues_found = 0
    
    for ch in sorted_chapters:
        scenes = sorted(structure[ch].keys())
        
        # Check Scene Gaps? 
        # Scenes might not be 0-indexed if scene 1 is first.
        # But within a scene, paragraphs MUST be sequential.
        
        for sc in scenes:
            paras = sorted(structure[ch][sc])
            
            # Check p0 exists
            if 0 not in paras:
                print(f" [Gap] Chapter {ch} Scene {sc}: Missing paragraph 0 (Starts at {paras[0]})")
                issues_found += 1
                
            # Check continuity
            for i in range(len(paras) - 1):
                curr = paras[i]
                next_p = paras[i+1]
                if next_p != curr + 1:
                    print(f" [Gap] Chapter {ch} Scene {sc}: Gap between p{curr} and p{next_p}")
                    issues_found += 1

    if issues_found == 0:
        print("Success: No paragraph sequence gaps found.")
    else:
        print(f"Found {issues_found} sequence gaps.")

    # 3. Duplicate Check
    if len(all_ids) != len(rows):
        print(f"\n[!] Duplicate IDs Detected: {len(rows)} rows vs {len(all_ids)} unique IDs")
    else:
        print("\nSuccess: No duplicate IDs.")

if __name__ == "__main__":
    check_integrity()
