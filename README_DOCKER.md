# ImmoLink Docker

Stack locale pour une plateforme d'annonces avec:

- FastAPI sur http://localhost:8000
- Postgres sur localhost:5432
- Elasticsearch sur http://localhost:9200
- Redis sur localhost:6379

## Lancer le projet

```powershell
docker compose up --build
```

Docs FastAPI:

```text
http://localhost:8000/docs
```

## Arreter

```powershell
docker compose down
```

## Reinitialiser les donnees

Cette commande supprime les volumes Postgres, Redis et Elasticsearch.

```powershell
docker compose down -v
docker compose up --build
```

## Connexions internes

Depuis le conteneur `api`, utilise ces URLs:

```text
DATABASE_URL=postgresql://immolink:immolink_password@postgres:5432/immolink
REDIS_URL=redis://redis:6379/0
ELASTICSEARCH_URL=http://elasticsearch:9200
```

Le fichier `docker/postgres/init.sql` cree les tables `users`, `categories` et `listings`.
