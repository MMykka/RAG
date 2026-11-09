# RAG Project

## Instructions for Claude
- After every update to this project (code change, new file, dependency, config, git action), append an entry to the **Change Log** below before finishing the turn.
- Each entry: date, what changed, which files, and why.
- Follow `RAG_Tech_Stack.md` and `RAG_TODO.md` to the dot (layout, names, order). Do not add, skip or reorder anything.
- Never start a step without the user's explicit approval. Propose the next step, then wait.
- Keep the **Project Overview** and **Setup** sections current when they change.

## Project Overview
RAG project. Remote: https://github.com/MMykka/RAG.git (branch: not yet set)

## Setup
- Git initialized locally, `origin` set to the remote above.

## Change Log
### 2026-11-09
- Initialized git repository and added `origin` remote https://github.com/MMykka/RAG.git.
- Created CLAUDE.md to track project overview and all updates.
- Committed CLAUDE.md and pushed to `origin/main` (branch renamed to `main`, upstream tracking set).

### 2026-11-09 (Day 0 setup)
- Read `RAG_Tech_Stack.md` and `RAG_TODO.md` (the plan: React+Vite, FastAPI, SQLAlchemy, Alembic, Supabase Postgres + pgvector, Ollama, Redis, Nginx, Docker Compose).
- Day 0 item 1: created `backend/` layout (`app/{models,schemas,routers,services}`, `alembic/versions`, `tests`) with `__init__.py` files.
- Day 0 item 2: created venv at `backend/.venv` and installed deps from `backend/requirements.txt` (fastapi, uvicorn, gunicorn, sqlalchemy, alembic, psycopg2-binary, pgvector, ollama, redis, slowapi, pytest, pydantic-settings, python-dotenv, httpx).
- Day 0 item 3: scaffolded `frontend/` with Vite + React template (`npm install` not run yet).
- Decisions: Ollama and Docker are NOT installed now; to be installed later. Only Day 0 items 1-3 are in scope for now; items 4-8 are pending.

### 2026-11-09 (layout fix)
- Fixed: the Vite scaffold had landed in `backend/frontend/` by mistake; moved it to the root `frontend/` and removed the stray folder.
- Brought the project to the exact layout in `RAG_Tech_Stack.md` (RAG root = `company-chatbot/`), with empty placeholder files:
  - backend: `app/{main,config,database,dependencies}.py`, `app/routers/{auth,conversations,stream,export,stats}.py`, `app/services/{llm,rag,export,cache}.py`, `Dockerfile`
  - frontend/src: `api/`, `components/{Sidebar,ChatWindow,MessageBubble,StatsDashboard}.jsx`, `hooks/useStream.js`, `pages/{ChatPage,StatsPage}.jsx`
  - root: `nginx/nginx.conf`, `docker-compose.yml`, `.env.example`, `README.md`

### 2026-11-09 (Day 0: Supabase)
- User created the Supabase project in the cloud (project ref `madhblhschpzxismtsxu`).
- Put the direct connection string (port 5432, for Alembic migrations) in root `.env` as `DATABASE_URL_DIRECT`, with `[YOUR-PASSWORD]` placeholder for the user to replace. `.env` is not committed.
- Pending: the pooler string (port 6543, for the running app) needs the region from the Supabase dashboard (Connect > Transaction pooler). `.gitignore` for `.env` is a later Day 0 step; do not commit until then.

### 2026-11-09 (Day 0: Supabase connection verified)
- Direct host `db.<ref>.supabase.co` failed (IPv6-only, user's network is IPv4). User switched `DATABASE_URL_DIRECT` in `.env` to the Supabase Session pooler string (IPv4, port 5432).
- Test with psycopg2 succeeded: PostgreSQL 17.11. Supabase connection works.
- Still pending: pooler string (6543) for the app. Migrations use the connection that was just verified.

### 2026-11-09 (Day 0: Supabase step complete, .env files)
- Marked complete: "Create the Supabase project and get the connection strings". Direct/session string verified; the app pooler string (6543) is deferred to when `config.py` / `database.py` are written.
- Kept the existing `.env` (holds the user's real `DATABASE_URL_DIRECT`; never commit).
- Created `.env.example` with a placeholder `DATABASE_URL_DIRECT` (no secrets).
- Created root `.gitignore` containing `.env`; verified with `git check-ignore`.

### 2026-11-09 (.gitignore)
- Added `.venv/`, `node_modules/`, `__pycache__/` to root `.gitignore` (alongside `.env`) so the virtual environment, npm packages and Python caches are never committed.

### 2026-11-09 (commit)
- Committed and pushed Day 0 progress (layout, requirements, frontend scaffold, `.env.example`, `.gitignore`) to `origin/main`. `.env` was excluded.
