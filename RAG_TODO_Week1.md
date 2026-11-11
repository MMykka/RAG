# Week 1: Conversation History & Persistence (reorganized)

Week 1 of `RAG_TODO.md`, reordered to match how the project is actually built. Every original item is kept (moved or merged); Day 0 and Week 2 are unchanged in `RAG_TODO.md`.

---

## Days 1-2: Database Schema

- [x]  Define SQLAlchemy models, one file each in `models/`:
  - [x]  `users` (id, username, email, password_hash, created_at, updated_at)
  - [x]  `conversations` (id, user_id, title default "New chat", created_at, updated_at)
  - [x]  `messages` (id, conversation_id, role [user/assistant], content, tokens_used, created_at)
- [x]  Add indexes on `user_id`, `conversation_id`, `created_at`
- [x]  Add foreign keys with cascading deletes (`ondelete="CASCADE"`)
- [x]  Add relationships with `relationship(..., cascade="all, delete-orphan")`
- [x]  Initialize Alembic (`alembic init`) and point it at the models
- [x]  Generate the first migration with `alembic revision --autogenerate` and review it
- [x]  Make the migration idempotent
- [x]  Apply it with `alembic upgrade head`
- [x]  Enable the pgvector extension in Supabase (`CREATE EXTENSION IF NOT EXISTS vector`)

## Day 3: Backend Foundation

- [x]  Create the FastAPI app (`main.py`) and one router per feature in `routers/` (auth, conversations, stream, export, stats)
- [x]  Keep routers thin: database work in `repositories/`, other logic in `services/` (llm, rag, export, cache)
- [x]  Add Pydantic schemas in `schemas/` to validate requests and responses
- [x]  Add a `GET /api/health` endpoint (used by Uptime Kuma later)
- [x]  Add authentication: Argon2 password hashing, JWT in an httpOnly cookie, `register` / `login` / `logout` / `me`
- [x]  Add the `get_current_user` dependency

## Day 4: Conversation APIs (all need login)

- [x]  `POST /api/conversations`: create a new chat
- [x]  `GET /api/conversations`: list the user's chats (pagination, newest first)
- [x]  `GET /api/conversations/:id`: one conversation + all its messages
- [x]  `POST /api/conversations/:id/messages`: save a message (user sends, store response)
- [x]  `DELETE /api/conversations/:id`: delete a chat (messages cascade)
- [x]  Ownership checks: every conversation query filters by `user_id = current_user.id`
- [x]  Write `pytest` tests for each endpoint with a `conftest.py` fixture
- [ ]  Test each endpoint with curl or Postman before frontend integration

## Day 5: Frontend UI

- [x]  Set up the Vite proxy so React calls `/api/...` with no hardcoded host (replaces CORS middleware)
- [x]  Put all fetch calls in `src/api/` (`client.js`, `auth.js`, `conversations.js`)
- [x]  Add a login page (the auth cookie is sent automatically)
- [x]  Build components: `Sidebar`, `ChatWindow`, `MessageBubble`
- [x]  Sidebar listing past conversations (timestamps, truncated titles)
- [x]  Click a conversation to load it and display all messages
- [x]  New chat button clears the UI and creates a fresh conversation
- [x]  Delete button with confirmation
- [x]  Documents page layout (upload is wired in Week 2)

## Week 1 Deliverables

- [x]  Database migrations (working schema with all tables and indexes)
- [x]  5 passing API endpoints
- [x]  Frontend loads and displays past conversations
- [x]  Alembic migrations apply cleanly to Supabase with `alembic upgrade head`
- [x]  `pytest` suite passing for all 5 endpoints

---

## What changed compared to the original Week 1

- `users` columns match the real table (the original said only id, email, created_at).
- Alembic steps are in real order: generate, review, make idempotent, apply.
- Backend foundation (app, layers, schemas, health, auth) comes before the endpoints, because every endpoint needs `get_current_user`.
- The CORS item is merged into the Vite proxy item (no CORS middleware was added).
- The login page is first in Day 5, since nothing works before logging in.
- Added: the Documents page layout and `auth.js` in `src/api/`.
