from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.database import engine, Base
from app.routers import users, listings, categories

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ImmoLink API")

API_PREFIX = "/api/v1"


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status_code": exc.status_code, "message": exc.detail, "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"status_code": 422, "message": "Erreur de validation des données", "data": exc.errors()},
    )


@app.get(f"{API_PREFIX}/")
def root():
    return {"message": "ImmoLink API en ligne"}


app.include_router(users.router, prefix=API_PREFIX)
app.include_router(listings.router, prefix=API_PREFIX)
app.include_router(categories.router, prefix=API_PREFIX)