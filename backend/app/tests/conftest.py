import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Set test env vars BEFORE any app import ──────────────────────────────────
os.environ["DATABASE_URL"] = "sqlite:///./test_clauseguard.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["UPLOAD_DIR"] = "test_uploads"
os.environ["CHROMA_PERSIST_DIRECTORY"] = ""   # signal to use ephemeral in tests

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

connection = engine.connect()
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
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
    """Redirect file storage to a per-test temp directory."""
    upload_dir = str(tmp_path / "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    import app.config as cfg
    monkeypatch.setattr(cfg.get_settings(), "UPLOAD_DIR", upload_dir)
    yield upload_dir


# ── Session-scoped shared Chroma client ──────────────────────────────────────
# A single EphemeralClient is created once per test session and injected
# into vector_store_service._get_client so all tests share the same
# in-memory vector store. Each test that uses vectors must clean up its
# own document_id entries (handled automatically by the delete fixtures).

@pytest.fixture(scope="session", autouse=True)
def shared_chroma_client():
    """
    Create one EphemeralClient for the whole test session and patch
    vector_store_service so it always uses this client (never hits disk).
    """
    import chromadb
    import app.services.vector_store_service as vs

    _client = chromadb.EphemeralClient()

    def _patched_get_client(persist_directory=None):
        return _client

    original = vs._get_client
    vs._get_client = _patched_get_client
    yield _client
    vs._get_client = original


@pytest.fixture
def mock_embed(monkeypatch):
    """
    Replace the real sentence-transformers model with a fast deterministic stub.
    Different texts produce different vectors (hash-based), so semantic
    search is testable without downloading the real model.

    The actual production code still uses the real model — this only
    applies inside the test process when this fixture is used.
    """
    import app.services.embedding_service as emb_svc

    def _fake_embed_texts(texts):
        results = []
        for text in texts:
            seed = sum(ord(c) for c in text)
            vec = [(seed * (i + 1)) % 997 / 997.0 for i in range(384)]
            results.append(vec)
        return results

    def _fake_embed_text(text):
        return _fake_embed_texts([text])[0]

    monkeypatch.setattr(emb_svc, "embed_texts", _fake_embed_texts)
    monkeypatch.setattr(emb_svc, "embed_text", _fake_embed_text)
    yield
