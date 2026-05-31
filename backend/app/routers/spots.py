from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.auth import get_current_user
from app.deps import get_db
from app.models import Spot, User
from app.schemas import SpotCreate, SpotRead

router = APIRouter(prefix="/api/spots", tags=["spots"])


@router.get("", response_model=list[SpotRead])
def list_spots(
    min_lat: float = Query(...),
    max_lat: float = Query(...),
    min_lng: float = Query(...),
    max_lng: float = Query(...),
    db: Session = Depends(get_db),
) -> list[SpotRead]:
    statement = select(Spot).where(
        Spot.lat >= min_lat,
        Spot.lat <= max_lat,
        Spot.lng >= min_lng,
        Spot.lng <= max_lng,
        Spot.is_approved == True,  # noqa: E712 — only show approved spots publicly
    )
    return db.exec(statement).all()


@router.post("", response_model=SpotRead, status_code=201)
def suggest_spot(
    payload: SpotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SpotRead:
    spot = Spot(**payload.model_dump())
    db.add(spot)
    db.commit()
    db.refresh(spot)
    return spot
