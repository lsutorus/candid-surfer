from fastapi import APIRouter, Query
from sqlmodel import Session, select

from app.deps import get_db
from app.models import Spot
from app.schemas import SpotRead
from fastapi import Depends

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
    )
    return db.exec(statement).all()
