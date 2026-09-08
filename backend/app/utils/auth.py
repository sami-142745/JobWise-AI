import base64
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pymongo.collection import Collection

from ..config import settings
from ..database import get_db

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _bcrypt_digest(password: str) -> bytes:
    """Pre-hash with SHA-256 so any password length is supported by bcrypt."""
    return base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_bcrypt_digest(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_bcrypt_digest(plain), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str, expires_minutes: Optional[int] = None) -> str:
    expire_minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expire_minutes),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


def serialize_user(user: dict) -> dict:
    user["id"] = str(user.pop("_id"))
    user.pop("password", None)
    return user


def find_user_by_id(user_id: str) -> Optional[dict]:
    """Look up a user by their string id (accepting both ObjectId and plain ids)."""
    users: Collection = get_db().users
    if ObjectId.is_valid(user_id):
        return users.find_one({"_id": ObjectId(user_id)})
    return users.find_one({"_id": user_id})


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error
    user_id = decode_token(token)
    if user_id is None:
        raise credentials_error

    user = find_user_by_id(user_id)
    if user is None:
        raise credentials_error
    return serialize_user(user)