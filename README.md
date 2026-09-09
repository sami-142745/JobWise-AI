# JobWise AI

**An AI-powered, resume-based job recommendation platform — React + FastAPI + MongoDB, with local Ollama LLM inference and automatic offline fallback.**

---

## Project Overview

JobWise AI analyzes a candidate's resume and recommends the jobs they fit best. A user registers, uploads (or pastes) their resume, and the system extracts their skills, experience, current role, education, career interests, and suggested roles. Each job in the catalogue is then scored against that profile and ranked by fit, with an explainable match percentage, a human-readable rationale, and actionable skill suggestions.

The "AI" is a **local Ollama model** (`qwen2.5-coder:7b` by default) that enriches resume analysis and writes per-job reasoning — with no API keys and no cloud dependency. When Ollama is unavailable, slow, or disabled, the application seamlessly falls back to a built-in rule-based engine, so the platform **always works offline**.

The API exposes clean **REST endpoints** (JWT-secured) with interactive OpenAPI documentation, and ships with **automated backend and frontend tests**.

## Key Features

- **React single-page application** — fast, modern UI (Welcome, Login, Register, Dashboard, Browse Jobs, Job Detail, Resume) with client-side routing and authenticated views.
- **FastAPI REST backend** — typed, self-documenting API with interactive docs at `/docs`, consistent JSON errors, and a global exception handler.
- **MongoDB persistence** — users, resume profiles, and the job catalogue stored in MongoDB with auto-created indexes.
- **Authentication & authorization** — JWT-based login/registration with **bcrypt-hashed passwords**; protected endpoints and route guards.
- **AI-powered resume analysis** — extracts skills, years of experience, a summary, recent roles, education, career interests, and suggested roles from a PDF, DOCX, or TXT resume (or pasted text).
- **Intelligent job matching** — every job is scored by skill coverage, experience fit, and location, then ranked with an explainable match percentage and skill-gap analysis.
- **Ollama LLM integration** — a local `qwen2.5-coder:7b` model provides enriched analysis, LLM-written reasoning, and suggested skills for the top matches.
- **Offline AI fallback** — if Ollama is disabled, unreachable, times out, or returns invalid JSON, the deterministic rule-based engine handles the request; the active engine is surfaced in the UI.
- **Job search & browse** — keyword and location search, job details, and links to external applications.
- **Dashboard** — personalized top matches, profile statistics, and an AI status indicator.
- **Resume management** — drag-and-drop upload, re-analysis, paste-as-text, and a view of the extracted profile.
- **Seed data** — the API seeds a realistic job catalogue on startup.
- **Automated tests** — 40 backend tests (Ollama fully mocked) and 4 frontend tests; CI-friendly build script.
- **Git-ignored secrets & uploads** — `.env`, uploaded resume files, and runtime data are never committed.

## Tech Stack

| Layer | Technology | Role |
| --- | --- | --- |
| Frontend | **React 19**, React Router 6 | SPA, routing, protected routes, state via context |
| Build tooling | Create React App (react-scripts 5) | Dev server, bundling, tests (Jest + Testing Library) |
| Backend | **FastAPI** (Python 3.10+), Uvicorn | REST API, validation (Pydantic v2), async server |
| Database | **MongoDB** (pymongo) | Users, resume profiles, job catalogue |
| AI / LLM | **Ollama** — local **`qwen2.5-coder:7b`** | Resume enrichment, recommendation reasoning |
| Auth | PyJWT + bcrypt | JWT access tokens, password hashing |
| File parsing | pypdf, python-docx | PDF / DOCX / TXT resume text extraction |
| Testing | pytest + HTTPX, Jest + Testing Library | Backend (40 tests) and frontend (4 tests) suites |

> Development environment used: Python 3.11, Node 24, MongoDB on `localhost:27017`, Ollama `0.33.x` with `qwen2.5-coder:7b`.

## System Architecture

```
┌────────────────┐   HTTP/JSON (Bearer JWT)   ┌──────────────────┐   pymongo   ┌──────────┐
│   React SPA    │ ─────────────────────────> │   FastAPI API    │ ─────────> │  MongoDB │
│  (port 3000)   │ <───────────────────────── │   (port 8000)    │ <───────── │          │
└────────────────┘                            └────────┬─────────┘             └──────────┘
                                                        │
                                             ┌──────────┴──────────┐
                                             │   AI agent services │
                                             │  resume analysis    │
                                             │  job matching       │
                                             └──────┬───────┬──────┘
                                                    │       │  REST (HTTP)
                                                    │       └──────────────►  Ollama
                                                    │                          (port 11434)
                                                    │                      local qwen2.5-coder:7b
                                                    └── offline fallback
                                                        (rule-based JobMatcher)
```

