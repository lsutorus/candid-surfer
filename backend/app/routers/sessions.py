import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth import get_current_user
from app.deps import get_db
from app.models import Session as SessionModel, Spot, User
from app.schemas import SessionCreate, SessionRead

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

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
