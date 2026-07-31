from pydantic import BaseModel, EmailStr
from datetime import datetime
from decimal import Decimal
from typing import Optional, Generic, TypeVar, List

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    status_code: int
    message: str
    data: Optional[T] = None


# ---------- USER ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]

    class Config:
        from_attributes = True


# ---------- LISTING ----------
class ListingCreate(BaseModel):
    user_id: int
    category_id: int
    title: str
    description: str
    listing_type: str = "classified"
    price: Optional[Decimal] = None
    currency: str = "EUR"
    location: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    tags: List[str] = []
    status: str = "draft"


class ListingUpdate(BaseModel):
    category_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    listing_type: Optional[str] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


class ListingResponse(BaseModel):
    id: int
    user_id: int
    category_id: int
    title: str
    description: str
    listing_type: str
    price: Optional[Decimal]
    currency: str
    location: Optional[str]
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    tags: List[str]
    status: str
    view_count: int
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]

    class Config:
        from_attributes = True