Flow in one line: the browser calls the React app, the React app calls the FastAPI REST API, the API reads/writes MongoDB, and the AI agent services call the local Ollama model — or the built-in offline matcher when the model isn't reachable.

## How the Application Works

1. **Create an account** — register or log in to obtain a JWT; the token is stored and sent with every request.
2. **Add your resume** — upload a PDF/DOCX/TXT file (drag‑and‑drop) or paste the text.
3. **Profile extraction** — the backend immediately parses the resume: first with a fast, deterministic offline parser (`resume_parser.py`), then enriched by the Ollama model when available. The result is stored as your resume profile.
4. **Job matching** — your profile is scored against every job in the catalogue using the offline matcher's weighted formula (see §8), producing a baseline ranking instantly.
5. **AI ranking (when available)** — the top candidates are sent to Ollama, which returns an adjusted score, a written reason, matched/missing skills, and `suggested_skills`. Enriched results are ranked first.
6. **Explore** — the Dashboard shows your top matches and profile stats; Browse Jobs lets you search by keyword/location and open external applications.
7. **Improve with feedback** — every recommendation shows why you match, where you fall short, and what to learn next.

## AI/Ollama Integration

- **Local and private** — no API keys, no cloud round-trips; the model runs on your machine via [Ollama](https://ollama.com).
- **Default model** — `qwen2.5-coder:7b` (configure with `OLLAMA_MODEL`).
- **Client layer** (`backend/app/services/ollama_service.py`) — an HTTP client for the Ollama REST API (`/api/tags`, `/api/generate`) with:
  - an **availability probe** that is cached for 15 seconds so status checks stay fast;
  - **robust JSON extraction** that tolerates surrounding prose and markdown
    code fences around the model's JSON response;
  - configurable timeout, max tokens, and temperature.
- **Structured prompts** — resume analysis and recommendation calls use strict "JSON only" system prompts so the raw text can be validated and merged deterministically.
- **Engine reporting** — `GET /api/ai/status` returns the active engine (`ollama` vs `offline-rules`), the configured model, and the pulled models list. The same info is folded into `GET /health`, and the frontend shows a live status pill in the navbar (polled every 30 seconds).
- **Test isolation** — every test that exercises the Ollama paths uses mocked responses; not a single test requires a real model server.

## Resume Analysis and Job Matching

**Resume analysis** (`file_reader.py` → `resume_parser.py` → `ai_agent.py`):

1. Text is extracted from the uploaded file (pypdf for PDF, python-docx for DOCX, plain text for TXT).
2. The offline parser matches the text against a skills taxonomy and estimates years of experience from date ranges and explicit statements.
3. When Ollama is enabled and reachable, the model receives the same resume and returns structured JSON — skills, years, roles, education, interests, and suggested roles — which is merged with (and deduplicated against) the offline result.
4. The final profile (`ResumeProfileOut`) exposes `ai_mode` so clients know which engine produced it.

**Job matching** (`ai_agent.py`):

- `JobMatcher` computes a baseline score for every job:

```
score = 60% · skill coverage + 25% · experience fit + 15% · location fit
```

- Each job returns `match_score` (0–100), `matched_skills`, `missing_skills`, and a clear `rationale`.
- When Ollama is available, the top candidates (capped to keep the request fast) are sent to the model, which returns a re-scored set with an `ai_reasoning` explanation and `suggested_skills` to close the gap. Enriched results are ranked ahead of the rest.
- Every result — Ollama or offline — carries the shared fields, so the frontend renders identically regardless of engine.

## API Endpoints

Interactive OpenAPI documentation: **`http://localhost:8000/docs`**

| Method | Endpoint | Auth | Description |
| --- | --- | --- | --- |
| GET  | `/` | – | Service info, links to docs/health/status |
| GET  | `/health` | – | Health check (database + AI engine status) |
| GET  | `/api/ai/status` | – | Active AI engine, configured model, pulled models |
| POST | `/api/auth/register` | – | Create account → returns JWT |
| POST | `/api/auth/login` | – | Log in → returns JWT |
| GET  | `/api/auth/me` | ✓ | Current user profile |
| GET  | `/api/jobs` | ✓ | List jobs (`?q=` keyword, `?location=`) |
| GET  | `/api/jobs/search` | ✓ | Keyword + location search |
| GET  | `/api/jobs/{id}` | ✓ | Job detail |
| POST | `/api/jobs` | ✓ | Create a job |
| POST | `/api/resume/upload` | ✓ | Upload resume file (PDF/DOCX/TXT) |
| POST | `/api/resume/analyze-text` | ✓ | Analyze pasted resume text |
| GET  | `/api/resume/profile` | ✓ | Latest extracted resume profile |
| GET  | `/api/resume/recommendations` | ✓ | Ranked job matches for the user |

Authenticated endpoints return HTTP `401` without a valid Bearer token. The API centralizes error handling for `500` (unexpected), `503` (database down), and Pydantic `422` (validation) responses.

### Example: recommendation result

```json
{
  "id": "6654f3c1…",
  "title": "Senior Python Backend Engineer",
  "company": "CloudWorks",
  "match_score": 84.5,
  "matched_skills": ["python", "fastapi", "postgresql", "docker", "aws"],
  "missing_skills": ["kubernetes"],
  "suggested_skills": ["kubernetes", "kafka"],
  "ai_reasoning": "The profile maps directly onto this role's stack.",
  "ai_mode": "ollama",
  "rationale": "Highly recommended: strong skills match, experience level fits well, location-friendly."
}
```

> `ai_mode` is `"ollama"` when the result came from the local model and `"offline-rules"` when the fallback engine produced it. `ai_reasoning` is the LLM's explanation (null in offline mode, where `rationale` is used).

## Project Structure

```
jobwise-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, error handlers, /health, /api/ai/status
│   │   ├── config.py            # Environment-based settings (incl. Ollama)
│   │   ├── database.py          # MongoDB connection + index creation
│   │   ├── models/              # Pydantic schemas (Token, User, Job, JobMatch, ResumeProfile)
│   │   ├── routes/              # auth.py · jobs.py · resume.py
│   │   ├── services/
│   │   │   ├── ai_agent.py      # RecommendationAgent + JobMatcher (Ollama + fallback)
│   │   │   ├── ollama_service.py# Ollama HTTP client, JSON parsing, availability probe
│   │   │   ├── resume_parser.py # Offline skill/experience extraction
│   │   │   ├── file_reader.py   # PDF / DOCX / TXT text extraction
│   │   │   ├── seed.py          # Seed job catalogue
│   │   │   └── job_service.py   # Resume/Job business logic + AI status helper
│   │   └── utils/auth.py        # Password hashing, JWT, current-user dependency
│   ├── tests/                   # 40 pytest tests (Ollama mocked)
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py                   # Dev entrypoint (port 8000)
└── frontend/
    ├── src/
    │   ├── App.js               # Routes + AuthProvider + layout
    │   ├── api.js               # Central API client, token handling
    │   ├── context/AuthContext.js
    │   ├── components/          # NavBar, AiStatusIndicator, JobCard, ProtectedRoute, Spinner, Alert
    │   └── pages/               # Welcome, Login, Register, Dashboard, Jobs, JobDetail, Resume, NotFound
    ├── public/
    ├── package.json
    └── src/setupTests.js, *.test.js  # Jest + Testing Library tests
```

## Installation and Setup

**Prerequisites:** Python 3.10+, Node 18+, MongoDB running locally, and (recommended) [Ollama](https://ollama.com).

### MongoDB

```bash
mongod --dbpath /path/to/data        # or, on Windows:
Start-Service MongoDB                # PowerShell
```

### Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate             # Windows
# source .venv/bin/activate          # macOS / Linux

pip install -r requirements.txt

# Optional: configure via environment (see backend/.env.example)
copy .env.example .env               # Windows
# cp .env.example .env               # macOS / Linux
```

### Ollama (recommended)

```bash
# install Ollama, then pull the default model
ollama pull qwen2.5-coder:7b

# verify the local server responds
curl http://localhost:11434/api/tags
```

> The app works without Ollama. If it's not running or times out, requests fall back to the built-in rule-based engine. Disable it entirely with `OLLAMA_ENABLED=false`.

### Frontend

```bash
cd frontend
npm install
```

## Environment Variables

All backend settings are read from environment variables (template: `backend/.env.example`):

| Variable | Default | Description |
| --- | --- | --- |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `DATABASE_NAME` | `job_recommender` | MongoDB database name |
| `SECRET_KEY` | placeholder | JWT signing key — **must change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT lifetime (24 h) |
| `OLLAMA_ENABLED` | `true` | Use local Ollama; falls back when unreachable |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Model used for analysis & ranking |
| `OLLAMA_TIMEOUT` | `300` | Request timeout (s) — first cold load is slow |
| `OLLAMA_MAX_TOKENS` | `2048` | Max tokens in the model response |
| `OLLAMA_TEMPERATURE` | `0.2` | Sampling temperature (lower = more deterministic) |
| `UPLOAD_DIR` | `uploads` | Where uploaded resumes are stored (git-ignored) |
| `MAX_UPLOAD_SIZE_MB` | `10` | Max resume file size |
| `SEED_JOBS` | `1` | Seed sample jobs at startup (`0` disables) |
| `CORS_ORIGINS` | `localhost:3000` | Allowed browser origins |

**Frontend:** `REACT_APP_API_URL` (default `http://localhost:8000`). During development the `package.json` proxy also forwards `/api` to the backend.

## Running the Application

**Backend** (terminal 1):

```bash
cd backend
python run.py                        # API on http://localhost:8000 · docs at /docs
```

On startup the API connects to MongoDB, creates indexes, and seeds the sample job catalogue.

**Frontend** (terminal 2):

```bash
cd frontend
npm start                            # UI on http://localhost:3000
```

Open **http://localhost:3000**, create an account, upload a resume, and view your AI job recommendations on the Dashboard.

**Production build (frontend):**

```bash
cd frontend
npm run build                        # optimized static bundle in frontend/build
```

## Testing

**Backend** (requires a running MongoDB; uses a real instance like the app):

```bash
cd backend
python -m pytest tests -v
```

- **40 tests** covering authentication, job search/CRUD, resume upload & parsing, recommendations, and the Ollama integration.
- The suite wipes `users`/`resumes` and re-seeds jobs for a deterministic run.
- **Ollama is always mocked** (`tests/test_ollama.py`); the deterministic suites force the offline engine, so no test ever calls a real model server.

**Frontend** (Jest + Testing Library):

```bash
cd frontend
CI=true npm test -- --watchAll=false  # 4 tests (routing smoke + JobCard AI fields)
```

## Security Notes

- Passwords are hashed with **bcrypt** (SHA-256 pre-hash keeps passwords of any length safe).
- JWTs are signed with `SECRET_KEY` — **change it in production**.
- CORS is locked to the local dev origin; update `CORS_ORIGINS` for any other origin you trust.
- Secrets (`MONGO_URI`, `SECRET_KEY`) are supplied via environment variables, never committed.
- Uploaded resume files are stored in a git-ignored directory.
- Ollama runs as a local service on `localhost:11434` — in production, keep it bound to localhost and do not expose it publicly.

## AI Offline Fallback

The system is designed so the model is an *enhancement*, never a dependency:

1. **Always available baseline** — every analysis and recommendation first runs through the deterministic offline parser and `JobMatcher`; results are ready immediately.
2. **Optional enrichment** — the same request is upgraded with the Ollama model only when it is enabled, reachable, and responsive.
3. **Graceful degradation** — if Ollama is disabled, offline, times out, or returns unparsable JSON, the offline result is returned unchanged (a fallback decision is logged and the response's `ai_mode` reads `offline-rules`).
4. **Transparency** — `GET /api/ai/status` (`status` / `engine` / `model`), the `/health` AI block, and the navbar indicator all tell the user which engine served the result.
5. **Safety-first defaults** — a generous `OLLAMA_TIMEOUT` (300 s) covers cold model loads; the top-candidate cap and token limits keep prompts lean; tests prove the fallback path with simulated failures.

Result: the platform fully works with **no** model installed, and gets smarter when Ollama is present.

## Future Enhancements

*Roadmap — none of these are implemented yet.*

- Resume up-skilling plans generated per candidate (a learning path built from `suggested_skills` gaps).
- More file formats (e.g., OCR for scanned PDFs).
- Saved job alerts / email or in-app notifications on new matches.
- Cloud deployment guide (containerized API + managed MongoDB) for production hosting.
- Swappable model configurations and a benchmark of recommendation quality across models.
- Candidate-preferences UI (locations, roles, salary filters) feeding the matcher.

---

## Contributing

1. Fork the repository and create a feature branch.
2. Keep the code style consistent.
3. Run backend tests: `cd backend && python -m pytest tests -v`
4. Verify the frontend builds: `cd frontend && npm run build`
5. Open a pull request describing the change and test results.

## License

MIT — see the [LICENSE](LICENSE) file for details.