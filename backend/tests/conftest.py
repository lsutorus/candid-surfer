import uuid
from collections.abc import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.deps import get_db
from app.main import app
from app.models import User


_test_engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})


@pytest.fixture(autouse=True)
def _create_tables() -> Generator[None, None, None]:
    SQLModel.metadata.create_all(_test_engine)
    yield
    SQLModel.metadata.drop_all(_test_engine)


def _get_test_db() -> Generator[Session, None, None]:
    with Session(_test_engine) as session:
        yield session


app.dependency_overrides[get_db] = _get_test_db


@pytest.fixture
def db_session() -> Session:
    with Session(_test_engine) as session:
        yield session


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def test_user(db_session: Session) -> User:
    user = User(id=uuid.uuid4(), email="test@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def mock_auth(test_user: User):
    """Patch _decode_jwt to return test_user claims. Returns headers dict."""
    with patch("app.auth._decode_jwt") as mock_decode:
        mock_decode.return_value = {"sub": str(test_user.id), "email": test_user.email}
        yield {"Authorization": f"Bearer fake-token-for-{test_user.id}"}
