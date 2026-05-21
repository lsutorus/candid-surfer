import hmac
import hashlib
import logging
import os
import uuid

import stripe
from dotenv import load_dotenv
from fastapi import APIRouter, Request, Response, status
from sqlmodel import Session

from app.db import engine
from app.models import Clip, Purchase, Session as SessionModel, StripeEvent

load_dotenv()

CF_STREAM_WEBHOOK_SECRET = os.environ.get("CF_STREAM_WEBHOOK_SECRET", "")
CF_STREAM_ACCOUNT_ID = os.environ.get("CF_STREAM_ACCOUNT_ID", "")

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

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


@router.post("/stripe")
async def stripe_webhook(request: Request) -> Response:
    body = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    if not STRIPE_WEBHOOK_SECRET:
        log.warning("STRIPE_WEBHOOK_SECRET not set, skipping verification")
        event = stripe.Event.construct_from(await request.json(), stripe.api_key)
    else:
        try:
            event = stripe.Webhook.construct_event(
                body, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)

    with Session(engine) as db:
        existing = db.get(StripeEvent, event.id)
        if existing is not None:
            log.info("stripe event %s already processed", event.id)
            return Response(status_code=status.HTTP_200_OK)

        db.add(StripeEvent(id=event.id, type=event.type))

        if event.type == "checkout.session.completed":
            obj = event.data.object
            metadata = obj.get("metadata", {}) if isinstance(obj, dict) else getattr(obj, "metadata", {})
            session_id = metadata.get("session_id")
            user_id = metadata.get("user_id")
            stripe_session_id = obj.get("id") if isinstance(obj, dict) else getattr(obj, "id", None)
            amount_total = obj.get("amount_total") if isinstance(obj, dict) else getattr(obj, "amount_total", None)

            if session_id and user_id:
                purchase = Purchase(
                    user_id=uuid.UUID(user_id),
                    session_id=uuid.UUID(session_id),
                    stripe_session_id=stripe_session_id or event.id,
                    amount_cents=amount_total or 0,
                )
                db.add(purchase)
                log.info(
                    "purchase recorded: user=%s session=%s amount=%s",
                    user_id, session_id, amount_total,
                )

        db.commit()

    return Response(status_code=status.HTTP_200_OK)
