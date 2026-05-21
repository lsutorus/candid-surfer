import uuid

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.auth import get_current_user
from app.deps import get_db
from app.models import Clip, Session as SessionModel, User
from app.r2 import MAX_FILE_SIZE_BYTES, R2_BUCKET, r2_client
from app.schemas import (
    MultipartCompleteRequest,
    MultipartInitiate,
    MultipartInitiateResponse,
    PresignPartsRequest,
)

router = APIRouter(prefix="/api/clips/multipart", tags=["uploads"])


@router.post("/initiate", response_model=MultipartInitiateResponse)
def initiate_upload(
    body: MultipartInitiate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MultipartInitiateResponse:
    if body.file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {MAX_FILE_SIZE_BYTES // (1024**3)} GB limit",
        )

    session = db.get(SessionModel, body.session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    if session.filmer_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your session",
        )

    clip_id = uuid.uuid4()
    key = f"raw/{body.session_id}/{clip_id}.mp4"

    try:
        resp = r2_client.create_multipart_upload(Bucket=R2_BUCKET, Key=key)
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"R2 create_multipart_upload failed: {e}",
        )

    upload_id = resp["UploadId"]

    clip = Clip(
        id=clip_id,
        session_id=body.session_id,
        captured_at=body.captured_at,
        r2_raw_key=key,
        status="uploading",
    )
    db.add(clip)
    db.commit()

    return MultipartInitiateResponse(clip_id=clip_id, upload_id=upload_id, key=key)


@router.post("/presign-parts")
def presign_parts(
    body: PresignPartsRequest,
    user: User = Depends(get_current_user),
) -> dict[int, str]:
    urls: dict[int, str] = {}
    for part_num in body.part_numbers:
        try:
            url = r2_client.generate_presigned_url(
                "upload_part",
                Params={
                    "Bucket": R2_BUCKET,
                    "Key": body.key,
                    "UploadId": body.upload_id,
                    "PartNumber": part_num,
                },
                ExpiresIn=3600,
            )
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"R2 presign failed for part {part_num}: {e}",
            )
        urls[part_num] = url
    return urls


@router.post("/complete")
def complete_upload(
    body: MultipartCompleteRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    clip = db.get(Clip, body.clip_id)
    if clip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clip not found",
        )

    session = db.get(SessionModel, clip.session_id)
    if session is None or session.filmer_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your clip",
        )

    parts = [{"PartNumber": p.PartNumber, "ETag": p.ETag} for p in body.parts]

    try:
        r2_client.complete_multipart_upload(
            Bucket=R2_BUCKET,
            Key=body.key,
            UploadId=body.upload_id,
            MultipartUpload={"Parts": parts},
        )
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"R2 complete_multipart_upload failed: {e}",
        )

    clip.status = "uploaded"
    db.add(clip)
    db.commit()

    return {"status": "uploaded"}
