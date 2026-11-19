"""Service-to-service credential for MCP call_api.

The token is compared with hmac.compare_digest over SHA-256 digests so the
check does not short-circuit on the secret and does not depend on equal length.
An unset, blank, or mismatched value never authenticates, and the Supabase
service key is not a substitute.
"""

import hashlib
import hmac
import os
import re

from ..models.auth_models import UserProfileDTO
from .permissions import TASK_READ_OWN

INTERNAL_HEADER = "X-Archon-Internal-Token"
INTERNAL_ACTOR_ID = "archon-mcp-internal"
# Task list/archive routes hard-code manager (or admin). Admin is refused.
INTERNAL_ACTOR_ROLE = "manager"
# RAG routes ask for this permission, which the static manager set does not include.
INTERNAL_EXTRA_PERMISSIONS = frozenset({TASK_READ_OWN})

_MCP_ROUTES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("GET", re.compile(r"^/api/tasks$")),
    ("GET", re.compile(r"^/api/tasks/[^/]+$")),
    ("GET", re.compile(r"^/api/projects/[^/]+/tasks$")),
    ("POST", re.compile(r"^/api/tasks$")),
    ("PUT", re.compile(r"^/api/tasks/[^/]+$")),
    ("PATCH", re.compile(r"^/api/tasks/[^/]+$")),
    ("DELETE", re.compile(r"^/api/tasks/[^/]+$")),
    ("POST", re.compile(r"^/api/rag/query$")),
    ("POST", re.compile(r"^/api/rag/code-examples$")),
)


def configured_internal_token() -> str | None:
    """Return the configured token, or None when it is missing or blank."""
    raw = os.environ.get("ARCHON_INTERNAL_TOKEN")
    if raw is None:
        return None
    if raw.strip() == "":
        return None
    return raw


def internal_header_decision(header_value: str | None) -> str:
    """Classify the internal header as absent, accepted, or rejected.

    The header value is never written to logs.
    """
    if header_value is None:
        return "absent"
    expected = configured_internal_token()
    if expected is None or header_value == "":
        return "rejected"
    presented_digest = hashlib.sha256(header_value.encode("utf-8")).digest()
    expected_digest = hashlib.sha256(expected.encode("utf-8")).digest()
    if hmac.compare_digest(presented_digest, expected_digest):
        return "accepted"
    return "rejected"


def internal_route_allowed(method: str, path: str) -> bool:
    """True only for the server routes MCP call_api authenticates against."""
    for allowed_method, pattern in _MCP_ROUTES:
        if method.upper() == allowed_method and pattern.match(path):
            return True
    return False


def internal_actor() -> UserProfileDTO:
    """Minimal MCP principal. Not an admin, and not the old system-agent id."""
    return UserProfileDTO(
        id=INTERNAL_ACTOR_ID,
        email="mcp-internal@archon.local",
        role=INTERNAL_ACTOR_ROLE,
        department=None,
    )
