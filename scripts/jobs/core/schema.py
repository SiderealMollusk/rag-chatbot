from pydantic import BaseModel
from typing import Dict, Any, Optional

class ManifestEntry(BaseModel):
    task: str
    args: list = []
    kwargs: Dict[str, Any] = {}
    
    # Metadata for the human operator
    meta: Dict[str, Any] = {}
    description: Optional[str] = None
    priority: int = 10
