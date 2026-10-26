from dataclasses import dataclass
from typing import TypedDict


@dataclass
class CredentialItem:
    """
    Represents a credential/setting item.

    This is used primarily for the Settings UI to represent the state
    of a specific configuration key.
    """

    key: str
    value: str | None = None
    encrypted_value: str | None = None
    is_encrypted: bool = False
    category: str | None = None
    description: str | None = None


class EncryptedCredentialDict(TypedDict):
    encrypted_value: str
    is_encrypted: bool
    category: str | None
    description: str | None


class MaskedEncryptedCredentialDict(TypedDict):
    value: str
    is_encrypted: bool
    category: str | None
    description: str | None


class CredentialStatusDict(TypedDict):
    key: str
    has_value: bool


class ActiveProviderDTO(TypedDict):
    provider: str
    api_key: str | None
    base_url: str | None
    chat_model: str
    embedding_model: str


class EmbeddingProviderConfigDTO(TypedDict):
    provider: str
    api_key: str | None
    base_url: str | None
    embedding_model: str
