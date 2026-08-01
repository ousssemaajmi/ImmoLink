from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from sqlalchemy.sql import func
from elasticsearch import NotFoundError

from app.database import get_db
from app.models import User, Listing, Category
from app.utils import get_active_or_404, get_deleted_or_404
from app.validate import ListingCreate, ListingUpdate, ListingResponse, ListingSearchResult, ApiResponse
from app.elasticsearch_client import es_client, index_listing, delete_listing_from_index, LISTINGS_INDEX

router = APIRouter(prefix="/listings", tags=["Listings"])


def _listing_query():
    """Requête de base qui charge automatiquement owner et category."""
    return select(Listing).options(joinedload(Listing.owner), joinedload(Listing.category))


# ---------- CREATE ----------
@router.post("", response_model=ApiResponse[ListingResponse], status_code=status.HTTP_201_CREATED)
def create_listing(listing: ListingCreate, db: Session = Depends(get_db)):
    user = db.get(User, listing.user_id)
    if not user or user.is_deleted:
        raise HTTPException(status_code=400, detail="user_id invalide : utilisateur introuvable ou supprimé")

    category = db.get(Category, listing.category_id)
    if not category:
        raise HTTPException(status_code=400, detail="category_id invalide : catégorie introuvable")

    nouvelle_annonce = Listing(**listing.model_dump())
    db.add(nouvelle_annonce)
    db.commit()
    db.refresh(nouvelle_annonce)

    index_listing(nouvelle_annonce)

    return ApiResponse(status_code=201, message="Annonce créée avec succès", data=nouvelle_annonce)


# ---------- GET ALL (actives) ----------
@router.get("", response_model=ApiResponse[list[ListingResponse]])
def get_all_listings(db: Session = Depends(get_db)):
    listings = db.execute(
        _listing_query().where(Listing.is_deleted == False)
    ).unique().scalars().all()
    return ApiResponse(status_code=200, message=f"{len(listings)} annonce(s) trouvée(s)", data=listings)


# ---------- GET BY ID ----------
@router.get("/{listing_id}", response_model=ApiResponse[ListingResponse])
def get_listing_by_id(listing_id: int, db: Session = Depends(get_db)):
    listing = db.execute(
        _listing_query().where(Listing.id == listing_id, Listing.is_deleted == False)
    ).unique().scalar_one_or_none()

    if not listing:
        raise HTTPException(status_code=404, detail="Annonce introuvable")

    return ApiResponse(status_code=200, message="Annonce récupérée avec succès", data=listing)


# ---------- UPDATE (PATCH) ----------
@router.patch("/{listing_id}", response_model=ApiResponse[ListingResponse])
def update_listing(listing_id: int, updated: ListingUpdate, db: Session = Depends(get_db)):
    listing = get_active_or_404(Listing, listing_id, db, "Annonce")

    donnees = updated.model_dump(exclude_unset=True)
    if not donnees:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

    if "category_id" in donnees:
        category = db.get(Category, donnees["category_id"])
        if not category:
            raise HTTPException(status_code=400, detail="category_id invalide : catégorie introuvable")

    for key, value in donnees.items():
        setattr(listing, key, value)

    db.commit()
    db.refresh(listing)

    index_listing(listing)

    return ApiResponse(status_code=200, message="Annonce mise à jour avec succès", data=listing)


# ---------- SOFT DELETE ----------
@router.delete("/{listing_id}/soft", response_model=ApiResponse[ListingResponse])
def soft_delete_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = get_active_or_404(Listing, listing_id, db, "Annonce")

    listing.is_deleted = True
    listing.deleted_at = func.now()
    db.commit()
    db.refresh(listing)

    index_listing(listing)

    return ApiResponse(status_code=200, message="Annonce supprimée (soft delete)", data=listing)


# ---------- RESTORE ----------
@router.post("/{listing_id}/restore", response_model=ApiResponse[ListingResponse])
def restore_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = get_deleted_or_404(Listing, listing_id, db, "Annonce")

    listing.is_deleted = False
    listing.deleted_at = None
    db.commit()
    db.refresh(listing)

    index_listing(listing)

    return ApiResponse(status_code=200, message="Annonce restaurée avec succès", data=listing)


# ---------- HARD DELETE (seulement si déjà soft deleted) ----------
@router.delete("/{listing_id}/hard", response_model=ApiResponse[None])
def hard_delete_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Annonce introuvable")

    if not listing.is_deleted:
        raise HTTPException(
            status_code=400,
            detail="Cette annonce doit d'abord être soft delete avant suppression définitive",
        )

    db.delete(listing)
    db.commit()

    delete_listing_from_index(listing_id)

    return ApiResponse(status_code=200, message="Annonce supprimée définitivement", data=None)


# ---------- GET ALL SOFT DELETED ----------
@router.get("/deleted/all", response_model=ApiResponse[list[ListingResponse]])
def get_all_soft_deleted_listings(db: Session = Depends(get_db)):
    listings = db.execute(
        _listing_query().where(Listing.is_deleted == True)
    ).unique().scalars().all()
    return ApiResponse(status_code=200, message=f"{len(listings)} annonce(s) supprimée(s)", data=listings)


# ---------- SEARCH (Elasticsearch) ----------
@router.get("/search/query", response_model=ApiResponse[list[ListingSearchResult]])
def search_listings(q: str):
    try:
        result = es_client.search(
            index=LISTINGS_INDEX,
            query={
                "bool": {
                    "must": [{
                        "multi_match": {
                            "query": q,
                            "fields": ["title", "description", "location"],
                        }
                    }],
                    "filter": [{"term": {"is_deleted": False}}],
                }
            },
        )
    except NotFoundError:
        return ApiResponse(status_code=200, message="0 résultat(s) trouvé(s)", data=[])

    hits = [hit["_source"] | {"id": int(hit["_id"])} for hit in result["hits"]["hits"]]
    return ApiResponse(status_code=200, message=f"{len(hits)} résultat(s) trouvé(s)", data=hits)