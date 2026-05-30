import os
import logging

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


def ingest_clip_to_cloudflare(r2_raw_key: str, clip_id: str) -> tuple[str | None, str | None]:
    """Call Cloudflare Stream copy API. No database interaction.

    Returns (stream_uid, None) on success, or (None, error_detail) on failure.
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
        return None, f"CF Stream copy failed: {resp.text}"

    data = resp.json()
    uid = data.get("result", {}).get("uid")
    if not uid:
        return None, f"CF Stream response missing result.uid: {resp.text}"

    return uid, None


def trigger_cloudflare_ingest(clip_id: str) -> None:
    with Session(engine) as db:
        clip = db.get(Clip, clip_id)
        if clip is None:
            log.error("clip %s not found for ingest", clip_id)
            return

        stream_uid, error = ingest_clip_to_cloudflare(clip.r2_raw_key, str(clip_id))
        if error:
            log.error("Ingest failed for clip %s: %s", clip_id, error)
            clip.status = "failed"
            db.add(clip)
            db.commit()
            return

        clip.stream_uid = stream_uid
        clip.status = "processing"
        db.add(clip)
        db.commit()
        log.info("clip %s → stream_uid %s, status=processing", clip_id, stream_uid)
