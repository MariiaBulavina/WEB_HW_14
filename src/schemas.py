from datetime import datetime, date
from typing import  Optional

from pydantic import BaseModel, Field, EmailStr


class ContactModel(BaseModel):

    name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    email: Optional[EmailStr]
    phone: str = Field(max_length=20)
    born_date: date
    

class ContactResponse(ContactModel):

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserModel(BaseModel):
    username: str 
    email: EmailStr
    password: str = Field(min_length=6, max_length=8)


class UserDb(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
    avatar: str

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    user: UserDb
    detail: str = 'User successfully created'


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class RequestEmail(BaseModel):
    email: EmailStr