# RAG Project

## Instructions for Claude
- After every update to this project (code change, new file, dependency, config, git action), append an entry to the **Change Log** below before finishing the turn.
- Each entry: date, what changed, which files, and why.
- Always refer to `RAG_Tech_Stack.md` (stack, layout, connection strings) and `RAG_TODO.md` (the step list) in the project root before starting or proposing any step. Tick items in `RAG_TODO.md` only once they are done.
- Follow `RAG_Tech_Stack.md` and `RAG_TODO.md` to the dot (layout, names, order). Do not add, skip or reorder anything.
- Never start a step without the user's explicit approval. Propose the next step, then wait.
- Keep the **Project Overview** and **Setup** sections current when they change.

## Working Style (learned from the user)
- The user writes the code themselves. Guide with hints and small snippets, create empty files only when asked, then review their code and report what is wrong. Do not rewrite their code unprompted.
- Explain in plain English, step by step, and give the exact commands (Windows PowerShell, e.g. `.venv\Scripts\alembic.exe ...`, run from `backend/`). Say what each line of code does when asked.
- When the user asks to "check" something, read the files and actually run the check; report real findings, including extras beyond the plan.
- Commit and push only when the user asks. Before pushing, make sure ignored files stay ignored and the Supabase password is in no pushed file.
- Never print or copy the password from `.env`; use placeholders in docs and logs. If the user pastes it, do not repeat it.
- Always log changes in this root `CLAUDE.md` (use its absolute path; a stray `backend/CLAUDE.md` was once created by running from the wrong directory).

## Project Overview
RAG project. Remote: https://github.com/MMykka/RAG.git (branch: main)

## Setup
- Git: `origin` is the remote above, branch `main`. `.env`, `.venv/`, `node_modules/`, `__pycache__/` are gitignored.
- Backend: Python 3.12 venv at `backend/.venv`, packages in `backend/requirements.txt` (fastapi, uvicorn, sqlalchemy, alembic, psycopg2-binary, pgvector, ollama, pytest). Run Alembic from `backend/`.
- Frontend: Vite + React scaffold in `frontend/` (`npm install` not run on this PC yet).
- Database: Supabase Postgres, reached through the Session pooler string in root `.env` as `DATABASE_URL_DIRECT` (IPv4 network, so the direct host does not work). Tables `users`, `conversations`, `messages` exist; Alembic is at `2e87aeab9ed0 (head)`; pgvector is enabled.
- Not installed (deliberate): Ollama, Docker. The app pooler string (port 6543) is not added yet; `settings.database_url` falls back to the direct URL.
- `README.md` documents new-PC setup and the Alembic workflow.

## Current Progress
- Done: `RAG_TODO.md` Day 0 (except confirming Supabase with the company and installing Ollama) and Week 1 Days 1-2 (Database Schema).
- Next: Week 1 Days 3-4, Backend APIs (waiting for user approval to start).

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

### 2026-11-09 (Day 0: backend install, redone to the dot)
- Approved step: `[stack] Backend: install fastapi uvicorn sqlalchemy alembic psycopg2-binary pgvector ollama pytest`.
- Earlier install had extras not in the plan; uninstalled gunicorn, redis, slowapi, pydantic-settings, python-dotenv from `backend/.venv` (httpx stays only as a dependency of ollama).
- Rewrote `backend/requirements.txt` to exactly those 8 packages. `pip check` clean and all imports verified.
- gunicorn, redis, slowapi come in later steps (Go-Live) when the plan calls for them.
- Cleanup: that backend-install entry had been written to a stray `backend/CLAUDE.md` by mistake; merged it into this file and removed the stray file.

### 2026-11-09 (Day 0: config.py and database.py)
- Approved step: `[stack] Add config.py (settings from .env) and database.py (engine, session, get_db())`. Both files were empty placeholders before.
- `backend/app/config.py`: loads root `.env` with a small stdlib loader (no extra package, since pydantic-settings/python-dotenv are not in the plan). `settings.database_url_direct` (Alembic) and `settings.database_url` (app; uses `DATABASE_URL` if set, else falls back to the direct URL until the 6543 pooler string is added).
- URLs are rewritten to `postgresql+psycopg2://` because SQLAlchemy 2.1 defaults plain `postgresql://` to psycopg v3, which is not installed.
- `backend/app/database.py`: `engine` (pool_pre_ping), `SessionLocal`, declarative `Base`, and `get_db()` generator.
- Verified against Supabase: `select 1` returned 1 through `get_db()`.

### 2026-11-09 (Week 1: users table, user writes it)
- Ollama step skipped by the user (not installing Ollama on this PC); moved on to Week 1.
- Step: `Create users table (id, email, created_at)`. The user is writing `backend/app/models/user.py` themselves with Claude guiding. A draft written by Claude was deleted at the user's request.
- Created empty `backend/app/models/user.py` for the user to fill in.
- Users table step complete: `backend/app/models/user.py` written by the user. Columns: `id`, `username` (unique), `email` (unique), `password_hash`, `created_at`, `updated_at`. The user deliberately kept `username`, `password_hash`, `updated_at` beyond the plan's `(id, email, created_at)` because they will be needed later. Model only; the table is not in Supabase until the Alembic steps.

