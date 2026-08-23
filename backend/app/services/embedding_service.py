"""
Embedding service.

Uses fastembed (ONNX) instead of sentence-transformers so the app fits
Render's memory limits. The model is loaded once as a module-level singleton.
"""
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

_model = None
_embedding_dimension: Optional[int] = None


def _get_model():
    global _model
    if _model is None:
        from fastembed import TextEmbedding
        from app.config import get_settings

        settings = get_settings()
        model_name = settings.EMBEDDING_MODEL
        logger.info("Loading embedding model: %s", model_name)
        _model = TextEmbedding(model_name=model_name)
        logger.info("Embedding model loaded.")
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of text strings."""
    if not texts:
        return []
    model = _get_model()
    return [vec.tolist() for vec in model.embed(texts)]


def embed_text(text: str) -> List[float]:
    """Generate an embedding for a single text string."""
    return embed_texts([text])[0]


def get_embedding_dimension() -> int:
    """Return the vector dimension of the loaded model."""
    global _embedding_dimension
    if _embedding_dimension is None:
        _embedding_dimension = len(embed_text("dimension probe"))
    return _embedding_dimension


def preload_embedding_model() -> None:
    """Warm up the embedding model (call during app startup)."""
    _get_model()
