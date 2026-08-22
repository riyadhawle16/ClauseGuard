"""
Indexing service.

Orchestrates generating embeddings for extracted clauses and
storing them in the Chroma vector store.

Called by processing_service after clauses are saved to PostgreSQL.
"""
import logging
from typing import List, Optional

from app.models.clause import Clause
from app.services import embedding_service, vector_store_service

logger = logging.getLogger(__name__)


def _clause_to_embed_text(clause: Clause) -> str:
    """
    Build the text to embed for a clause.
    If a heading exists, prepend it so the embedding captures section context.
    """
    if clause.heading:
        return f"{clause.heading}\n{clause.content}"
    return clause.content


def index_clauses(
    clauses: List[Clause],
    document_id: str,
    persist_directory: Optional[str] = None,
) -> int:
    """
    Generate embeddings for all clauses and store them in Chroma.

    Returns the number of vectors stored.
    Raises on failure — caller (processing_service) handles cleanup.
    """
    if not clauses:
        logger.warning("index_clauses called with empty clause list for document %s", document_id)
        return 0

    texts = [_clause_to_embed_text(c) for c in clauses]
    embeddings = embedding_service.embed_texts(texts)

    clause_ids = [str(c.id) for c in clauses]
    metadatas = []
    for clause in clauses:
        meta: dict = {
            "document_id": str(document_id),
            "clause_id": str(clause.id),
            "clause_number": clause.clause_number,
            "page_number": clause.page_number,
        }
        if clause.heading:
            meta["heading"] = clause.heading
        metadatas.append(meta)

    vector_store_service.add_clause_embeddings(
        document_id=document_id,
        clause_ids=clause_ids,
        embeddings=embeddings,
        metadatas=metadatas,
        persist_directory=persist_directory,
    )

    logger.info("Indexed %d clause(s) for document %s", len(clauses), document_id)
    return len(clauses)


def delete_document_index(
    document_id: str,
    persist_directory: Optional[str] = None,
) -> None:
    """Remove all vectors for a document from Chroma."""
    vector_store_service.delete_document_embeddings(document_id, persist_directory)
