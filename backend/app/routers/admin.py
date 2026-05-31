from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.auth import require_admin
from app.deps import get_db
from app.models import Spot, User
from app.schemas import SpotApprove, SpotRead

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/spots", response_model=list[SpotRead])
def list_pending_spots(
    is_approved: bool = False,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[SpotRead]:
    statement = select(Spot).where(Spot.is_approved == is_approved)
    return db.exec(statement).all()


@router.patch("/spots/{spot_id}", response_model=SpotRead)
def update_spot(
    spot_id: str,
    payload: SpotApprove,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SpotRead:
    spot = db.get(Spot, spot_id)
    if spot is None:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")
    spot.is_approved = payload.is_approved
    db.add(spot)
    db.commit()
    db.refresh(spot)
    return spot
