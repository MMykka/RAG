from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.conversations import Conversation
from app.models.messages import Message


def get_user_stats(db: Session, user_id: int) -> dict:
    # One query (one database trip) for all three numbers. The LEFT OUTER JOIN keeps chats
    # without messages, so DISTINCT counts every chat once; SUM/AVG skip messages without a count.
    total_conversations, total_tokens, average = (
        db.query(
            func.count(func.distinct(Conversation.id)),
            func.coalesce(func.sum(Message.tokens_used), 0),
            func.avg(Message.tokens_used),
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .filter(Conversation.user_id == user_id)
        .one()
    )
    return {
        "total_conversations": total_conversations,
        "total_tokens": total_tokens,
        "avg_tokens_per_message": round(float(average), 1) if average is not None else 0.0,
    }
