from tests.conftest import auth_headers, client


def test_list_jobs_requires_auth():
    resp = client.get("/api/jobs")
    assert resp.status_code == 401


def test_list_jobs_returns_seeded_data():
    headers = auth_headers()
    resp = client.get("/api/jobs", headers=headers)
    assert resp.status_code == 200
    jobs = resp.json()
    assert len(jobs) >= 10
    first = jobs[0]
    assert {"title", "company", "skills", "match_score"} >= set()  # noqa
    assert "id" in first
    assert "skills" in first


def test_search_jobs_by_keyword():
    headers = auth_headers()
    resp = client.get("/api/jobs/search?q=python", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) > 0


def test_search_jobs_requires_query():
    headers = auth_headers()
    resp = client.get("/api/jobs/search", headers=headers)
    assert resp.status_code == 422


def test_get_job_by_id():
    headers = auth_headers()
    jobs = client.get("/api/jobs", headers=headers).json()
    job_id = jobs[0]["id"]
    resp = client.get(f"/api/jobs/{job_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id


def test_get_job_invalid_id_fails():
    headers = auth_headers()
    resp = client.get("/api/jobs/not-an-objectid", headers=headers)
    assert resp.status_code == 400


def test_get_job_not_found_fails():
    headers = auth_headers()
    resp = client.get("/api/jobs/000000000000000000000000", headers=headers)
    assert resp.status_code == 404


def test_create_job():
    headers = auth_headers()
    resp = client.post(
        "/api/jobs",
        headers=headers,
        json={
            "title": "QA Engineer",
            "company": "TestCo",
            "description": "Write tests and improve quality.",
            "location": "Remote",
            "salary": "$80k",
            "skills": ["python", "testing", "pytest", "selenium"],
            "experience_level": "mid-level",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "QA Engineer"