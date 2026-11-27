# Optimizations

Everything tried to make the app faster: what was slow, what was changed, and what it gave.
Newest at the bottom. "Trip" = one round trip between the backend and the database (~60 ms to Paris).

## Summary

| # | Date | Layer | What | Where | Result |
|---|---|---|---|---|---|
| 1 | 2026-11-11 | Database | Moved the database from Tokyo to Paris | Supabase, `.env` | Trip ~250 ms -> ~61 ms; "+" ~3 s -> ~0.75 s; tests ~3 min -> ~35 s |
| 2 | 2026-11-11 | Frontend | "+" no longer reloads the chat list | `frontend/src/pages/ChatPage.jsx` | "+" ~0.75 s -> ~0.5 s (one request instead of two) |
| 3 | 2026-11-12 | Backend | Fewer database trips per request | `backend/app/database.py`, `backend/app/repositories/conversations.py`, `backend/app/models/` | Create ~5 -> ~4 trips, send ~8 -> ~6, delete ~7 (+1 per message) -> ~5 |
| 4 | 2026-11-12 | Frontend | Send and delete update the screen first, check with the database after | `frontend/src/pages/ChatPage.jsx` | Sidebar updates instantly; the list reload no longer blocks |
| 5 | 2026-11-25 | Backend | `pool_pre_ping=True` -> `pool_recycle=300` (no connection test trip before each request) | `backend/app/database.py` | On the alexm PC (~237 ms trip): me 445 -> 337 ms, list 602 -> 369 ms, open chat 638 -> 472 ms, stats 601 -> 471 ms |
| 6 | 2026-11-25 | Backend | One query per request: trust the login token (no user lookup), chat + messages in one query, one stats query | `backend/app/dependencies.py`, `backend/app/routers/*.py`, `backend/app/repositories/conversations.py`, `backend/app/repositories/stats.py` | Same network (~70 ms trip): list 313 -> 209 ms, open chat 391 -> 215 ms, stats 329 -> 204 ms (2-3 queries -> 1) |
| 7 | 2026-11-27 | Database | App connects through the Supabase Transaction pooler (6543) instead of the Session pooler (5432) | root `.env` (`DATABASE_URL`), `.env.example` | 25 parallel connections: 6 ok / 19 refused -> 25/25 ok; 40 parallel health checks: 5 x 503 -> 0; trip unchanged (62 vs 63 ms) |
| 8 | 2026-11-27 | Backend | Cache the chat list and stats per user (Redis, 60 s TTL, cleared on every change) | `backend/app/services/cache.py`, `backend/app/routers/conversations.py`, `stats.py`, `stream.py` | Repeat reads: list 149 -> 5 ms, stats 122 -> 5 ms (no database trip) |

**Backend changes:** #3 (`expire_on_commit=False`, no `db.refresh`, `passive_deletes=True`), #5 (`pool_recycle` instead of `pool_pre_ping`), #6 (one query per request), #8 (list/stats cache).
**Frontend changes:** #2 ("+" without reload) and #4 (show first, correct after on send and delete).
**Database / hosting:** #1 (Paris region), #7 (Transaction pooler for the app).

## 1. Database: moved closer (Tokyo -> Paris)

- **Problem:** "+" took about 2-3 s. Measured: one database trip was ~250 ms because the Supabase project was in `ap-northeast-1` (Tokyo), and every request makes several trips one after another.
- **Change:** new Supabase project in `eu-west-3` (Paris), migrations applied, pgvector enabled, `DATABASE_URL_DIRECT` in `.env` switched.
- **Result:** trip ~61 ms, health check ~1 s -> ~0.18 s, "+" ~3 s -> ~0.75 s, pytest ~3 min -> ~35 s.
- **Lesson:** distance to the database multiplies with every trip. This was the biggest single win.

## 2. Frontend: "+" without a list reload

- **Problem:** after `POST /api/conversations` the frontend made a second request (`GET /api/conversations`) and waited for it before the new chat showed.
- **Change:** `newChat` puts the chat returned by the POST at the top of the list itself: `setConversations((list) => [chat, ...list])`.
- **Result:** one request instead of two, ~0.5 s.