### 2026-11-09 (Week 1: conversations table)
- Step `Create conversations table (id, user_id, title, created_at, updated_at)`: user wrote `backend/app/models/conversations.py` (`Conversation`, table `conversations`). Reviewed by Claude: columns match the plan and the model loads.
- Open points: `user_id` has no ForeignKey yet (comes with the "foreign key constraints and cascading deletes" item); `title` is `nullable=False` with no default, which a new empty chat will hit. Table not in Supabase until the Alembic steps.

### 2026-11-09 (Week 1: messages table)
- Step `Create messages table (id, conversation_id, role, content, tokens_used, created_at)`: user wrote `backend/app/models/messages.py` (`Message`). Columns match the plan and the model loads.
- Review findings given to the user (not yet changed): `content` is `String(255)` (too short for LLM replies, should be `Text`); `tokens_used` is not nullable/no default (user messages have no count yet); `created_at` is annotated `Mapped[DateTime]` (should be `Mapped[datetime]`); `conversation_id` has no ForeignKey yet (later item).
- Messages model fixes checked: `content` is now `Text`, `tokens_used` nullable, `created_at` annotated `Mapped[datetime]`. Remaining nit: `content` annotation is `Mapped[Text]` (should be `Mapped[str]`). FK on `conversation_id` still pending (later item).
- Messages model re-checked: `content` is `Mapped[str]` with `Text`, `tokens_used` is `Mapped[int | None]`. All review findings resolved except the FK on `conversation_id` (later item). Loads cleanly.

