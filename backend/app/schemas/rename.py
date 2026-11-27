# Schema for renaming a chat (PATCH /api/conversations/{id}, routers/rename.py)
from pydantic import BaseModel, Field


# New title. Spaces around it are removed first, so "   " counts as empty and is refused.
class ConversationRename(BaseModel):
    model_config = {"str_strip_whitespace": True}
    title: str = Field(min_length=1, max_length=255)
