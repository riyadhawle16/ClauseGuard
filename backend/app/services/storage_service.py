"""
Storage service abstraction for uploaded PDF files.

All filesystem operations are isolated here so the document API
does not manipulate paths directly. Replacing this with cloud
storage (S3, GCS, etc.) in the future only requires changing
this module.
"""
import os
from pathlib import Path
from app.config import get_settings

settings = get_settings()


def _uploads_dir() -> Path:
    """Return the configured upload directory, creating it if needed."""
    path = Path(settings.UPLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_upload(document_id: str, file_bytes: bytes) -> None:
    """Persist uploaded PDF bytes under a safe, UUID-based filename."""
    dest = _uploads_dir() / f"{document_id}.pdf"
    dest.write_bytes(file_bytes)


def load_upload(document_id: str) -> bytes:
    """Load the raw bytes of a stored PDF. Raises FileNotFoundError if missing."""
    src = _uploads_dir() / f"{document_id}.pdf"
    return src.read_bytes()


def delete_upload(document_id: str) -> bool:
    """
    Remove the stored PDF for a document.
    Returns True if the file existed and was deleted, False otherwise.
    """
    path = _uploads_dir() / f"{document_id}.pdf"
    if path.exists():
        path.unlink()
        return True
    return False


def upload_exists(document_id: str) -> bool:
    """Return True if a stored PDF exists for the given document ID."""
    path = _uploads_dir() / f"{document_id}.pdf"
    return path.exists()
