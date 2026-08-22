from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.chat import router as chat_router
from app.api.attention import router as attention_router
from app.api.missing_info import router as missing_info_router

settings = get_settings()

app = FastAPI(
    title="ClauseGuard API",
    description="AI-powered rental agreement analysis platform",
    version="0.1.0",
)

origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(attention_router, prefix="/api/v1")
app.include_router(missing_info_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
