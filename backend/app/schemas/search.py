# Schema for searching your chats (GET /api/conversations/search, routers/search.py)
from datetime import datetime

from pydantic import BaseModel


# One search result: a chat whose title or messages match the search.
# `snippet` is a short piece of the best matching message, with each matching word between
# the characters \x02 and \x03 (the frontend turns those into highlights); None when only the title matched.
class ConversationSearchHit(BaseModel):
    id: int
    title: str
    updated_at: datetime
    message_id: int | None
    snippet: str | None
