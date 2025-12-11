import cv2
import glob
import os
import argparse
import numpy as np
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--asin", required=True)
    args = parser.parse_args()
    
    img_dir = os.path.join("kindle-ai-export", "out", args.asin, "pages")
    images = sorted(glob.glob(os.path.join(img_dir, "*.png")))
    
    if not images:
        images = sorted(glob.glob(os.path.join(img_dir, "*.jpg")))
        
    print(f"Scanning {len(images)} images for Blue content...")
    
    results = []
    
    for img_path in tqdm(images):
        img_name = os.path.basename(img_path)
        # Parse index from 'page_001.png' or similar
        # Assuming filename format is not strict, just store name
        
        img = cv2.imread(img_path)
        if img is None: continue
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Define Blue in HSV
        # OpenCV Hue is 0-179. Blue is around 120.
        # Cyan is 90, Violet is 150.
        lower_blue = np.array([100, 50, 50])
        upper_blue = np.array([140, 255, 255])
        
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        blue_pixels = cv2.countNonZero(mask)
        
        if blue_pixels > 100: # Noise floor
            results.append((img_name, blue_pixels))
            
    # Sort by index if possible, else name
    # usually page_1.png, page_2.png... lexicographical sort 'page_10' < 'page_2' is bad
    # Use natural sort
    import re
    def natural_key(p):
        return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', p[0])]
        
    results.sort(key=natural_key)
    
    print("\n--- Potential Chapter Headers (Blue Pixel Count) ---")
    for name, count in results:
        # Simple ASCII bar
        bar = "|" * (count // 500)
        if len(bar) > 50: bar = bar[:50] + "..."
        print(f"{name: <15} : {count: >6} {bar}")

if __name__ == "__main__":
    main()
