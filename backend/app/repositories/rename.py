# Database code for renaming a chat
from sqlalchemy.orm import Session

from app.models.conversations import Conversation


# rename a conversation without moving it in the list
def rename_conversation(db: Session, conversation: Conversation, title: str) -> Conversation:
    conversation.title = title
    # updated_at has onupdate=now(), so any UPDATE would make the chat the newest one and move it to the
    # top of the sidebar. "SET updated_at = updated_at" keeps the old value: the list order stays the same.
    conversation.updated_at = Conversation.updated_at
    db.commit()
    return conversation
