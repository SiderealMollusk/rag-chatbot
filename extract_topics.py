import json
import os
import re
from collections import Counter
from glob import glob

def extract_topics():
    base_dir = "/Users/virgil/Developer/novel-rag/kindle-ai-export/out/B000FBJAGO/chapter_analysis"
    files = sorted(glob(os.path.join(base_dir, "*.json")))
    
    character_counts = Counter()
    location_counts = Counter()
    
    # Heuristic: Gather capitalized phrases from summaries for potential "Concepts" or "Items"
    # This is a naive regex for the "False Positive" pass
    potential_entities = Counter()
    
    for f_path in files:
        try:
            with open(f_path, 'r') as f:
                data = json.load(f)
                
                # Extract Structured Data
                scenes = data.get('scenes', [])
                for scene in scenes:
                    # Characters
                    chars = scene.get('characters_present', [])
                    for c in chars:
                        character_counts[c.strip()] += 1
                        
                    # Locations
                    loc = scene.get('location', '')
                    if loc:
                        location_counts[loc.strip()] += 1
                        
                    # Text Analysis for Summaries and Key Events
                    text_content = []
                    if 'summary' in scene: text_content.append(scene['summary'])
                    if 'key_events' in scene: text_content.extend(scene['key_events'])
                    if 'chapter_summary' in data: text_content.append(data['chapter_summary'])
                    
                    for text in text_content:
                        # Find capitalized phrases (2+ words) that might be proper nouns
                        # e.g. "Countermeasure", "Zones of Thought", "Slow Zone"
                        # Regex: Capitalized word, followed by space, followed by Capitalized word
                        # Also catch single capitalized words that aren't start of sentence (harder without NLP lib)
                        
                        # Just grabbing everything capitalized that isn't a basic stopword is "Pass 1"
                        words = re.findall(r'\b[A-Z][a-zA-Z0-9\-\']+\b', text)
                        for w in words:
                             # very basic stoplist for "start of sentence" false positives
                             if w.lower() not in ['the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'but', 'so', 'then', 'when', 'he', 'she', 'it', 'they', 'we', 'you', 'if', 'as', 'scene', 'chapter']:
                                 potential_entities[w] += 1
                                 
        except Exception as e:
            print(f"Error processing {f_path}: {e}")

    result = {
        "characters": dict(character_counts.most_common()),
        "locations": dict(location_counts.most_common()),
        "text_mentions": dict(potential_entities.most_common())
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    extract_topics()
