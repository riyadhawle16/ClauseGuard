import uuid as uuid_module
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.types import TypeDecorator, CHAR
from app.database import Base


class GUID(TypeDecorator):
    """Store UUIDs as CHAR(36) strings — matches Alembic migrations on all DBs."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid_module.UUID):
            return str(uuid_module.UUID(str(value)))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid_module.UUID):
            value = uuid_module.UUID(str(value))
        return value


class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
