import os
import json
import argparse
import spacy
import re
from collections import Counter
import yaml
import sys

def load_dictionary():
    word_file = "/usr/share/dict/words"
    if os.path.exists(word_file):
        with open(word_file, "r") as f:
            valid_words = set(word.strip().lower() for word in f)
        return valid_words
    return set()

def main():
    parser = argparse.ArgumentParser(description="Extract Entities (Smart Filter)")
    parser.add_argument("--asin", required=True, help="ASIN of the book")
    args = parser.parse_args()

    # Paths
    base_dir = os.path.join(os.getcwd(), "kindle-ai-export", "out", args.asin)
    input_path = os.path.join(base_dir, "content.json")
    output_path = os.path.join(base_dir, "entities_candidates.yaml")
    
    # 1. Load Data
    print(f"Loading content from {input_path}...")
    with open(input_path, 'r') as f:
        chunks = json.load(f)
    full_text = "\n".join([c['text'] for c in chunks])
    
    # 2. Init Resources
    print("Loading SpaCy & Dictionary...")
    nlp = spacy.load("en_core_web_sm")
    english_vocab = load_dictionary()
    nlp.max_length = len(full_text) + 100000 
    
    # 3. Execution
    print("Running NLP...")
    doc = nlp(full_text)
    
    # Buckets
    bucket_high = Counter() # SpaCy says YES
    bucket_ambiguous = Counter() # Not English, Not SpaCy (Likely Sci-Fi Name)
    bucket_noise = Counter() # English Word (Common Noun/Verb)
    
    # Set of known entities to avoid double counting in greedy pass
    known_entities = set()
    
    # A) SpaCy Pass (High Confidence)
    for ent in doc.ents:
        clean = ent.text.strip().replace('\n', ' ')
        if len(clean) < 3: continue
        if ent.label_ in ["PERSON", "ORG", "GPE", "LOC", "FAC"]:
            bucket_high[clean] += 1
            known_entities.add(clean)

    # B) Greedy Pass (Catch strict Capitalized phrases not found by SpaCy)
    # We look for Capitalized Words that are NOT in the high bucket
    pattern = r'\b[A-Z][a-z]+\b'
    candidates = re.findall(pattern, full_text)
    
    for word in candidates:
        if word in known_entities: continue
        if len(word) < 3: continue
        
        # Check Dictionary
        if word.lower() in english_vocab:
            # It's a dictionary word (e.g. "Suddenly", "Table")
            bucket_noise[word] += 1
        else:
            # It's NOT a dictionary word (e.g. "Skroderider", "OOB")
            bucket_ambiguous[word] += 1
            
    # 4. Result Stats
    print("\n--- Extraction Results ---")
    print(f"HIGH Confidence (SpaCy): {len(bucket_high)} unique items")
    print(f"AMBIGUOUS (Sci-Fi/OOB):  {len(bucket_ambiguous)} unique items")
    print(f"NOISE (Dictionary Words):{len(bucket_noise)} unique items (Auto-Discarded)")
    
    # 5. formatting for YAML
    # We only save HIGH and AMBIGUOUS
    
    final_cats = {
        "meta": {"version": 0, "generator": "smart_filter_v1"},
        "HIGH_CONFIDENCE": [],
        "AMBIGUOUS": []
    }
    
    # Flatten High
    for name, freq in bucket_high.most_common():
        if freq < 2: continue # Min support
        # Clean up some overlaps? No, just dump.
        final_cats["HIGH_CONFIDENCE"].append({
            "name": name, "frequency": freq, "aliases": []
        })

    # Flatten Ambiguous
    for name, freq in bucket_ambiguous.most_common():
        if freq < 3: continue # Ambiguous needs more proof
        final_cats["AMBIGUOUS"].append({
            "name": name, "frequency": freq, "aliases": []
        })

    print(f"Saving {len(final_cats['HIGH_CONFIDENCE']) + len(final_cats['AMBIGUOUS'])} items to {output_path}...")
    
    with open(output_path, 'w') as f:
        yaml.dump(final_cats, f, sort_keys=False)

if __name__ == "__main__":
    main()
