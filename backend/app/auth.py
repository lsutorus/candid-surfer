import os
import uuid
from datetime import UTC, datetime

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlmodel import Session

from app.db import engine
from app.models import User

load_dotenv()

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")
if not SUPABASE_JWT_SECRET:
    raise RuntimeError(
        "SUPABASE_JWT_SECRET is missing! Copy backend/.env.example to backend/.env and fill in your Supabase JWT secret."
    )

ALGORITHM = "HS256"

_bearer = HTTPBearer()


def _decode_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    exp = payload.get("exp")
    if exp is None or datetime.fromtimestamp(exp, UTC) < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    return payload


def _upsert_user(session: Session, user_id: uuid.UUID, email: str) -> User:
    user = session.get(User, user_id)
    if user is not None:
        return user
    user = User(id=user_id, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> User:
    payload = _decode_jwt(creds.credentials)
    try:
        user_id = uuid.UUID(payload["sub"])
        email = payload["email"]
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")

    with Session(engine) as session:
        return _upsert_user(session, user_id, email)
