import os
import json
import argparse
import re
import sys

def load_dictionary():
    # A simple set of common english words would be best, but for now 
    # we can use a heuristic or a small embedded list if we don't want external deps.
    # Actually, on macOS, we can use the system dictionary at /usr/share/dict/words
    word_file = "/usr/share/dict/words"
    if os.path.exists(word_file):
        with open(word_file, "r") as f:
            valid_words = set(word.strip().lower() for word in f)
        return valid_words
    return None

def main():
    parser = argparse.ArgumentParser(description="Check OCR Quality")
    parser.add_argument("--asin", required=True, help="ASIN of the book")
    args = parser.parse_args()

    # Paths
    base_dir = os.path.join(os.getcwd(), "kindle-ai-export", "out", args.asin)
    input_path = os.path.join(base_dir, "content.json")

    if not os.path.exists(input_path):
        print(f"Error: File not found {input_path}")
        sys.exit(1)

    with open(input_path, 'r') as f:
        chunks = json.load(f)

    full_text = " ".join([c['text'] for c in chunks])
    
    # 1. Trivial Check
    if not full_text.strip():
        print("FAIL: Text is empty.")
        sys.exit(1)

    words = re.findall(r'\b[a-zA-Z]+\b', full_text)
    total_words = len(words)
    
    if total_words < 100:
         print("FAIL: Too few words to analyze.")
         sys.exit(1)

    # 2. Dictionary Hit Rate
    valid_words = load_dictionary()
    if valid_words:
        hits = sum(1 for w in words if w.lower() in valid_words)
        hit_rate = hits / total_words
        print(f"Dictionary Hit Rate: {hit_rate:.2%}")
        
        # Sci-fi has made up words, so 85% is a safe "pass" threshold
        if hit_rate < 0.70:
            print("FAIL: OCR quality is likely poor (Hit rate < 70%)")
        elif hit_rate < 0.85:
            print("WARN: OCR quality is questionable (Hit rate < 85%) - Normal for Hard Sci-Fi")
        else:
            print("PASS: Quality looks good.")
    else:
        print("WARN: Could not load system dictionary. Skipping Hit Rate check.")

    # 3. Garbage Density (Symbols in middles of words)
    # Looking for things like "th!s" or "wh@t"
    garbage_pattern = r'[a-zA-Z]+[^a-zA-Z\s\.,\'"\-?!]+[a-zA-Z]+'
    garbage_matches = re.findall(garbage_pattern, full_text)
    garbage_rate = len(garbage_matches) / total_words
    
    print(f"Garbage String Rate: {garbage_rate:.4%}")
    if garbage_rate > 0.05:
         print("FAIL: Too much symbol noise in words.")

if __name__ == "__main__":
    main()