## 3. Backend: fewer database trips

| Change | File | Trip saved |
|---|---|---|
| `expire_on_commit=False` on `SessionLocal` | `app/database.py` | Objects are not forgotten after `commit()`, so FastAPI does not re-read them to build the response |
| Removed `db.refresh(...)` after create and after saving a message | `app/repositories/conversations.py` | 1 per create, 1 per send (Postgres `INSERT ... RETURNING` already gives `id`, `created_at`, `"New chat"`) |
| `passive_deletes=True` on `Conversation.messages` and `User.conversations` | `app/models/conversations.py`, `app/models/user.py` | SQLAlchemy no longer loads and deletes every message one by one; the database's `ON DELETE CASCADE` does it. Saves 2+ per delete, more for long chats |

- **Checked:** counted the real SQL statements per request. Create = SELECT user + INSERT; send = SELECT user + SELECT chat + UPDATE + INSERT; delete = SELECT user + SELECT chat + DELETE (messages removed by Postgres). pytest 27 passed.
- **Note:** `expire_on_commit=False` and removing `refresh` only help together. Removing `refresh` alone saves nothing.

## 4. Frontend: show first, correct after

- **Problem:** after sending a message or deleting a chat, the page waited for a full list reload (~0.25 s, ~3 trips) before the sidebar changed.
- **Change** in `sendMessage` and `deleteChat`:
  1. **Show first:** the browser updates the sidebar itself (sent-to chat moves to the top; deleted chat disappears at once).
  2. **Save:** the real request goes to the server.
  3. **Correct after:** `refreshList()` runs without `await`, so the list is still checked against the database in the background.
  4. **Undo on failure:** if a delete fails, the old list (and the open chat) come back and the error shows.
- **Trade-off:** the database still runs the list query (same server load); only the waiting is gone. If two actions happen very fast, a late background reload can briefly show an old state before the next one fixes it.

## 5. Backend: pool_recycle instead of pool_pre_ping (2026-11-25)

- **Problem:** pages felt slow on the alexm PC. One trip to Paris is ~237 ms from there, and `pool_pre_ping=True` sent an extra test query ("is this connection alive?") before every request.
- **Change:** `create_engine(settings.database_url, pool_recycle=300)` in `backend/app/database.py`. A pooled connection is replaced once it is 5 minutes old; this is decided from its age, with no trip.
- **Result** (TestClient against Supabase, median of 5, same PC and network): me 445 -> 337 ms, list 602 -> 369 ms, open chat 638 -> 472 ms, stats 601 -> 471 ms. pytest 55 passed. The Docker backend was rebuilt with it.
- **Risk checked:** if Supabase silently closed an idle connection, the next request would fail once (SQLAlchemy then drops the bad connections). Test with no pre_ping and no recycle: a connection idle for 60 s and for 290 s was still alive, so 300 s is within what the pooler allows. A failure would show as `OperationalError ... server closed the connection` in the backend log (later in Sentry).
- **Also found:** Docker Desktop on Windows makes each trip ~2.4x slower (~577 ms from inside the container); this does not happen on a Linux server.

## 6. Backend: one query per request (2026-11-25)

- **Problem:** every request looked the user up first (1 trip), opening a chat loaded the chat and then its messages (2 trips), and stats ran two queries.
- **Changes:**
  1. `get_current_user_id` in `app/dependencies.py` reads the user id from the signed JWT with no database trip; every endpoint uses it except `GET /api/auth/me`, which still looks the user up (via `get_current_user`) because it returns the username and email.
  2. `get_chat_with_messages` in `app/repositories/conversations.py` uses `joinedload(Conversation.messages)` (one LEFT JOIN); `get_chat_or_404(..., with_messages=True)` uses it for opening and exporting a chat. Message order is kept.
  3. `get_user_stats` in `app/repositories/stats.py`: `COUNT(DISTINCT conversations.id)`, `SUM` and `AVG` over a LEFT OUTER JOIN in one query (same numbers as before; the existing stats tests pass unchanged).
