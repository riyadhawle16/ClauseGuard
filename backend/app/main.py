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
# CORS_ORIGINS is a comma-separated string in the environment variable.
# We parse it here at module load time (when uvicorn starts).
# On Render, environment variables are injected BEFORE the Python process starts,
# so this is safe and will always read the correct production value.
#
# The production Vercel URL is also added as a hardcoded safety net to ensure
# it is always allowed even if CORS_ORIGINS is misconfigured on Render.
_PRODUCTION_VERCEL_URL = "https://clause-guard-ruddy.vercel.app"

_raw_origins = os.environ.get("CORS_ORIGINS", settings.CORS_ORIGINS).strip()
if _raw_origins:
    origins = [o.strip().rstrip("/") for o in _raw_origins.split(",") if o.strip()]
else:
    origins = ["http://localhost:5173"]

# Always include the production Vercel URL
if _PRODUCTION_VERCEL_URL not in origins:
    origins.append(_PRODUCTION_VERCEL_URL)

# SAFE startup log — never logs secrets
logger.info("ClauseGuard starting | CORS allowed origins: %s", origins)

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="ClauseGuard API",
    description="AI-powered rental agreement analysis platform",
    version="0.1.0",
)

# Middleware MUST be added before the app starts (not inside a startup event)
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
    Automatically apply all pending Alembic migrations when the server starts.
    Also logs the active CORS origins so they are visible in Render logs.
    """
    # Log CORS origins at startup so they appear in Render logs
    # SAFE — never logs secrets (DATABASE_URL, JWT_SECRET_KEY, GROQ_API_KEY)
    logger.warning("=== ClauseGuard startup ===")
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
        logger.info("Database migrations applied successfully.")
    except Exception as exc:
        logger.error("Migration failed on startup: %s", exc)


@app.get("/health")
def health_check():
    """Health check — also returns active CORS origins for verification."""
    return {
        "status": "ok",
        "cors_origins": origins,  # shows what origins are actually active
    }
