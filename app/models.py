from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Annonce(Base):
    __tablename__ = "annonces"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String, nullable=False)
    description = Column(String)
    prix = Column(Float, nullable=False)
    ville = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())