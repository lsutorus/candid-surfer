from unittest.mock import MagicMock, patch

from app.services.stream import ingest_clip_to_cloudflare, trigger_cloudflare_ingest


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

        result = ingest_clip_to_cloudflare("raw/session-id/clip.mp4", "clip-123")

    assert result.stream_uid == "stream-uid-123"
    assert result.ok


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

        result = ingest_clip_to_cloudflare("raw/session-id/clip.mp4", "clip-123")

    assert result.stream_uid is None
    assert not result.ok
    assert "500" in result.error or "Internal Server Error" in result.error


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

        result = ingest_clip_to_cloudflare("raw/session-id/clip.mp4", "clip-123")

    assert result.stream_uid is None
    assert not result.ok
    assert "result.uid" in result.error


def test_ingest_retry_on_5xx():
    """5xx error triggers one retry, second call succeeds."""
    fail_response = MagicMock()
    fail_response.status_code = 503
    fail_response.text = "Service Unavailable"

    success_response = MagicMock()
    success_response.status_code = 200
    success_response.json.return_value = {"result": {"uid": "stream-uid-retry"}}

    call_count = 0
    def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return fail_response if call_count == 1 else success_response

    with patch("app.services.stream.r2_client") as mock_r2, \
         patch("app.services.stream.httpx.Client") as mock_client_cls, \
         patch("app.services.stream.time.sleep"):
        mock_r2.generate_presigned_url.return_value = "https://r2.example/presigned"
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = mock_post
        mock_client_cls.return_value = mock_client

        with patch("app.services.stream.Session") as mock_session_cls, \
             patch("app.services.stream.engine"):
            mock_db = MagicMock()
            mock_clip = MagicMock()
            mock_clip.r2_raw_key = "raw/s/clip.mp4"
            mock_clip.id = "clip-123"
            mock_db.get.return_value = mock_clip
            mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_db)
            mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

            trigger_cloudflare_ingest("clip-123")

    assert call_count == 2
    assert mock_clip.status == "processing"
    assert mock_clip.stream_uid == "stream-uid-retry"


def test_trigger_ingest_marks_failed_after_retry():
    """Both attempts fail → clip status = failed."""
    fail_response = MagicMock()
    fail_response.status_code = 503
    fail_response.text = "Service Unavailable"

    with patch("app.services.stream.r2_client") as mock_r2, \
         patch("app.services.stream.httpx.Client") as mock_client_cls, \
         patch("app.services.stream.time.sleep"):
        mock_r2.generate_presigned_url.return_value = "https://r2.example/presigned"
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = fail_response
        mock_client_cls.return_value = mock_client

        with patch("app.services.stream.Session") as mock_session_cls, \
             patch("app.services.stream.engine"):
            mock_db = MagicMock()
            mock_clip = MagicMock()
            mock_clip.r2_raw_key = "raw/s/clip.mp4"
            mock_db.get.return_value = mock_clip
            mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_db)
            mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

            trigger_cloudflare_ingest("clip-123")

    assert mock_clip.status == "failed"


def test_trigger_ingest_clip_not_found():
    """Clip not in DB → early return, no crash."""
    with patch("app.services.stream.Session") as mock_session_cls, \
         patch("app.services.stream.engine"):
        mock_db = MagicMock()
        mock_db.get.return_value = None
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        trigger_cloudflare_ingest("nonexistent-clip")

    from app.models import Clip
    mock_db.get.assert_called_once_with(Clip, "nonexistent-clip")
