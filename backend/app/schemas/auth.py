
from pydantic import BaseModel, Field
from datetime import datetime


class CreateUser(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    
class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    
    model_config = {"from_attributes": True}
    

class UserLogin(BaseModel):
    username: str
    password: str
