from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.conversations import ConversationCreate, ConversationOut, ConversationWithMessages, MessageCreate, MessageOut
from app.repositories.conversations import create_conversation, delete_chat, get_chat_by_id, get_conversations, save_message
from app.dependencies import get_current_user
from app.models.user import User


router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def get_chat_or_404(db: Session, user_id: int, conversation_id: int):
    conversation = get_chat_by_id(db, user_id, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.post("", response_model=ConversationOut, status_code=201)
def create(data: ConversationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_conversation(db, data, current_user.id)


@router.get("", response_model=list[ConversationOut])
def get_chats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db), limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return get_conversations(db, current_user.id, limit, offset)


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
def get_chat_id(conversation_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversation = get_chat_or_404(db, current_user.id, conversation_id)
    return conversation


# save new message to a conversation
@router.post("/{conversation_id}/messages", response_model=MessageOut, status_code=201)
def save_message_to_chat(conversation_id: int, data: MessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversation = get_chat_or_404(db, current_user.id, conversation_id)
    message = save_message(db, conversation, data)
    return message


@router.delete("/{conversation_id}", status_code=204)
def delete(conversation_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversation = get_chat_or_404(db, current_user.id, conversation_id)
    delete_chat(db, conversation)
    return None
