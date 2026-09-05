"""
conftest.py – Patch database BEFORE any app import so startup uses SQLite not PostgreSQL.
"""
import os
import pytest

# ── Patch env to use SQLite before any app code runs ──────────────────────
os.environ["DATABASE_URL"] = "sqlite:///./test_financeai.db"

from sqlalchemy import create_engine                           # noqa: E402
from sqlalchemy.orm import sessionmaker                        # noqa: E402
import app.database as db_module                              # noqa: E402

TEST_DB_URL = "sqlite:///./test_financeai.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Patch the module-level engine used by the app
db_module.engine = test_engine
db_module.SessionLocal = TestSession

from app.database import Base, get_db  # noqa: E402
from app.main import app               # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    from app.models import (  # noqa
        user, account, transaction, reconciliation,
        forecast, tax_match, alert, ai_insight, settings
    )
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    if os.path.exists("test_financeai.db"):
        try:
            os.remove("test_financeai.db")
        except PermissionError:
            pass


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    client.post("/api/auth/register", json={
        "name": "Test User", "email": "test@test.com", "password": "testpass123"
    })
    r = client.post("/api/auth/login", json={
        "email": "test@test.com", "password": "testpass123"
    })
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
