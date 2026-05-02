from dataclasses import dataclass


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
