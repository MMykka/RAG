
from pydantic import BaseModel, Field


class StreamRequest(BaseModel):
    conversation_id: int
    content: str = Field(min_length=1)

