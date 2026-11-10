# Auth router: login, register (endpoints come in the authentication step)
from fastapi import APIRouter

router = APIRouter(prefix="/api/auth", tags=["auth"])
