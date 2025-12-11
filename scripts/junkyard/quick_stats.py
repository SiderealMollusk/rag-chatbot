import sqlite3
import re
from collections import Counter
import json
import math

DB_PATH = "data/bible.db"

# A basic stopword list to filter out common English words
STOPWORDS = set([
    "the", "of", "and", "a", "to", "in", "is", "you", "that", "it", "he", "was", "for", "on", "are", "as", "with", "his", "they", "i", "at", "be", "this", "have", "from", "or", "one", "had", "by", "word", "but", "not", "what", "all", "were", "we", "when", "your", "can", "said", "there", "use", "an", "each", "which", "she", "do", "how", "their", "if", "will", "up", "other", "about", "out", "many", "then", "them", "these", "so", "some", "her", "would", "make", "like", "him", "into", "time", "has", "look", "two", "more", "write", "go", "see", "number", "no", "way", "could", "people", "my", "than", "first", "water", "been", "call", "who", "oil", "its", "now", "find", "long", "down", "day", "did", "get", "come", "made", "may", "part", 
    "chapter", "scene", "page", "mr", "mrs", "miss", "dr"
])

def get_corpus_text():
    conn = sqlite3.connect(DB_PATH)
    # Get all content
    rows = conn.execute("SELECT content FROM text_chunks").fetchall()
    conn.close()
    return [r[0] for r in rows]

def analyze_frequency():
    print("Loading corpus...")
    texts = get_corpus_text()
    all_text = " ".join(texts).lower()
    
    # 1. Word Frequency (Bag of Words)
    # Remove punctuation basic
    clean_text = re.sub(r'[^\w\s]', '', all_text)
    words = clean_text.split()
    
    # Filter stopwords
    filtered_words = [w for w in words if w not in STOPWORDS and len(w) > 3]
    
    counts = Counter(filtered_words)
    
    print("\n--- TOP 50 MOST FREQUENT WORDS ---")
    for word, count in counts.most_common(50):
        print(f"{word}: {count}")
        
    # 2. Bigram Frequency (Phrases)
    # "automation" might appear with other words
    bigrams = zip(filtered_words, filtered_words[1:])
    bigram_counts = Counter(bigrams)
    
    print("\n--- TOP 20 BIGRAMS (Recurring Concepts) ---")
    for bg, count in bigram_counts.most_common(20):
        print(f"{bg[0]} {bg[1]}: {count}")

def analyze_keyword_concordance(target_word="automation"):
    print(f"\n--- CONCORDANCE FOR '{target_word.upper()}' ---")
    conn = sqlite3.connect(DB_PATH)
    
    # Use the FTS index for speed
    rows = conn.execute(
        "SELECT text_chunks.content, chapter_title, scene_index FROM text_chunks_fts JOIN text_chunks ON text_chunks_fts.rowid = text_chunks.rowid WHERE text_chunks_fts MATCH ? LIMIT 10", 
        (target_word,)
    ).fetchall()
    
    print(f"Found {len(rows)} samples (showing first 10):")
    for r in rows:
        # Highlight the word
        text = r[0]
        # basic highlighter
        highlighted = re.sub(f"({target_word})", r"\033[1m\1\033[0m", text, flags=re.IGNORECASE)
        print(f"[{r[1]} Sc{r[2]}] ...{highlighted[:100]}...") # Just print start for brevity
    
    conn.close()

if __name__ == "__main__":
    analyze_frequency()
    analyze_keyword_concordance("automation")
    analyze_keyword_concordance("blight")
