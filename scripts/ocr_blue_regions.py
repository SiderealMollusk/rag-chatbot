import cv2
import easyocr
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

    # Initializing OCR
    reader = easyocr.Reader(['en'], gpu=True) # Use GPU if available (User has M1)
    
    # We first scan for candidates to save OCR time
    candidates = []
    for img_path in images:
        img = cv2.imread(img_path)
        if img is None: continue
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([100, 50, 50]), np.array([140, 255, 255]))
        if cv2.countNonZero(mask) > 500:
            candidates.append(img_path)
            
    print(f"OCRing {len(candidates)} Blue Candidates...")
    
    results = []
    
    for img_path in tqdm(candidates):
        img_name = os.path.basename(img_path)
        
        # Preprocess: Mask non-blue to White
        img = cv2.imread(img_path)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([100, 50, 50]), np.array([140, 255, 255]))
        
        # Create white background
        white_bg = np.ones_like(img) * 255
        # Copy original pixels where mask is blue
        # mask is single channel 0/255
        
        # Bitwise AND to get colored text
        start_img = cv2.bitwise_and(img, img, mask=mask)
        
        # The result has Black background. OCR likes white background usually? EasyOCR is robust.
        # But inverted (Blue text on Black) might work. 
        # Better: Replace black background with White.
        
        # Start with White
        final_img = np.ones_like(img) * 255
        # Copy masked pixels
        final_img[mask > 0] = img[mask > 0]
        
        # Run OCR
        # easyocr expects path or numpy array
        try:
            # detail=0 returns just the list of strings
            texts = reader.readtext(final_img, detail=0)
            text_line = " ".join(texts).strip()
            results.append((img_name, text_line))
        except Exception as e:
            results.append((img_name, f"Error: {e}"))
            
    print("\n--- OCR Results on Blue Text ---")
    for name, text in results:
        print(f"{name: <15} : {text}")

if __name__ == "__main__":
    main()
