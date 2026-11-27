#imports
from fastapi import FastAPI
from app.routers import auth, conversations, documents, export, rename, search, stats, stream
from fastapi import Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from fastapi import Request
from slowapi.errors import RateLimitExceeded
from app.dependencies import limiter
import sentry_sdk
from app.config import settings
import logging, time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("rag")

class RequestLogMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        start = time.perf_counter()
        status = {"code": 500}

        async def send_and_remember_status(message):
            if message["type"] == "http.response.start":
                status["code"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_and_remember_status)
        finally:
            ms = (time.perf_counter() - start) * 1000
            log.info("request method=%s path=%s status=%s ms=%.0f", scope["method"], scope["path"], status["code"], ms)

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        # Keep company data out of the error reports (sentry-sdk 3.x option names):
        data_collection={
            "user_info": False,                         # no user ids, e-mails or IP addresses
            "cookies": {"mode": "off"},                 # never the login cookie
            "http_headers": {"request": {"mode": "off"}},  # no request headers
            "http_bodies": [],                          # no request bodies (questions, passwords)
            "stack_frame_variables": False,             # no variable values (e.g. chat text) in stack traces
        },
        max_request_body_size="never",
        traces_sample_rate=None,  # errors only, no performance tracing
    )
    
app = FastAPI()

app.add_middleware(RequestLogMiddleware)

# slowapi looks for the limiter here when an endpoint has @limiter.limit(...)
app.state.limiter = limiter


# Too many requests: answer 429 with "detail", which the frontend shows as the error text.
@app.exception_handler(RateLimitExceeded)
def rate_limit_exceeded(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Too many questions. Please wait a minute and try again."})


# one router per feature
app.include_router(auth.router)
app.include_router(search.router)  # before conversations: "/search" must not be read as a chat id
app.include_router(conversations.router)
app.include_router(rename.router)
app.include_router(stream.router)
app.include_router(export.router)
app.include_router(stats.router)
app.include_router(documents.router)


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "error", "database": "unreachable"})
    return {"status": "ok", "database": "ok"}

