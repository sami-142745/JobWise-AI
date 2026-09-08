import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError

from ..database import get_db
from ..models.user import Token, UserCreate, UserLogin, UserOut
from ..utils.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    serialize_user,
    verify_password,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate):
    users = get_db().users
    existing = users.find_one(
        {"$or": [{"email": payload.email}, {"username": payload.username}]}
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email or username already exists.",
        )
    user = {
        "username": payload.username,
        "email": payload.email,
        "full_name": payload.full_name,
        "password": hash_password(payload.password),
        "skills": [],
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result = users.insert_one(user)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email or username already exists.",
        )
    user["_id"] = result.inserted_id
    serialized = serialize_user(user)
    token = create_access_token(serialized["id"])
    return Token(access_token=token, user=UserOut(**serialized))


@router.post("/login", response_model=Token)
def login(payload: UserLogin):
    users = get_db().users
    user = users.find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    serialized = serialize_user(user)
    token = create_access_token(serialized["id"])
    return Token(access_token=token, user=UserOut(**serialized))


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)):
    return UserOut(**user)