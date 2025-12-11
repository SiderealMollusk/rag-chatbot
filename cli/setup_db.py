import sqlite3
import json
import os
from glob import glob

DB_PATH = "/data/bible.db"
JSON_DIR = "/data/json_out" # Mapped volume

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. ENTITIES
    c.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            data JSON
        )
    ''')
    
    # 2. SCENES
    c.execute('''
        CREATE TABLE IF NOT EXISTS scenes (
            id TEXT PRIMARY KEY,
            chapter_title TEXT,
            sequence_index INTEGER,
            summary TEXT,
            location_id TEXT
        )
    ''')

    # 3. SCENE_MENTIONS (The Graph)
    c.execute('''
        CREATE TABLE IF NOT EXISTS scene_mentions (
            scene_id TEXT,
            entity_id TEXT,
            role TEXT,
            context TEXT,
            FOREIGN KEY(scene_id) REFERENCES scenes(id),
            FOREIGN KEY(entity_id) REFERENCES entities(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == "__main__":
    init_db()
