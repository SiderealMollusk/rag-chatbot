import sqlite3
import json
import os
import glob
from typing import Dict, List

DB_PATH = "/data/bible.db"
# Map volume paths
WIKI_INDEX_PATH = "/data/wiki_candidates/master_wiki_index.json"
CHAPTER_ANALYSIS_DIR = "/data/passes/01_scene_summary"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def ingest_entities(conn, entities: List[Dict]):
    print(f"Ingesting {len(entities)} entities...")
    cursor = conn.cursor()
    
    # Pre-calculate alias map for later
    alias_map = {}
    
    for entity in entities:
        # 1. Insert Entity
        cursor.execute('''
            INSERT OR REPLACE INTO entities (id, name, category, data)
            VALUES (?, ?, ?, ?)
        ''', (
            entity['id'],
            entity['name'],
            entity['category'],
            json.dumps(entity)
        ))
        
        # 2. Build Alias Map (Name + Aliases -> ID)
        eid = entity['id']
        if isinstance(entity['name'], str):
             alias_map[entity['name'].lower()] = eid
        
        for alias in entity.get('aliases', []):
            if isinstance(alias, str):
                alias_map[alias.lower()] = eid
            
    conn.commit()
    return alias_map

def ingest_scenes(conn, alias_map: Dict[str, str]):
    print("Ingesting scenes from chapter files...")
    files = sorted(glob.glob(os.path.join(CHAPTER_ANALYSIS_DIR, "*.json")))
    cursor = conn.cursor()
    
    scene_count = 0
    mention_count = 0
    
    for f_path in files:
        data = load_json(f_path)
        chapter_title = data.get('chapter_title', 'Unknown')
        
        # Try to extract chapter number from filename (e.g., 046_thirtyseven.json)
        filename = os.path.basename(f_path)
        try:
            chapter_num = int(filename.split('_')[0])
        except:
            chapter_num = 0

        scenes = data.get('scenes', [])
        for scene in scenes:
            seq = scene.get('scene_index', 0)
            scene_id = f"scene_{chapter_num:03d}_{seq:02d}"
            
            # 1. Insert Scene
            summary = scene.get('summary', '')
            location_text = scene.get('location', '')
            
            # Try to resolve location ID
            location_id = None
            if isinstance(location_text, str):
                location_id = alias_map.get(location_text.lower())
            
            cursor.execute('''
                INSERT OR REPLACE INTO scenes (id, chapter_title, sequence_index, summary, location_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (scene_id, chapter_title, (chapter_num * 1000) + seq, summary, location_id))
            
            # 2. Insert Character Mentions (Cast)
            chars = scene.get('characters_present', [])
            for char_name in chars:
                # Resolve ID
                clean_name = char_name.strip().split('(')[0].strip() # Remove (Radio) etc
                entity_id = alias_map.get(clean_name.lower())
                
                if entity_id:
                    cursor.execute('''
                        INSERT OR REPLACE INTO scene_mentions (scene_id, entity_id, role, context)
                        VALUES (?, ?, ?, ?)
                    ''', (scene_id, entity_id, 'APPEARANCE', 'In scene cast list'))
                    mention_count += 1
                else:
                    # Optional: Log missing entities?
                    pass
            
            # 3. Explicit Location Mention
            if location_id:
                 cursor.execute('''
                        INSERT OR REPLACE INTO scene_mentions (scene_id, entity_id, role, context)
                        VALUES (?, ?, ?, ?)
                    ''', (scene_id, location_id, 'LOCATION', 'Scene setting'))
                 mention_count += 1
                 
            scene_count += 1
            
    conn.commit()
    print(f"Ingested {scene_count} scenes and {mention_count} graph connections.")

def main():
    conn = get_db_connection()
    
    # 1. Entities
    try:
        entities = load_json(WIKI_INDEX_PATH)
        alias_map = ingest_entities(conn, entities)
        
        # 2. Scenes & Mentions
        ingest_scenes(conn, alias_map)
        
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
