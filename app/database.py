from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings


def _make_engine():
    url = settings.DATABASE_URL
    is_sqlite = url.startswith("sqlite")
    kwargs = {"pool_pre_ping": True}
    if is_sqlite:
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_size"] = 5
        kwargs["max_overflow"] = 10
    return create_engine(url, **kwargs)


engine = _make_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables – called at app startup."""
    from app.models import (  # noqa: F401
        user, account, transaction, reconciliation,
        forecast, tax_match, alert, ai_insight, settings as settings_model,
    )
    Base.metadata.create_all(bind=engine)
