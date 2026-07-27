from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class UserPreferences(BaseModel):
    genres: List[str] = Field(default_factory=list)
    mood: Optional[str] = ""
    era: Optional[str] = ""
    minRating: Optional[str] = ""
    runtime: Optional[str] = ""

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    preferences: UserPreferences = Field(default_factory=UserPreferences)

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
