"""
Vector store service — Chroma abstraction.

All Chroma operations are isolated here. The rest of the application
never imports chromadb directly.

Collection: clauseguard_clauses
  - All documents share one collection.
  - Searches are always filtered by document_id for isolation.

Vector ID strategy:
  - Each vector is stored with a deterministic ID = str(clause_id).
  - This makes deletion and upsert idempotent and avoids duplicates.

Metadata stored per vector:
  document_id, clause_id, clause_number, page_number, heading (optional)
"""
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

COLLECTION_NAME = "clauseguard_clauses"


def _get_client(persist_directory: Optional[str] = None):
    """
    Return a Chroma client.
    If persist_directory is None, use the configured production directory.
    If persist_directory is an empty string '', use an in-memory EphemeralClient.
    """
    import chromadb
    if persist_directory == "":
        # In-memory client for tests
        return chromadb.EphemeralClient()
    if persist_directory is None:
        from app.config import get_settings
        persist_directory = get_settings().CHROMA_PERSIST_DIRECTORY
    return chromadb.PersistentClient(path=persist_directory)


def _get_collection(persist_directory: Optional[str] = None):
    client = _get_client(persist_directory)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# ── Write operations ──────────────────────────────────────────────────────────

def add_clause_embeddings(
    document_id: str,
    clause_ids: List[str],
    embeddings: List[List[float]],
    metadatas: List[Dict[str, Any]],
    persist_directory: Optional[str] = None,
) -> None:
    """
    Upsert clause embeddings into Chroma.
    Vector IDs = clause_ids (deterministic, UUID-based).
    """
    collection = _get_collection(persist_directory)
    collection.upsert(
        ids=clause_ids,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def delete_document_embeddings(
    document_id: str,
    persist_directory: Optional[str] = None,
) -> None:
    """
    Delete all vectors belonging to document_id.
    Uses metadata filter — safe and idempotent even if no vectors exist.
    """
    try:
        collection = _get_collection(persist_directory)
        results = collection.get(where={"document_id": document_id})
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            logger.info(
                "Deleted %d vector(s) for document %s", len(ids_to_delete), document_id
            )
    except Exception:
        logger.exception("Failed to delete vectors for document %s", document_id)
        raise


def count_document_embeddings(
    document_id: str,
    persist_directory: Optional[str] = None,
) -> int:
    """Return the number of vectors stored for a document."""
    try:
        collection = _get_collection(persist_directory)
        results = collection.get(where={"document_id": document_id})
        return len(results.get("ids", []))
    except Exception:
        return 0


# ── Search operations ─────────────────────────────────────────────────────────

def semantic_search(
    query_embedding: List[float],
    document_id: str,
    top_k: int = 5,
    persist_directory: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search for the top_k most semantically similar clauses within document_id.

    Returns a list of dicts, each containing:
      clause_id, clause_number, page_number, heading, content_preview, distance
    """
    collection = _get_collection(persist_directory)

    # Check if the document has any indexed vectors first
    existing = collection.get(where={"document_id": document_id})
    if not existing.get("ids"):
        return []

    n_results = min(top_k, len(existing["ids"]))

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={"document_id": document_id},
        include=["metadatas", "distances"],
    )

    hits = []
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for meta, dist in zip(metadatas, distances):
        hits.append({
            "clause_id": meta.get("clause_id", ""),
            "clause_number": meta.get("clause_number", 0),
            "page_number": meta.get("page_number", 0),
            "heading": meta.get("heading") or None,
            "distance": round(dist, 4),
        })

    return hits
