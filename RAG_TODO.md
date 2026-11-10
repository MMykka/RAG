# RAG

# LLM Chatbot Project: Phase 2 Todo List

2-week expansion: conversation persistence, real-time streaming, export, and usage analytics.

Daily 15-minute standups on Days 2, 4 and 5 of each week.

Items tagged **[stack]** were added to match the chosen tech stack (React + Vite, FastAPI, SQLAlchemy, Alembic, PostgreSQL on Supabase, pgvector, Ollama, Redis, Nginx, Docker Compose, Sentry, Uptime Kuma).

---

## Day 0: Project Setup [stack]

- [x]  **[stack]** Create repo layout: `backend/` (app, alembic, tests) and `frontend/`
- [x]  **[stack]** Backend: install `fastapi uvicorn sqlalchemy alembic psycopg2-binary pgvector ollama pytest`
- [x]  **[stack]** Frontend: scaffold with `npm create vite@latest frontend -- --template react`
- [x]  **[stack]** Create the Supabase project and get the connection strings (direct port 5432 for migrations, pooler port 6543 for the app)
- [x]  **[stack]** Create `.env` (never commit) and `.env.example`, and add `.env` to `.gitignore`
- [x]  **[stack]** Add `config.py` (settings from `.env`) and `database.py` (engine, session, `get_db()`)
- [x]  **[stack]** Confirm with the company that storing chats and documents on Supabase (cloud) is acceptable, otherwise use a local Postgres
- [x]  **[stack]** Install Ollama and pull the Llama model and `nomic-embed-text`

---

## Week 1: Conversation History & Persistence

### Days 1-2: Database Schema

- [x]  Create `users` table (id, email, created_at)
- [x]  Create `conversations` table (id, user_id, title, created_at, updated_at)
- [x]  Create `messages` table (id, conversation_id, role [user/assistant], content, tokens_used, created_at)
- [x]  Add indexes on `user_id`, `conversation_id`, `created_at`
- [x]  Add foreign key constraints and cascading deletes
- [x]  Make migrations idempotent
- [x]  **[stack]** Define SQLAlchemy models (one file each in `models/`) with `relationship(..., cascade="all, delete-orphan")`
- [x]  **[stack]** Initialize Alembic (`alembic init`) and point it at the models
- [x]  **[stack]** Generate migrations with `alembic revision --autogenerate` and review them before running `alembic upgrade head`
- [x]  **[stack]** Enable the pgvector extension in Supabase (`CREATE EXTENSION IF NOT EXISTS vector`)

### Days 3-4: Backend APIs

- [x]  `POST /api/conversations`: create new chat
- [x]  `GET /api/conversations`: list user’s chats (with pagination)
- [ ]  `GET /api/conversations/:id`: fetch one conversation + all messages
- [ ]  `POST /api/conversations/:id/messages`: save new message (user sends, store response)
- [ ]  `DELETE /api/conversations/:id`: delete chat
- [ ]  Test each endpoint with curl or Postman before frontend integration
- [ ]  **[stack]** Create the FastAPI app (`main.py`) and one router per feature in `routers/`
- [ ]  **[stack]** Add Pydantic schemas in `schemas/` to validate requests and responses
- [ ]  **[stack]** Keep routers thin and put logic in `repositories/` (database) and `services/` (llm, rag, export, cache)
- [ ]  **[stack]** Add authentication (login, password hashing, token or cookie session) and a `get_current_user` dependency
- [ ]  **[stack]** Add ownership checks: every conversation query filters by `user_id = current_user.id`
- [ ]  **[stack]** Add a `GET /api/health` endpoint (used by Uptime Kuma later)
- [ ]  **[stack]** Add CORS middleware for `http://localhost:5173` (or use the Vite proxy)
- [ ]  **[stack]** Write `pytest` tests for each endpoint with a `conftest.py` fixture

### Day 5: Frontend UI

