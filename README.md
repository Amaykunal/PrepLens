# PrepLens

Editorial aggregation and comparison for competitive-exam aspirants. **This is a working core (MVP slice), not the full SRS.**
All articles are fictional **DEMO DATA**. Without `GEMINI_API_KEY` the app runs in demo mode and makes no AI calls.

## Run locally
```bash
cp .env.example .env                      # edit JWT_SECRET
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload             # API on :8000, docs at /docs, SQLite by default
pytest -q                                 # backend tests
cd ../frontend && npm install && npm run dev   # UI on :5173 (proxies /api to :8000)
```
With Postgres: `docker compose up --build` (set `DATABASE_URL` as in `.env.example` to use it locally).

## Environment variables
`DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `ADMIN_EMAIL` (that email becomes ADMIN on register), `GEMINI_API_KEY`, `GEMINI_MODEL`, `VITE_API_URL` (frontend build).

## GitHub and deployment
`git init && git add . && git commit -m "Initial commit"`, create an empty GitHub repo, then `git remote add origin <url> && git push -u origin main`. CI runs backend tests and the frontend build.
Deploy the backend (Docker image in `backend/`) to a container host with managed Postgres and set the env vars. Deploy `frontend/dist` (`npm run build`) to any static host with `VITE_API_URL` set to the backend URL, and add that origin to `CORS_ORIGINS`. GitHub Pages can host only the static frontend, never the FastAPI backend.

## Implemented
Register/login (PBKDF2 hashing, JWT), USER/ADMIN roles with `/api/admin/stats`, keyword search with type/publisher/date/sort filters and pagination, persistent bookmarks, Compare Viewpoints (demo mode or Gemini through a central prompt template with untrusted-text fencing and caching), editorial UI.

## Not implemented yet
Semantic search/pgvector, Celery/Redis ingestion and connectors, per-article AI analysis, topic intelligence, syllabus mapping, notes and folders, mains assistant, practice questions, digest, dashboard, admin UI, Alembic migrations, rate limiting, password reset, frontend tests.
