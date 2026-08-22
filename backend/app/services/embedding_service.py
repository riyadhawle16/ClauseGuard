"""
Embedding service.

Loads the sentence-transformers model once as a module-level singleton
and exposes a simple encode function.

Model: all-MiniLM-L6-v2
- 384-dimensional vectors
- Fast, lightweight, no API key required
- Good semantic similarity for English text
"""
import logging
from typing import List

logger = logging.getLogger(__name__)

# Module-level singleton — loaded once, reused for all requests.
# Wrapped in a lazy loader so import of this module does not trigger
# the (slow) model download during tests unless explicitly needed.
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        from app.config import get_settings
        settings = get_settings()
        model_name = settings.EMBEDDING_MODEL
        logger.info("Loading embedding model: %s", model_name)
        _model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded.")
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of text strings.
    Returns a list of float vectors, one per input text.
    """
    model = _get_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return [emb.tolist() for emb in embeddings]


def embed_text(text: str) -> List[float]:
    """Generate an embedding for a single text string."""
    return embed_texts([text])[0]


def get_embedding_dimension() -> int:
    """Return the vector dimension of the loaded model."""
    model = _get_model()
    return model.get_sentence_embedding_dimension()
