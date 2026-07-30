from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.validate import ApiResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("")
def get_categories(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT id, name, slug FROM categories ORDER BY name"))
    categories = [dict(row._mapping) for row in result]
    return ApiResponse(status_code=200, message=f"{len(categories)} catégorie(s)", data=categories)