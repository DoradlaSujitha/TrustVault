from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
class LoginRequest(BaseModel):
    email: EmailStr
    password: str=Field(min_length=1,max_length=256)
class UserOut(BaseModel):
    id:int; email:EmailStr; role:str
    class Config: from_attributes=True
class PermissionCreate(BaseModel):
    email:EmailStr
    permission:str=Field(pattern="^(read|edit)$")
class DocumentUpdate(BaseModel):
    name:str|None=Field(default=None,min_length=1,max_length=255)
    category:str|None=Field(default=None,min_length=1,max_length=100)
    description:str|None=Field(default=None,max_length=2000)
class DocumentOut(BaseModel):
    id:int; name:str; category:str; description:str; original_filename:str; content_type:str; size_bytes:int; owner_id:int; owner_email:str; created_at:datetime; updated_at:datetime