- [ ]  Sidebar listing past conversations (timestamps, truncated titles)
- [ ]  Click a conversation to load it and display all messages
- [ ]  New chat button clears the UI and creates a fresh conversation
- [ ]  Delete button with confirmation
- [ ]  **[stack]** Set up the Vite proxy so React calls `/api/...` with no hardcoded host
- [ ]  **[stack]** Put all fetch calls in `src/api/` (`client.js`, `conversations.js`)
- [ ]  **[stack]** Build components: `Sidebar`, `ChatWindow`, `MessageBubble`
- [ ]  **[stack]** Add a login page and attach the auth token to API requests

### Week 1 Deliverables

- [ ]  Database migrations (working schema with all tables and indexes)
- [ ]  5 passing API endpoints
- [ ]  Frontend loads and displays past conversations
- [ ]  **[stack]** Alembic migrations apply cleanly to Supabase with `alembic upgrade head`
- [ ]  **[stack]** `pytest` suite passing for all 5 endpoints

---

## Week 2: Streaming Responses & Export

### Days 1-2: Streaming Backend

- [ ]  Research how the Llama backend works (native streaming support?)
- [ ]  Modify Llama inference to stream tokens instead of waiting for the full response
- [ ]  Create `POST /api/stream` (SSE) that accepts a message and returns a chunked response
- [ ]  Each chunk includes: token content, cumulative text, completion percentage
- [ ]  Save the full message to the database after the stream completes
- [ ]  Mock the Llama backend for testing if needed
- [ ]  **[stack]** Implement `services/llm.py` using Ollama with `stream=True`
- [ ]  **[stack]** Return the stream with FastAPI `StreamingResponse` (`media_type="text/event-stream"`)
- [ ]  **[stack]** Format each event as `data: {...}\n\n`
- [ ]  **[stack]** Read `tokens_used` from the final Ollama chunk (`eval_count`, `prompt_eval_count`) and save it with the message
- [ ]  **[stack]** Send an error event if Ollama fails mid-stream
- [ ]  **[stack]** Implement `services/rag.py`: embed the query with `nomic-embed-text` and retrieve the top chunks from pgvector
- [ ]  **[stack]** Create a `chunks` table with a vector column, and a script to chunk and embed company documents
- [ ]  **[stack]** Build the prompt from the retrieved chunks and save source references with the message
- [ ]  **[stack]** Mock Ollama in `pytest` so stream tests run without a model

### Day 3: Frontend Streaming UI

- [ ]  Connect to the SSE endpoint and display tokens as they arrive
- [ ]  Show a progress/loading indicator with token count
- [ ]  Disable the send button during streaming
- [ ]  **[stack]** Build `hooks/useStream.js` using `fetch` + `ReadableStream` (POST, so not `EventSource`)
- [ ]  **[stack]** Buffer partial chunks so an event split across network reads never breaks `JSON.parse`
- [ ]  **[stack]** Add a Stop button using `AbortController`
- [ ]  **[stack]** Show an error message in the UI when the stream fails

### Day 4: Export Feature

- [ ]  Export as Markdown: conversation title as h1, alternating user/assistant messages
- [ ]  Export as JSON: structured with metadata (timestamp, model, tokens used)
- [ ]  Add a download button in the conversation view
- [ ]  **[stack]** Add `routers/export.py` and `services/export.py` (Python `json` + Markdown templating)
- [ ]  **[stack]** Return files with a `Content-Disposition` header so the browser downloads them
- [ ]  **[stack]** Check ownership before exporting

### Day 5: Basic Analytics & Polish

- [ ]  `GET /api/users/:id/stats` endpoint
- [ ]  Stats: total conversations, total tokens used, average tokens per message
- [ ]  Simple dashboard page showing the stats (no fancy charting)
- [ ]  Polish and fix issues
- [ ]  **[stack]** Compute stats with SQLAlchemy aggregates (`func.count`, `func.sum`, `func.avg`)
- [ ]  **[stack]** Only allow a user to read their own stats
- [ ]  **[stack]** Build `StatsPage` and `StatsDashboard` components

### Week 2 Deliverables

- [ ]  Streaming endpoint working end-to-end
- [ ]  Frontend displays tokens in real time
- [ ]  Export to Markdown and JSON working
- [ ]  Basic analytics dashboard with user stats
- [ ]  **[stack]** RAG answers use retrieved document chunks from pgvector
- [ ]  **[stack]** Streaming, export and stats covered by `pytest` tests

---

