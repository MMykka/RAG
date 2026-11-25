# RAG Chatbot

An LLM chatbot with conversation history, streaming responses, export and usage stats, and RAG over company documents.

**Stack:** React + Vite, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL on Supabase (with pgvector), Ollama.
See [RAG_Tech_Stack.md](RAG_Tech_Stack.md) for the full stack and layout, and [RAG_TODO.md](RAG_TODO.md) for the step list and progress.

## Project layout

```
backend/    FastAPI app (app/), Alembic migrations (alembic/), tests, Dockerfile
frontend/   React + Vite app, Dockerfile (builds the app and serves it with Nginx)
nginx/      Nginx config (go-live)
docker-compose.yml   backend + nginx + redis (go-live)
```

## Set up on a new PC

You need Python 3.12, Node.js and git. The database is on Supabase, so there is nothing to migrate: every PC uses the same database.

Files that are git-ignored (`.env`, `backend/.venv`, `frontend/node_modules`) are not in the repo, so you rebuild them.

### 1. Get the code

```powershell
git clone https://github.com/MMykka/RAG.git
cd RAG
```

If you already cloned it, run `git pull` instead.

### 2. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
cd ..
```

### 3. Create `.env`

`.env` holds the database password and is never committed.

```powershell
copy .env.example .env
```

Open `.env` and replace the placeholder with your real Supabase connection string:

```
DATABASE_URL_DIRECT=postgresql://postgres.<project-ref>:<your-password>@aws-0-<region>.pooler.supabase.com:5432/postgres
```

- Use the **Session pooler** string from Supabase (Connect button). The direct host (`db.<ref>.supabase.co`) is IPv6-only and fails on IPv4 networks.
- Keep the variable name `DATABASE_URL_DIRECT`. If the password has special characters, URL-encode them.

Then set a new secret key for signing login tokens (the app refuses to start without one). Generate it from `backend/` and paste it into `.env`:

```powershell
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

```
SECRET_KEY=<the generated value>
COOKIE_SECURE=false
```

`COOKIE_SECURE=false` is for plain `http://localhost`. On the HTTPS server set it to `true`.

Optional: `OLLAMA_HOST` (default `http://localhost:11434`), `OLLAMA_MODEL` (default `llama3.2`) and `OLLAMA_MAX_TOKENS` (longest answer, default 512). Leave them out on a normal PC; set them when Ollama runs elsewhere (e.g. in Docker).

### 4. Frontend

```powershell
cd frontend
npm install
cd ..
```

### 5. Check the connection

```powershell
cd backend
.venv\Scripts\alembic.exe current
```

It should print `2e87aeab9ed0 (head)`, which means the connection works and the tables already exist.

In VS Code, select `backend\.venv\Scripts\python.exe` as the interpreter (Ctrl+Shift+P, then Python: Select Interpreter).

## Run the backend

From `backend/`:

```powershell
.venv\Scripts\uvicorn.exe app.main:app --reload
```

- API docs with "Try it out": http://localhost:8000/docs
- Health check: http://localhost:8000/api/health (200 when the app and database work, 503 when the database is unreachable)

Login is a JWT in an httpOnly cookie (`access_token`, 60 minutes). Register with `POST /api/auth/register`, log in with `POST /api/auth/login`; the browser (or `/docs`, or Postman) then sends the cookie automatically. All `/api/conversations` endpoints need that login and only ever show the logged-in user's own chats.

AI answers: `POST /api/stream` with `{"conversation_id": ..., "content": "..."}` streams Llama's answer as Server-Sent Events: `data: {"token": "...", "text": "<answer so far>", "percent": n}` per piece, then `data: {"done": true, "text": "<full answer>", "percent": 100, "sources": [{"source": "<file>", "chunk_index": n}, ...]}`. If Ollama fails, a single `data: {"error": "...", "text": "<answer so far>"}` is sent instead of `done`. Before answering, the question is embedded and the `RAG_TOP_K` (default 5) closest document chunks are put in a system message; Llama is told to answer only from them. The user message and the answer (with its `sources` and token counts) are saved to the chat. Answers are capped at `OLLAMA_MAX_TOKENS` (default 512) and `percent` is measured against that cap (at most 99 until done). Ollama must be running first (start the Ollama app or `ollama serve`). `app/services/llm.py` talks to Ollama; `app/routers/stream.py` turns the pieces into SSE.

Export: `GET /api/conversations/{id}/export?format=md` (default) or `format=json` downloads one of your chats as a file (`Content-Disposition: attachment`). Markdown: the title as a heading, then each message with who wrote it and when. JSON: the chat's id, title and dates, `exported_at`, `model`, `message_count`, `total_tokens` and every message with `created_at`, `tokens_used` and `sources`. Another user's chat gives 404. `app/services/export.py` builds the files, `app/routers/export.py` checks ownership and sends them.

## Run the frontend

Start the backend first (above), then from `frontend/`:

```powershell
npm run dev
```

Open http://localhost:5173, create an account on the login page (or log in), and chat.