- **Result** (same PC and network, ~70 ms trip, old code vs new code back to back): me 225 -> 204 ms, list 313 -> 209 ms (2 -> 1 queries), open chat 391 -> 215 ms (3 -> 1), stats 329 -> 204 ms (3 -> 1). pytest 56 passed.
- **Trade-off (accepted by the user):** a deleted user's token keeps working until it expires (8 h). Checked: `/me` gives 401, so the page logs them out on load; the list is empty and their old chats give 404 (CASCADE removed them); creating a chat gives 401 instead of a 500 (the `IntegrityError` is caught). New test `test_deleted_user_token`.
- **What is left per request:** the one query, plus the `ROLLBACK` SQLAlchemy sends when it returns the connection to the pool (another trip, not counted above). Skipping that reset (`pool_reset_on_return=None`) was not done: a connection could then be handed on in an unfinished transaction.

## 7. Database: Transaction pooler for the app (2026-11-27)

- **Problem:** 40 parallel `/api/health` requests through Nginx gave 5 x 503. Inside the backend container, 25 parallel connections gave 6 ok and 19 `EMAXCONNSESSION max clients reached in session mode - max clients are limited to pool_size: 15`. The app used `DATABASE_URL_DIRECT` (Session pooler, port 5432), where every open connection holds one of 15 slots shared by every Gunicorn worker, PC, test run and script.
- **Change:** new `DATABASE_URL` in root `.env` = the same Supabase string on port 6543 (Transaction pooler: a database connection is only held for one transaction). `config.py` already used `DATABASE_URL` when set, so no code changed. Alembic keeps `DATABASE_URL_DIRECT` (5432) for migrations. Nothing in the app needs session features (`SET`, `LISTEN`, temp tables, advisory locks; psycopg2 uses no prepared statements).
- **Result:** 25 parallel connections 25/25 ok; 40 parallel health checks all 200; `SELECT 1` median 62 ms (5432) vs 63 ms (6543), so single requests are not faster or slower; pytest 56 passed. Matters for the 30-concurrent-chat load test. The other PCs need the `DATABASE_URL` line in their own `.env`.

## 8. Backend: cache the chat list and stats (2026-11-27)

- **Problem:** the sidebar list (`GET /api/conversations`) and the Stats page (`GET /api/users/{id}/stats`) are read far more often than they change, and every read cost a database trip (~60 ms to Paris, more from slower networks). `RAG_TODO.md` Go-Live item: cache them with a TTL and invalidate on changes.
- **Change:**
  1. `services/cache.py`: one Redis hash per user, `cache:user:<id>`, holding each list page (`list:<limit>:<offset>`) and `stats` as JSON. `cache_get` / `cache_set` / `invalidate_user` (deletes the whole hash). The 60 s TTL is set once (`EXPIRE ... NX`), so the entry cannot live on by being refilled. Without Redis (`REDIS_URL=memory://`: plain uvicorn, pytest) an in-memory dict with the same behaviour is used.
  2. `get_chats` and `get_stats` read the cache first and store the result (`model_dump(mode="json")`) after a database read.
  3. `invalidate_user(user_id)` after every change: new chat, saved message, deleted chat (`routers/conversations.py`), and in `POST /api/stream` after the question is saved (chat moves to the top) and after the answer is saved (new token counts).
- **Result** (real uvicorn on the CCINTL PC, in-memory cache, Transaction pooler, median of 6; first read straight after a change vs the repeat read): list 149 -> 5 ms, stats 122 -> 5 ms. With Redis in Docker a hit adds about 1 ms (same machine). The first read after a change is unchanged.
- **Tests:** new `tests/test_cache.py` (8 tests): a chat or message written straight into the database does not show until the cache is cleared (proves reads come from the cache), separate pages, create / delete / stream refresh the list and stats, one user's cache does not affect another, the TTL expires. Checked that the 4 refresh tests fail when `invalidate_user` is switched off. `conftest.py` clears the cache around every test. pytest 68 passed.
- **Trade-off:** correctness depends on every write calling `invalidate_user`. All writes today go through those 5 places; a new write path (e.g. renaming chats, a stretch goal) must call it too. The TTL limits the damage of a missed call to 60 s.
- **Not cached (on purpose):** opening one chat (`GET /api/conversations/{id}`) changes with every message and is read once per click, so a cache would mostly be cleared before it was used.

