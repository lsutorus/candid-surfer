"""Delete clips older than 30 days.

Usage:
    uv run python scripts/ttl_delete.py [--days N] [--dry-run]

Queries Clips where captured_at > N days ago and is_deleted=False.
For each: calls CF Stream DELETE, marks is_deleted=True.
R2 raw objects are auto-deleted by bucket lifecycle rule.
"""

import argparse
import os
import sys
import logging
from datetime import UTC, datetime, timedelta

import httpx
from dotenv import load_dotenv
from sqlmodel import Session, select

# Allow running as script from backend/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import engine
from app.models import Clip

load_dotenv()

CF_STREAM_ACCOUNT_ID = os.environ.get("CF_STREAM_ACCOUNT_ID", "")
CF_STREAM_API_TOKEN = os.environ.get("CF_STREAM_API_TOKEN", "")

log = logging.getLogger(__name__)

DEFAULT_TTL_DAYS = 30
STREAM_API_BASE = "https://api.cloudflare.com/client/v4/accounts"


def delete_stream_video(stream_uid: str) -> bool:
    """Delete a video from Cloudflare Stream. Returns True on success."""
    if not CF_STREAM_ACCOUNT_ID or not CF_STREAM_API_TOKEN:
        log.error("CF_STREAM_ACCOUNT_ID or CF_STREAM_API_TOKEN not set")
        return False

    url = f"{STREAM_API_BASE}/{CF_STREAM_ACCOUNT_ID}/stream/{stream_uid}"
    headers = {"Authorization": f"Bearer {CF_STREAM_API_TOKEN}"}

    with httpx.Client(timeout=30) as client:
        resp = client.delete(url, headers=headers)

    if resp.status_code in (200, 204, 404):
        log.info("Stream DELETE %s → %d", stream_uid, resp.status_code)
        return True

    log.error("Stream DELETE %s failed: %d %s", stream_uid, resp.status_code, resp.text)
    return False


def run(days: int, dry_run: bool) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    log.info("Finding clips captured before %s (is_deleted=False)", cutoff.isoformat())

    with Session(engine) as db:
        statement = select(Clip).where(
            Clip.captured_at < cutoff,
            Clip.is_deleted == False,  # noqa: E712
        )
        clips = list(db.exec(statement).all())

    if not clips:
        log.info("No expired clips found.")
        return 0

    log.info("Found %d expired clips", len(clips))

    deleted = 0
    for clip in clips:
        log.info(
            "Clip %s: captured=%s stream_uid=%s",
            clip.id,
            clip.captured_at.isoformat(),
            clip.stream_uid,
        )

        if dry_run:
            log.info("[dry-run] Would delete clip %s", clip.id)
            deleted += 1
            continue

        # Delete from Cloudflare Stream if we have a UID
        if clip.stream_uid:
            ok = delete_stream_video(clip.stream_uid)
            if not ok:
                log.warning("Skipping DB mark for clip %s (Stream DELETE failed)", clip.id)
                continue

        # Mark deleted in DB
        with Session(engine) as db:
            db_clip = db.get(Clip, clip.id)
            if db_clip and not db_clip.is_deleted:
                db_clip.is_deleted = True
                db.add(db_clip)
                db.commit()
                log.info("Clip %s marked is_deleted=True", clip.id)

        deleted += 1

    log.info("Done: %d/%d clips processed", deleted, len(clips))
    return deleted


def main():
    parser = argparse.ArgumentParser(description="Delete expired clips")
    parser.add_argument("--days", type=int, default=DEFAULT_TTL_DAYS, help="TTL in days")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run(args.days, args.dry_run)


if __name__ == "__main__":
    main()
