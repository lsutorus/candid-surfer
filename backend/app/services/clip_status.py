"""Clip status aggregation — single source of truth for the status enum."""

from __future__ import annotations

class ClipStatus:
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    PARTIAL = "partial"

    ALL: frozenset[str] = frozenset(
        {UPLOADING, UPLOADED, PROCESSING, READY, FAILED, PARTIAL}
    )


def aggregate_clip_status(statuses: set[str]) -> str:
    """Derive a session-level status from the set of its clip statuses."""
    if not statuses:
        return ClipStatus.READY
    if statuses == {ClipStatus.READY}:
        return ClipStatus.READY
    if statuses == {ClipStatus.FAILED}:
        return ClipStatus.FAILED
    if ClipStatus.UPLOADING in statuses:
        return ClipStatus.UPLOADING
    if ClipStatus.PROCESSING in statuses:
        return ClipStatus.PROCESSING
    if ClipStatus.UPLOADED in statuses:
        return ClipStatus.UPLOADED
    if ClipStatus.READY in statuses and len(statuses) > 1:
        return ClipStatus.PARTIAL
    return next(iter(statuses))
