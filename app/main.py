from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import engine, get_db, Base
from app.models import Annonce
from app.validate import AnnonceCreate, AnnonceResponse

# Crée les tables dans Postgres si elles n'existent pas encore
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ImmoLink API")


@app.get("/")
def root():
    return {"message": "ImmoLink API en ligne"}


# CREATE
@app.post("/annonces", response_model=AnnonceResponse)
def create_annonce(annonce: AnnonceCreate, db: Session = Depends(get_db)):
    nouvelle_annonce = Annonce(**annonce.model_dump())
    db.add(nouvelle_annonce)
    db.commit()
    db.refresh(nouvelle_annonce)
    return nouvelle_annonce


# READ (liste)
@app.get("/annonces", response_model=list[AnnonceResponse])
def list_annonces(db: Session = Depends(get_db)):
    return db.execute(select(Annonce)).scalars().all()


# READ (une seule)
@app.get("/annonces/{annonce_id}", response_model=AnnonceResponse)
def get_annonce(annonce_id: int, db: Session = Depends(get_db)):
    annonce = db.get(Annonce, annonce_id)
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce introuvable")
    return annonce


# UPDATE
@app.put("/annonces/{annonce_id}", response_model=AnnonceResponse)
def update_annonce(annonce_id: int, updated: AnnonceCreate, db: Session = Depends(get_db)):
    annonce = db.get(Annonce, annonce_id)
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce introuvable")

    for key, value in updated.model_dump().items():
        setattr(annonce, key, value)

    db.commit()
    db.refresh(annonce)
    return annonce


# DELETE
@app.delete("/annonces/{annonce_id}")
def delete_annonce(annonce_id: int, db: Session = Depends(get_db)):
    annonce = db.get(Annonce, annonce_id)
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce introuvable")

    db.delete(annonce)
    db.commit()
    return {"message": "Annonce supprimée"}