
from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db
from app.schemas.conversations import ConversationCreate, ConversationOut
from app.repositories.conversations import create_conversation


router = APIRouter(prefix="/api/conversations", tags=["conversations"])

@router.post("", response_model=ConversationOut, status_code=201)
def create(data: ConversationCreate, db: Session = Depends(get_db)):
    # one line: call the repository
    return create_conversation(db, data)