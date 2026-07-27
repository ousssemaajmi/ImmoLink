from elasticsearch import Elasticsearch
import os

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
es_client = Elasticsearch(ELASTICSEARCH_URL)

INDEX_NAME = "annonces"


def index_annonce(annonce):
    """Indexe (ou met à jour) une annonce dans Elasticsearch."""
    es_client.index(
        index=INDEX_NAME,
        id=annonce.id,
        document={
            "titre": annonce.titre,
            "description": annonce.description,
            "prix": annonce.prix,
            "ville": annonce.ville,
            "is_deleted": annonce.is_deleted,
        },
    )


def delete_annonce_from_index(annonce_id: int):
    """Supprime une annonce de l'index ES (hard delete)."""
    es_client.delete(index=INDEX_NAME, id=annonce_id, ignore=[404])