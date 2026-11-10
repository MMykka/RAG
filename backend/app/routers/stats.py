# Stats router: GET /api/users/:id/stats, comes in Week 2 analytics
from fastapi import APIRouter

router = APIRouter(prefix="/api/users", tags=["stats"])
