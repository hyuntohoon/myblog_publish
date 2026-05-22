import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.publish import router as publish_router

logger = logging.getLogger(__name__)

APP_ENV = os.getenv("APP_ENV", "prod")

if APP_ENV == "dev":
    try:
        from dotenv import load_dotenv
        load_dotenv(".env")
    except Exception:
        pass

FRONT_ORIGIN = os.getenv("FRONT_ORIGIN", "http://localhost:4321")
EDGE_SECRET = os.getenv("EDGE_SECRET", "")
PUBLIC_PATHS = {"/health"}

app = FastAPI(title="Publisher API")

allow_origins = [FRONT_ORIGIN]
if APP_ENV == "dev":
    allow_origins += ["http://localhost:4321", "http://127.0.0.1:4321"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "x-origin-verify"],
)


@app.middleware("http")
async def edge_guard(request: Request, call_next):
    if APP_ENV == "dev":
        return await call_next(request)

    if request.method == "OPTIONS":
        return await call_next(request)

    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    if request.headers.get("x-origin-verify") != EDGE_SECRET:
        logger.warning("Forbidden request to %s from %s", request.url.path, request.client.host)
        raise HTTPException(status_code=403, detail="Forbidden")

    return await call_next(request)


@app.get("/health")
def health():
    return {"ok": True, "env": APP_ENV}


app.include_router(publish_router, prefix="/api/publish", tags=["publish"])

try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = None
