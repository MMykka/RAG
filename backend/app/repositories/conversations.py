#function to create a new conversation
from sqlalchemy.orm import Session

from app.models.conversations import Conversation
from app.schemas.conversations import ConversationCreate


def create_conversation(db: Session, data: ConversationCreate) -> Conversation:

    conversation = Conversation(user_id=data.user_id, title=data.title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation