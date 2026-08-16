import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.dependencies import get_db
from app.database.database import Base
from app.main import app

# Isolated SQLite in-memory database configuration for unit tests
TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="function")
def db_session():
    """Fixture that creates clean database tables for each test and rolls back changes."""
    Base.metadata.create_all(bind=engine_test)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def client(db_session):
    """Fixture providing a FastAPI TestClient configured with isolated test DB dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_headers(client):
    """Fixture registering user1 and returning Bearer Authorization header."""
    user_payload = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "Password123"
    }
    client.post("/api/v1/auth/register", json=user_payload)
    
    login_payload = {
        "username": "testuser",
        "password": "Password123"
    }
    response = client.post("/api/v1/auth/login", data=login_payload)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def second_auth_headers(client):
    """Fixture registering user2 and returning Bearer Authorization header (for ownership tests)."""
    user_payload = {
        "username": "otheruser",
        "email": "otheruser@example.com",
        "password": "Password123"
    }
    client.post("/api/v1/auth/register", json=user_payload)
    
    login_payload = {
        "username": "otheruser",
        "password": "Password123"
    }
    response = client.post("/api/v1/auth/login", data=login_payload)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
