import logging
import re
from typing import Any, Optional

from ..config import settings
from .ollama_service import OllamaClient, OllamaError, ollama_client

logger = logging.getLogger(__name__)


class AIAgentError(Exception):
    """Raised when the AI agent cannot produce a recommendation."""


class JobMatcher:
    """Rule-based scoring agent used for job matching.

    The agent analyzes a candidate's profile (skills, experience) against
    each job posting, producing an interpretable match score plus a
    human-readable rationale. This is the offline fallback engine.
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
            "suggested_skills": missing[:4],
            "ai_reasoning": None,
            "ai_mode": RecommendationAgent.ENGINE_OFFLINE,
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


RESUME_ANALYSIS_SYSTEM = (
    "You are an expert resume analyst and career coach. Read the candidate's "
    "resume and extract structured facts. Respond with JSON ONLY — no prose, "
    "no markdown. Use this exact shape:\n"
    '{\n'
    '  "skills": ["skill", "skill"],\n'
    '  "years_experience": 5.0,\n'
    '  "job_titles": ["Most Recent Role"],\n'
    '  "education": "Highest degree received",\n'
    '  "career_interests": ["area the candidate enjoys"],\n'
    '  "suggested_roles": ["role that fits the profile"]\n'
    '}\n'
    "years_experience must be a number. Lists must be arrays of strings."
)

RECOMMENDATION_SYSTEM = (
    "You are an AI career-matching agent. Given a candidate profile and a "
    "list of job postings, rank how well each job fits the candidate. "
    "Respond with JSON ONLY — no prose, no markdown. Use this exact shape:\n"
    '{\n'
    '  "recommendations": [\n'
    '    {\n'
    '      "job_id": "the job id string",\n'
    '      "match_score": 85,\n'
    '      "reason": "why this is a good fit in one or two sentences",\n'
    '      "matched_skills": ["skill"],\n'
    '      "missing_skills": ["skill"],\n'
    '      "suggested_skills": ["skill the candidate should learn"]\n'
    '    }\n'
    "  ]\n"
    "}\n"
    "match_score is an integer 0-100. Only include job ids from the input."
)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items or []:
        key = str(item).strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(str(item).strip())
    return out


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, str):
        return [value]
    return []


class RecommendationAgent:
    """Ollama-powered agent with automatic offline fallback.

    Behavior
    --------
    1. Every analysis/recommendation first produces a fast, deterministic
       result using the rule-based :class:`JobMatcher`.
    2. When Ollama is enabled and reachable, the same request is enriched
       with the local LLM (structured JSON).
    3. If Ollama is disabled, unreachable, times out, or returns unparsable
       JSON, the offline result is returned unchanged — the app always works.
    """

    ENGINE_OFFLINE = "offline-rules"
    ENGINE_OLLAMA = "ollama"

    def __init__(self, matcher: JobMatcher | None = None,
                 ollama: OllamaClient | None = None):
        self.matcher = matcher or JobMatcher()
        self.ollama = ollama or ollama_client

    @property
    def llm_available(self) -> bool:
        if not settings.OLLAMA_ENABLED:
            return False
        try:
            return self.ollama.is_available()
        except Exception:
            logger.exception("Error while probing Ollama availability.")
            return False

    # ── Resume analysis ─────────────────────────────────────────────────
    def analyze_resume(self, text: str) -> dict[str, Any]:
        from .resume_parser import extract_skills, extract_years_experience, summarize

        if not text.strip():
            raise AIAgentError("Resume text is empty.")

        skills = extract_skills(text)
        years = extract_years_experience(text)
        summary = summarize(text)

        profile = {
            "skills": skills,
            "years_experience": years,
            "summary": summary,
            "job_titles": [],
            "education": "",
            "career_interests": [],
            "suggested_roles": [],
            "ai_mode": self.ENGINE_OFFLINE,
        }

        if not self.llm_available:
            return profile

        try:
            result = self.ollama.generate_json(
                self._analysis_prompt(text),
                system=RESUME_ANALYSIS_SYSTEM,
            )
            if not isinstance(result, dict):
                raise OllamaError("Resume analysis response was not an object.")
            profile["skills"] = _dedupe(list(skills) + _as_str_list(result.get("skills")))
            years_llm = result.get("years_experience")
            try:
                if years_llm is not None:
                    profile["years_experience"] = float(years_llm)
            except (TypeError, ValueError):
                pass
            profile["job_titles"] = _as_str_list(result.get("job_titles"))
            profile["education"] = str(result.get("education", "") or "").strip()
            profile["career_interests"] = _as_str_list(result.get("career_interests"))
            profile["suggested_roles"] = _as_str_list(result.get("suggested_roles"))
            profile["ai_mode"] = self.ENGINE_OLLAMA
        except Exception:
            logger.info("Ollama resume analysis failed; using offline profile.", exc_info=True)
        return profile

    def _analysis_prompt(self, text: str) -> str:
        return (
            "Analyze this resume and extract the structured facts requested. "
            f"Resume text:\n\n{text[:8000]}"
        )

    # ── Recommendations ─────────────────────────────────────────────────
    def recommend(self, profile: dict[str, Any], jobs: list[dict],
                  preferred_location: str | None = None,
                  limit: int = 10) -> list[dict[str, Any]]:
        matcher = JobMatcher(
            candidate_skills=profile.get("skills", []),
            years_experience=profile.get("years_experience", 0.0),
            preferred_location=preferred_location,
        )
        scored = []
        for job in jobs:
            score = matcher.score_job(job)
            item = {**job, **score}
            item["suggested_skills"] = score.get("missing_skills", [])[:4]
            scored.append(item)

        scored.sort(key=lambda r: r["match_score"], reverse=True)

        if self.llm_available:
            # Keep the prompt lean: qwen2.5-coder:7b is slow to emit very long
            # JSON, so rank only the top few candidates with the LLM.
            candidates = scored[: min(max(limit * 2, 10), 8)]
            try:
                payload = self.ollama.generate_json(
                    self._recommendation_prompt(profile, candidates),
                    system=RECOMMENDATION_SYSTEM,
                )
                if isinstance(payload, dict):
                    items = payload.get("recommendations", [])
                else:
                    items = payload
                if isinstance(items, list) and items:
                    scored = self._apply_ollama(items, scored, candidates)
            except Exception:
                logger.info("Ollama recommendations failed; using offline results.", exc_info=True)

        # Order enriched (Ollama) results first, then remaining offline ones.
        enriched = [r for r in scored if r.get("ai_mode") == self.ENGINE_OLLAMA]
        rest = [r for r in scored if r.get("ai_mode") != self.ENGINE_OLLAMA]
        enriched.sort(key=lambda r: r["match_score"], reverse=True)
        rest.sort(key=lambda r: r["match_score"], reverse=True)
        return (enriched + rest)[:limit]

    def _apply_ollama(self, llm_items: list[dict], scored: list[dict],
                      candidates: list[dict]) -> list[dict]:
        """Splice Ollama's structured per-job data back onto the results."""
        by_id = {}
        for item in llm_items:
            if not isinstance(item, dict):
                continue
            job_id = str(item.get("job_id", ""))
            if job_id:
                by_id[job_id] = item

        # Only jobs we actually sent to the model may be enriched with its output.
        candidate_ids = {
            str(c.get("id") or c.get("_id") or "")
            for c in candidates
            if c.get("id") or c.get("_id")
        }

        applied = 0
        for entry in scored:
            # Jobs come straight from MongoDB with "_id"; resolve either key.
            entry_id = str(entry.get("id") or entry.get("_id") or "")
            if entry_id not in candidate_ids:
                continue
            llm = by_id.get(entry_id)
            if not llm:
                continue
            score = llm.get("match_score")
            try:
                score = float(score) if score is not None else None
            except (TypeError, ValueError):
                score = None
            if score is not None:
                entry["match_score"] = round(min(max(score, 0.0), 100.0), 1)
            reason = str(llm.get("reason", "") or "").strip()
            if reason:
                entry["ai_reasoning"] = reason
                entry["rationale"] = reason
            matched = _as_str_list(llm.get("matched_skills"))
            if matched:
                entry["matched_skills"] = _dedupe(matched)
            missing = _as_str_list(llm.get("missing_skills"))
            if missing:
                entry["missing_skills"] = _dedupe(missing)
            suggested = _as_str_list(llm.get("suggested_skills"))
            if suggested:
                entry["suggested_skills"] = _dedupe(suggested)
            entry["ai_mode"] = self.ENGINE_OLLAMA
            applied += 1
        if applied == 0:
            logger.info("Ollama returned recommendations but none matched job ids.")
        return scored

    def _recommendation_prompt(self, profile: dict, jobs: list[dict]) -> str:
        profile_blob = (
            f"- Skills: {', '.join(profile.get('skills', [])) or 'unknown'}\n"
            f"- Years of experience: {profile.get('years_experience', 0)}\n"
            f"- Recent roles: {', '.join(profile.get('job_titles', [])) or 'unknown'}\n"
            f"- Career interests: {', '.join(profile.get('career_interests', [])) or 'unknown'}\n"
            f"- Suggested roles: {', '.join(profile.get('suggested_roles', [])) or 'unknown'}"
        )
        job_lines = []
        for job in jobs:
            job_id = job.get("id") or job.get("_id")
            job_lines.append(
                f"- id: {job_id} | title: {job.get('title')} | company: "
                f"{job.get('company')} | location: {job.get('location')} | level: "
                f"{job.get('experience_level') or 'any'} | skills: "
                f"{', '.join(job.get('skills', [])) or 'none'} | overview: "
                f"{(job.get('description') or '')[:120].strip()}"
            )
        return (
            "Using the candidate profile below, score each listed job for fit.\n\n"
            f"CANDIDATE PROFILE\n{profile_blob}\n\n"
            f"JOBS\n{chr(10).join(job_lines)}\n\n"
            "Return the required JSON object with a recommendation per job id."
        )


def generate_interview_questions(job: dict) -> list[str]:
    """Produce a few sample interview questions for a matched job."""
    title = job.get("title", "this role")
    skills = job.get("skills", [])[:4]
    questions = [
        f"Tell us about your experience that makes you a great fit for {title}.",
    ]
    for skill in skills:
        questions.append(f"Describe a project where you used {skill}.")
    questions.append("Where do you see yourself growing in the next two years?")
    return questions[:5]