import uuid
from datetime import datetime

from ..config.logfire_config import get_logger
from ..services.embeddings.embedding_service import create_embedding
from ..services.source_management_service import (
    SourceManagementService,
    extract_source_summary,
    update_source_info,
)
from ..utils import get_supabase_client
from ..repositories.knowledge_repository import KnowledgeRepository
from .knowledge.chunking_service import KnowledgeChunkingService
from .shared_constants import AgentUUIDs

logger = get_logger(__name__)


class LibrarianService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.source_service = SourceManagementService(self.supabase)
        self.repo = KnowledgeRepository(self.supabase)
        self.chunker = KnowledgeChunkingService()

    async def archive_any_url(self, url: str, user_role: str = "member", depth: int = 0, max_depth: int = 1) -> str:
        """
        New (Phase 4.7): Dynamically crawls ANY authorized URL and indexes it.
        Supports HTML and recursive Sitemap ingestion.
        """
        if depth > max_depth:
            logger.info(f"Librarian: Max depth reached ({max_depth}) | skipping {url}")
            return "depth-limit-reached"

        try:
            from .crawler_service import CrawlerService
            from .threading_service import ProcessingMode, get_threading_service

            crawler = CrawlerService(user_role=user_role)
            threading_service = get_threading_service()

            # 1. Fetch and Analyze
            result = await crawler.fetch_and_analyze(url)
            if result.get("status") == "error":
                raise Exception(result.get("message", "Crawler failed."))

            # 2. Route based on Type (Page vs Sitemap)
            if result.get("type") == "sitemap":
                links = result.get("discovered_links", [])
                logger.info(f"Librarian: Processing Sitemap | discovered={len(links)} links | depth={depth}")

                # Use ThreadingService to process links with rate limiting protection
                # We limit to first 5 links to avoid runaway costs/load
                target_links = links[:5]

                async def process_link(link: str):
                    if not link.endswith(".xml"):
                        return await self.archive_any_url(
                            link, user_role=user_role, depth=depth + 1, max_depth=max_depth
                        )
                    return None

                await threading_service.batch_process(
                    items=target_links, process_func=process_link, mode=ProcessingMode.NETWORK_BOUND
                )

                return f"batch-processed-{len(target_links)}-items"

            # 3. Standard Page Ingestion
            content = result["content"]
            title = result["title"]

            source_id = await self.archive_file(
                file_name=f"External: {title[:50]}", content=content, file_path=url, knowledge_type="external_knowledge"
            )

            logger.info(f"Librarian: Successfully ingested external URL | url={url} | id={source_id}")
            return source_id

        except Exception as e:
            logger.error(f"Librarian: Failed to archive URL {url} | error={str(e)}")
            return ""

    async def archive_sales_pitch(self, company: str, job_title: str, content: str, references: list[str]) -> str:
        """
        Archives a generated sales pitch into the knowledge base.
        """
        try:
            # 1. Generate unique Source ID
            safe_company = "".join(c for c in company if c.isalnum()).lower()
            unique_suffix = str(uuid.uuid4())[:8]
            source_id = f"pitch-{safe_company}-{unique_suffix}"

            # 2. Prepare Metadata
            title = f"Pitch: {company} - {job_title}"
            summary = f"Auto-generated sales pitch for {job_title} at {company}."
            word_count = len(content.split())
            tags = ["sales_pitch", "outbound", "email"]
            if references:
                tags.append("has_references")

            metadata = {
                "knowledge_type": "sales_pitch",
                "tags": tags,
                "references": references,
                "target_company": company,
                "target_job": job_title,
                "source_type": "generated",
                "auto_generated": True,
                "created_at": datetime.now().isoformat(),
            }

            logger.info(f"Librarian: Archiving pitch | source_id={source_id} | company={company}")

            # 3. Create Source Info (archon_sources)
            await update_source_info(
                client=self.supabase,
                source_id=source_id,
                summary=summary,
                word_count=word_count,
                content=content,
                knowledge_type="sales_pitch",
                tags=tags,
                source_display_name=title,
            )

            # 4. Insert Content (archon_crawled_pages)
            try:
                embedding_vector = await create_embedding(content)
            except Exception as e:
                logger.error(f"Librarian: Failed to generate embedding for pitch {source_id} | error={str(e)}")
                embedding_vector = None

            page_data = {
                "source_id": source_id,
                "url": f"generated://pitch/{source_id}",
                "chunk_number": 0,
                "content": content,
                "embedding": embedding_vector,
                "metadata": {**metadata, "title": title},
            }

            self.repo.insert_crawled_page(page_data)

            # 5. Record version
            self.repo.insert_document_version(
                document_id=source_id,
                field_name="sales_pitch",
                change_summary=f"Archived generated pitch for {company}",
                content={"source_id": source_id, "company": company, "job": job_title},
                created_by=AgentUUIDs.LIBRARIAN,
            )

            logger.info(f"Librarian: Pitch archived successfully | source_id={source_id}")
            return source_id

        except Exception as e:
            logger.error(f"Librarian: Failed to archive pitch | error={str(e)}")
            return ""

    async def get_style_constraints(self, category: str = "marketing") -> str:
        """
        Retrieves physical brand voice constraints and style rules from the knowledge base.
        Fulfills EXP-03 (Creative Resilience) requirements for Phase 4.6.46.
        """
        try:
            # Query for style lessons and brand voice rules
            res = self.supabase.table("archon_sources").select("title, content_summary").ilike("source_id", "style-lesson-%").limit(5).execute()

            rules = []
            if res.data:
                for entry in res.data:
                    rules.append(f"Rule: {entry.get('title')}\nConstraint: {entry.get('content_summary')}")

            if not rules:
                return "No specific brand voice constraints found. Use professional, data-driven tone."

            return "\n---\n".join(rules)
        except Exception as e:
            logger.warning(f"Librarian: Failed to fetch style constraints: {e}")
            return ""

    async def archive_web_research(self, query: str, content: str, references: list[str]) -> str:
        """
        Archives web research results into the knowledge base.
        """
        try:
            # 1. Generate unique Source ID
            safe_query = "".join(c for c in query if c.isalnum())[:20].lower()
            unique_suffix = str(uuid.uuid4())[:8]
            source_id = f"web-{safe_query}-{unique_suffix}"

            # 2. Prepare Metadata
            title = f"Research: {query}"
            summary = f"Web research results for: {query}"
            word_count = len(content.split())
            tags = ["web_research", "external_knowledge", "google_grounding"]

            logger.info(f"Librarian: Archiving web research | source_id={source_id} | query={query}")

            # 3. Create Source Info
            await update_source_info(
                client=self.supabase,
                source_id=source_id,
                summary=summary,
                word_count=word_count,
                content=content,
                knowledge_type="web_research",
                tags=tags,
                source_display_name=title,
            )

            # 4. Insert Content & Embedding
            try:
                embedding_vector = await create_embedding(content[:8000])
            except Exception as e:
                logger.error(f"Librarian: Failed to generate embedding for research {source_id}: {e}")
                embedding_vector = None

            page_data = {
                "source_id": source_id,
                "url": f"generated://research/{source_id}",
                "chunk_number": 0,
                "content": content,
                "embedding": embedding_vector,
                "metadata": {
                    "knowledge_type": "web_research",
                    "tags": tags,
                    "query": query,
                    "references": references,
                    "title": title,
                },
            }

            self.repo.insert_crawled_page(page_data)

            # 5. Record version
            self.repo.insert_document_version(
                document_id=source_id,
                field_name="web_research",
                change_summary=f"Archived research for: {query}",
                content={"source_id": source_id, "query": query, "refs_count": len(references)},
                created_by=AgentUUIDs.LIBRARIAN,
            )

            return source_id

        except Exception as e:
            logger.error(f"Librarian: Failed to archive web research | error={str(e)}")
            return ""

    async def archive_file(
        self,
        file_name: str,
        content: str,
        file_path: str,
        knowledge_type: str = "technical",
        authority_level: str = "normal",
    ) -> str:
        """
        Archives a local file into the knowledge base.
        """
        try:
            # 1. Generate Source ID
            safe_name = "".join(c for c in file_name if c.isalnum()).lower()
            unique_suffix = str(uuid.uuid4())[:8]
            source_id = f"file-{safe_name}-{unique_suffix}"

            # 2. Metadata
            title = file_name
            word_count = len(content.split())
            tags = ["file_upload", "seeded_knowledge"]
            if authority_level == "high":
                tags.append("policy")

            summary = await extract_source_summary(source_id, content)

            logger.info(f"Librarian: Archiving file | source_id={source_id} | file={file_name}")

            # 3. Source Info
            await update_source_info(
                client=self.supabase,
                source_id=source_id,
                summary=summary,
                word_count=word_count,
                content=content,
                knowledge_type=knowledge_type,
                tags=tags,
                source_display_name=title,
                original_url=f"file://{file_path}",
            )

            # 4. Content & Embedding
            page_data_list = await self.chunker.process_document_into_pages(
                source_id=source_id,
                content=content,
                base_url=f"file://{file_path}",
                metadata={
                    "knowledge_type": knowledge_type,
                    "tags": tags,
                    "file_path": file_path,
                },
                title_prefix=title
            )

            if page_data_list:
                self.repo.insert_crawled_page(page_data_list)

            # 5. Record version
            self.repo.insert_document_version(
                document_id=source_id,
                field_name="knowledge_file",
                change_summary=f"Indexed local file: {file_name}",
                content={"source_id": source_id, "file": file_name, "path": file_path},
                created_by=AgentUUIDs.LIBRARIAN,
            )

            return source_id

        except Exception as e:
            logger.error(f"Librarian: Failed to archive file {file_name} | error={str(e)}")
            return ""

    async def archive_failure_case(
        self, content: str, reason: str, company: str, job_title: str, metadata: dict | None = None
    ) -> str:
        """
        Archives a failed sales lead or rejected content as negative expertise.
        """
        try:
            unique_id = str(uuid.uuid4())[:8]
            source_id = f"fail-{company.lower().replace(' ', '-')}-{unique_id}"

            tags = ["failure_case", "risk_factor", "lesson_learned"]
            title = f"Failure Analysis: {company} - {job_title}"
            summary = f"Loss analysis for {company}. Reason: {reason}"

            full_content = (
                f"# Failure Analysis Report\n"
                f"**Entity**: {company} | **Context**: {job_title}\n"
                f"**Root Cause**: {reason}\n\n"
                f"## Full Context\n{content}"
            )

            await update_source_info(
                client=self.supabase,
                source_id=source_id,
                summary=summary,
                word_count=len(full_content.split()),
                content=full_content,
                knowledge_type="failure_analysis",
                tags=tags,
                source_display_name=title,
            )

            embedding_vector = await create_embedding(full_content[:8000])
            page_data = {
                "source_id": source_id,
                "url": f"analysis://failure/{source_id}",
                "chunk_number": 0,
                "content": full_content,
                "embedding": embedding_vector,
                "metadata": {
                    "outcome": "failure",
                    "reason": reason,
                    "company": company,
                    "job": job_title,
                    **(metadata or {}),
                },
            }
            self.repo.insert_crawled_page(page_data)

            return source_id

        except Exception as e:
            logger.error(f"Librarian: Failed to archive failure case: {e}")
            return ""

    async def archive_style_critique(self, post_title: str, original_content: str, review_notes: str) -> str:
        """
        Processes manager's review notes to extract reusable style constraints.
        """
        source_id = ""
        try:
            from google import genai
            from google.genai import types

            from ..config.model_ssot import SYSTEM_MODELS
            from ..services.credential_service import credential_service

            api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
            client = genai.Client(api_key=api_key)

            extraction_prompt = (
                "You are an AI Style Auditor. Analyze the following 'Review Notes' provided by a manager "
                "regarding a blog post. Extract 1-2 concrete, reusable 'Brand Voice Constraints' or 'Style Rules' "
                "that should be followed in the future. Avoid fluff.\n\n"
                f"Post Title: {post_title}\n"
                f"Review Notes: {review_notes}\n\n"
                "Return the rules as a clear Markdown list."
            )

            response = client.models.generate_content(
                model=SYSTEM_MODELS["DEFAULT_TEXT"],
                contents=extraction_prompt,
                config=types.GenerateContentConfig(temperature=0.1),
            )
            extracted_rules = response.text

            unique_id = str(uuid.uuid4())[:8]
            source_id = f"style-lesson-{unique_id}"
            tags = ["brand_voice_constraint", "style_lesson", "bob_feedback"]

            summary = f"Style lesson learned from rejection of '{post_title}'"
            full_lesson = (
                f"# Style Lesson: {post_title}\n"
                f"## Feedback Received\n{review_notes}\n\n"
                f"## Extracted Constraints\n{extracted_rules}\n"
            )

            await update_source_info(
                client=self.supabase,
                source_id=source_id,
                summary=summary,
                word_count=len(full_lesson.split()),
                content=full_lesson,
                knowledge_type="brand_voice",
                tags=tags,
                source_display_name=f"Style Lesson: {post_title}",
            )

            embedding_vector = await create_embedding(full_lesson[:8000])
            page_data = {
                "source_id": source_id,
                "url": f"lesson://style/{source_id}",
                "chunk_number": 0,
                "content": full_lesson,
                "embedding": embedding_vector,
                "metadata": {"type": "style_constraint", "tags": tags, "post_title": post_title},
            }
            self.repo.insert_crawled_page(page_data)

            return source_id

        except Exception as e:
            logger.error(f"Librarian: Failed to archive style critique: {e}")
            return ""
