from typing import List
from sqlalchemy.orm import Session
from app.models.missing_info_flag import MissingInfoFlag


def create_flags_bulk(db: Session, flags: List[MissingInfoFlag]) -> None:
    db.add_all(flags)
    db.commit()


def get_flags_by_document(db: Session, document_id: str) -> List[MissingInfoFlag]:
    return (
        db.query(MissingInfoFlag)
        .filter(MissingInfoFlag.document_id == str(document_id))
        .order_by(MissingInfoFlag.category)
        .all()
    )


def delete_flags_by_document(db: Session, document_id: str) -> int:
    count = (
        db.query(MissingInfoFlag)
        .filter(MissingInfoFlag.document_id == str(document_id))
        .delete(synchronize_session=False)
    )
    db.commit()
    return count
