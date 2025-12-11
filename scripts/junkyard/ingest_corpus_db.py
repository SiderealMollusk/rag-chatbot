import sqlite3
import json
import os

DB_PATH = "data/bible.db"
CORPUS_FILE = "data/corpus.jsonl"

def init_db(conn):
    c = conn.cursor()
    
    # Text Chunks Table
    # This stores the lowest level granular text (paragraphs)
    c.execute('''
        CREATE TABLE IF NOT EXISTS text_chunks (
            id TEXT PRIMARY KEY,
            content TEXT,
            source_file TEXT,
            chapter_title TEXT,
            scene_index INTEGER,
            paragraph_index INTEGER,
            
            -- Denormalized meta for fast grep
            location_name TEXT,
            primary_characters TEXT,
            tags TEXT
        )
    ''')
    
    # Full Text Search Virtual Table
    c.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS text_chunks_fts USING fts5(
            content,
            location_name,
            primary_characters,
            tags,
            content=text_chunks,
            content_rowid=rowid
        )
    ''')
    
    conn.commit()

def ingest_corpus():
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    
    with open(CORPUS_FILE, 'r') as f:
        rows = []
        for line in f:
            if not line.strip(): continue
            doc = json.loads(line)
            
            # Extract basic IDs
            # id format: ch006_sc01_p01
            # We can parse indices from the ID or metadata
            meta = doc.get("metadata", {})
            
            loc_name = meta.get("location", {}).get("name", "") if isinstance(meta.get("location"), dict) else str(meta.get("location", ""))
            
            chars = ", ".join(meta.get("characters", []))
            tags = ", ".join(meta.get("tags", []))
            
            # Robust integer parsing
            s_idx = meta.get("scene_index", 0)
            
            # P_index from ID
            p_idx = 0
            try:
                p_idx = int(doc["id"].split("_p")[1])
            except:
                pass
                
            rows.append((
                doc["id"],
                doc["text"],
                meta.get("source", ""),
                meta.get("chapter_title", ""),
                s_idx,
                p_idx,
                loc_name,
                chars,
                tags
            ))
            
    print(f"Inserting {len(rows)} rows into SQLite...")
    
    c = conn.cursor()
    c.executemany('''
        INSERT OR REPLACE INTO text_chunks 
        (id, content, source_file, chapter_title, scene_index, paragraph_index, location_name, primary_characters, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', rows)
    
    # Rebuild FTS index
    print("Rebuilding Search Index...")
    c.execute("INSERT INTO text_chunks_fts(text_chunks_fts) VALUES('rebuild')")
    
    conn.commit()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    ingest_corpus()
