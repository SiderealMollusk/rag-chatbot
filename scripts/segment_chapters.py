import cv2
import glob
import os
import argparse
import json
import numpy as np
from tqdm import tqdm
import re

def natural_key(p):
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', p)]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--asin", required=True)
    args = parser.parse_args()
    
    base_dir = os.path.join("kindle-ai-export", "out", args.asin)
    img_dir = os.path.join(base_dir, "pages")
    content_path = os.path.join(base_dir, "content.json")
    
    with open(content_path, 'r') as f:
        content = json.load(f)
        
    # Map filename -> Content Item
    # Content item has 'screenshot': 'kindle-ai-export/out/B000FBJAGO/pages/001-006.png'
    # We need to map basename
    
    content_map = {}
    for item in content:
        fname = os.path.basename(item['screenshot'])
        content_map[fname] = item
        
    images = sorted(glob.glob(os.path.join(img_dir, "*.png")))
    if not images:
        images = sorted(glob.glob(os.path.join(img_dir, "*.jpg")))
        
    print(f"Scanning {len(images)} images for Chapter Breaks...")
    
    chapter_starts = []
    
    for img_path in tqdm(images):
        img_name = os.path.basename(img_path)
        
        img = cv2.imread(img_path)
        if img is None: continue
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([100, 50, 50])
        upper_blue = np.array([140, 255, 255])
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        blue_pixels = cv2.countNonZero(mask)
        
        if blue_pixels > 500: # Threshold
            chapter_starts.append(img_name)

    print(f"Found {len(chapter_starts)} potential breaks.")
    
    # Sort content by index
    content.sort(key=lambda x: x['index'])
    
    # Generate Output
    chapters_dir = os.path.join(base_dir, "chapters")
    os.makedirs(chapters_dir, exist_ok=True)
    
    current_chapter_lines = []
    chapter_num = 0
    
    # Logic: precise mapping
    # Iterate content in order. If item's screenshot is in chapter_starts, start new chapter.
    
    # We need a start for the first chapter even if no blue (Prologue?)
    # But usually first page is blue?
    
    # If first item hasn't triggered, we buffer until trigger.
    # Actually, simplistic approach: Start Chapter 0 (Prologue). When hits Blue, Start Chapter 1.
    
    for item in content:
        fname = os.path.basename(item['screenshot'])
        
        is_break = fname in chapter_starts
        
        if is_break:
            # Save previous chapter
            if current_chapter_lines:
                chapter_text = "\n\n".join(current_chapter_lines)
                out_name = f"chapter_{chapter_num:03d}.txt"
                with open(os.path.join(chapters_dir, out_name), 'w') as f:
                    f.write(chapter_text)
                # print(f"Saved {out_name} ({len(chapter_text)} chars)")
            
            chapter_num += 1
            current_chapter_lines = [] # Reset
            
            # Add Header
            current_chapter_lines.append(f"## CHAPTER {chapter_num}")
            
        current_chapter_lines.append(item['text'])
        
    # Flush last
    if current_chapter_lines:
        chapter_text = "\n\n".join(current_chapter_lines)
        out_name = f"chapter_{chapter_num:03d}.txt"
        with open(os.path.join(chapters_dir, out_name), 'w') as f:
            f.write(chapter_text)
            
    print(f"Generated {chapter_num + 1} chapter files in {chapters_dir}")

if __name__ == "__main__":
    main()
