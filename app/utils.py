from passlib.context import CryptContext
from fastapi import HTTPException
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_active_or_404(model, entity_id, db: Session, label: str = "Ressource"):
    """Récupère une ligne active (is_deleted=False), sinon lève une 404."""
    entity = db.get(model, entity_id)
    if not entity or entity.is_deleted:
        raise HTTPException(status_code=404, detail=f"{label} introuvable")
    return entity


def get_deleted_or_404(model, entity_id, db: Session, label: str = "Ressource"):
    """Récupère une ligne soft-deleted, sinon lève une 404."""
    entity = db.get(model, entity_id)
    if not entity or not entity.is_deleted:
        raise HTTPException(status_code=404, detail=f"{label} introuvable ou déjà active")
    return entity