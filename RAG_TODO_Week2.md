# Week 2: Streaming Responses, RAG & Export (reorganized)

Week 2 of `RAG_TODO.md`, reordered to match how the project was actually built. Every original item is kept (moved, merged or made concrete); Day 0, Week 1 and Go-Live are unchanged in `RAG_TODO.md`. Week 1 has its own version in `RAG_TODO_Week1.md`.

---

## Day 1: Streaming Backend

- [x]  Research how the Llama backend works: Ollama streams natively (`stream=True`, the last chunk carries `done`, `prompt_eval_count`, `eval_count`)
- [x]  Implement `services/llm.py`: `stream_chat()` yields tokens from Ollama instead of waiting for the full response
- [x]  Create `POST /api/stream` (login required, ownership checked before streaming) and return a FastAPI `StreamingResponse` (`media_type="text/event-stream"`)
- [x]  Format each event as `data: {...}\n\n`: token, cumulative text, completion percentage (measured against the `OLLAMA_MAX_TOKENS` cap), then a final `done` event
- [x]  Save the user message before streaming and the full answer after the stream completes
- [x]  Read token counts from the final Ollama chunk and save them: `prompt_eval_count` on the user message, `eval_count` on the answer
- [x]  Send an `error` event if Ollama fails mid-stream (the partial answer is not saved)
- [x]  Add an `OLLAMA_MOCK` switch for running the app without a model

## Day 2: Knowledge Base & RAG

- [x]  Create a `chunks` table with a `vector(768)` column and an HNSW index (migration)
- [x]  Write `scripts/ingest_documents.py`: cut `.txt` / `.md` files from `documents/` into chunks (one per Markdown section, long sections split with the heading repeated), embed them with `nomic-embed-text` and store them
- [x]  Implement `services/rag.py`: embed the question with `nomic-embed-text` and retrieve the top chunks from pgvector (cosine distance, one query)
- [x]  Build the prompt from the retrieved chunks (system message with the context, user message with the question)
- [x]  Save source references with the answer (`messages.sources`, migration) and send them in the `done` event
- [x]  Mock Ollama in `pytest` (`monkeypatch`) so stream tests run without a model; add tests for the stream and the chunking

## Day 3: Frontend Streaming UI

- [x]  Read the stream with `fetch` + `ReadableStream` in `src/api/stream.js` (POST, so not `EventSource`)
- [x]  Buffer partial chunks so an event split across network reads never breaks `JSON.parse`
- [x]  Build `hooks/useStream.js` to hold the streaming state (text so far, token count, start / stop)
- [x]  Display tokens as they arrive in a live message bubble
- [x]  Show a progress indicator with the token count ("Thinking…", then "Writing · N tokens")
- [x]  Disable sending during streaming: the send button turns into a Stop button using `AbortController`
- [x]  Show an error message in the UI when the stream fails

## Day 4: Export Feature

- [x]  Add `services/export.py` (Python `json` + Markdown templating) and `routers/export.py`: `GET /api/conversations/:id/export?format=md|json`
- [x]  Check ownership before exporting (another user's chat returns 404)
- [x]  Export as Markdown: conversation title as h1, then the user and assistant messages in order with their time
- [x]  Export as JSON: conversation metadata, export timestamp, model, total tokens, and every message with its time, tokens used and sources
- [x]  Return files with a `Content-Disposition` header so the browser downloads them
- [x]  Add a download button (Markdown / JSON menu) in the conversation view
- [x]  Write `pytest` tests for the export

## Day 5: Basic Analytics & Polish

- [x]  `GET /api/users/:id/stats`: total conversations, total tokens used, average tokens per message
- [x]  Compute the stats with SQLAlchemy aggregates (`func.count`, `func.sum`, `func.avg`)
- [x]  Only allow a user to read their own stats (another user's id returns 403)
- [x]  Build `StatsPage` and `StatsDashboard`: a simple dashboard page with stat tiles (no fancy charting), reached from the sidebar
- [x]  Write `pytest` tests for the stats
- [x]  Polish and fix issues

## Week 2 Deliverables

- [x]  Streaming endpoint working end-to-end
- [x]  Frontend displays tokens in real time
- [x]  Export to Markdown and JSON working
- [x]  Basic analytics dashboard with user stats
- [x]  RAG answers use retrieved document chunks from pgvector
- [x]  Streaming, export and stats covered by `pytest` tests

---

## What changed compared to the original Week 2

- **Days 1-2 are split in two.** The original packed streaming and the whole RAG pipeline into one block of 15 items. Day 1 is now streaming only; Day 2 is the knowledge base and RAG.
- **RAG is in build order.** The `chunks` table and the ingest script come before `services/rag.py`, because retrieval needs stored chunks to search (the original listed `rag.py` first).
- **Duplicates are merged.** "Modify Llama inference to stream tokens" and "Implement `services/llm.py` with `stream=True`" are one item; "Create `POST /api/stream`", `StreamingResponse` and the `data: {...}` format are two; "Each chunk includes..." is folded into the event format.
- **The two mocks are told apart.** "Mock the Llama backend if needed" is the `OLLAMA_MOCK` switch for running the app (Day 1); "Mock Ollama in `pytest`" is the test fake (Day 2).
- **Items name what was built.** Token counts say which count goes on which message; source references name `messages.sources`; the percentage says what it is measured against; the chunking says how documents are cut.
- **The streaming UI is in dependency order.** Reading and buffering the stream comes first, then the hook, then what the user sees. "Disable the send button" and "Add a Stop button" are one item, because the send button becomes the Stop button.
- **Each feature has its tests.** The original only asked for `pytest` coverage in the deliverables; the stream, chunking, export and stats each have a test item on their day.
- **Stats items are merged.** The endpoint and the list of stats are one item; the dashboard page and the `StatsPage` / `StatsDashboard` components are one item.
- **"[stack]" tags are dropped.** In this version every item is part of the chosen stack.
