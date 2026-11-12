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

**Backend changes:** #3 (`expire_on_commit=False`, no `db.refresh`, `passive_deletes=True`).
**Frontend changes:** #2 ("+" without reload) and #4 (show first, correct after on send and delete).
**Database / hosting:** #1 (Paris region).

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

## Ideas not done (yet)

| Idea | Saves | Why not (yet) |
|---|---|---|
| Replace `pool_pre_ping=True` with `pool_recycle=300` | 1 trip per request | Rare error if Supabase drops an idle connection |
| Delete in one query (`DELETE ... WHERE id AND user_id`) | 1 trip per delete | Small gain; `get_chat_or_404` keeps the router simple |
| ~~Remove `db.refresh(user)` in `repositories/users.py`~~ | 1 trip per register | **Done 2026-11-12** (commented out by the user; tests pass) |
| Skip the user lookup in `get_current_user` (trust the JWT) | 1 trip per request | A deleted user could keep using the app until the token expires (60 min) |
| Transaction pooler (port 6543) | none per request | Helps with many connections at once, not speed of one request |
| Show a sent message before the server answers | feels instant | More code (temporary ids, failed sends); better done with Week 2 streaming |

## Open follow-ups

- `backend/tests/conftest.py` builds its own `Session(...)` without `expire_on_commit=False`, so the tests do not run with the same setting as the app.
