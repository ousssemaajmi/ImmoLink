from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AnnonceCreate(BaseModel):
    titre: str
    description: Optional[str] = None
    prix: float
    ville: str

class AnnonceResponse(BaseModel):
    id: int
    titre: str
    description: Optional[str]
    prix: float
    ville: str
    created_at: datetime

    class Config:
        from_attributes = True