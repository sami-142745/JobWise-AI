import logging
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ..database import get_db
from ..models.job import ResumeProfileOut
from ..models.user import ResumeSubmission
from ..services.ai_agent import AIAgentError
from ..services.job_service import (
    get_latest_profile,
    recommend_jobs_for_user,
    save_resume,
    serialize_resume,
)
from ..services.ai_agent import RecommendationAgent
from ..utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resume", tags=["resume"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".csv"}

_agent = RecommendationAgent()


@router.post("/upload", response_model=ResumeProfileOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    filename = file.filename or "resume.txt"
    ext = f".{filename.rsplit('.', 1)[-1].lower()}" if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Upload a PDF, DOCX, or TXT.",
        )
    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    resume = save_resume(user["id"], filename, data)

    users = get_db().users
    from ..utils.auth import find_user_by_id
    users.update_one(
        {"_id": find_user_by_id(user["id"])["_id"]},
        {"$set": {"skills": list(resume["skills"]), "updated_resume_at": datetime.now(timezone.utc)}},
    )
    return ResumeProfileOut(
        id=resume["id"],
        filename=resume["filename"],
        parsed_at=resume["parsed_at"],
        skills=resume["skills"],
        years_experience=resume["years_experience"],
        summary=resume.get("summary", resume["content"][:300]),
        ai_mode=resume.get("ai_mode", "offline-rules"),
        job_titles=resume.get("job_titles", []),
        education=resume.get("education", ""),
        career_interests=resume.get("career_interests", []),
        suggested_roles=resume.get("suggested_roles", []),
    )


@router.post("/analyze-text", response_model=ResumeProfileOut)
def analyze_resume_text(
    payload: ResumeSubmission,
    user: dict = Depends(get_current_user),
):
    text = (payload.resume_text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Resume text is required.")
    try:
        profile = _agent.analyze_resume(text)
    except AIAgentError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    resume = {
        "user_id": user["id"],
        "filename": "text-resume.txt",
        "disk_path": "",
        "content": text,
        "skills": profile["skills"],
        "years_experience": profile["years_experience"],
        "summary": profile.get("summary", ""),
        "job_titles": profile.get("job_titles", []),
        "education": profile.get("education", ""),
        "career_interests": profile.get("career_interests", []),
        "suggested_roles": profile.get("suggested_roles", []),
        "ai_mode": profile.get("ai_mode", "offline-rules"),
        "parsed_at": datetime.now(timezone.utc),
    }
    result = get_db().resumes.insert_one(resume)
    resume["_id"] = result.inserted_id
    users = get_db().users
    from ..utils.auth import find_user_by_id
    users.update_one(
        {"_id": find_user_by_id(user["id"])["_id"]},
        {"$set": {"skills": resume["skills"]}},
    )
    serialized = serialize_resume(resume)
    return ResumeProfileOut(
        id=serialized["id"],
        filename=serialized["filename"],
        parsed_at=serialized["parsed_at"],
        skills=serialized["skills"],
        years_experience=serialized["years_experience"],
        summary=serialized.get("summary", serialized["content"][:300]),
        ai_mode=serialized.get("ai_mode", "offline-rules"),
        job_titles=serialized.get("job_titles", []),
        education=serialized.get("education", ""),
        career_interests=serialized.get("career_interests", []),
        suggested_roles=serialized.get("suggested_roles", []),
    )


@router.get("/profile", response_model=ResumeProfileOut)
def get_profile(user: dict = Depends(get_current_user)):
    resume = get_latest_profile(user["id"])
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume uploaded yet.",
        )
    serialized = serialize_resume(resume)
    return ResumeProfileOut(
        id=serialized["id"],
        filename=serialized["filename"],
        parsed_at=serialized["parsed_at"],
        skills=serialized["skills"],
        years_experience=serialized["years_experience"],
        summary=serialized.get("summary", serialized["content"][:300]),
        ai_mode=serialized.get("ai_mode", "offline-rules"),
        job_titles=serialized.get("job_titles", []),
        education=serialized.get("education", ""),
        career_interests=serialized.get("career_interests", []),
        suggested_roles=serialized.get("suggested_roles", []),
    )


@router.get("/recommendations")
def recommendations(
    limit: int = 10,
    user: dict = Depends(get_current_user),
):
    try:
        return recommend_jobs_for_user(user["id"], limit=limit)
    except AIAgentError as exc:
        raise HTTPException(status_code=422, detail=str(exc))