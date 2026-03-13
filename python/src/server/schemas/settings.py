
from pydantic import BaseModel


class CredentialCreate(BaseModel):
    key: str
    value: str
    is_encrypted: bool = False
    category: str = "ai"
    description: str | None = None

class CredentialResponse(BaseModel):
    key: str
    category: str
    description: str | None = None
    updated_at: str

class CredentialStatusResponse(BaseModel):
    provider: str
    status: str
    message: str | None = None

class UserUpdateRequest(BaseModel):
    name: str | None = None
    full_name: str | None = None
    avatar: str | None = None
    role: str | None = None
    department: str | None = None
