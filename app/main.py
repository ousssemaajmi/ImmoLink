from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import engine, get_db, Base
from app.models import Annonce
from app.validate import AnnonceCreate, AnnonceResponse, ApiResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ImmoLink API")


# Gestion uniforme des erreurs HTTPException (404, etc.)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "message": exc.detail,
            "data": None,
        },
    )


@app.get("/")
def root():
    return {"message": "ImmoLink API en ligne"}


# CREATE
@app.post("/annonces", response_model=ApiResponse[AnnonceResponse])
def create_annonce(annonce: AnnonceCreate, db: Session = Depends(get_db)):
    nouvelle_annonce = Annonce(**annonce.model_dump())
    db.add(nouvelle_annonce)
    db.commit()
    db.refresh(nouvelle_annonce)
    return ApiResponse(
        status_code=201,
        message="Annonce créée avec succès",
        data=nouvelle_annonce,
    )


# READ (liste)
@app.get("/annonces", response_model=ApiResponse[list[AnnonceResponse]])
def list_annonces(db: Session = Depends(get_db)):
    annonces = db.execute(select(Annonce)).scalars().all()
    return ApiResponse(
        status_code=200,
        message=f"{len(annonces)} annonce(s) trouvée(s)",
        data=annonces,
    )


# READ (une seule)
@app.get("/annonces/{annonce_id}", response_model=ApiResponse[AnnonceResponse])
def get_annonce(annonce_id: int, db: Session = Depends(get_db)):
    annonce = db.get(Annonce, annonce_id)
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce introuvable")
    return ApiResponse(
        status_code=200,
        message="Annonce récupérée avec succès",
        data=annonce,
    )


# UPDATE
@app.put("/annonces/{annonce_id}", response_model=ApiResponse[AnnonceResponse])
def update_annonce(annonce_id: int, updated: AnnonceCreate, db: Session = Depends(get_db)):
    annonce = db.get(Annonce, annonce_id)
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce introuvable")

    for key, value in updated.model_dump().items():
        setattr(annonce, key, value)

    db.commit()
    db.refresh(annonce)
    return ApiResponse(
        status_code=200,
        message="Annonce mise à jour avec succès",
        data=annonce,
    )


# DELETE
@app.delete("/annonces/{annonce_id}", response_model=ApiResponse[None])
def delete_annonce(annonce_id: int, db: Session = Depends(get_db)):
    annonce = db.get(Annonce, annonce_id)
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce introuvable")

    db.delete(annonce)
    db.commit()
    return ApiResponse(
        status_code=200,
        message="Annonce supprimée avec succès",
        data=None,
    )