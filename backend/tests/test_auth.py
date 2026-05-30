import uuid
from unittest.mock import patch

from fastapi import status
from sqlmodel import Session

from app.models import User


def test_get_current_user_resolves_existing_user(client, test_user, mock_auth):
    resp = client.get(f"/api/sessions/{test_user.id}/status", headers=mock_auth)
    assert resp.status_code in {status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND}


def test_get_current_user_creates_new_user(client, db_session):
    new_id = uuid.uuid4()
    new_email = "new@example.com"
    with patch("app.auth._decode_jwt") as mock_decode:
        mock_decode.return_value = {"sub": str(new_id), "email": new_email}
        headers = {"Authorization": "Bearer fake-token"}
        resp = client.get(f"/api/sessions/{new_id}/status", headers=headers)
        assert resp.status_code in {status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND}

    user = db_session.get(User, new_id)
    assert user is not None
    assert user.email == new_email


def test_get_current_user_rejects_missing_token(client):
    resp = client.get("/api/sessions/00000000-0000-0000-0000-000000000000/status")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_auth_and_endpoint_share_session(client, db_session):
    new_id = uuid.uuid4()
    with patch("app.auth._decode_jwt") as mock_decode:
        mock_decode.return_value = {"sub": str(new_id), "email": "shared@example.com"}
        headers = {"Authorization": "Bearer fake-token"}
        client.get(f"/api/sessions/{new_id}/status", headers=headers)

    user = db_session.get(User, new_id)
    assert user is not None
