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
    
    

class MessageCreate(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)
    tokens_used: int | None = Field(default=None, ge=0)

    
class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    tokens_used: int | None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
    
class ConversationWithMessages(ConversationOut):
    messages: list[MessageOut]
    

