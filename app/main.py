from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.sql import func

from app.database import engine, get_db, Base
from app.models import Annonce
from app.validate import AnnonceCreate, AnnonceUpdate, AnnonceResponse, ApiResponse
from app.elasticsearch_client import es_client, index_annonce, delete_annonce_from_index, INDEX_NAME

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ImmoLink API")


# ---------- Gestion uniforme des erreurs ----------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status_code": exc.status_code, "message": exc.detail, "data": None},
    )


@app.get("/")
def root():
    return {"message": "ImmoLink API en ligne"}


# ---------- CREATE ----------
@app.post("/annonces", response_model=ApiResponse[AnnonceResponse], status_code=status.HTTP_201_CREATED)
def create_annonce(annonce: AnnonceCreate, db: Session = Depends(get_db)):
    nouvelle_annonce = Annonce(**annonce.model_dump())
    db.add(nouvelle_annonce)
    db.commit()
    db.refresh(nouvelle_annonce)

    index_annonce(nouvelle_annonce)

    return ApiResponse(status_code=201, message="Annonce créée avec succès", data=nouvelle_annonce)


# ---------- GET ALL (actives uniquement) ----------
@app.get("/annonces", response_model=ApiResponse[list[AnnonceResponse]])
def get_all_annonces(db: Session = Depends(get_db)):
    annonces = db.execute(
        select(Annonce).where(Annonce.is_deleted == False)
    ).scalars().all()
    return ApiResponse(status_code=200, message=f"{len(annonces)} annonce(s) trouvée(s)", data=annonces)


# ---------- GET BY ID ----------
@app.get("/annonces/{annonce_id}", response_model=ApiResponse[AnnonceResponse])
def get_by_id(annonce_id: int, db: Session = Depends(get_db)):
    annonce = db.get(Annonce, annonce_id)
    if not annonce or annonce.is_deleted:
        raise HTTPException(status_code=404, detail="Annonce introuvable")
    return ApiResponse(status_code=200, message="Annonce récupérée avec succès", data=annonce)


# ---------- UPDATE (PATCH = partiel) ----------
@app.patch("/annonces/{annonce_id}", response_model=ApiResponse[AnnonceResponse])
def update_annonce(annonce_id: int, updated: AnnonceUpdate, db: Session = Depends(get_db)):
    annonce = db.get(Annonce, annonce_id)
    if not annonce or annonce.is_deleted:
        raise HTTPException(status_code=404, detail="Annonce introuvable")

    donnees_a_modifier = updated.model_dump(exclude_unset=True)

    if not donnees_a_modifier:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

    for key, value in donnees_a_modifier.items():
        setattr(annonce, key, value)

    db.commit()
    db.refresh(annonce)
    index_annonce(annonce)

    return ApiResponse(status_code=200, message="Annonce mise à jour avec succès", data=annonce)


# ---------- SOFT DELETE ----------
@app.delete("/annonces/{annonce_id}/soft", response_model=ApiResponse[AnnonceResponse])
def soft_delete(annonce_id: int, db: Session = Depends(get_db)):
    annonce = db.get(Annonce, annonce_id)
    if not annonce or annonce.is_deleted:
        raise HTTPException(status_code=404, detail="Annonce introuvable")

    annonce.is_deleted = True
    annonce.deleted_at = func.now()
    db.commit()
    db.refresh(annonce)

    index_annonce(annonce)

    return ApiResponse(status_code=200, message="Annonce supprimée (soft delete)", data=annonce)


# ---------- RESTORE ----------
@app.post("/annonces/{annonce_id}/restore", response_model=ApiResponse[AnnonceResponse])
def restore_annonce(annonce_id: int, db: Session = Depends(get_db)):
    annonce = db.get(Annonce, annonce_id)
    if not annonce or not annonce.is_deleted:
        raise HTTPException(status_code=404, detail="Annonce introuvable ou déjà active")

    annonce.is_deleted = False
    annonce.deleted_at = None
    db.commit()
    db.refresh(annonce)

    index_annonce(annonce)

    return ApiResponse(status_code=200, message="Annonce restaurée avec succès", data=annonce)


# ---------- HARD DELETE ----------
@app.delete("/annonces/{annonce_id}/hard", response_model=ApiResponse[None])
def hard_delete(annonce_id: int, db: Session = Depends(get_db)):
    annonce = db.get(Annonce, annonce_id)
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce introuvable")

    db.delete(annonce)
    db.commit()

    delete_annonce_from_index(annonce_id)

    return ApiResponse(status_code=200, message="Annonce supprimée définitivement", data=None)


# ---------- GET ALL SOFT DELETED ----------
@app.get("/annonces/deleted/all", response_model=ApiResponse[list[AnnonceResponse]])
def get_all_soft_deleted(db: Session = Depends(get_db)):
    annonces = db.execute(
        select(Annonce).where(Annonce.is_deleted == True)
    ).scalars().all()
    return ApiResponse(status_code=200, message=f"{len(annonces)} annonce(s) supprimée(s)", data=annonces)


# ---------- SEARCH dans Postgres (par titre) ----------
@app.get("/annonces/search/postgres", response_model=ApiResponse[list[AnnonceResponse]])
def search_annonces_postgres(titre: str, db: Session = Depends(get_db)):
    annonces = db.execute(
        select(Annonce).where(
            Annonce.titre.ilike(f"%{titre}%"),
            Annonce.is_deleted == False,
        )
    ).scalars().all()

    return ApiResponse(status_code=200, message=f"{len(annonces)} annonce(s) trouvée(s)", data=annonces)


# ---------- SEARCH dans Elasticsearch (wildcard = contient n'importe où) ----------
@app.get("/annonces/search/query", response_model=ApiResponse[list[dict]])
def search_annonces_elasticsearch(q: str):
    result = es_client.search(
        index=INDEX_NAME,
        query={
            "bool": {
                "must": [{
                    "wildcard": {
                        "titre": {"value": f"*{q.lower()}*"}
                    }
                }],
                "filter": [{"term": {"is_deleted": False}}],
            }
        },
    )
    hits = [hit["_source"] | {"id": hit["_id"]} for hit in result["hits"]["hits"]]
    return ApiResponse(status_code=200, message=f"{len(hits)} résultat(s) trouvé(s)", data=hits)