from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.sql import func

from app.database import get_db
from app.models import User, Listing
from app.utils import hash_password, get_active_or_404, get_deleted_or_404
from app.validate import UserCreate, UserUpdate, UserResponse, ListingResponse, ApiResponse

router = APIRouter(prefix="/users", tags=["Users"])


# ---------- CREATE ----------
@router.post("", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.execute(select(User).where(User.email == user.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    nouvel_user = User(
        email=user.email,
        password_hash=hash_password(user.password),
        full_name=user.full_name,
    )
    db.add(nouvel_user)
    db.commit()
    db.refresh(nouvel_user)

    return ApiResponse(status_code=201, message="Utilisateur créé avec succès", data=nouvel_user)


# ---------- GET ALL (actifs) ----------
@router.get("", response_model=ApiResponse[list[UserResponse]])
def get_all_users(db: Session = Depends(get_db)):
    users = db.execute(select(User).where(User.is_deleted == False)).scalars().all()
    return ApiResponse(status_code=200, message=f"{len(users)} utilisateur(s) trouvé(s)", data=users)


# ---------- GET BY ID ----------
@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = get_active_or_404(User, user_id, db, "Utilisateur")
    return ApiResponse(status_code=200, message="Utilisateur récupéré avec succès", data=user)


# ---------- UPDATE (PATCH) ----------
@router.patch("/{user_id}", response_model=ApiResponse[UserResponse])
def update_user(user_id: int, updated: UserUpdate, db: Session = Depends(get_db)):
    user = get_active_or_404(User, user_id, db, "Utilisateur")

    donnees = updated.model_dump(exclude_unset=True)
    if not donnees:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

    if "password" in donnees:
        donnees["password_hash"] = hash_password(donnees.pop("password"))

    for key, value in donnees.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return ApiResponse(status_code=200, message="Utilisateur mis à jour avec succès", data=user)


# ---------- SOFT DELETE ----------
@router.delete("/{user_id}/soft", response_model=ApiResponse[UserResponse])
def soft_delete_user(user_id: int, db: Session = Depends(get_db)):
    user = get_active_or_404(User, user_id, db, "Utilisateur")

    user.is_deleted = True
    user.deleted_at = func.now()
    db.commit()
    db.refresh(user)

    return ApiResponse(status_code=200, message="Utilisateur supprimé (soft delete)", data=user)


# ---------- RESTORE ----------
@router.post("/{user_id}/restore", response_model=ApiResponse[UserResponse])
def restore_user(user_id: int, db: Session = Depends(get_db)):
    user = get_deleted_or_404(User, user_id, db, "Utilisateur")

    user.is_deleted = False
    user.deleted_at = None
    db.commit()
    db.refresh(user)

    return ApiResponse(status_code=200, message="Utilisateur restauré avec succès", data=user)


# ---------- HARD DELETE ----------
@router.delete("/{user_id}/hard", response_model=ApiResponse[None])
def hard_delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    db.delete(user)  # supprime aussi ses annonces (ON DELETE CASCADE)
    db.commit()
    return ApiResponse(status_code=200, message="Utilisateur supprimé définitivement (et ses annonces)", data=None)


# ---------- GET ALL SOFT DELETED ----------
@router.get("/deleted/all", response_model=ApiResponse[list[UserResponse]])
def get_all_soft_deleted_users(db: Session = Depends(get_db)):
    users = db.execute(select(User).where(User.is_deleted == True)).scalars().all()
    return ApiResponse(status_code=200, message=f"{len(users)} utilisateur(s) supprimé(s)", data=users)


# ---------- LISTINGS D'UN USER (relation) ----------
@router.get("/{user_id}/listings", response_model=ApiResponse[list[ListingResponse]])
def get_listings_by_user(user_id: int, db: Session = Depends(get_db)):
    user = get_active_or_404(User, user_id, db, "Utilisateur")

    listings = db.execute(
        select(Listing).where(Listing.user_id == user_id, Listing.is_deleted == False)
    ).scalars().all()

    return ApiResponse(status_code=200, message=f"{len(listings)} annonce(s) trouvée(s)", data=listings)