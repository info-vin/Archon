
from pydantic import BaseModel


class CredentialCreate(BaseModel):
    key: str
    value: str
    is_encrypted: bool = False
    category: str = "ai"
    description: str | None = None

class CredentialResponse(BaseModel):
    key: str
    value: str | None = None
    encrypted_value: str | None = None
    is_encrypted: bool = False
    category: str | None = None
    description: str | None = None
    updated_at: str | None = None

class CredentialStatusResponse(BaseModel):
    provider: str
    status: str
    message: str | None = None

class CredentialStatusRequest(BaseModel):
    keys: list[str]

class UserUpdateRequest(BaseModel):
    name: str | None = None
    full_name: str | None = None
    avatar: str | None = None
    role: str | None = None
    department: str | None = None
