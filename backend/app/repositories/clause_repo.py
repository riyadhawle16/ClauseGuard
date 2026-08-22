from typing import List
from sqlalchemy.orm import Session
from app.models.clause import Clause


def create_clauses_bulk(db: Session, clauses: List[Clause]) -> None:
    """Insert a list of Clause ORM objects in one transaction."""
    db.add_all(clauses)
    db.commit()


def get_clauses_by_document(db: Session, document_id: str) -> List[Clause]:
    """Return all clauses for a document, ordered by clause_number."""
    return (
        db.query(Clause)
        .filter(Clause.document_id == str(document_id))
        .order_by(Clause.clause_number)
        .all()
    )


def delete_clauses_by_document(db: Session, document_id: str) -> int:
    """Delete all clauses for a document. Returns the count deleted."""
    count = (
        db.query(Clause)
        .filter(Clause.document_id == str(document_id))
        .delete(synchronize_session=False)
    )
    db.commit()
    return count


def count_clauses_by_document(db: Session, document_id: str) -> int:
    return db.query(Clause).filter(Clause.document_id == str(document_id)).count()
