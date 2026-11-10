
from fastapi import APIRouter, Query
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db
from app.schemas.conversations import ConversationCreate, ConversationOut, ConversationWithMessages
from app.repositories.conversations import create_conversation, get_chat_by_id, get_conversations


router = APIRouter(prefix="/api/conversations", tags=["conversations"])

@router.post("", response_model=ConversationOut, status_code=201)
def create(data: ConversationCreate, db: Session = Depends(get_db)):
    # one line: call the repository
    return create_conversation(db, data)


@router.get("", response_model=list[ConversationOut])
def get_chats(user_id: int, db: Session = Depends(get_db), limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    
    return get_conversations(db, user_id, limit, offset)

@router.get("/{conversation_id}", response_model=ConversationWithMessages)
def get_chat_id(conversation_id: int, user_id: int, db: Session = Depends(get_db)):
    return get_chat_by_id(db, user_id, conversation_id)