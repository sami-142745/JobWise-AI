import logging
import re
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.errors import DuplicateKeyError

from ..database import get_db
from ..models.job import JobCreate, JobOut
from ..services.job_service import serialize_job
from ..utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=list[JobOut])
def list_jobs(
    q: str | None = Query(None, description="Search by title, company, skills"),
    location: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    _: dict = Depends(get_current_user),
):
    jobs = get_db().jobs
    query = {}
    if q:
        regex = {"$regex": f".*{re.escape(q)}.*", "$options": "i"}
        query["$or"] = [
            {"title": regex},
            {"company": regex},
            {"description": regex},
            {"skills": regex},
        ]
    if location:
        loc_regex = {"$regex": f".*{re.escape(location)}.*", "$options": "i"}
        query["$or"] = query.get("$or", []) + [{"location": loc_regex}]
        if "$or" not in query:
            query["location"] = loc_regex
    results = list(jobs.find(query).sort("posted_at", -1).limit(limit))
    return [JobOut(**serialize_job(job)) for job in results]


@router.get("/search", response_model=list[JobOut])
def search_jobs(
    q: str = Query(..., min_length=1),
    location: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    _: dict = Depends(get_current_user),
):
    jobs = get_db().jobs
    regex = {"$regex": f".*{re.escape(q)}.*", "$options": "i"}
    query: dict = {
        "$or": [
            {"title": regex},
            {"company": regex},
            {"description": regex},
            {"skills": regex},
        ]
    }
    if location:
        loc_regex = {"$regex": f".*{re.escape(location)}.*", "$options": "i"}
        query["$or"].append({"location": loc_regex})
    results = list(jobs.find(query).sort("posted_at", -1).limit(limit))
    return [JobOut(**serialize_job(job)) for job in results]


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, _: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job id.")
    job = get_db().jobs.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobOut(**serialize_job(job))


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, _: dict = Depends(get_current_user)):
    jobs = get_db().jobs
    document = {
        "title": payload.title,
        "company": payload.company,
        "description": payload.description,
        "location": payload.location,
        "salary": payload.salary,
        "skills": list(dict.fromkeys(s.lower() for s in payload.skills)),
        "experience_level": payload.experience_level,
        "url": payload.url,
        "posted_at": datetime.now(timezone.utc),
    }
    try:
        result = jobs.insert_one(document)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Duplicate job entry.")
    document["_id"] = result.inserted_id
    return JobOut(**serialize_job(document))