"""
Shared pytest fixtures for the Language Learner backend test suite.
"""
import json
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app

# ---------------------------------------------------------------------------
# In-memory SQLite database — isolated per test session
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables once for the whole test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session():
    """Provide a transactional database session that rolls back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def override_db(db_session):
    """Override the FastAPI get_db dependency with the test session."""
    def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture()
async def client(override_db):
    """Async HTTP client wired to the FastAPI app with the test DB."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Helper fixtures — pre-registered users and their tokens
# ---------------------------------------------------------------------------

USER_A = {"email": "usera@example.com", "password": "passwordA1"}
USER_B = {"email": "userb@example.com", "password": "passwordB1"}


@pytest_asyncio.fixture()
async def token_a(client: AsyncClient) -> str:
    """Register user A and return their JWT token."""
    await client.post("/auth/register", json=USER_A)
    resp = await client.post(
        "/auth/login",
        data={"username": USER_A["email"], "password": USER_A["password"]},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture()
async def token_b(client: AsyncClient) -> str:
    """Register user B and return their JWT token."""
    await client.post("/auth/register", json=USER_B)
    resp = await client.post(
        "/auth/login",
        data={"username": USER_B["email"], "password": USER_B["password"]},
    )
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Sample payload factories
# ---------------------------------------------------------------------------

SAMPLE_VOCABULARY = json.dumps([
    {"word": "gato", "meaning_in_target": "un animal", "equivalent_in_english": "cat"}
])

def story_payload(**overrides) -> dict:
    base = {
        "title": "El Gato",
        "story_content": "El gato es bonito.",
        "language": "Spanish",
        "vocabulary": SAMPLE_VOCABULARY,
    }
    return {**base, **overrides}


def lyric_payload(**overrides) -> dict:
    base = {
        "title": "Test Song",
        "video_id": "abc123",
        "language": "French",
        "transcript": json.dumps([{"id": 0, "start": 0.0, "end": 1.0, "text": "Bonjour"}]),
    }
    return {**base, **overrides}


def visual_payload(**overrides) -> dict:
    base = {
        "word": "neko",
        "language": "Japanese",
        "images": json.dumps([]),
        "prompt": "A cute cat",
    }
    return {**base, **overrides}
