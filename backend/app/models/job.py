from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    title: str
    company: str
    description: str
    location: str = "Remote"
    salary: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    experience_level: Optional[str] = None
    url: Optional[str] = None


class JobOut(BaseModel):
    id: str
    title: str
    company: str
    description: str
    location: str
    salary: Optional[str]
    skills: list[str]
    experience_level: Optional[str]
    url: Optional[str]
    posted_at: datetime


class JobMatch(JobOut):
    match_score: float = 0.0
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    rationale: Optional[str] = None


class ResumeProfileOut(BaseModel):
    id: str
    filename: str
    parsed_at: datetime
    skills: list[str]
    years_experience: float = 0.0
    summary: str = ""