## Ideas not done (yet)

| Idea | Saves | Why not (yet) |
|---|---|---|
| ~~Replace `pool_pre_ping=True` with `pool_recycle=300`~~ | 1 trip per request | **Done 2026-11-25** (#5; idle connections tested safe up to 290 s) |
| Delete in one query (`DELETE ... WHERE id AND user_id`) | 1 trip per delete | Small gain; `get_chat_or_404` keeps the router simple |
| ~~Remove `db.refresh(user)` in `repositories/users.py`~~ | 1 trip per register | **Done 2026-11-12** (commented out by the user; tests pass) |
| ~~Skip the user lookup in `get_current_user` (trust the JWT)~~ | 1 trip per request | **Done 2026-11-25** (#6; `/me` still checks, so the page logs a deleted user out) |
| Transaction pooler (port 6543) | none per request | Helps with many connections at once, not speed of one request |
| Show a sent message before the server answers | feels instant | More code (temporary ids, failed sends); better done with Week 2 streaming |

## RAG retrieval speed (considered 2026-11-20, nothing changed yet)

Question: is the `chunks` table with an HNSW index (`ix_chunks_embedding`, `vector_cosine_ops`) the fastest way to retrieve?

- **Measured** (Supabase Paris, 5000 fake chunks inside a rolled-back transaction, top 5 by cosine distance): search ~77 ms, of which ~55 ms is the network trip (`SELECT 1` alone). The search itself is ~20 ms. At this size Postgres skipped the HNSW index and compared every row (`Sort`), which is just as fast. HNSW pays off at tens of thousands of chunks, so it stays.
- **Embedding the question, measured 2026-11-24** (local Ollama 0.21.0, `nomic-embed-text`): first call ~2.7 s (model load), then ~60-67 ms per question; 2 document texts in one call ~66 ms. So a warm question costs about embed ~65 ms + search ~77 ms ≈ 0.15 s before Llama starts. The vectors come back normalized (length 1.0), so the inner-product idea below would give the same ranking.

| Idea | Saves | Status |
|---|---|---|
| Keep `nomic-embed-text` loaded (`keep_alive` on `embed`) | the model load after 5 idle minutes (seconds) | **Done 2026-11-20**: `keep_alive="30m"` on both `client.embed` calls (`embed_documents`, `embed_query` in `services/llm.py`). Measured 2026-11-24: cold ~2.7 s vs warm ~65 ms, so keeping it loaded saves ~2.6 s on the first question after a pause |
| One database trip per search (`ORDER BY embedding <=> :vec LIMIT k`, embed in Python first) | extra trips, ~60 ms each | **Done 2026-11-20**: `search_chunks` in `repositories/chunks.py`; checked 1 query per search, and the plan uses `ix_chunks_embedding` when a full scan is not cheaper |
| Check with `EXPLAIN` that the HNSW index is used once real data is in | avoids a silent full scan at large sizes | **To do** after the ingest script; a `WHERE` filter or a mismatched operator can make Postgres skip the index |
| Inner product (`vector_ip_ops`, `<#>`) instead of cosine | ~1 ms | Skipped: tiny gain, only correct if the embeddings are normalized |
| `halfvec(768)` instead of `vector(768)` | half the storage, ~1 ms | Skipped: not needed at this size; needs a migration |
| Tune `hnsw.ef_search` (default 40) | ~1 ms | Skipped: only matters once the index is in use on many rows |
| Separate vector database or in-memory FAISS | a few ms | Rejected: `RAG_Tech_Stack.md` chose pgvector so chats and embeddings live in one database; the ~55 ms trip would stay anyway |

## Open follow-ups

- ~~`backend/tests/conftest.py` builds its own `Session(...)` without `expire_on_commit=False`, so the tests do not run with the same setting as the app.~~ **Done 2026-11-24** (Day 5 polish): the test session now uses `expire_on_commit=False` too; 48 tests pass.
