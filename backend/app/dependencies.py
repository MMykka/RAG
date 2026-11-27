from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.auth import decode_access_token
from app.repositories.users import get_user_by_id

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings



# Fast check used by almost every endpoint: reads the user's id from the signed login token,
# with no database trip. The token is signed with SECRET_KEY, so it cannot be faked.
# Trade-off: a deleted user's token keeps working until it expires; GET /api/auth/me
# (called when the page loads) still checks the database and logs them out.
def get_current_user_id(access_token: str | None = Cookie(default=None)) -> int:
    if access_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = decode_access_token(access_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return user_id


# Full check with a database lookup: only for GET /api/auth/me, which needs the username and email.
def get_current_user(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)) -> User:
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return user


def user_or_ip(request: Request) -> str:
    cookie = request.cookies.get("access_token")
    if cookie:
        user_id = decode_access_token(cookie)
        if user_id is not None:
            return f"user:{user_id}"
    # no valid login cookie: count per IP address instead
    return get_remote_address(request)


# One shared limiter. In Docker the counts live in Redis (shared by both Gunicorn workers);
# on a PC without Redis (plain uvicorn, pytest) they live in memory.
limiter = Limiter(key_func=user_or_ip, storage_uri=settings.redis_url)