## Go-Live Preparation (100+ users) [stack]

### Containers & Proxy

- [ ]  **[stack]** Write a `Dockerfile` for the backend
- [ ]  **[stack]** Write `docker-compose.yml` with services: backend, nginx, redis (and Ollama or vLLM)
- [ ]  **[stack]** Run the backend with Gunicorn + Uvicorn workers (`k uvicorn.workers.UvicornWorker`)
- [ ]  **[stack]** Build the React app (`npm run build`) and serve it from Nginx
- [ ]  **[stack]** Write `nginx.conf`: route `/` to React and `/api/` to FastAPI
- [ ]  **[stack]** Set `proxy_buffering off` and `proxy_read_timeout 300s` on `/api/stream` so SSE works
- [ ]  **[stack]** Set up HTTPS (certbot or a company-supplied certificate) and redirect HTTP to HTTPS
- [ ]  **[stack]** Set request size limits and `limit_req` throttling in Nginx

### Redis: Limits & Caching

- [ ]  **[stack]** Rate limit `/api/stream` per user (e.g. 20 requests per minute)
- [ ]  **[stack]** Cap concurrent generations across all workers with a shared Redis counter
- [ ]  **[stack]** Return a clear “server busy, try again” message when the cap is reached
- [ ]  **[stack]** Cache the conversation list and stats with a TTL, and invalidate on changes

### LLM Serving

- [ ]  **[stack]** Decide between Ollama and vLLM for production
- [ ]  **[stack]** If Ollama, raise `OLLAMA_NUM_PARALLEL` and test its limits

### Monitoring & Operations

- [ ]  **[stack]** Add Sentry to the backend (and optionally the frontend) for error tracking
- [ ]  **[stack]** Run Uptime Kuma and monitor `/api/health` with alerts
- [ ]  **[stack]** Log latency, tokens and errors per request
- [ ]  **[stack]** Confirm database backups (Supabase plan or scheduled `pg_dump`)
- [ ]  **[stack]** Move all secrets to environment variables or a secrets manager

### Pre-Launch Testing

- [ ]  **[stack]** Load test with locust or k6 simulating about 30 concurrent chats
- [ ]  **[stack]** Verify user A cannot read, export, delete or see stats of user B’s data
- [ ]  **[stack]** Run the full flow through Nginx over HTTPS (login, stream, save, export, stats)

---

## Success Criteria

- [ ]  All conversations are persisted across sessions
- [ ]  User can load past conversations from the sidebar
- [ ]  Response streaming displays in real time (no waiting for the full response)
- [ ]  Conversations can be exported to at least 2 formats
- [ ]  User dashboard shows basic stats without errors
- [ ]  **[stack]** Users can only access their own data
- [ ]  **[stack]** App runs with one command (`docker compose up -d`) behind Nginx with HTTPS
- [ ]  **[stack]** Errors and downtime trigger alerts (Sentry, Uptime Kuma)

---

## Stretch Goals (if time allows)

- [ ]  Search across all conversations (full-text or keyword)
- [ ]  Rename conversations / edit titles
- [ ]  Conversation folders / organization (tagging)
- [ ]  Performance: database query caching for frequently accessed conversations
- [ ]  **[stack]** Use Postgres full-text search (`tsvector`) for conversation search
- [ ]  **[stack]** Use Redis for the query caching goal
- [ ]  **[stack]** Add GitHub Actions to run `pytest` on every push

---

## Notes

- Database: PostgreSQL on Supabase via SQLAlchemy and Alembic (SQLite remains fine for early local development, since only the connection URI changes).
- Use SSE for streaming. Ollama supports streaming natively, so no manual chunking of the generation loop is needed.
- If streaming proves difficult, it is optional for the core deliverable. Persistence alone is a solid 2-week phase, and streaming can move to Phase 3.
- The Go-Live Preparation section is outside the original 2-week plan. Treat it as the next phase before launching to 100+ users.
- Open decision: Supabase is cloud-hosted. If company data must stay on their servers, swap the connection URI for a local Postgres and nothing else changes.

[Tech Stack](https://app.notion.com/p/Tech-Stack-413c61fa0c3680cbbef1d12b42336081?pvs=21)