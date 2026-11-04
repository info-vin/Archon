"""
Backward-compatibility stub: re-exports agent_rules_compaction.
"""
from src.server.services.scheduler.jobs.agent_rules_compaction import (  # noqa: F401
    HEADING_CLEAN_RE,
    _resolve_jules_dir,
    _resolve_rules_dir,
    compact_markdown_content,
    run_monthly_agent_rules_compaction,
    run_monthly_jules_compaction,
)

__all__ = [
    "HEADING_CLEAN_RE",
    "_resolve_jules_dir",
    "_resolve_rules_dir",
    "compact_markdown_content",
    "run_monthly_agent_rules_compaction",
    "run_monthly_jules_compaction",
]
