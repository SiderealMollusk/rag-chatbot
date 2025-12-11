from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any
import sqlite3
import json

app = FastAPI(title="Movie Bible API")

# Allow CORS for Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "/data/bible.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Models ---
class Entity(BaseModel):
    id: str
    name: str
    category: str
    data: Optional[Any] = None

class Scene(BaseModel):
    id: str
    chapter_title: str
    summary: str
    sequence_index: int

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"status": "Movie Bible API Online"}

@app.get("/entities", response_model=List[Entity])
def get_entities():
    conn = get_db()
    rows = conn.execute("SELECT id, name, category, data FROM entities ORDER BY name").fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "data": json.loads(row["data"]) if row["data"] else None
        })
    return results

@app.get("/scenes", response_model=List[Scene])
def get_scenes():
    conn = get_db()
    rows = conn.execute("SELECT * FROM scenes ORDER BY sequence_index").fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- Chapter / Timeline Endpoints ---

class ChapterSummary(BaseModel):
    title: str
    scene_count: int
    first_scene_id: str

class EntityRef(BaseModel):
    id: str
    name: str
    category: str
    role: str

class SceneDetail(BaseModel):
    id: str
    chapter_title: str
    sequence_index: int
    summary: str
    location_id: Optional[str]
    mentions: List[EntityRef]

@app.get("/chapters", response_model=List[ChapterSummary])
def get_chapters():
    conn = get_db()
    # Group by chapter title, order by the sequence of the first scene in that chapter
    sql = """
        SELECT 
            chapter_title as title, 
            COUNT(id) as scene_count, 
            MIN(id) as first_scene_id,
            MIN(sequence_index) as sort_order
        FROM scenes 
        GROUP BY chapter_title 
        ORDER BY sort_order
    """
    rows = conn.execute(sql).fetchall()
    conn.close()
    return [{
        "title": row["title"],
        "scene_count": row["scene_count"],
        "first_scene_id": row["first_scene_id"]
    } for row in rows]

@app.get("/chapters/{title}/scenes", response_model=List[SceneDetail])
def get_chapter_scenes(title: str):
    conn = get_db()
    
    # 1. Get Scenes
    scenes_rows = conn.execute(
        "SELECT * FROM scenes WHERE chapter_title = ? ORDER BY sequence_index", 
        (title,)
    ).fetchall()
    
    if not scenes_rows:
        raise HTTPException(status_code=404, detail="Chapter not found")
        
    results = []
    for s_row in scenes_rows:
        scene_id = s_row["id"]
        
        # 2. Get Mentions for this scene (The "Connected Elements")
        mentions_sql = """
            SELECT 
                e.id, e.name, e.category, m.role 
            FROM scene_mentions m
            JOIN entities e ON m.entity_id = e.id
            WHERE m.scene_id = ?
        """
        m_rows = conn.execute(mentions_sql, (scene_id,)).fetchall()
        
        mentions = [{
            "id": m["id"],
            "name": m["name"],
            "category": m["category"],
            "role": m["role"]
        } for m in m_rows]

        results.append({
            "id": scene_id,
            "chapter_title": s_row["chapter_title"],
            "sequence_index": s_row["sequence_index"],
            "summary": s_row["summary"],
            "location_id": s_row["location_id"],
            "mentions": mentions
        })
    
    conn.close()
    return results
