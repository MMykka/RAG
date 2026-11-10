# Conversation schemas
from pydantic import BaseModel
from datetime import datetime


# ConversationCreate schema that will be used to create a new conversation
class ConversationCreate(BaseModel):
    user_id: int
    title: str| None = None

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
    

