"""Tests for the Ollama integration.

Ollama is ALWAYS mocked here — no test ever calls a real Ollama server.
Every scenario covered:
  - availability detection (online / offline)
  - successful resume analysis via Ollama
  - successful recommendations via Ollama
  - Ollama failure -> automatic offline fallback
"""

from unittest import mock

from app.config import settings
from app.services.ollama_service import OllamaClient, OllamaError, ollama_client, _extract_json
from tests.conftest import RESUME_TEXT, auth_headers, client


# ── Helpers ─────────────────────────────────────────────────────────────
def enable_ollama(monkeypatch):
    """Turn on the Ollama codepath for a test (conftest defaults it off)."""
    monkeypatch.setattr(settings, "OLLAMA_ENABLED", True)
    ollama_client._available = None
    ollama_client._available_at = 0.0


def patch_available(*, available: bool = True):
    return mock.patch.object(ollama_client, "is_available", return_value=available)


ENRICHED_PROFILE = {
    "skills": ["python", "fastapi", "react", "kubernetes", "llm"],
    "years_experience": 8.0,
    "job_titles": ["Senior Backend Engineer"],
    "education": "BSc Computer Science",
    "career_interests": ["AI", "backend systems"],
    "suggested_roles": ["AI Platform Engineer", "Staff Backend Engineer"],
}


def recommendations_payload(job_ids: list[str]) -> dict:
    return {
        "recommendations": [
            {
                "job_id": job_id,
                "match_score": 93,
                "reason": "The profile maps directly onto this role's stack.",
                "matched_skills": ["python", "fastapi"],
                "missing_skills": ["terraform"],
                "suggested_skills": ["terraform", "kafka"],
            }
            for job_id in job_ids
        ]
    }


# ── JSON parsing robustness ─────────────────────────────────────────────
def test_extract_json_from_code_fence():
    raw = '```json\n{"a": 1}\n```'
    assert _extract_json(raw) == {"a": 1}


def test_extract_json_from_prose():
    raw = 'Here is the result: [{"x": 2}] Enjoy!'
    assert _extract_json(raw) == [{"x": 2}]


def test_extract_json_raises_on_garbage():
    try:
        _extract_json("no json here")
        assert False, "expected OllamaError"
    except OllamaError:
        pass


