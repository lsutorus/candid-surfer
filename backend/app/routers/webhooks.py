import hmac
import hashlib
import logging
import os

from dotenv import load_dotenv
from fastapi import APIRouter, Request, Response, status
from sqlmodel import Session

from app.db import engine
from app.models import Clip, Session as SessionModel

load_dotenv()

CF_STREAM_WEBHOOK_SECRET = os.environ.get("CF_STREAM_WEBHOOK_SECRET", "")
CF_STREAM_ACCOUNT_ID = os.environ.get("CF_STREAM_ACCOUNT_ID", "")

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def _verify_signature(signature_header: str, body: bytes) -> bool:
    if not CF_STREAM_WEBHOOK_SECRET:
        log.warning("CF_STREAM_WEBHOOK_SECRET not set, skipping verification")
        return True

    try:
        parts = dict(p.split("=") for p in signature_header.split(","))
        timestamp = parts["time"]
        sig1 = parts["sig1"]
    except (KeyError, ValueError):
        return False

    message = f"{timestamp}.{body.decode()}".encode()
    expected = hmac.new(
        CF_STREAM_WEBHOOK_SECRET.encode(), message, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig1)


@router.post("/cloudflare")
async def cloudflare_webhook(request: Request) -> Response:
    body = await request.body()
    sig = request.headers.get("Webhook-Signature", "")

    if not _verify_signature(sig, body):
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    payload = await request.json()
    meta = payload.get("meta", {})
    clip_id = meta.get("clip_id")
    cf_status = payload.get("status", {})

    if not clip_id:
        log.warning("webhook missing meta.clip_id: %s", payload)
        return Response(status_code=status.HTTP_200_OK)

    state = cf_status.get("state", "")

    with Session(engine) as db:
        clip = db.get(Clip, clip_id)
        if clip is None:
            log.warning("webhook clip %s not found", clip_id)
            return Response(status_code=status.HTTP_200_OK)

        if state == "ready":
            clip.status = "ready"
            db.add(clip)

            session = db.get(SessionModel, clip.session_id)
            if session is not None and session.thumbnail_url is None and clip.stream_uid:
                session.thumbnail_url = (
                    f"https://customer-{CF_STREAM_ACCOUNT_ID}.cloudflarestream.com"
                    f"/{clip.stream_uid}/thumbnails/thumbnail.jpg"
                )
                db.add(session)

            db.commit()
            log.info("clip %s ready", clip_id)

        elif state == "error":
            clip.status = "failed"
            db.add(clip)
            db.commit()
            log.info("clip %s failed", clip_id)

    return Response(status_code=status.HTTP_200_OK)
