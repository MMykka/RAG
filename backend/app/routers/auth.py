# Auth router: login, register (endpoints come in the authentication step)
from fastapi import Response

from fastapi import APIRouter, HTTPException
from app.schemas.auth import CreateUser, UserLogin, UserOut
from app.repositories.users import create_user, get_user_by_username, get_user_by_email
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db
from app.services.auth import create_access_token, verify_password
from app.config import settings
from app.dependencies import get_current_user
from app.models.user import User


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: CreateUser, db: Session = Depends(get_db)):
    existing_username = get_user_by_username(db, data.username)
    existing_email = get_user_by_email(db, data.email)
    if existing_username:
        raise HTTPException(status_code=409, detail="Username already exists")
    if existing_email:
        raise HTTPException(status_code=409, detail="Email already exists")
    return create_user(db, data)

@router.post("/login", response_model=UserOut)
def login(data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = get_user_by_username(db, data.username)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    response.set_cookie(
        key="access_token",
        value=create_access_token(user.id),
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.access_token_expire_minutes * 60,  # seconds
)
    return user


@router.post("/logout", status_code=204)
def logout(response: Response):
    # same settings as login, so the browser reliably removes the cookie
    response.delete_cookie(key="access_token", httponly=True, samesite="lax", secure=settings.cookie_secure)
    return None

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user