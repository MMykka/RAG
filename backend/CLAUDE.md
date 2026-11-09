
### 2026-11-09 (Day 0: backend install, redone to the dot)
- Approved step: `[stack] Backend: install fastapi uvicorn sqlalchemy alembic psycopg2-binary pgvector ollama pytest`.
- Earlier install had extras not in the plan; uninstalled gunicorn, redis, slowapi, pydantic-settings, python-dotenv from `backend/.venv` (httpx stays only as a dependency of ollama).
- Rewrote `backend/requirements.txt` to exactly those 8 packages. `pip check` clean and all imports verified.
- gunicorn, redis, slowapi come in later steps (Go-Live) when the plan calls for them.
