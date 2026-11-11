import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.main import app


@pytest.fixture
def db():
    # one transaction per test, undone at the end, so the database stays clean
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    # a test client whose endpoints use the test session above
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_client(db):
    # returns a function that registers + logs in a user and gives back their own client (holding the cookie)
    app.dependency_overrides[get_db] = lambda: db
    def _make(username="alice", password="secret123"):
        c = TestClient(app)
        c.post("/api/auth/register", json={"username": username, "email": f"{username}@test.local", "password": password})
        c.post("/api/auth/login", json={"username": username, "password": password})
        return c
    yield _make
    app.dependency_overrides.clear()
