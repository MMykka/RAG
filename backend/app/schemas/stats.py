
from pydantic import BaseModel




class StatsOut(BaseModel):
    total_conversations: int
    total_tokens: int
    avg_tokens_per_message: float
