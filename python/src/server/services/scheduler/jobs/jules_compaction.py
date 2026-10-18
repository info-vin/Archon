import re
from pathlib import Path

from src.server.config.logfire_config import get_logger
from src.server.schemas.settings import SchedulerConfig
from src.server.services.log_service import log_service
from src.server.services.settings_service import SettingsService

logger = get_logger(__name__)

# Matches either "## 2024-05-18 - Rule Title" or "## 1. Rule Title" or "## Rule Title"
HEADING_CLEAN_RE = re.compile(
    r"^(?:\d{4}-\d{2}-\d{2}\s*[-:–—]\s*|\d+\.\s*)+",
    re.IGNORECASE,
)


def _resolve_jules_dir(explicit_dir: Path | None = None) -> Path | None:
    if explicit_dir is not None:
        return explicit_dir if explicit_dir.exists() else None

    candidates = (
        Path("/app/.jules"),
        Path.cwd() / ".jules",
        Path.cwd().parent / ".jules",
    )
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def compact_markdown_content(content: str, max_entries: int = 5) -> tuple[str, int, int]:
    """
    Compacts a .jules/*.md file by:
    1. Stripping hallucinated YYYY-MM-DD date prefixes from ## headings.
    2. Deduplicating sections with identical normalized titles or bodies.
    3. Capping the total number of core rules to `max_entries`.
    4. Renumbering headings sequentially (## 1. Title, ## 2. Title, ...).

    Returns (compacted_content, original_count, compacted_count).
    """
    lines = content.splitlines()
    header_lines: list[str] = []
    raw_sections: list[tuple[str, list[str]]] = []

    current_title: str | None = None
    current_body: list[str] = []

    for line in lines:
        if line.startswith("## "):
            if current_title is not None:
                raw_sections.append((current_title, current_body))
            current_title = line[3:].strip()
            current_body = []
        else:
            if current_title is None:
                header_lines.append(line)
            else:
                current_body.append(line)

    if current_title is not None:
        raw_sections.append((current_title, current_body))

    original_count = len(raw_sections)
    if original_count == 0:
        return content, 0, 0

    unique_sections: list[tuple[str, str]] = []
    seen_titles: set[str] = set()
    seen_bodies: set[str] = set()

    for raw_title, body_lines in raw_sections:
        clean_title = HEADING_CLEAN_RE.sub("", raw_title).strip()
        if not clean_title:
            clean_title = raw_title.strip()

        body_text = "\n".join(body_lines).strip()
        norm_title = re.sub(r"\s+", " ", clean_title.lower())
        norm_body = re.sub(r"\s+", " ", body_text.lower())

        if norm_title in seen_titles or (norm_body and norm_body in seen_bodies):
            continue

        seen_titles.add(norm_title)
        if norm_body:
            seen_bodies.add(norm_body)
        unique_sections.append((clean_title, body_text))

    capped_sections = unique_sections[:max_entries]
    compacted_count = len(capped_sections)

    top_header = "\n".join(header_lines).strip()
    if not top_header:
        top_header = "# Guidelines (Consolidated)"

    output_blocks: list[str] = [top_header]
    for idx, (title, body) in enumerate(capped_sections, start=1):
        section_block = f"## {idx}. {title}"
        if body:
            section_block += f"\n{body}"
        output_blocks.append(section_block)

    compacted_content = "\n\n".join(output_blocks) + "\n"
    return compacted_content, original_count, compacted_count


async def run_monthly_jules_compaction(jules_dir: Path | None = None) -> dict[str, int]:
    """
    Monthly scheduled job to compact .jules/*.md guideline files,
    removing hallucinated dates, duplicate blocks, and excess entries.
    """
    logger.info("🧹 Clockwork: Running Monthly Jules Guidelines (.jules/*.md) Compaction...")

    try:
        raw_settings = SettingsService().get_all_settings()
        config = SchedulerConfig.model_validate(raw_settings)
    except Exception:
        config = SchedulerConfig()

    max_entries = config.jules_max_entries_per_file
    target_dir = _resolve_jules_dir(jules_dir)

    stats: dict[str, int] = {
        "files_scanned": 0,
        "files_modified": 0,
        "entries_before": 0,
        "entries_after": 0,
    }

    if target_dir is None:
        logger.warning("🧹 Clockwork: .jules directory not found, skipping compaction.")
        return stats

    md_files = sorted(target_dir.glob("*.md"))
    for md_file in md_files:
        stats["files_scanned"] += 1
        original_text = md_file.read_text(encoding="utf-8")
        compacted_text, before_cnt, after_cnt = compact_markdown_content(
            original_text,
            max_entries=max_entries,
        )
        stats["entries_before"] += before_cnt
        stats["entries_after"] += after_cnt

        if compacted_text != original_text:
            md_file.write_text(compacted_text, encoding="utf-8")
            stats["files_modified"] += 1

    summary_msg = (
        f"Monthly .jules/*.md compaction completed: scanned {stats['files_scanned']} files, "
        f"modified {stats['files_modified']} files (entries {stats['entries_before']} -> {stats['entries_after']})."
    )
    try:
        log_service.create_log_entry(
            {
                "project_name": "clockwork-scheduler",
                "user_name": "system",
                "user_input": "monthly_jules_compaction",
                "gemini_response": summary_msg,
            }
        )
    except Exception as log_err:
        logger.warning(f"🧹 Clockwork: Failed to persist compaction log entry: {log_err}")

    logger.info(f"✅ Clockwork: {summary_msg}")
    return stats
