# Conversation schemas
from typing import Literal

from pydantic import BaseModel, Field
from datetime import datetime


# ConversationCreate schema that will be used to create a new conversation
class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)

# ConversationOut schema that will be used to return conversation data
class ConversationOut(BaseModel):
    id: int
    user_id: int
    title: str 
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


# One source reference: which document file and which piece of it an answer used.
# Defined before MessageCreate/MessageOut because they use it.
class SourceRef(BaseModel):
    source: str
    chunk_index: int


class MessageCreate(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)
    tokens_used: int | None = Field(default=None, ge=0)
    sources: list[SourceRef] | None = None

    
class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    tokens_used: int | None
    created_at: datetime
    sources: list[SourceRef] | None

    model_config = {
        "from_attributes": True
    }
    
class ConversationWithMessages(ConversationOut):
    messages: list[MessageOut]

