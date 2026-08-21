import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# ── Set test env vars BEFORE any app import ──────────────────────────────────
os.environ["DATABASE_URL"] = "sqlite:///./test_clauseguard.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["UPLOAD_DIR"] = "test_uploads"

# Import all models so Base.metadata knows about every table
import app.models  # noqa: F401, E402

from app.main import app as fastapi_app  # noqa: E402
from app.database import Base  # noqa: E402
from app.dependencies import get_db  # noqa: E402

# Use in-memory SQLite so each test session starts completely clean
SQLALCHEMY_TEST_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
)

# Keep the same connection alive for the whole session so in-memory tables persist
connection = engine.connect()
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)

# Create all tables once at module load time
Base.metadata.create_all(bind=connection)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def override_db():
    """Override the DB dependency and clean all table data between tests."""
    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield
    # Truncate all tables so each test starts with a clean slate
    for table in reversed(Base.metadata.sorted_tables):
        connection.execute(table.delete())
    connection.commit()
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client():
    with TestClient(fastapi_app) as c:
        yield c


@pytest.fixture
def tmp_uploads(tmp_path, monkeypatch):
    """
    Redirect file storage to a temporary directory for each test.
    Ensures tests are isolated and don't leave files on disk.
    """
    upload_dir = str(tmp_path / "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    import app.config as cfg
    monkeypatch.setattr(cfg.get_settings(), "UPLOAD_DIR", upload_dir)

    yield upload_dir
