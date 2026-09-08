import os
import time

# Force the deterministic offline engine for the whole suite. Ollama-specific
# behavior is tested separately with mocked responses (see test_ollama.py).
os.environ["OLLAMA_ENABLED"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import connect  # noqa: E402
from app.main import app  # noqa: E402
from app.services.seed import seed_jobs  # noqa: E402

connect()

from app.database import get_db  # noqa: E402

# Deterministic test database: wipe user/resume state, reseed fresh jobs.
get_db().users.delete_many({})
get_db().resumes.delete_many({})
seed_jobs(force=True)

client = TestClient(app)


def auth_headers() -> dict:
    resp = client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "secret123",
        },
    )
    if resp.status_code == 200:
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "secret123",
            "full_name": "Test User",
        },
    )
    data = resp.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


RESUME_TEXT = """
John Doe — Senior Full-Stack Developer

Summary
Python developer with 7 years of experience building web applications.
Strong skills in Python, FastAPI, React, PostgreSQL, Docker and AWS.

Experience
2020 – present: Senior Backend Engineer, CloudWorks
    Built microservices with FastAPI and Kubernetes.
2016 – 2020: Full Stack Developer, Startify
    Developed web apps with React and Node.js.

Education
BSc Computer Science, 2015

Skills
Python, FastAPI, Django, React, TypeScript, PostgreSQL, MongoDB,
Docker, Kubernetes, AWS, Terraform, CI/CD, REST API, Machine Learning, Pandas
"""


def wait_for(recommendations: bool = False):
    time.sleep(0.1)