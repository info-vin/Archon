from typing import Any

from pydantic import BaseModel, Field


class UserProfileDTO(BaseModel):
    """
    Data Transfer Object representing a User Profile from the database.
    This serves as the SSOT for the authenticated user context.
    """
    id: str
    email: str | None = None
    role: str
    name: str | None = None
    department: str | None = None
    permission_overrides: dict[str, Any] | None = Field(default_factory=dict)

class UserTokenPayload(BaseModel):
    """
    Data Transfer Object representing the extracted payload from a valid JWT auth token.
    """
    id: str
    email: str | None = None
    user_metadata: dict[str, Any] = Field(default_factory=dict)
