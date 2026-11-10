# Tech Stack

# LLM Chatbot Project: Tech Stack

## Overview

| Layer | Tech | Notes |
| --- | --- | --- |
| **Frontend** | React + Vite | Built to static files for production |
| **Streaming client** | `fetch` + `ReadableStream` | Used instead of `EventSource` because the stream endpoint is POST |
| **Reverse proxy** | Nginx | HTTPS, serves React build, proxies `/api` |
| **Backend** | Python + FastAPI | Gunicorn + Uvicorn workers in production |
| **Streaming** | SSE (`StreamingResponse`) | Required by the Phase 2 plan |
| **ORM** | SQLAlchemy 2.0 |  |
| **Migrations** | Alembic | Idempotent, versioned schema changes |
| **Database** | PostgreSQL on Supabase | Relational: users, conversations, messages |
| **Driver** | `psycopg2-binary` | Connects SQLAlchemy to Postgres |
| **Vector store (RAG)** | pgvector (inside Supabase) | One database for chats and embeddings |
| **LLM** | Llama via Ollama (dev) | vLLM optional for scale |
| **Embeddings** | `nomic-embed-text` via Ollama |  |
| **Cache / rate limiting** | Redis | For go-live |
| **Deployment** | Docker Compose | For go-live |
| **Monitoring** | Sentry + Uptime Kuma | Errors and uptime |
| **Testing** | curl/Postman, `pytest` with mocked Ollama |  |

## Request Flow

```
React (Vite)
   |  POST /api/stream
   v
Nginx (HTTPS) -> FastAPI (Gunicorn + Uvicorn)
                   |- Redis: rate limit + GPU slot check
                   |- embed query (nomic-embed-text)
                   |- retrieve chunks (pgvector in Supabase)
                   |- stream tokens (Llama via Ollama / vLLM) -> SSE -> React
                   '- save message + tokens_used (SQLAlchemy -> Supabase Postgres)
```

## Tool Roles

| Tool | Role |
| --- | --- |
| **Alembic** | Tracks and applies schema changes |
| **Nginx** | Front door: HTTPS, static files, routing |
| **Docker Compose** | Starts all services with one command |
| **Sentry** | Reports code errors |
| **Uptime Kuma** | Alerts when the site is down |
| **Driver (`psycopg2`)** | Lets Python talk to PostgreSQL |
| **Redis** | Rate limiting, caching, shared concurrency limit |

## Project Layout

```
company-chatbot/
|- backend/
|  |- app/
|  |  |- main.py            # FastAPI app, router registration
|  |  |- config.py          # settings from .env
|  |  |- database.py        # engine, session, get_db()
|  |  |- dependencies.py    # get_current_user, rate limiting
|  |  |- models/            # SQLAlchemy tables
|  |  |- schemas/           # Pydantic request/response shapes
|  |  |- routers/           # auth, conversations, stream, export, stats
|  |  |- repositories/      # database queries (conversations, ...)
|  |  '- services/          # llm, rag, export, cache
|  |- alembic/versions/     # migrations
|  |- tests/
|  |- Dockerfile
|  '- requirements.txt
|- frontend/
|  '- src/
|     |- api/               # all fetch calls
|     |- components/        # Sidebar, ChatWindow, MessageBubble, StatsDashboard
|     |- hooks/             # useStream.js
|     '- pages/             # ChatPage, StatsPage
|- nginx/nginx.conf
|- docker-compose.yml
|- .env.example
'- README.md
```

Pattern: layered architecture (routers -> repositories -> models for database work, routers -> services for llm, rag, export and cache), with schemas validating input and output.

## Install

```bash
# backend
pip install fastapi uvicorn gunicorn sqlalchemy alembic psycopg2-binary pgvector ollama redis slowapi pytest

# frontend
npm create vite@latest frontend -- --template react
```

## Connection String (Supabase)

```python
DATABASE_URL = "postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres"
```

Use the direct connection (port 5432) for `alembic upgrade head` and the pooler (port 6543) for the running app. Keep credentials in `.env`, never in code.

## Phases

- **Phase 2 (2 weeks):** React, FastAPI, SQLAlchemy, Alembic, Postgres, SSE streaming, export, stats, pytest.
- **Go-live (100+ users):** Redis, Nginx with HTTPS, Gunicorn, Docker Compose, Sentry, Uptime Kuma, auth hardening, load test (~30 concurrent chats).

## Open Decisions

- **LLM serving:** Ollama is fine for development. vLLM is better if many users chat at once.
- **Data location:** Supabase is cloud-hosted. Confirm the company accepts chat history and documents stored outside their servers. If not, swap the connection URI for a local Postgres and nothing else changes.