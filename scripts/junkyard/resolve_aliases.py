import yaml
import os
import argparse
import shutil
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Pass 1.5: Alias Resolution")
    parser.add_argument("--asin", required=True, help="ASIN")
    args = parser.parse_args()
    
    base_dir = os.path.join(os.getcwd(), "kindle-ai-export", "out", args.asin)
    input_path = os.path.join(base_dir, "entities_manual.yaml")
    
    if not os.path.exists(input_path):
        print("Error: Manual file not found.")
        return

    # Backup
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = os.path.join(base_dir, "backups", f"entities_pre_alias_{ts}.yaml")
    os.makedirs(os.path.dirname(backup), exist_ok=True)
    shutil.copy(input_path, backup)
    print(f"Backed up to {backup}")

    with open(input_path, 'r') as f:
        data = yaml.safe_load(f)

    # We need a flat list to compare
    # But we want to preserve categories?
    # If "Ravna" is Char and "Ravna Bergsndot" is Char -> Merge.
    # If "Ravna" is Char and "Ravna System" is Loc -> DO NOT MERGE.
    
    # Strategy: Resolve strictly within Categories first?
    # Or just resolve globally but warn on category mismatch?
    # Safe bet: Resolve within Category for now.
    
    merged_count = 0
    
    new_data = {"meta": data.get("meta", {})}
    new_data["meta"]["generator"] = "alias_resolver_v1"
    
    for cat, items in data.items():
        if cat == 'meta': continue
        if not items: 
            new_data[cat] = []
            continue
            
        print(f"\nProcessing {cat} ({len(items)} items)...")
        
        # Sort by length descending (Longest first)
        # We want "Pham Nuwen" to claim "Pham".
        sorted_items = sorted(items, key=lambda x: len(x['name']), reverse=True)
        
        final_list = []
        claimed_names = {} # Map 'short_name' -> 'long_name'
        
        # O(N^2) but N is small per category (<100 usually)
        
        # First pass: Build the master list
        for item in sorted_items:
            name = item['name']
            
            # Check if this name is a substring of an already accepted name
            # e.g. We accepted "Pham Nuwen" already. Now we see "Pham".
            
            parent = None
            for existing in final_list:
                existing_name = existing['name']
                # Check 1: Strict substring (word boundary safe?)
                # "Pham" in "Pham Nuwen" -> Yes
                # "Ham" in "Pham Nuwen" -> No (hopefully)
                
                # Simple check: Name is substring
                if name in existing_name and name != existing_name:
                    # Check word boundaries roughly
                    # If "Pham" is in "Pham Nuwen", it's likely an alias.
                    parent = existing
                    break
            
            if parent:
                print(f"  Merging '{name}' -> '{parent['name']}'")
                parent['aliases'].append(name)
                parent['frequency'] += item['frequency']
                merged_count += 1
            else:
                final_list.append(item)
        
        new_data[cat] = final_list
        
    print(f"\nTotal Merges: {merged_count}")
    
    with open(input_path, 'w') as f:
        yaml.dump(new_data, f, sort_keys=False)
        
    print("Done.")

if __name__ == "__main__":
    main()
