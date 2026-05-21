import uuid
from datetime import datetime

from sqlmodel import SQLModel


class SessionCreate(SQLModel):
    spot_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    price: int  # cents


class SessionRead(SQLModel):
    id: uuid.UUID
    spot_id: uuid.UUID
    filmer_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    price: int
    thumbnail_url: str | None
    created_at: datetime
