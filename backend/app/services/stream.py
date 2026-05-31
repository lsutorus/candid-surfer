import os
import logging
import time

import httpx
from dotenv import load_dotenv
from sqlmodel import Session

from app.db import engine
from app.models import Clip
from app.r2 import R2_BUCKET, r2_client

load_dotenv()

CF_STREAM_ACCOUNT_ID = os.environ.get("CF_STREAM_ACCOUNT_ID", "")
CF_STREAM_API_TOKEN = os.environ.get("CF_STREAM_API_TOKEN", "")
CF_STREAM_WATERMARK_UID = os.environ.get("CF_STREAM_WATERMARK_UID", "")

_missing = [
    k for k, v in {
        "CF_STREAM_ACCOUNT_ID": CF_STREAM_ACCOUNT_ID,
        "CF_STREAM_API_TOKEN": CF_STREAM_API_TOKEN,
    }.items() if not v
]

if _missing:
    raise RuntimeError(
        f"Missing Cloudflare Stream env vars: {', '.join(_missing)}. "
        "Set CF_STREAM_ACCOUNT_ID and CF_STREAM_API_TOKEN in backend/.env."
    )

log = logging.getLogger(__name__)

STREAM_API_BASE = "https://api.cloudflare.com/client/v4/accounts"
MAX_RETRIES = 1
RETRY_BACKOFF_SECONDS = 3


class IngestResult:
    """Structured result from ingest_clip_to_cloudflare."""

    __slots__ = ("stream_uid", "error", "status_code")

    def __init__(
        self,
        stream_uid: str | None = None,
        error: str | None = None,
        status_code: int | None = None,
    ):
        self.stream_uid = stream_uid
        self.error = error
        self.status_code = status_code

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def is_5xx(self) -> bool:
        return self.status_code is not None and 500 <= self.status_code < 600


def ingest_clip_to_cloudflare(r2_raw_key: str, clip_id: str) -> IngestResult:
    """Call Cloudflare Stream copy API. No database interaction.

    Returns IngestResult with stream_uid on success, or error + status_code on failure.
    """
    presigned_url = r2_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": R2_BUCKET, "Key": r2_raw_key},
        ExpiresIn=3600,
    )

    payload: dict = {"url": presigned_url, "meta": {"clip_id": clip_id}}
    if CF_STREAM_WATERMARK_UID:
        payload["watermark"] = {"uid": CF_STREAM_WATERMARK_UID}

    url = f"{STREAM_API_BASE}/{CF_STREAM_ACCOUNT_ID}/stream/copy"
    headers = {"Authorization": f"Bearer {CF_STREAM_API_TOKEN}"}

    with httpx.Client(timeout=30) as client:
        resp = client.post(url, json=payload, headers=headers)

    if resp.status_code != 200:
        return IngestResult(
            error=f"CF Stream copy failed (status={resp.status_code}): {resp.text}",
            status_code=resp.status_code,
        )

    data = resp.json()
    uid = data.get("result", {}).get("uid")
    if not uid:
        return IngestResult(
            error=f"CF Stream response missing result.uid: {resp.text}",
            status_code=200,
        )

    return IngestResult(stream_uid=uid)


def get_stuck_clips(minutes: int = 15) -> list[Clip]:
    """Return clips stuck in 'processing' for longer than *minutes*.

    These are clips where the Cloudflare Stream webhook never arrived.
    Used by the re-ingest endpoint to identify candidates.
    """
    from datetime import datetime, timedelta, timezone
    from sqlmodel import select

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    with Session(engine) as db:
        statement = select(Clip).where(
            Clip.status == "processing",
            Clip.updated_at < cutoff,
        )
        return list(db.exec(statement).all())


def trigger_cloudflare_ingest(clip_id: str) -> None:
    with Session(engine) as db:
        clip = db.get(Clip, clip_id)
        if clip is None:
            log.error("clip %s not found for ingest", clip_id)
            return

        log.info(
            "Starting Stream ingest for clip %s (r2_raw_key=%s, current_status=%s)",
            clip_id, clip.r2_raw_key, clip.status,
        )

        result = ingest_clip_to_cloudflare(clip.r2_raw_key, str(clip_id))

        if result.is_5xx:
            log.warning(
                "Transient ingest error for clip %s (status=%d), retrying in %ds",
                clip_id, result.status_code, RETRY_BACKOFF_SECONDS,
            )
            time.sleep(RETRY_BACKOFF_SECONDS)
            result = ingest_clip_to_cloudflare(clip.r2_raw_key, str(clip_id))

        if not result.ok:
            log.error(
                "Ingest failed for clip %s (r2_raw_key=%s): %s",
                clip_id, clip.r2_raw_key, result.error,
            )
            clip.status = "failed"
            db.add(clip)
            db.commit()
            return

        clip.stream_uid = result.stream_uid
        clip.status = "processing"
        db.add(clip)
        db.commit()
        log.info("clip %s → stream_uid %s, status=processing", clip_id, result.stream_uid)
