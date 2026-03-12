from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.publish import router as publish_router
from dotenv import load_dotenv

load_dotenv(".env")

app = FastAPI(title="Publisher API")

# 필요하면 프론트 도메인만 허용하도록 바꾸세요
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(publish_router, prefix="/api/publish", tags=["publish"])

# Lambda 핸들러 (API Gateway 프록시 통합)
try:
    from mangum import Mangum
    handler = Mangum(app)
except Exception:
    handler = None
