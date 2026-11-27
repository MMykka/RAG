from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.conversations import ConversationCreate, ConversationOut, ConversationWithMessages, MessageCreate, MessageOut
from app.repositories.conversations import create_conversation, delete_chat, get_chat_by_id, get_chat_with_messages, get_conversations, save_message
from app.dependencies import get_current_user_id
from app.services.cache import cache_get, cache_set, invalidate_user


router = APIRouter(prefix="/api/conversations", tags=["conversations"])


# with_messages=True loads the chat and its messages in one query (for showing or exporting a chat)
def get_chat_or_404(db: Session, user_id: int, conversation_id: int, with_messages: bool = False):
    find = get_chat_with_messages if with_messages else get_chat_by_id
    conversation = find(db, user_id, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.post("", response_model=ConversationOut, status_code=201)
def create(data: ConversationCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    try:
        new_chat = create_conversation(db, data, user_id)
        invalidate_user(user_id)  # new chat: drop the cached list and stats
        return new_chat
    except IntegrityError:
        # The token is valid but its user no longer exists (account deleted): treat as logged out
        db.rollback()
        raise HTTPException(status_code=401, detail="Not authenticated")


@router.get("", response_model=list[ConversationOut])
def get_chats(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db), limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    field = f"list:{limit}:{offset}"
    cached = cache_get(user_id, field)
    if cached is not None:
        return cached
    chats = get_conversations(db, user_id, limit, offset)
    data = [ConversationOut.model_validate(c).model_dump(mode="json") for c in chats]
    cache_set(user_id, field, data)
    return data


# (search lives in routers/search.py, rename in routers/rename.py)
@router.get("/{conversation_id}", response_model=ConversationWithMessages)
def get_chat_id(conversation_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    # Cached in the user's own cache entry (services/cache.py), next to the list and stats, so it is
    # cleared by the same invalidate_user call on every new message, answer, rename or delete.
    # Only a chat that was found is cached: a 404 always asks the database again.
    field = f"chat:{conversation_id}"
    cached = cache_get(user_id, field)
    if cached is not None:
        return cached
    conversation = get_chat_or_404(db, user_id, conversation_id, with_messages=True)
    data = ConversationWithMessages.model_validate(conversation).model_dump(mode="json")
    cache_set(user_id, field, data)
    return data


# save new message to a conversation
@router.post("/{conversation_id}/messages", response_model=MessageOut, status_code=201)
def save_message_to_chat(conversation_id: int, data: MessageCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    conversation = get_chat_or_404(db, user_id, conversation_id)
    message = save_message(db, conversation, data)
    invalidate_user(user_id)  # the chat moved to the top: drop the cached list and stats
    return message


@router.delete("/{conversation_id}", status_code=204)
def delete(conversation_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    conversation = get_chat_or_404(db, user_id, conversation_id)
    delete_chat(db, conversation)
    invalidate_user(user_id)  # chat gone: drop the cached list and stats
    return None
