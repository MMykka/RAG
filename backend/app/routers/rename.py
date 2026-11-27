# Rename router: PATCH /api/conversations/{id}, a new title for one of your chats.
# Same URL prefix as routers/conversations.py; the chat keeps its place in the list.
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.repositories.rename import rename_conversation
from app.routers.conversations import get_chat_or_404
from app.schemas.conversations import ConversationOut
from app.schemas.rename import ConversationRename
from app.services.cache import invalidate_user

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.patch("/{conversation_id}", response_model=ConversationOut)
def rename(conversation_id: int, data: ConversationRename, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    conversation = get_chat_or_404(db, user_id, conversation_id)  # 404 for a chat that is not yours
    renamed = rename_conversation(db, conversation, data.title)
    invalidate_user(user_id)  # new title: drop the cached list and the cached chat
    return renamed
