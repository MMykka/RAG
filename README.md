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

- `users` (id, username, email, password_hash, created_at, updated_at)
- `conversations` (id, user_id, title, created_at, updated_at): one user has many conversations
- `messages` (id, conversation_id, role, content, tokens_used, created_at): one conversation has many messages

Deleting a user deletes their conversations, and deleting a conversation deletes its messages.
The pgvector extension is enabled in Supabase for the RAG step.

## Status

Done: project setup, database schema, Alembic, pgvector.
Next: backend APIs (Week 1, Days 3-4). Not installed yet: Ollama and Docker.
See [RAG_TODO.md](RAG_TODO.md) for the full checklist.
