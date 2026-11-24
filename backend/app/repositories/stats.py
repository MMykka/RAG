from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.conversations import Conversation
from app.models.messages import Message


def get_user_stats(db: Session, user_id: int) -> dict:
    total_conversations = db.query(func.count(Conversation.id)).filter(Conversation.user_id == user_id).scalar()
    
    total_tokens, average = (
    db.query(func.coalesce(func.sum(Message.tokens_used), 0), func.avg(Message.tokens_used))
    .join(Conversation)
    .filter(Conversation.user_id == user_id)
    .one()
)
    return {
        "total_conversations": total_conversations,
        "total_tokens": total_tokens,
        "avg_tokens_per_message": round(float(average), 1) if average is not None else 0.0

    }
