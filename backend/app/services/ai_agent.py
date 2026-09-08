import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class AIAgentError(Exception):
    """Raised when the AI agent cannot produce a recommendation."""


class JobMatcher:
    """Rule-based scoring agent used for job matching.

    The agent analyzes a candidate's profile (skills, experience) against
    each job posting, producing an interpretable match score plus a
    human-readable rationale.
    """

    WEIGHT_SKILLS = 0.6
    WEIGHT_EXPERIENCE = 0.25
    WEIGHT_LOCATION = 0.15

    def __init__(self, candidate_skills: list[str] | None = None,
                 years_experience: float = 0.0,
                 preferred_location: str | None = None):
        self.candidate_skills = {s.lower() for s in (candidate_skills or [])}
        self.years_experience = years_experience or 0.0
        self.preferred_location = (preferred_location or "").lower()

    def score_job(self, job: dict) -> dict[str, Any]:
        job_skills = {s.lower() for s in job.get("skills", [])}
        matched = sorted(self.candidate_skills & job_skills)
        missing = sorted(job_skills - self.candidate_skills)

        if job_skills:
            coverage = len(matched) / len(job_skills)
        else:
            coverage = 0.0
        skill_score = coverage

        exp_level = (job.get("experience_level") or "").lower()
        exp_score = self._experience_score(exp_level)

        location_score = self._location_score(job.get("location", ""))

        total = (
            self.WEIGHT_SKILLS * skill_score
            + self.WEIGHT_EXPERIENCE * exp_score
            + self.WEIGHT_LOCATION * location_score
        ) * 100.0
        total = round(min(max(total, 0.0), 100.0), 1)

        return {
            "match_score": total,
            "matched_skills": matched,
            "missing_skills": missing,
            "rationale": self._rationale(total, skill_score, exp_score, location_score, job),
        }

    def _experience_score(self, level: str) -> float:
        if not level:
            return 0.5
        if level == "entry":
            return 1.0 if self.years_experience <= 2 else 0.7
        if level in ("junior", "mid-level", "midlevel"):
            return 1.0 if 1 <= self.years_experience <= 5 else 0.5
        if level == "senior":
            return 1.0 if self.years_experience >= 4 else 0.4
        if level in ("lead", "manager", "principal", "staff", "director", "executive"):
            return 1.0 if self.years_experience >= 6 else 0.3
        return 0.5

    def _location_score(self, job_location: str) -> float:
        loc = (job_location or "").lower()
        if not loc or "remote" in loc:
            return 1.0
        if self.preferred_location and (
            self.preferred_location in loc or loc in self.preferred_location
        ):
            return 1.0
        return 0.5

    def _rationale(self, total: float, skill_score: float, exp_score: float,
                   location_score: float, job: dict) -> str:
        parts: list[str] = []
        if skill_score >= 0.8:
            parts.append("strong skills match")
        elif skill_score >= 0.5:
            parts.append("decent skills overlap")
        elif skill_score > 0:
            parts.append("basic skills overlap")
        else:
            parts.append("no explicit skill overlap detected")

        if exp_score >= 0.8:
            parts.append("experience level fits well")
        elif exp_score >= 0.5:
            parts.append("experience level is borderline")
        else:
            parts.append("potential experience gap")

        if location_score >= 1.0:
            parts.append("location-friendly")
        else:
            parts.append("consider location requirements")

        verdict = "Highly recommended" if total >= 70 else \
                  "Recommended" if total >= 50 else \
                  "Possible match" if total >= 30 else "Not a strong match"
        return f"{verdict}: {', '.join(parts)}."


class RecommendationAgent:
    """High-level agent that orchestrates resume analysis + recommendations."""

    def __init__(self, matcher: JobMatcher | None = None):
        self.matcher = matcher or JobMatcher()

    def analyze_resume(self, text: str) -> dict[str, Any]:
        from .resume_parser import extract_skills, extract_years_experience, summarize
        if not text.strip():
            raise AIAgentError("Resume text is empty.")
        skills = extract_skills(text)
        years = extract_years_experience(text)
        summary = summarize(text)
        return {
            "skills": skills,
            "years_experience": years,
            "summary": summary,
        }

    def recommend(self, profile: dict[str, Any], jobs: list[dict],
                  preferred_location: str | None = None) -> list[dict[str, Any]]:
        matcher = JobMatcher(
            candidate_skills=profile.get("skills", []),
            years_experience=profile.get("years_experience", 0.0),
            preferred_location=preferred_location,
        )
        results = []
        for job in jobs:
            score = matcher.score_job(job)
            results.append({**job, **score})
        results.sort(key=lambda r: r["match_score"], reverse=True)
        return results


def generate_interview_questions(job: dict) -> list[str]:
    """Produce a few sample interview questions for a matched job."""
    title = job.get("title", "this role")
    skills = job.get("skills", [])[:4]
    questions = [
        f"Tell us about your experience that makes you a great fit for {title}.",
    ]
    for skill in skills:
        questions.append(f"Describe a project where you used {skill}." )
    questions.append("Where do you see yourself growing in the next two years?")
    return questions[:5]