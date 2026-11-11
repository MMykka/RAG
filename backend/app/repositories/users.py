from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import CreateUser
from app.services.auth import hash_password


def get_user_by_username(db: Session, username:str) -> User | None:
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> User |None:
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

def create_user(db:Session, data: CreateUser) -> User:
    hashed_password = hash_password(data.password)
    user = User(username=data.username, email=data.email, password_hash=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user:User) -> None:
    db.delete(user)
    db.commit()