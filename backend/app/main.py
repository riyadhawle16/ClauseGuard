import logging
import os
import sys
import threading
import uuid

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import get_settings
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.chat import router as chat_router
from app.api.attention import router as attention_router
from app.api.missing_info import router as missing_info_router
from app.dependencies import get_db
from app.models.user import User

_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
)
logging.basicConfig(level=logging.INFO, handlers=[_handler], force=True)
for _logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    _uvicorn_logger = logging.getLogger(_logger_name)
    _uvicorn_logger.handlers.clear()
    _uvicorn_logger.propagate = True
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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Safety net: return JSON (not plain-text) for any unhandled exception."""
    logger.exception(
        "Unhandled exception on %s %s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


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

    def _preload_embedding_model() -> None:
        try:
            from app.services.embedding_service import preload_embedding_model
            preload_embedding_model()
            logger.warning("Embedding model preloaded successfully.")
        except Exception:
            logger.exception("Embedding model preload failed")

    threading.Thread(target=_preload_embedding_model, daemon=True).start()


@app.get("/health")
def health_check():
    """Health check — returns CORS origins for production verification."""
    return {
        "status": "ok",
        "cors_origins": origins,
    }


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    """
    Database diagnostic — verifies connectivity and that user INSERT works.
    Uses a rolled-back savepoint so no test data is persisted.
    """
    from app.services.auth_service import hash_password

    try:
        db.execute(text("SELECT 1"))
        user_count = db.query(User).count()

        insert_ok = True
        insert_error = None
        savepoint = db.begin_nested()
        try:
            probe = User(
                email=f"__probe_{uuid.uuid4()}@probe.invalid",
                password_hash=hash_password("__health_probe__"),
            )
            db.add(probe)
            db.flush()
        except Exception as exc:
            insert_ok = False
            insert_error = f"{type(exc).__name__}: {exc}"
        finally:
            savepoint.rollback()

        payload = {
            "status": "ok" if insert_ok else "degraded",
            "db_connected": True,
            "user_count": user_count,
            "insert_probe": insert_ok,
        }
        if insert_error:
            payload["insert_error"] = insert_error
        return payload
    except Exception as exc:
        logger.exception("Database health check failed")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "db_connected": False,
                "error": f"{type(exc).__name__}: {exc}",
            },
        )
