import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.auth import get_current_user
from app.deps import get_db
from app.models import Clip, Purchase, Session as SessionModel, Spot, User
from app.r2 import R2_BUCKET, r2_client
from app.schemas import ClipStatusRead, SessionCreate, SessionFeedRead, SessionFeedResponse, SessionRead, SessionStatusResponse
from app.services.clip_status import aggregate_clip_status

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
def get_session_status(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SessionStatusResponse:
    session = db.get(SessionModel, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.filmer_id != user.id:
        raise HTTPException(status_code=403, detail="Not your session")

    clips = db.exec(
        select(Clip).where(Clip.session_id == session_id)
    ).all()

    clip_statuses = [ClipStatusRead(clip_id=c.id, status=c.status) for c in clips]
    aggregate = aggregate_clip_status({c.status for c in clips})

    return SessionStatusResponse(clips=clip_statuses, aggregate=aggregate)


@router.get("/{session_id}/clips")
def get_session_clips(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> list[str]:
    clips = db.exec(
        select(Clip)
        .where(Clip.session_id == session_id, Clip.status == "ready")
        .order_by(Clip.captured_at.asc())
    ).all()
    return [c.stream_uid for c in clips if c.stream_uid]

MIN_PRICE_CENTS = 500


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session(
    body: SessionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SessionRead:
    if body.price < MIN_PRICE_CENTS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Price must be at least {MIN_PRICE_CENTS} cents ($5)",
        )

    spot = db.get(Spot, body.spot_id)
    if spot is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Spot not found",
        )

    session = SessionModel(
        spot_id=body.spot_id,
        filmer_id=user.id,
        start_time=body.start_time,
        end_time=body.end_time,
        price=body.price,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("", response_model=SessionFeedResponse)
def list_sessions(
    spot_id: uuid.UUID | None = Query(None),
    cursor: datetime | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> SessionFeedResponse:
    statement = select(SessionModel).order_by(SessionModel.created_at.desc())

    if spot_id is not None:
        statement = statement.where(SessionModel.spot_id == spot_id)
    if cursor is not None:
        statement = statement.where(SessionModel.created_at < cursor)

    statement = statement.limit(limit + 1)
    rows = db.exec(statement).all()

    has_next = len(rows) > limit
    sessions = rows[:limit]
    next_cursor = sessions[-1].created_at if has_next and sessions else None

    session_ids = [s.id for s in sessions]
    all_clips = db.exec(
        select(Clip).where(Clip.session_id.in_(session_ids))
    ).all() if session_ids else []

    clip_map: dict[uuid.UUID, set[str]] = {}
    for c in all_clips:
        clip_map.setdefault(c.session_id, set()).add(c.status)

    feed_items = [
        SessionFeedRead(
            id=s.id,
            spot_id=s.spot_id,
            filmer_id=s.filmer_id,
            start_time=s.start_time,
            end_time=s.end_time,
            price=s.price,
            thumbnail_url=s.thumbnail_url,
            clip_status=aggregate_clip_status(clip_map.get(s.id, set())),
            created_at=s.created_at,
        )
        for s in sessions
    ]

    return SessionFeedResponse(
        sessions=feed_items,
        next_cursor=next_cursor,
    )


@router.get("/{session_id}/download-links")
def get_download_links(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    purchase = db.exec(
        select(Purchase).where(
            Purchase.user_id == current_user.id,
            Purchase.session_id == session_id,
        )
    ).first()
    if purchase is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have not purchased this session",
        )

    clips = db.exec(
        select(Clip).where(
            Clip.session_id == session_id,
            Clip.status == "ready",
        )
    ).all()

    links = {}
    for clip in clips:
        url = r2_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": R2_BUCKET, "Key": clip.r2_raw_key},
            ExpiresIn=3600,
        )
        links[str(clip.id)] = url

    return {"links": links}
