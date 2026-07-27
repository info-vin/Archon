"""
Code Extraction Service

Orchestrates extraction, processing, and storage of code examples from documents.
Refactored for L2 modularity while maintaining 100% logic alignment.
"""

import re
from collections.abc import Callable
from typing import Any

from src.server.config.logfire_config import safe_logfire_error
from src.server.repositories.base_repository import BaseRepository
from src.server.services.storage.code_storage_service import (
    add_code_examples_to_supabase,
    generate_code_summaries_batch,
)

from .logic.ast_processor import clean_code_content, get_text_extraction_patterns
from .logic.code_validator import validate_code_quality

# Logic Layer Imports
from .logic.constants import LANGUAGE_PATTERNS


class CodeExtractionService(BaseRepository):
    """
    Orchestrator for code extraction logic.
    Facade pattern maintained for full backward compatibility with test mocks.
    """

    LANGUAGE_PATTERNS = LANGUAGE_PATTERNS

    def __init__(self, supabase_client: Any = None) -> None:
        super().__init__(supabase_client)
        self._settings_cache: dict[str, Any] = {}

    async def _get_config(self):
        if not hasattr(self, "_config_cache"):
            from src.server.schemas.settings import CodeExtractionConfig
            from src.server.services.settings_service import SettingsService
            try:
                settings_service = SettingsService(self.supabase_client)
                self._config_cache = CodeExtractionConfig.model_validate(settings_service.get_all_settings())
            except Exception as e:
                from src.server.config.logfire_config import safe_logfire_error
                safe_logfire_error(f"Failed to parse CodeExtractionConfig: {e}")
                self._config_cache = CodeExtractionConfig()
        return self._config_cache

    # --- Setting Accessors ---
    async def _get_min_code_length(self) -> int:
        return int((await self._get_config()).min_code_block_length)

    async def _get_max_code_length(self) -> int:
        return int((await self._get_config()).max_code_block_length)

    async def _is_prose_filtering_enabled(self) -> bool:
        return bool((await self._get_config()).enable_prose_filtering)

    async def _get_max_prose_ratio(self) -> float:
        return float((await self._get_config()).max_prose_ratio)

    async def _get_min_code_indicators(self) -> int:
        return int((await self._get_config()).min_code_indicators)

    async def _is_diagram_filtering_enabled(self) -> bool:
        return bool((await self._get_config()).enable_diagram_filtering)

    async def _is_contextual_length_enabled(self) -> bool:
        return bool((await self._get_config()).enable_contextual_length)

    async def extract_and_store_code_examples(
        self,
        documents: list[dict[str, Any]],
        url_to_full_document: dict[str, str] | None = None,
        source_id: str | None = None,
        progress_callback: Callable | None = None,
        start_progress: int = 0,
        end_progress: int = 100,
        cancellation_check: Callable[[], None] | None = None,
        cancellation_token: dict[str, Any] | None = None,
        progress_id: str | None = None,
    ) -> int:
        """
        Entry point for code extraction. Signature sequence RESTORED for Test compatibility.
        """
        if not documents:
            return 0
        try:
            if progress_callback:
                await progress_callback(
                    {
                        "status": "code_extraction",
                        "progress": start_progress + 5,
                        "log": f"Extracting code from {len(documents)} documents...",
                    }
                )

            # RESTORED: Pass source_id explicitly to align with positional Mock expectations
            blocks = await self._extract_code_blocks_from_documents(documents, source_id)
            if not blocks:
                return 0

            if progress_callback:
                await progress_callback(
                    {
                        "status": "code_extraction",
                        "progress": start_progress + 25,
                        "log": f"Generating AI summaries for {len(blocks)} blocks...",
                    }
                )

            summaries = await self._generate_code_summaries(
                blocks, progress_callback, start_progress + 25, end_progress - 30, cancellation_check
            )
            storage_data = self._prepare_code_examples_for_storage(blocks, summaries)

            # CRITICAL: Propagation check
            if source_id:
                for meta in storage_data["metadatas"]:
                    meta["source_id"] = source_id

            final_doc_map = url_to_full_document or {
                d["url"]: d.get("content", d.get("markdown", "")) for d in documents if "url" in d
            }
            return await self._store_code_examples(
                storage_data, final_doc_map, progress_callback, end_progress - 30, end_progress
            )
        except Exception as e:
            safe_logfire_error(f"Extraction failed: {e}")
            return 0

    async def _extract_code_blocks_from_documents(
        self, documents: list[dict[str, Any]], source_id: str | None = None
    ) -> list[dict[str, Any]]:
        all_blocks = []
        for doc in documents:
            url = doc.get("url", "")
            # RESTORED: Support 'markdown' field used in tests
            content = doc.get("content", doc.get("markdown", ""))
            if not content:
                continue
            try:
                if url.endswith(".txt") or "llms.txt" in url:
                    blocks = await self._extract_text_file_code_blocks(content, url)
                else:
                    blocks = await self._extract_html_code_blocks(content)

                for b in blocks:
                    # Fix FB-04: Attach source_id from doc or parameter to the individual blocks
                    block_source_id = source_id or doc.get("source_id", url)
                    all_blocks.append({"block": b, "source_url": url, "source_id": block_source_id})
            except Exception as e:
                safe_logfire_error(f"Doc process error {url}: {e}")
        return all_blocks

    async def _extract_html_code_blocks(self, content: str) -> list[dict[str, Any]]:
        # PHYSICAL ALIGNMENT: 100% Sync with original working regex patterns
        patterns = [
            (
                r'<div[^>]*class=["\'][^"\']*highlight[^"\']*["\'][^>]*>.*?<pre[^>]*class=["\'][^"\']*(?:language-)?(\w+)[^"\']*["\'][^>]*><code[^>]*>(.*?)</code></pre>',
                "github-highlight",
            ),
            (
                r'<pre[^>]*><code[^>]*class=["\'][^"\']*language-(\w+)[^"\']*["\'][^>]*>(.*?)</code></pre>',
                "standard-lang",
            ),
            (r"<pre[^>]*>\s*<code[^>]*>(.*?)</code>\s*</pre>", "standard"),
        ]

        code_blocks = []
        extracted_positions: set[tuple[int, int]] = set()

        for pat_str, src_type in patterns:
            for match in re.finditer(pat_str, content, re.DOTALL | re.IGNORECASE):
                if src_type in ["github-highlight", "standard-lang"]:
                    if match.lastindex and match.lastindex >= 2:
                        lang = match.group(1)
                        code = match.group(2).strip()
                    else:
                        lang = ""
                        code = match.group(1).strip()
                else:
                    code = match.group(1).strip()
                    lm = re.search(r'class=["\'].*?language-(\w+)', match.group(0))
                    lang = lm.group(1) if lm else ""

                start_p, end_p = match.start(), match.end()
                min_l = await self._calculate_min_length(lang, content[max(0, start_p - 500) : start_p + 500])
                if len(code) < min_l:
                    continue

                if not any(not (end_p <= es or start_p >= ee) for es, ee in extracted_positions):
                    extracted_positions.add((start_p, end_p))
                    cleaned = self._clean_code_content(code, lang)
                    if await self._validate_code_quality(cleaned, lang):
                        code_blocks.append(
                            {
                                "code": cleaned,
                                "language": lang,
                                "context_before": content[max(0, start_p - 1000) : start_p].strip(),
                                "context_after": content[end_p : end_p + 1000].strip(),
                                "source_type": src_type,
                            }
                        )
        return code_blocks

    async def _extract_text_file_code_blocks(self, content: str, url: str) -> list[dict[str, Any]]:
        patterns = get_text_extraction_patterns()
        blocks = []
        for m in re.finditer(patterns["backtick"], content, re.DOTALL):
            lang, code = m.group(1), m.group(2).strip()
            min_l = await self._calculate_min_length(lang, content[max(0, m.start() - 500) : m.end() + 500])
            if len(code) >= min_l:
                cl = self._clean_code_content(code, lang)
                if await self._validate_code_quality(cl, lang):
                    blocks.append({"code": cl, "language": lang, "source_type": "text_backticks"})
        return blocks

    async def _calculate_min_length(self, lang: str, ctx: str) -> int:
        if not await self._is_contextual_length_enabled():
            return await self._get_min_code_length()
        base = {"json": 100, "python": 200, "typescript": 250}.get(lang.lower(), 250)
        return max(100, min(1000, base))

    def _clean_code_content(self, code: str, lang: str = "") -> str:
        return clean_code_content(code, lang)

    async def _validate_code_quality(self, code: str, lang: str) -> bool:
        return await validate_code_quality(
            code,
            lang,
            await self._is_diagram_filtering_enabled(),
            await self._get_min_code_indicators(),
            await self._is_prose_filtering_enabled(),
            await self._get_max_prose_ratio(),
        )

    async def _generate_code_summaries(self, blocks, callback, start, end, cancel) -> list[dict[str, str]]:
        if not (await self._get_config()).enable_code_summaries:
            return [{"example_name": "Code", "summary": "Demo"}] * len(blocks)
        return await generate_code_summaries_batch([b["block"] for b in blocks], 3, progress_callback=callback)

    def _prepare_code_examples_for_storage(self, blocks, summaries) -> dict[str, list[Any]]:
        res: dict[str, list[Any]] = {"urls": [], "chunk_numbers": [], "examples": [], "summaries": [], "metadatas": []}
        for i, (b, s) in enumerate(zip(blocks, summaries, strict=False)):
            res["urls"].append(b["source_url"])
            res["chunk_numbers"].append(i)
            res["examples"].append(b["block"]["code"])
            res["summaries"].append(s.get("summary", ""))
            res["metadatas"].append({"source_id": b["source_id"], "language": b["block"].get("language", "")})
        return res

    async def _store_code_examples(self, data, doc_map, callback, start, end) -> int:
        await add_code_examples_to_supabase(client=self.supabase_client, **data, url_to_full_document=doc_map)
        return len(data["examples"])
