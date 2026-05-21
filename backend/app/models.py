import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, ForeignKey, Unicode
from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(UTC)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True)
    stripe_account_id: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=_now)


class Spot(SQLModel, table=True):
    __tablename__ = "spots"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    lat: float = Field(index=True)
    lng: float = Field(index=True)
    timezone: str
    is_approved: bool = Field(default=False)


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    spot_id: uuid.UUID = Field(
        sa_column=Column(ForeignKey("spots.id", ondelete="CASCADE"), nullable=False),
    )
    filmer_id: uuid.UUID = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    )
    start_time: datetime
    end_time: datetime
    price: int  # cents, minimum $500 enforced at API layer
    thumbnail_url: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=_now)


class Clip(SQLModel, table=True):
    __tablename__ = "clips"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(
        sa_column=Column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True),
    )
    captured_at: datetime = Field(index=True)
    r2_raw_key: str
    stream_uid: str | None = Field(default=None)
    status: str = Field(default="uploading")  # uploading | uploaded | processing | ready | failed
    is_deleted: bool = Field(default=False)


class Purchase(SQLModel, table=True):
    __tablename__ = "purchases"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    )
    session_id: uuid.UUID = Field(
        sa_column=Column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
    )
    stripe_session_id: str = Field(unique=True)
    amount_cents: int
    created_at: datetime = Field(default_factory=_now)


class StripeEvent(SQLModel, table=True):
    __tablename__ = "stripe_events"

    id: str = Field(primary_key=True)  # Stripe Event ID
    type: str
    processed_at: datetime = Field(default_factory=_now)
