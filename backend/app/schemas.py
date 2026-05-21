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


class MultipartInitiate(SQLModel):
    session_id: uuid.UUID
    filename: str
    file_size: int
    captured_at: datetime


class MultipartInitiateResponse(SQLModel):
    clip_id: uuid.UUID
    upload_id: str
    key: str


class PresignPartsRequest(SQLModel):
    key: str
    upload_id: str
    part_numbers: list[int]


class CompletedPart(SQLModel):
    PartNumber: int
    ETag: str


class MultipartCompleteRequest(SQLModel):
    clip_id: uuid.UUID
    upload_id: str
    key: str
    parts: list[CompletedPart]