### 2026-11-09 (Week 1: indexes)
- Step `Add indexes on user_id, conversation_id, created_at`: user added `index=True` and Claude checked. Registered: `conversations` (user_id, created_at, updated_at), `messages` (conversation_id, created_at), `users` (created_at).
- Beyond the plan / my advice: `users.created_at` and `conversations.updated_at` indexes (user's choice; to be kept or removed). Simple single-column indexes chosen over composites since scale is ~100 users. Not in Supabase until the Alembic steps.

### 2026-11-09 (Week 1: foreign keys, in progress)
- User added `ForeignKey` imports and FKs in `conversations.py` (`user_id`) and `messages.py` (`conversation_id`). Check found a bug: `ondelete="CASCADE"` was written outside the `ForeignKey(...)` parentheses, so the models raise `TypeError` on import. Fix pending (user).
- Foreign keys fixed by the user (`ondelete="CASCADE"` moved inside `ForeignKey(...)`). Verified by the user's check: `conversations.user_id -> users.id CASCADE`, `messages.conversation_id -> conversations.id CASCADE`. Step `Add foreign key constraints and cascading deletes` complete (model level; not in Supabase until Alembic).

### 2026-11-09 (Week 1: relationships, in progress)
- User started `relationship(...)` lines. Check found: wrong/circular imports (`from backend.app.models... import ...`, causes ModuleNotFoundError); `User.conversations` missing `cascade="all, delete-orphan"`; `Conversation.messages` missing; `models/__init__.py` still empty. Fixes pending (user).
- Relationships check: imports fixed, cascade added, `Conversation.messages` added, `models/__init__.py` filled. Remaining error: `Conversation.user` and `Message.conversation` lines were lost in editing, so `back_populates` has nothing to match. Restore pending (user).
- Relationships complete: user's check printed `relationships ok`. `User.conversations` and `Conversation.messages` use `cascade="all, delete-orphan"`; `Conversation.user` and `Message.conversation` are the back-references; `models/__init__.py` imports all three models. Step `Define SQLAlchemy models ... with relationship(..., cascade="all, delete-orphan")` complete.

### 2026-11-09 (plan files added)
- Copied the user's original `RAG_TODO.md` and `RAG_Tech_Stack.md` from Downloads into the project root (unmodified). These are the source of truth for the build.
- Ticked completed items in `RAG_TODO.md`: Day 0 (repo layout, backend install, frontend scaffold, Supabase project, `.env`/`.env.example`/`.gitignore`, `config.py`/`database.py`) and Week 1 Days 1-2 (users, conversations, messages tables, indexes, foreign keys/cascades, SQLAlchemy models with relationships). Left unticked: confirm Supabase with company, install Ollama (skipped), idempotent migrations, Alembic items, pgvector.
- Added a standing instruction to the top of this file: always refer to `RAG_Tech_Stack.md` and `RAG_TODO.md` before starting or proposing any step. Also corrected the Project Overview branch to `main`.

### 2026-11-09 (Week 1: Alembic init)
- Step `Initialize Alembic (alembic init) and point it at the models`, part 1: removed my empty `backend/alembic/versions` placeholder (init refuses a non-empty dir) and ran `alembic init alembic` from `backend/`. Created `backend/alembic.ini`, `backend/alembic/{env.py,README,script.py.mako,versions/}`.
- Part 2 pending (user edits `backend/alembic/env.py`): import `settings`, `Base` and `app.models`; set `target_metadata = Base.metadata`; set `sqlalchemy.url` from `settings.database_url_direct` (migrations use the direct/session connection).
- Alembic env.py edited by the user (imports `settings`, `Base`, `app.models`; `target_metadata = Base.metadata`; `sqlalchemy.url` from `settings.database_url_direct`). `alembic current` connected to Supabase successfully (PostgresqlImpl, transactional DDL). Step `Initialize Alembic (alembic init) and point it at the models` complete and ticked in `RAG_TODO.md`.

### 2026-11-09 (Week 1: first migration generated)
- Ran `alembic revision --autogenerate -m "create users conversations messages"`: created `backend/alembic/versions/275de5630e6f_create_users_conversations_messages.py` (revision `275de5630e6f`, first migration). Database not changed yet.
- Reviewed by Claude: creates `users`, `conversations`, `messages` with the right columns, unique constraints on `username`/`email`, FKs with `ondelete='CASCADE'`, `messages.content` as Text, `tokens_used` nullable, all indexes, and `downgrade()` drops in reverse order. Nothing wrong found.
- Pending: `alembic upgrade head` (not run). `RAG_TODO.md` item left unticked until the upgrade is done.

### 2026-11-09 (Week 1: migration regenerated with title default)
- User set `conversations.title` to `server_default="New chat"` (still NOT NULL), deleted the first migration `275de5630e6f_...` (never applied) and regenerated: `backend/alembic/versions/2e87aeab9ed0_create_users_conversations_messages.py` (revision `2e87aeab9ed0`, the only migration).
- Claude reviewed the new migration and all three models + `models/__init__.py`: all consistent. `title` now has `server_default='New chat'`. Database still unchanged; `alembic upgrade head` pending.
- Ran `alembic upgrade head` against Supabase (user approved): applied `2e87aeab9ed0`. Verified with SQLAlchemy inspector: tables `users`, `conversations`, `messages` and `alembic_version` exist with the expected columns; `alembic current` shows `2e87aeab9ed0 (head)`. Ticked `Generate migrations ... before running alembic upgrade head` in `RAG_TODO.md`.

### 2026-11-09 (Week 1: pgvector)
- User ran `CREATE EXTENSION IF NOT EXISTS vector;` in the Supabase SQL Editor (Success). Claude verified via `pg_extension` query from the backend connection; extension `vector` is enabled. Ticked in `RAG_TODO.md`. No migration needed (extension only; the `chunks` table with a vector column comes in Week 2).

### 2026-11-09 (Week 1: idempotent migration)
- User made `2e87aeab9ed0_create_users_conversations_messages.py` idempotent: `upgrade()` wraps each table + its indexes in `if "<table>" not in existing`, `downgrade()` guards each drop with `if "<table>" in existing`, using `sa.inspect(op.get_bind()).get_table_names()`.
- Claude reviewed it (compiles, structure correct) and tested: ran `upgrade()` against the live DB inside a rolled-back transaction; no error and tables unchanged. Ticked `Make migrations idempotent` in `RAG_TODO.md`. This completes the Days 1-2 Database Schema section.
- Idempotency tested by the user: `alembic stamp base` then `alembic upgrade head` re-ran `2e87aeab9ed0` against existing tables with no error; `alembic current` shows `2e87aeab9ed0 (head)`. Claude confirmed tables `alembic_version`, `conversations`, `messages`, `users` still present.

### 2026-11-09 (commit: database schema complete)
- Committed and pushed Week 1 Days 1-2 (Database Schema): models (`user.py`, `conversations.py`, `messages.py`), `config.py`/`database.py`, Alembic (`alembic.ini`, `alembic/`, migration `2e87aeab9ed0`), `RAG_TODO.md`, `RAG_Tech_Stack.md`.
- Pre-push check: `.env`, `.venv/`, `node_modules/`, `__pycache__/` are ignored and not tracked; the Supabase password appears in no pushed file (`alembic.ini` keeps Alembic's placeholder URL).

### 2026-11-09 (README)
- Wrote root `README.md` (shown on GitHub): overview, links to the two plan files, new-PC setup steps (clone, venv + requirements, `.env` from `.env.example`, `npm install`, `alembic current` check), Alembic workflow and rules, schema summary, status. Uses placeholders only; verified the real password is not in it.

### 2026-11-09 (CLAUDE.md refresh)
- Updated the Setup section and added a Current Progress section so the top of this file reflects the real state of the project.

### 2026-11-09 (working style)
- Added a Working Style section to this file so a Claude session on another PC knows how the user works (they write the code, Claude guides and reviews, plain-English explanations, commit/push only on request, never expose the password).
