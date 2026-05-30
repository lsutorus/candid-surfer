from unittest.mock import MagicMock, patch

from app.services.stream import ingest_clip_to_cloudflare


def test_ingest_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"uid": "stream-uid-123"}}

    with patch("app.services.stream.r2_client") as mock_r2, \
         patch("app.services.stream.httpx.Client") as mock_client_cls:
        mock_r2.generate_presigned_url.return_value = "https://r2.example/presigned"
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        uid, error = ingest_clip_to_cloudflare("raw/session-id/clip.mp4", "clip-123")

    assert uid == "stream-uid-123"
    assert error is None


def test_ingest_non_200_failure():
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    with patch("app.services.stream.r2_client") as mock_r2, \
         patch("app.services.stream.httpx.Client") as mock_client_cls:
        mock_r2.generate_presigned_url.return_value = "https://r2.example/presigned"
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        uid, error = ingest_clip_to_cloudflare("raw/session-id/clip.mp4", "clip-123")

    assert uid is None
    assert "500" in error or "Internal Server Error" in error


def test_ingest_missing_uid():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {}}
    mock_response.text = '{"result": {}}'

    with patch("app.services.stream.r2_client") as mock_r2, \
         patch("app.services.stream.httpx.Client") as mock_client_cls:
        mock_r2.generate_presigned_url.return_value = "https://r2.example/presigned"
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        uid, error = ingest_clip_to_cloudflare("raw/session-id/clip.mp4", "clip-123")

    assert uid is None
    assert "result.uid" in error
