# RAG Chatbot

An LLM chatbot with conversation history, streaming responses, export and usage stats, and RAG over company documents.

**Stack:** React + Vite, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL on Supabase (with pgvector), Ollama.
See [RAG_Tech_Stack.md](RAG_Tech_Stack.md) for the full stack and layout, and [RAG_TODO.md](RAG_TODO.md) for the step list and progress.

## Project layout

```
backend/    FastAPI app (app/), Alembic migrations (alembic/), tests
frontend/   React + Vite app
nginx/      Nginx config (go-live)
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

Optional: `OLLAMA_HOST` (default `http://localhost:11434`) and `OLLAMA_MODEL` (default `llama3.2`). Leave them out on a normal PC; set them when Ollama runs elsewhere (e.g. in Docker).

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

AI answers: `POST /api/stream` with `{"conversation_id": ..., "content": "..."}` streams Llama's answer as Server-Sent Events (`data: {"token": "..."}` per piece, then `data: {"done": true}`). Ollama must be running first (start the Ollama app or `ollama serve`). `app/services/llm.py` talks to Ollama; `app/routers/stream.py` turns the pieces into SSE.

## Run the frontend

Start the backend first (above), then from `frontend/`:

```powershell
npm run dev
```

Open http://localhost:5173, create an account on the login page (or log in), and chat.

- The Vite proxy (`frontend/vite.config.js`) forwards every `/api/...` call to `http://localhost:8000`, so the browser sees one origin and the login cookie just works. No CORS setup is needed.
- `src/api/`: all fetch calls (`client.js` shared helper + health, `auth.js`, `conversations.js`).
- `src/components/`: `Sidebar`, `ChatWindow`, `MessageBubble`, `Icons` (inline SVGs).
- `src/pages/`: `LoginPage`, `ChatPage` (holds the state, calls the API), `DocumentsPage` (upload panel; layout only until Week 2).
- Styles: `src/index.css` (colours at the top as CSS variables).
- Check the code: `npm run lint`; production build: `npm run build`.

## Run the tests

From `backend/`:

```powershell
.venv\Scripts\pytest.exe -v
```

The tests run against the real Supabase database, but each test runs inside a transaction that is rolled back, so nothing is left behind. They need internet and a filled-in `.env`, and take a few minutes.

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

Done: project setup, database schema, Alembic, pgvector, backend APIs (Week 1, Days 3-4): conversations and messages endpoints, JWT cookie authentication with ownership checks, health endpoint, pytest suite (27 tests). Frontend UI (Week 1, Day 5): login page, sidebar with past chats, chat window, new chat, delete with confirmation, Documents page layout, Vite proxy.
Week 2 in progress: `services/llm.py` streams from Ollama and `POST /api/stream` sends it as SSE. Next: cumulative text and progress in each event, saving the answer, token counts, error events, then the frontend streaming UI. Not installed yet: Docker.
See [RAG_TODO.md](RAG_TODO.md) for the full checklist.
