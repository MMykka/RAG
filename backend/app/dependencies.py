from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.auth import decode_access_token
from app.repositories.users import get_user_by_id

def get_current_user(access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)) -> User:
    if access_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    decoded_user_id = decode_access_token(access_token)
    if decoded_user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = get_user_by_id(db, decoded_user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return user