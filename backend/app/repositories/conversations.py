
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.conversations import Conversation
from app.schemas.conversations import ConversationCreate, MessageCreate
from app.models.messages import Message


# function to create a new conversation
def create_conversation(db: Session, data: ConversationCreate, user_id: int) -> Conversation:

    conversation = Conversation(user_id=user_id, title=data.title)
    db.add(conversation)
    db.commit()
    return conversation

#function to get all conversations for a user with pagination using limit and offset
def get_conversations(db: Session, user_id: int, limit: int = 20, offset: int = 0) -> list[Conversation]:
    return db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc()).limit(limit).offset(offset).all()


def get_chat_by_id(db: Session, user_id: int, conversation_id:int) -> Conversation | None:
    conversation = db.query(Conversation).filter(Conversation.user_id == user_id, Conversation.id == conversation_id).first()
    return conversation


# Same as get_chat_by_id, but the messages come in the same query (LEFT JOIN),
# so opening a chat is one database trip instead of two.
def get_chat_with_messages(db: Session, user_id: int, conversation_id: int) -> Conversation | None:
    return (
        db.query(Conversation)
        .options(joinedload(Conversation.messages))
        .filter(Conversation.user_id == user_id, Conversation.id == conversation_id)
        .first()
    )

# save message to a conversation
def save_message(db: Session, conversation: Conversation, data: MessageCreate) -> Message:
    
    sources = [s.model_dump() for s in data.sources] if data.sources else None

    message = Message(conversation_id=conversation.id, role=data.role, content=data.content, tokens_used=data.tokens_used, sources=sources)
    db.add(message)
    conversation.updated_at = func.now()
    db.commit()
    return message
    
    
def delete_chat(db: Session, conversation: Conversation) -> None:
    db.delete(conversation)
    db.commit()