import os
import uuid

import stripe
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, SQLModel

from app.auth import get_current_user
from app.deps import get_db
from app.models import Session as SessionModel, User

load_dotenv()

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

if not STRIPE_SECRET_KEY:
    raise RuntimeError(
        "STRIPE_SECRET_KEY is missing! Set it in backend/.env"
    )

stripe.api_key = STRIPE_SECRET_KEY

router = APIRouter(prefix="/api/purchases", tags=["purchases"])

APPLICATION_FEE_PERCENT = 20


class CheckoutRequest(SQLModel):
    session_id: uuid.UUID


@router.post("/checkout")
def create_checkout(
    body: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    session = db.get(SessionModel, body.session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    filmer = db.get(User, session.filmer_id)
    if filmer is None or filmer.stripe_account_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filmer cannot receive funds yet",
        )

    price_cents = session.price
    application_fee_amount = int(price_cents * APPLICATION_FEE_PERCENT / 100)

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Session {session.id}",
                    },
                    "unit_amount": price_cents,
                },
                "quantity": 1,
            },
        ],
        mode="payment",
        payment_intent_data={
            "application_fee_amount": application_fee_amount,
            "transfer_data": {
                "destination": filmer.stripe_account_id,
            },
        },
        metadata={
            "session_id": str(session.id),
            "user_id": str(current_user.id),
        },
        success_url=f"{FRONTEND_URL}/purchase/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/purchase/cancel",
    )

    return {"url": checkout_session.url}
