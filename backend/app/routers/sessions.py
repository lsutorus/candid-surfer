import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.auth import get_current_user
from app.deps import get_db
from app.models import Clip, Purchase, Session as SessionModel, Spot, User
from app.r2 import R2_BUCKET, r2_client
from app.schemas import SessionCreate, SessionFeedRead, SessionFeedResponse, SessionRead

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


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

    return SessionFeedResponse(
        sessions=sessions,
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
