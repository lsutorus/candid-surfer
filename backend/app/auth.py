import os
import threading
import time
import uuid
from datetime import UTC, datetime

import jwt
import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.db import engine
from app.models import User

SUPABASE_JWKS_URL = (
    f"https://{os.environ.get('SUPABASE_PROJECT_REF', 'dyhymlvaiegktcoiyhcl')}"
    f".supabase.co/auth/v1/.well-known/jwks.json"
)
JWKS_CACHE_TTL = 600  # 10 minutes

_bearer = HTTPBearer()


class _JWKSCache:
    def __init__(self):
        self._lock = threading.Lock()
        self._keys: dict[str, jwt.PyJWK] = {}
        self._fetched_at: float = 0

    def get_key(self, kid: str) -> jwt.PyJWK | None:
        with self._lock:
            if self._keys and time.monotonic() - self._fetched_at < JWKS_CACHE_TTL:
                return self._keys.get(kid)
            return None

    def fetch(self) -> dict[str, jwt.PyJWK]:
        with self._lock:
            if self._keys and time.monotonic() - self._fetched_at < JWKS_CACHE_TTL:
                return self._keys
            resp = requests.get(SUPABASE_JWKS_URL, timeout=10)
            resp.raise_for_status()
            jwks = resp.json()
            self._keys = {}
            for jwk_data in jwks.get("keys", []):
                k = jwk_data.get("kid")
                if k:
                    self._keys[k] = jwt.PyJWK(jwk_data)
            self._fetched_at = time.monotonic()
            return self._keys


_jwks_cache = _JWKSCache()


def _decode_jwt(token: str) -> dict:
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
    except jwt.exceptions.DecodeError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if not kid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing key ID in token")

    signing_key = _jwks_cache.get_key(kid)
    if signing_key is None:
        keys = _jwks_cache.fetch()
        signing_key = keys.get(kid)
    if signing_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signing key not found")

    try:
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid audience")
    except jwt.InvalidSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

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
