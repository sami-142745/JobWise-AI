# JobWise AI — AI-Powered Job Recommendation Platform

A full-stack web application that analyzes a user's resume with an AI agent and
recommends the best matching jobs. Built with **React**, **FastAPI**, and
**MongoDB**.

[![Stack](https://img.shields.io/badge/React-19-blue)](https://react.dev)
[![Backend](https://img.shields.io/badge/FastAPI-0.115-orange)](https://fastapi.tiangolo.com)
[![DB](https://img.shields.io/badge/MongoDB-green)](https://mongodb.com)
[![Python](https://img.shields.io/badge/Python-3.11-blueviolet)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-26%20passed-brightgreen)](#running-the-tests)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## Quick start

> Requires: Python 3.10+, Node 18+, and a running MongoDB server.

```bash
# 1. Backend  — http://localhost:8000  (API docs at /docs)
cd backend
pip install -r requirements.txt
python run.py

# 2. Frontend — http://localhost:3000 (in a second terminal)
cd frontend
npm install
npm start
```

Open **http://localhost:3000**, create an account, upload a resume, and view
your AI job recommendations. The API seeds a sample job catalogue on startup.

---

## Features

- **User registration & login** — secure JWT-based authentication with
  bcrypt-hashed passwords (`backend/app/routes/auth.py`).
- **AI resume analysis** — an agent (`backend/app/services/ai_agent.py`) that
  extracts skills, years of experience, and a summary from an uploaded resume
  (PDF, DOCX, or TXT, plus paste-as-text).
- **Job matching engine** — every job is scored against the candidate profile
  (skill coverage, experience level fit, and location) and ranked with an
  explainable match percentage and rationale.
- **Job search** — browse, search by keyword/location, view details, and open
  external applications.
- **Dashboard** — personalized top matches and profile statistics.
- **Resume management** — upload, drag-and-drop, re-analyse, and view the
  extracted profile.
- **Seed data** — the API seeds a realistic job catalogue on startup.
- **Tests & error handling** — 26 backend tests and consistent JSON error
  responses (401/404/409/413/422/503) with a global error handler.

---

## Architecture

```
┌───────────────┐  HTTP/JSON (JWT)   ┌─────────────────┐   pymongo   ┌─────────┐
│  React SPA    │ ─────────────────> │   FastAPI API   │ ──────────> │ MongoDB │
│  (port 3000)  │ <───────────────── │  (port 8000)   │ <────────── │         │
└───────────────┘                    └────────┬────────┘             └─────────┘
                                              │
                                   ┌──────────┴──────────┐
                                   │  AI Agent services  │
                                   │  resume analysis    │
                                   │  job matching       │
                                   └─────────────────────┘
```

### Backend layout

| Path | Purpose |
| --- | --- |
| `backend/app/main.py` | FastAPI app, CORS, global error handlers, health check |
| `backend/app/config.py` | Environment-based settings |
| `backend/app/database.py` | MongoDB connection + index creation |
| `backend/app/models/` | Pydantic request/response schemas |
| `backend/app/routes/` | `auth`, `jobs`, `resume` API endpoints |
| `backend/app/services/ai_agent.py` | The recommendation agent & matcher |
| `backend/app/services/resume_parser.py` | Skill/experience extraction |
| `backend/app/services/file_reader.py` | PDF / DOCX / TXT text extraction |
| `backend/app/services/seed.py` | Seed job catalogue |
| `backend/app/utils/auth.py` | Password hashing, JWT, current-user dependency |
| `backend/tests/` | pytest suite (26 tests) |

### Frontend layout

| Path | Purpose |
| --- | --- |
| `frontend/src/App.js` | Routes + auth provider |
| `frontend/src/api.js` | Centralized API client & token handling |
| `frontend/src/context/AuthContext.js` | Auth state (login/logout/session) |
| `frontend/src/components/` | NavBar, JobCard, ProtectedRoute, Spinner, Alert |
| `frontend/src/pages/` | Welcome, Login, Register, Dashboard, Jobs, JobDetail, Resume |

---

## Requirements

- Python 3.10+
- Node.js 18+
- MongoDB running locally on `localhost:27017` (or a `MONGO_URI` you supply)

---

## Getting started

### 1. MongoDB

Make sure MongoDB is running:

```bash
mongod --dbpath /path/to/data
```

or, on Windows, start the service:

```powershell
Start-Service MongoDB
```

### 2. Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt

# Optional: configure via environment (see backend/.env.example)
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux

python run.py                   # starts API on http://localhost:8000
```

The API will:

- connect to MongoDB and create indexes,
- seed a catalogue of sample jobs,
- serve interactive docs at `http://localhost:8000/docs`.

> ℹ️ The built-in recommendation **agent works fully offline**. To optionally
> power analysis with a real LLM, set `OPENAI_API_KEY` in `.env`.

### 3. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm start                       # starts UI on http://localhost:3000
```

Open **http://localhost:3000** — create an account, upload a resume, and view
your AI job recommendations.

> The frontend uses the API at `http://localhost:8000` (set via the
> `REACT_APP_API_URL` environment variable). The `package.json` proxy also
> forwards `/api` requests to the backend during development.

---

## Configuration

All backend settings are read from environment variables (a template ships at
`backend/.env.example`):

| Variable | Default | Description |
| --- | --- | --- |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `DATABASE_NAME` | `job_recommender` | MongoDB database name |
| `SECRET_KEY` | placeholder | JWT signing key — **must change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT lifetime (24h) |
| `OPENAI_API_KEY` | *(empty)* | Optional — the bundled agent works offline |
| `UPLOAD_DIR` | `uploads` | Where uploaded resumes are stored (git-ignored) |
| `MAX_UPLOAD_SIZE_MB` | `10` | Max resume file size |
| `SEED_JOBS` | `1` | Seed sample jobs at startup (set `0` to disable) |
| `CORS_ORIGINS` | `localhost:3000` | Allowed browser origins |

Frontend: `REACT_APP_API_URL` (default `http://localhost:8000`).

---

## Screenshots

*Add screenshots here by placing images in `docs/screenshots/` and referencing
them, e.g.*

```markdown
![Dashboard](docs/screenshots/dashboard.png)
```

---

## Running the tests

```bash
cd backend
python -m pytest tests -v
```

The tests use a real MongoDB instance (wiping `users`/`resumes` collections and
re-seeding jobs for a deterministic run). 26 tests cover authentication, job
search/CRUD, resume upload & parsing, and recommendations.

### Frontend smoke tests

```bash
cd frontend
CI=true npm test -- --watchAll=false     # create-react-app default
```

---

## API reference (summary)

Interactive OpenAPI docs: `http://localhost:8000/docs`

| Method | Endpoint | Auth | Description |
| --- | --- | --- | --- |
| POST | `/api/auth/register` | – | Create account → returns JWT |
| POST | `/api/auth/login` | – | Login → returns JWT |
| GET  | `/api/auth/me` | ✓ | Current user profile |
| GET  | `/api/jobs` | ✓ | List jobs (`?q=`, `?location=`) |
| GET  | `/api/jobs/search?q=python` | ✓ | Keyword search |
| GET  | `/api/jobs/{id}` | ✓ | Job detail |
| POST | `/api/jobs` | ✓ | Create a job |
| POST | `/api/resume/upload` | ✓ | Upload resume file (PDF/DOCX/TXT) |
| POST | `/api/resume/analyze-text` | ✓ | Analyze pasted resume text |
| GET  | `/api/resume/profile` | ✓ | Latest extracted resume profile |
| GET  | `/api/resume/recommendations` | ✓ | Ranked job matches for the user |

### Sample recommendation response

```json
{
  "id": "6654f3c1…",
  "title": "Senior Python Backend Engineer",
  "company": "CloudWorks",
  "match_score": 84.5,
  "matched_skills": ["python", "fastapi", "postgresql", "docker", "aws"],
  "missing_skills": ["kubernetes"],
  "rationale": "Highly recommended: strong skills match, experience level fits well, location-friendly."
}
```

---

## How the AI agent works

1. **Resume parsing** (`file_reader.py`) — extracts text from the uploaded
   file.
2. **Profile extraction** (`resume_parser.py`) — matches the text against a
   skills taxonomy and estimates years of experience from date ranges and
   explicit statements.
3. **Scoring** (`ai_agent.py`) — `JobMatcher` scores every job using a weighted
   formula:

```
score = 60% · skill coverage + 25% · experience fit + 15% · location fit
```

4. **Ranking** — results are sorted descending and returned with a rationale
   string and skill gap analysis (matched/missing) so users know how to
   improve.

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `ServerSelectionTimeoutError` / `could not connect to MongoDB` | Ensure MongoDB is running (see step 1). |
| `ModuleNotFoundError` | `pip install -r requirements.txt` in the activated venv. |
| Frontend API calls failing | Confirm the backend is on port 8000, or set `REACT_APP_API_URL`. |
| 401 on all endpoints | Log in again — your JWT may have expired. |
| Scanned-image PDF upload | Parsing requires text-based PDFs; export to text/DOCX first. |
| `password cannot be longer than 72 bytes` (old pip installs) | Ensure `bcrypt>=4.1` from `requirements.txt`; passlib-free hashing is used. |

---

## Security notes

- Passwords are hashed with **bcrypt** (SHA-256 pre-hash keeps any length
  safe).
- JWTs are signed with `SECRET_KEY` — **change it** in production.
- CORS is locked to the local dev origin; update `CORS_ORIGINS` for other
  origins.
- Set `MONGO_URI`, `SECRET_KEY`, and `OPENAI_API_KEY` via the environment, not
  the repository.

---

## Contributing

Contributions are welcome!

1. Fork the repository and create a feature branch.
2. Make your changes; keep the code style consistent.
3. Run the backend tests: `cd backend && python -m pytest tests -v`
4. Verify the frontend builds: `cd frontend && npm run build`
5. Open a pull request describing the change and any test results.

---

## License

MIT — see the [LICENSE](LICENSE) file for details.