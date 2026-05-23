import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.publish import router as publish_router
from app.core.config import settings

logger = logging.getLogger(__name__)

PUBLIC_PATHS = {"/health"}

app = FastAPI(title="Publisher API")

allow_origins = [settings.FRONT_ORIGIN]
if settings.APP_ENV == "dev":
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
    if settings.APP_ENV == "dev":
        return await call_next(request)

    if request.method == "OPTIONS":
        return await call_next(request)

    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    if request.headers.get("x-origin-verify") != settings.EDGE_SECRET:
        client_ip = request.client.host if request.client else "unknown"
        logger.warning("Forbidden request to %s from %s", request.url.path, client_ip)
        raise HTTPException(status_code=403, detail="Forbidden")

    return await call_next(request)


@app.get("/health")
def health():
    return {"ok": True, "env": settings.APP_ENV}


app.include_router(publish_router, prefix="/api/publish", tags=["publish"])

try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = None
