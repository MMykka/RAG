#imports
from fastapi import FastAPI
from app.routers import auth, conversations, export, stats, stream


app = FastAPI()

# one router per feature
app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(stream.router)
app.include_router(export.router)
app.include_router(stats.router)
