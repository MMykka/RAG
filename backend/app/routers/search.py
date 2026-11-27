# Search router: GET /api/conversations/search?q=..., search your own chats (titles and messages).
# main.py must include this router BEFORE routers/conversations.py: otherwise "/api/conversations/search"
# would match "/api/conversations/{conversation_id}" there and "search" would be read as a chat id (422).
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.repositories.search import search_conversations
from app.schemas.search import ConversationSearchHit

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("/search", response_model=list[ConversationSearchHit])
def search(q: str = Query(min_length=2, max_length=200), limit: int = Query(20, ge=1, le=50), user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return search_conversations(db, user_id, q.strip(), limit)
