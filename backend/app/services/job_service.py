import logging
import os
import uuid
from typing import Optional

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.collection import Collection

from ..config import settings
from ..database import get_db
from ..services.file_reader import extract_text_from_bytes
from ..services.resume_parser import extract_skills, extract_years_experience
from ..utils.auth import serialize_user
from .ai_agent import AIAgentError, RecommendationAgent

logger = logging.getLogger(__name__)

agent = RecommendationAgent()


def serialize_job(job: dict) -> dict:
    job["id"] = str(job.pop("_id"))
    job["posted_at"] = job.get("posted_at")
    return job


def get_jobs_collection() -> Collection:
    return get_db().jobs


def get_resumes_collection() -> Collection:
    return get_db().resumes


def get_latest_profile(user_id: str) -> Optional[dict]:
    resume = list(
        get_resumes_collection()
        .find({"user_id": user_id})
        .sort("parsed_at", -1)
        .limit(1)
    )
    if not resume:
        return None
    return resume[0]


def save_resume(user_id: str, filename: str, data: bytes) -> dict:
    """Parse + store a resume. Raises HTTPException on bad input."""
    if len(data) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large (max {settings.MAX_UPLOAD_SIZE_MB} MB).",
        )
    try:
        text = extract_text_from_bytes(filename, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    skills = extract_skills(text)
    years = extract_years_experience(text)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{os.path.basename(filename)}"
    disk_path = os.path.join(settings.UPLOAD_DIR, safe_name)
    try:
        with open(disk_path, "wb") as fh:
            fh.write(data)
    except OSError as exc:
        logger.warning("Could not persist resume file: %s", exc)

    resume = {
        "user_id": user_id,
        "filename": filename,
        "disk_path": disk_path,
        "content": text,
        "skills": skills,
        "years_experience": years,
        "parsed_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
    }
    result = get_resumes_collection().insert_one(resume)
    resume["_id"] = result.inserted_id
    return serialize_resume(resume)


def serialize_resume(resume: dict) -> dict:
    resume["id"] = str(resume.pop("_id"))
    return resume


def recommend_jobs_for_user(user_id: str, limit: int = 10,
                            query_profile: Optional[dict] = None) -> list[dict]:
    profile = query_profile or get_latest_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume found. Upload a resume first to get recommendations.",
        )
    if not profile.get("skills") and not profile.get("years_experience"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unable to extract skills from resume. Please upload a clearer resume.",
        )
    jobs = list(get_jobs_collection().find({}))
    if not jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No jobs in the system yet.",
        )
    recommendations = agent.recommend(profile, jobs)
    recommendations = recommendations[:limit]
    return [
        {**serialize_job(job), "match_score": job["match_score"],
         "matched_skills": job["matched_skills"], "missing_skills": job["missing_skills"],
         "rationale": job["rationale"]}
        for job in recommendations
    ]