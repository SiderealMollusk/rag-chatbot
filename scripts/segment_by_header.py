import os
import argparse
import json
import re

def sanitize(name):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name.strip())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--asin", required=True)
    args = parser.parse_args()
    
    base_dir = os.path.join("kindle-ai-export", "out", args.asin)
    content_path = os.path.join(base_dir, "content.json")
    headers_path = os.path.join(base_dir, "blue_headers.txt")
    out_dir = os.path.join(base_dir, "named_chapters")
    
    os.makedirs(out_dir, exist_ok=True)
    
    # Load Headers Map
    # Format: "filename.png     : text header"
    header_map = {}
    with open(headers_path, 'r') as f:
        for line in f:
            if ':' not in line: continue
            parts = line.split(':', 1)
            fname = parts[0].strip()
            label = parts[1].strip()
            header_map[fname] = label
            
    # Load Content
    with open(content_path, 'r') as f:
        content = json.load(f)
    content.sort(key=lambda x: x['index'])
    
    current_lines = []
    current_label = "000_prologue" # Default start
    seq = 0
    
    print(f"Segmenting into {out_dir}...")
    
    for item in content:
        img_name = os.path.basename(item['screenshot'])
        
        if img_name in header_map:
            # Dump previous
            if current_lines:
                out_name = f"{seq:03d}_{sanitize(current_label)}.txt"
                with open(os.path.join(out_dir, out_name), 'w') as f:
                    f.write("\n\n".join(current_lines))
                # print(f"Saved {out_name}")
                
            # Start New
            seq += 1
            current_label = header_map[img_name]
            current_lines = []
            
            # Add Header Text to file?
            # User wants "text file per header".
            # Usually the page text includes the header text if OCR was good, 
            # but usually Blue Text page might have scant standard text.
            # I'll just append the content text as usual.
            
        current_lines.append(item['text'])
        
    # Flush last
    if current_lines:
        out_name = f"{seq:03d}_{sanitize(current_label)}.txt"
        with open(os.path.join(out_dir, out_name), 'w') as f:
            f.write("\n\n".join(current_lines))
            
    print(f"Finished. Created {seq+1} files.")

if __name__ == "__main__":
    main()
