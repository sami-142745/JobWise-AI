from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ResumeSubmission(BaseModel):
    resume_text: Optional[str] = None


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    skills: list[str] = []
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


def utcnow() -> datetime:
    return datetime.now(timezone.utc)