- The Vite proxy (`frontend/vite.config.js`) forwards every `/api/...` call to `http://localhost:8000`, so the browser sees one origin and the login cookie just works. No CORS setup is needed.
- `src/api/`: all fetch calls (`client.js` shared helper + health, `auth.js`, `conversations.js`, `stream.js` = `POST /api/stream` read with a `ReadableStream`, partial events buffered).
- `src/hooks/useStream.js`: state of the answer being streamed (text so far, token count) plus `start` / `stop` (`AbortController`). Answers appear word by word with "Thinking…" / "Writing · N tokens" under them; while an answer streams the send button turns into a Stop button (sending is blocked); a stopped answer stays on screen marked "Stopped · not saved"; stream errors show above the input box.
- `src/components/`: `Sidebar`, `ChatWindow`, `MessageBubble`, `Icons` (inline SVGs).
- `src/pages/`: `LoginPage`, `ChatPage` (holds the state, calls the API), `DocumentsPage` (upload panel; layout only, see the Documents Page section in `RAG_TODO.md`), `StatsPage` (your usage, via `src/api/stats.js` and `components/StatsDashboard`).
- Styles: `src/index.css`, with every colour, font and size in `src/tokens.css`.
- Check the code: `npm run lint`; production build: `npm run build`.

## Run the tests

From `backend/`:

```powershell
.venv\Scripts\pytest.exe -v
```

The tests run against the real Supabase database, but each test runs inside a transaction that is rolled back, so nothing is left behind. They need internet and a filled-in `.env`, and take under a minute. Ollama is not needed: `tests/test_stream.py` replaces it with a fake (pytest `monkeypatch`), and a safety net makes any accidental call to the real Ollama fail.

## Run with Docker (go-live, not tested yet)

For the live server only; on the PCs keep using uvicorn and `npm run dev` as above. Needs Docker (Docker Desktop on Windows). Written but not built yet, because no PC has Docker so far.

From the project root:

```powershell
docker compose up -d --build   # build and start backend, nginx, redis
docker compose logs backend    # backend output
docker compose down            # stop
```

- `backend/Dockerfile`: Python 3.12, runs Gunicorn with 2 Uvicorn workers (`uvicorn-worker`) on port 8000. Gunicorn only runs on Linux, which the container is.
- `frontend/Dockerfile`: Node builds the React app, then Nginx serves `dist/`.
- `nginx/nginx.conf`: `/` serves the React app, `/api/` goes to the backend. Only Nginx is open to the outside (port 80).
- Settings come from the root `.env` when the containers start (never copied into an image). Ollama is not in Docker for now: the backend reaches the host's Ollama at `host.docker.internal:11434`.

## Database migrations (Alembic)

Alembic keeps the database tables in sync with the models in `backend/app/models/`. You only need it when the **structure** changes (a new table or column). Saving users, chats and messages is normal app code and needs no migration.

Run these from `backend/`:

1. Change the model in `app/models/`.
2. Generate the migration (this does not change the database):
   ```powershell
   .venv\Scripts\alembic.exe revision --autogenerate -m "what changed"
   ```
3. Open the new file in `alembic/versions/` and review it, then apply it:
   ```powershell
   .venv\Scripts\alembic.exe upgrade head
   ```

Other useful commands:

```powershell
.venv\Scripts\alembic.exe current        # which migration the database is on
.venv\Scripts\alembic.exe history        # list of migrations
.venv\Scripts\alembic.exe downgrade -1   # undo the last migration (drops tables and their data)
```

Rules:
- Always review the generated file before running `upgrade`.
- If a migration has not been applied and is wrong, delete the file and generate it again.
- Never edit a migration that has already been applied. Make a new one.
- The first migration (`2e87aeab9ed0`) is idempotent: each table is created only if it is missing.

## Database schema

- `users` (id, username, email, password_hash, created_at, updated_at): passwords are stored only as Argon2 hashes
- `conversations` (id, user_id, title, created_at, updated_at): one user has many conversations
- `messages` (id, conversation_id, role, content, tokens_used, created_at): one conversation has many messages

Deleting a user deletes their conversations, and deleting a conversation deletes its messages.
The pgvector extension is enabled in Supabase for the RAG step.

## Status

Done: project setup, database schema, Alembic, pgvector, backend APIs (Week 1, Days 3-4): conversations and messages endpoints, JWT cookie authentication with ownership checks, health endpoint, pytest suite (55 tests, incl. 8 stream tests with a fake Ollama, 8 export tests, 5 stats tests and 7 ingest tests). Frontend UI (Week 1, Day 5): login page, sidebar with past chats, chat window, new chat, delete with confirmation, Documents page layout, Vite proxy.
Week 2 complete: `POST /api/stream` streams Llama's answer as SSE (token, text so far, percentage), saves both messages with token counts, sends an error event if Ollama fails, and answers from company documents (RAG): `chunks` table with pgvector, `scripts/ingest_documents.py` to load `.txt`/`.md` files from `documents/`, `services/rag.py` to retrieve the closest chunks, source references saved with each answer. The frontend streaming UI is done too (Week 2 Day 3: live answer, token count, Stop, error message). Export is done too (Week 2 Day 4): `GET /api/conversations/{id}/export?format=md|json` downloads a chat as Markdown or JSON, from the download button in the chat header. Stats: `GET /api/users/{id}/stats` returns your total conversations, total tokens and average tokens per message (only your own id; another id gives 403). The Stats page (sidebar "Stats") shows them as three tiles. Logins last 8 hours.
Go-Live in progress: backend and frontend Dockerfiles, `docker-compose.yml`, Gunicorn and `nginx.conf` routing are written but not built yet (no Docker installed so far); next: streaming settings for `/api/stream` in Nginx.
See [RAG_TODO.md](RAG_TODO.md) for the full checklist.
