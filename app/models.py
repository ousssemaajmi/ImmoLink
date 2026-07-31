from sqlalchemy import (
    Column, Integer, String, Text, Numeric, BigInteger, Boolean, ForeignKey, TIMESTAMP, ARRAY
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    full_name = Column(String(255))

    is_deleted = Column(Boolean, nullable=False, default=False)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    listings = relationship("Listing", back_populates="owner", cascade="all, delete")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, unique=True)
    slug = Column(String(140), nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    listings = relationship("Listing", back_populates="category")


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    listing_type = Column(String(40), nullable=False, default="classified")
    price = Column(Numeric(12, 2))
    currency = Column(String(3), nullable=False, default="EUR")
    location = Column(String(255))
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))
    tags = Column(ARRAY(Text), nullable=False, default=list)
    status = Column(String(30), nullable=False, default="draft")
    view_count = Column(BigInteger, nullable=False, default=0)

    is_deleted = Column(Boolean, nullable=False, default=False)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    owner = relationship("User", back_populates="listings")
    category = relationship("Category", back_populates="listings")