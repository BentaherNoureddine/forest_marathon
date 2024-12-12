from pydantic import BaseModel, EmailStr
from datetime import datetime


# CREATE USER SCHEMA
class UserCreate(BaseModel):
    email: EmailStr
    password: str


# LOGIN REQUEST
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# GET USER SCHEMA

class GetUser(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class AddPosition(BaseModel):
    id: int
    position: dict