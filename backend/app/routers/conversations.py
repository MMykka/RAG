
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db
from app.schemas.conversations import ConversationCreate, ConversationOut, ConversationWithMessages, MessageCreate, MessageOut
from app.repositories.conversations import create_conversation, get_chat_by_id, get_conversations, save_message


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
    conversation = get_chat_by_id(db, user_id, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

#save new message to a conversation
@router.post("/{conversation_id}/messages", response_model=MessageOut, status_code=201)
def save_message_to_chat(conversation_id:int, user_id:int, data: MessageCreate, db: Session = Depends(get_db)):
    conversation = get_chat_by_id(db, user_id, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    message = save_message(db, conversation, data)
    return message
