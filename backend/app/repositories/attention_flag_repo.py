from typing import List
from sqlalchemy.orm import Session
from app.models.attention_flag import AttentionFlag


def create_flags_bulk(db: Session, flags: List[AttentionFlag]) -> None:
    db.add_all(flags)
    db.commit()


def get_flags_by_document(db: Session, document_id: str) -> List[AttentionFlag]:
    return (
        db.query(AttentionFlag)
        .filter(AttentionFlag.document_id == str(document_id))
        .order_by(AttentionFlag.created_at)
        .all()
    )


def delete_flags_by_document(db: Session, document_id: str) -> int:
    count = (
        db.query(AttentionFlag)
        .filter(AttentionFlag.document_id == str(document_id))
        .delete(synchronize_session=False)
    )
    db.commit()
    return count


def count_flags_by_document(db: Session, document_id: str) -> int:
    return (
        db.query(AttentionFlag)
        .filter(AttentionFlag.document_id == str(document_id))
        .count()
    )
