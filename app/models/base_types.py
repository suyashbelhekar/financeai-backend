"""
base_types.py
Cross-database UUID column that works on both PostgreSQL and SQLite.
PostgreSQL  → native UUID type
SQLite/other → String(36)
"""
import uuid as _uuid
from sqlalchemy import String, types
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class GUID(types.TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type when available, String(36) elsewhere.
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, _uuid.UUID):
            return _uuid.UUID(str(value))
        return value


def new_uuid():
    return str(_uuid.uuid4())
