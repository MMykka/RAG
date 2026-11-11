#imports
from fastapi import FastAPI
from app.routers import auth, conversations, export, stats, stream
from fastapi import Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db


app = FastAPI()


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

