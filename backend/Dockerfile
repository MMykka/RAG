# Backend image: FastAPI app on Python 3.12 (same version as backend/.venv).
# Build from backend/:  docker build -t rag-backend .
# Run:                  docker run --env-file ../.env -e OLLAMA_HOST=http://host.docker.internal:11434 -p 8000:8000 rag-backend
# Secrets (.env) are never copied into the image; they are passed in when the container starts.

# Small Debian image with Python 3.12 already installed.
FROM python:3.12-slim

# Show print()/errors in `docker logs` straight away, and don't write .pyc files.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Folder inside the container where the code lives.
WORKDIR /app

# Install the packages first, before copying the code: Docker caches this step,
# so a code change does not reinstall every package.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the code (app/, alembic/, scripts/, alembic.ini). .dockerignore keeps .venv, caches, tests and .env out.
COPY . .

# Run as a normal user instead of root (safer if the app is ever broken into).
RUN useradd --create-home appuser
USER appuser

# The port Gunicorn listens on.
EXPOSE 8000

# Start the app. 0.0.0.0 = reachable from outside the container (localhost would only be the container itself).
# 2 Gunicorn processes, each a Uvicorn worker (async, so SSE streaming works). Gunicorn only runs on Linux;
# on the Windows PCs the backend is still started with plain uvicorn.
CMD ["gunicorn", "app.main:app", "-k", "uvicorn_worker.UvicornWorker", "--workers", "2", "--bind", "0.0.0.0:8000"]

