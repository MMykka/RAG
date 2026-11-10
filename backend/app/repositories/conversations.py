#function to create a new conversation
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.models.conversations import Conversation
from app.schemas.conversations import ConversationCreate

# function to create a new conversation
def create_conversation(db: Session, data: ConversationCreate) -> Conversation:

    conversation = Conversation(user_id=data.user_id, title=data.title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

#function to get all conversations for a user with pagination using limit and offset
def get_conversations(db: Session, user_id: int, limit: int = 20, offset: int = 0) -> list[Conversation]:
    return db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc()).limit(limit).offset(offset).all()


def get_chat_by_id(db: Session, user_id: int, conversation_id:int) -> Conversation | None:
    conversation = db.query(Conversation).filter(Conversation.user_id == user_id, Conversation.id == conversation_id).first()
    if conversation is None:
       raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation