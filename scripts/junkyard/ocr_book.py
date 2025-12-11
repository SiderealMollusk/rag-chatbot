import os
import json
import argparse
import easyocr
import glob
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser(description="OCR Kindle Screenshots")
    parser.add_argument("--asin", required=True, help="ASIN of the book to process")
    parser.add_argument("--lang", default="en", help="Language code (default: en)")
    parser.add_argument("--gpu", action="store_true", default=True, help="Use GPU if available (default: True)")
    
    args = parser.parse_args()
    
    # Paths
    base_dir = os.path.join(os.getcwd(), "kindle-ai-export", "out", args.asin)
    pages_dir = os.path.join(base_dir, "pages")
    metadata_path = os.path.join(base_dir, "metadata.json")
    output_path = os.path.join(base_dir, "content.json")
    
    if not os.path.exists(pages_dir):
        print(f"Error: Pages directory not found at {pages_dir}")
        return

    # Load metadata to get proper ordering if available
    metadata = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            print(f"Loaded metadata for: {metadata.get('meta', {}).get('title', 'Unknown Title')}")

    # Initialize Reader
    print(f"Initializing EasyOCR for language '{args.lang}'...")
    reader = easyocr.Reader([args.lang], gpu=args.gpu)

    # Get list of images
    # If we have metadata with pages, verify against it, otherwise glob
    image_files = sorted(glob.glob(os.path.join(pages_dir, "*.png")))
    
    if not image_files:
        print("No images found to process.")
        return

    content_results = []
    
    print(f"Start processing {len(image_files)} pages...")
    
    for img_path in tqdm(image_files):
        filename = os.path.basename(img_path)
        # Expected format: index-page.png (e.g. 000-003.png)
        parts = filename.replace('.png', '').split('-')
        
        index = int(parts[0]) if parts[0].isdigit() else 0
        page_num = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0

        try:
            # detail=0 returns just the text list
            result_text_list = reader.readtext(img_path, detail=0, paragraph=True)
            full_text = "\n\n".join(result_text_list)
            
            content_results.append({
                "index": index,
                "page": page_num,
                "text": full_text,
                "screenshot": f"out/{args.asin}/pages/{filename}" # Relative path as expected by key
            })
            
        except Exception as e:
            print(f"Failed to process {filename}: {e}")

    # Save results
    with open(output_path, 'w') as f:
        json.dump(content_results, f, indent=2)
        
    print(f"Done! Saved content to {output_path}")

if __name__ == "__main__":
    main()
