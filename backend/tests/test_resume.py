import io

from tests.conftest import RESUME_TEXT, auth_headers, client


def upload_resume_text():
    headers = auth_headers()
    return client.post(
        "/api/resume/analyze-text",
        headers=headers,
        json={"resume_text": RESUME_TEXT},
    )


def test_analyze_text_extracts_skills():
    resp = upload_resume_text()
    assert resp.status_code == 200
    data = resp.json()
    assert "fastapi" in data["skills"]
    assert "react" in data["skills"]
    assert any(s in ["python", "docker", "aws"] for s in data["skills"])


def test_analyze_text_requires_content():
    headers = auth_headers()
    resp = client.post(
        "/api/resume/analyze-text",
        headers=headers,
        json={"resume_text": "   "},
    )
    assert resp.status_code == 400


def test_profile_returns_latest_resume():
    upload_resume_text()
    resp = client.get("/api/resume/profile", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json()["skills"]


def test_profile_without_resume_fails():
    client.post(
        "/api/auth/register",
        json={
            "username": "noresume",
            "email": "noresume@example.com",
            "password": "password123",
            "full_name": "No Resume",
        },
    )
    token = client.post(
        "/api/auth/login",
        json={"email": "noresume@example.com", "password": "password123"},
    ).json()["access_token"]
    resp = client.get("/api/resume/profile", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_upload_txt_resume():
    headers = auth_headers()
    files = {"file": ("resume.txt", RESUME_TEXT.encode(), "text/plain")}
    resp = client.post("/api/resume/upload", headers=headers, files=files)
    assert resp.status_code == 201
    assert resp.json()["skills"]


def test_upload_unsupported_file_fails():
    headers = auth_headers()
    files = {"file": ("resume.exe", b"MZ\x90\x00", "application/octet-stream")}
    resp = client.post("/api/resume/upload", headers=headers, files=files)
    assert resp.status_code == 400


def test_bad_pdf_returns_clear_error():
    headers = auth_headers()
    files = {"file": ("resume.pdf", b"%PDF-1.4\nthis is not a real pdf", "application/pdf")}
    resp = client.post("/api/resume/upload", headers=headers, files=files)
    assert resp.status_code == 400


def test_recommendations_after_resume():
    upload_resume_text()
    resp = client.get("/api/resume/recommendations", headers=auth_headers())
    assert resp.status_code == 200
    recs = resp.json()
    assert len(recs) > 0
    rec = recs[0]
    assert "match_score" in rec
    assert "rationale" in rec
    assert "matched_skills" in rec
    # Python-heavy candidates should rank python jobs near the top
    top_titles = [r["title"].lower() for r in recs[:3]]
    assert any("python" in t for t in top_titles)


def test_recommendations_without_resume_fails():
    client.post(
        "/api/auth/register",
        json={
            "username": "norec",
            "email": "norec@example.com",
            "password": "password123",
            "full_name": "No Rec",
        },
    )
    token = client.post(
        "/api/auth/login",
        json={"email": "norec@example.com", "password": "password123"},
    ).json()["access_token"]
    resp = client.get(
        "/api/resume/recommendations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404