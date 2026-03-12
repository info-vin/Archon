from pydantic import BaseModel
from typing import Optional

class CredentialCreate(BaseModel):
    key: str
    value: str
    is_encrypted: bool = False
    category: str = "ai"
    description: Optional[str] = None

class CredentialResponse(BaseModel):
    key: str
    category: str
    description: Optional[str] = None
    updated_at: str

class CredentialStatusResponse(BaseModel):
    provider: str
    status: str
    message: Optional[str] = None

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
