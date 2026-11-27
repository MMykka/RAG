#imports
from fastapi import FastAPI
from app.routers import auth, conversations, export, stats, stream
from fastapi import Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from fastapi import Request
from slowapi.errors import RateLimitExceeded
from app.dependencies import limiter


app = FastAPI()

# slowapi looks for the limiter here when an endpoint has @limiter.limit(...)
app.state.limiter = limiter


# Too many requests: answer 429 with "detail", which the frontend shows as the error text.
@app.exception_handler(RateLimitExceeded)
def rate_limit_exceeded(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Too many questions. Please wait a minute and try again."})


# one router per feature
app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(stream.router)
app.include_router(export.router)
app.include_router(stats.router)


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "error", "database": "unreachable"})
    return {"status": "ok", "database": "ok"}