# ── Availability ────────────────────────────────────────────────────────
def test_api_ai_status_reports_offline(monkeypatch):
    enable_ollama(monkeypatch)
    with patch_available(available=False):
        resp = client.get("/api/ai/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "offline"
    assert body["engine"] == "offline-rules"
    assert body["model"] is None


def test_api_ai_status_reports_ollama(monkeypatch):
    enable_ollama(monkeypatch)
    with patch_available(available=True), \
         mock.patch.object(ollama_client, "available_models", return_value=["qwen2.5-coder:7b"]):
        resp = client.get("/api/ai/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "available"
    assert body["engine"] == "ollama"
    assert body["model"] == "qwen2.5-coder:7b"


def test_api_ai_status_lists_unpulled_model(monkeypatch):
    enable_ollama(monkeypatch)
    with patch_available(available=True), \
         mock.patch.object(ollama_client, "available_models", return_value=["llama3.2:3b"]):
        resp = client.get("/api/ai/status")
    body = resp.json()
    assert body["status"] == "available"
    assert body["model"] == "qwen2.5-coder:7b"  # configured model, but not in list below
    assert "not pulled yet" in body["message"]


def test_client_is_available_caches_result():
    client_inst = OllamaClient(base_url="http://unreachable-test:1", timeout=1)
    with mock.patch.object(client_inst, "available_models",
                           side_effect=[OllamaError("down"), OllamaError("still down")]):
        assert client_inst.is_available() is False
        # Second call must use the cache and NOT re-hit available_models.
        assert client_inst.is_available() is False
        assert client_inst.available_models.call_count == 1


# ── Resume analysis via Ollama ──────────────────────────────────────────
def test_resume_analysis_uses_ollama_when_available(monkeypatch):
    enable_ollama(monkeypatch)
    with patch_available(available=True), \
         mock.patch.object(ollama_client, "generate_json", return_value=ENRICHED_PROFILE):
        resp = client.post(
            "/api/resume/analyze-text",
            headers=auth_headers(),
            json={"resume_text": RESUME_TEXT},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_mode"] == "ollama"
    assert "llm" in data["skills"]  # an Ollama-only skill got merged in
    assert data["years_experience"] == 8.0
    assert "AI Platform Engineer" in data["suggested_roles"]


def test_resume_analysis_falls_back_offline_on_error(monkeypatch):
    enable_ollama(monkeypatch)
    with patch_available(available=True), \
         mock.patch.object(ollama_client, "generate_json", side_effect=OllamaError("boom")):
        resp = client.post(
            "/api/resume/analyze-text",
            headers=auth_headers(),
            json={"resume_text": RESUME_TEXT},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_mode"] == "offline-rules"
    assert "fastapi" in data["skills"]  # offline taxonomy extraction still worked


def test_resume_analysis_falls_back_offline_when_disabled():
    # conftest forces OLLAMA_ENABLED=false; make sure no Ollama call happens.
    with mock.patch.object(ollama_client, "is_available") as is_avail, \
         mock.patch.object(ollama_client, "generate_json") as gen:
        resp = client.post(
            "/api/resume/analyze-text",
            headers=auth_headers(),
            json={"resume_text": RESUME_TEXT},
        )
    assert resp.status_code == 200
    assert resp.json()["ai_mode"] == "offline-rules"
    is_avail.assert_not_called()
    gen.assert_not_called()


# ── Recommendations via Ollama ──────────────────────────────────────────
def _upload_profile() -> dict:
    return client.post(
        "/api/resume/analyze-text",
        headers=auth_headers(),
        json={"resume_text": RESUME_TEXT},
    ).json()


def test_recommendations_use_ollama_response(monkeypatch):
    enable_ollama(monkeypatch)
    jobs = client.get("/api/jobs?limit=10", headers=auth_headers()).json()
    payload = recommendations_payload([j["id"] for j in jobs])

    # generate_json is called once during profile upload, once for scoring.
    with patch_available(available=True), \
         mock.patch.object(ollama_client, "generate_json", side_effect=[ENRICHED_PROFILE, payload]):
        profile = _upload_profile()
        assert profile["ai_mode"] == "ollama"
        resp = client.get("/api/resume/recommendations?limit=10", headers=auth_headers())

    assert resp.status_code == 200
    recs = resp.json()
    assert recs, "expected at least one recommendation"

    # The agent only sends the top 8 offline-scored candidates to Ollama.
    enriched = [r for r in recs if r["ai_mode"] == "ollama"]
    assert 1 <= len(enriched) <= 8
    top = enriched[0]
    assert top["ai_reasoning"] == "The profile maps directly onto this role's stack."
    assert "kafka" in top["suggested_skills"]
    assert top["matched_skills"] == ["python", "fastapi"]

    # Every result, Ollama or not, still carries the shared fields.
    assert all("suggested_skills" in r and "match_score" in r for r in recs)


def test_recommendations_fall_back_offline_on_ollama_failure(monkeypatch):
    enable_ollama(monkeypatch)
    with patch_available(available=True), \
         mock.patch.object(
             ollama_client, "generate_json",
             side_effect=[ENRICHED_PROFILE, OllamaError("timeout")],
         ):
        _upload_profile()
        resp = client.get("/api/resume/recommendations", headers=auth_headers())

    assert resp.status_code == 200
    recs = resp.json()
    assert recs
    assert all(r["ai_mode"] == "offline-rules" for r in recs)
    assert all("rationale" in r and "match_score" in r for r in recs)


def test_recommendations_offline_when_ollama_unavailable(monkeypatch):
    enable_ollama(monkeypatch)
    with patch_available(available=False), \
         mock.patch.object(ollama_client, "generate_json") as gen:
        _upload_profile()
        resp = client.get("/api/resume/recommendations", headers=auth_headers())

    assert resp.status_code == 200
    recs = resp.json()
    assert all(r["ai_mode"] == "offline-rules" for r in recs)
    gen.assert_not_called()


def test_health_endpoint_reports_ai(monkeypatch):
    enable_ollama(monkeypatch)
    with patch_available(available=True), \
         mock.patch.object(ollama_client, "available_models", return_value=["qwen2.5-coder:7b"]):
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["ai"]["status"] == "available"