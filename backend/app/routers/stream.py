# Stream router: POST /api/stream (SSE), comes in Week 2 Streaming Backend
from fastapi import APIRouter

router = APIRouter(prefix="/api/stream", tags=["stream"])
