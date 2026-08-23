import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.chat import router as chat_router
from app.api.attention import router as attention_router
from app.api.missing_info import router as missing_info_router

logger = logging.getLogger(__name__)

# ── Load settings ─────────────────────────────────────────────────────────────
settings = get_settings()

# ── Parse CORS origins ────────────────────────────────────────────────────────
_PRODUCTION_VERCEL_URL = "https://clause-guard-ruddy.vercel.app"

_raw_origins = os.environ.get("CORS_ORIGINS", settings.CORS_ORIGINS).strip()
if _raw_origins:
    origins = [o.strip().rstrip("/") for o in _raw_origins.split(",") if o.strip()]
else:
    origins = ["http://localhost:5173"]

if _PRODUCTION_VERCEL_URL not in origins:
    origins.append(_PRODUCTION_VERCEL_URL)

logger.info("ClauseGuard starting | CORS allowed origins: %s", origins)

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="ClauseGuard API",
    description="AI-powered rental agreement analysis platform",
    version="0.1.0",
)

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


@app.on_event("startup")
def run_migrations_on_startup():
    """
    Startup tasks:
    1. Log DB host (safe — no password)
    2. Log CORS origins
    3. Apply Alembic migrations
    """
    # Import here to get the fixed URL after postgres:// → postgresql:// correction
    from app.database import _db_url as resolved_db_url

    # Log only host+dbname, never the password
    if "@" in resolved_db_url:
        safe_db_info = resolved_db_url.split("@")[-1]
    else:
        safe_db_info = resolved_db_url[:30] + "..."

    logger.warning("=== ClauseGuard startup ===")
    logger.warning("DB host/name (safe): %s", safe_db_info)
    logger.warning("CORS allowed origins: %s", origins)

    try:
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
        alembic_cfg.set_main_option(
            "script_location",
            os.path.join(os.path.dirname(__file__), "..", "migrations"),
        )
        command.upgrade(alembic_cfg, "head")
        logger.warning("Database migrations applied successfully.")
    except Exception as exc:
        logger.error("Migration failed on startup: %s", exc)


@app.get("/health")
def health_check():
    """Health check — returns CORS origins for production verification."""
    print("HEALTH CHECK HIT", flush=True)
    return {
        "status": "ok",
        "cors_origins": origins,
    }
