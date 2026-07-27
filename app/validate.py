from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Generic, TypeVar

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    status_code: int
    message: str
    data: Optional[T] = None


class AnnonceCreate(BaseModel):
    titre: str
    description: Optional[str] = None
    prix: float
    ville: str


class AnnonceUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    prix: Optional[float] = None
    ville: Optional[str] = None


class AnnonceResponse(BaseModel):
    id: int
    titre: str
    description: Optional[str]
    prix: float
    ville: str
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]

    class Config:
        from_attributes = True