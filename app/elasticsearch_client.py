from elasticsearch import Elasticsearch
import os

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
es_client = Elasticsearch(ELASTICSEARCH_URL)

LISTINGS_INDEX = "listings"
USERS_INDEX = "users"


# ---------- LISTINGS ----------
def index_listing(listing):
    """Indexe (ou met à jour) une annonce dans Elasticsearch."""
    es_client.index(
        index=LISTINGS_INDEX,
        id=listing.id,
        document={
            "title": listing.title,
            "description": listing.description,
            "listing_type": listing.listing_type,
            "price": float(listing.price) if listing.price is not None else None,
            "currency": listing.currency,
            "location": listing.location,
            "tags": listing.tags,
            "status": listing.status,
            "user_id": listing.user_id,
            "category_id": listing.category_id,
            "is_deleted": listing.is_deleted,
        },
    )


def delete_listing_from_index(listing_id: int):
    """Supprime une annonce de l'index ES (hard delete uniquement)."""
    es_client.delete(index=LISTINGS_INDEX, id=listing_id, ignore=[404])


# ---------- USERS ----------
def index_user(user):
    """Indexe (ou met à jour) un utilisateur dans Elasticsearch."""
    es_client.index(
        index=USERS_INDEX,
        id=user.id,
        document={
            "email": user.email,
            "full_name": user.full_name,
            "is_deleted": user.is_deleted,
        },
    )


def delete_user_from_index(user_id: int):
    """Supprime un utilisateur de l'index ES (hard delete uniquement)."""
    es_client.delete(index=USERS_INDEX, id=user_id, ignore=[404])