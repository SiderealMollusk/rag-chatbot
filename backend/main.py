from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Movie Bible API")

@app.get("/")
def read_root():
    return {"status": "Movie Bible API is Online", "version": "1.0.0"}

# Skeleton Endpoints for Entities

class Entity(BaseModel):
    id: str
    name: str
    category: str

@app.get("/entities", response_model=List[Entity])
def get_entities():
    # TODO: Hook up to SQLite
    return []

@app.get("/entities/{entity_id}")
def get_entity(entity_id: str):
    return {"id": entity_id, "name": "Unknown", "description": "Placeholder"}
