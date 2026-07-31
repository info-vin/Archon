import asyncio
from typing import TYPE_CHECKING, Any

from ....config.logfire_config import get_logger, safe_logfire_error, safe_logfire_info
from .registry import unregister_orchestration

if TYPE_CHECKING:
    from ..crawling_service import CrawlingService

logger = get_logger(__name__)


class CrawlOrchestrator:
    """
    Handles the asynchronous lifecycle of a crawl operation.
    Physically isolated for Phase 4.6.16 modularization.
    """

    def __init__(self, service: "CrawlingService") -> None:
        self.service = service

    async def run(self, request: dict[str, Any], task_id: str):
        """
        Async orchestration that runs in the main event loop.
        """
        last_heartbeat = asyncio.get_event_loop().time()
        heartbeat_interval = 30.0

        async def send_heartbeat_if_needed() -> float:
            current_time = asyncio.get_event_loop().time()
            if current_time - last_heartbeat >= heartbeat_interval:
                await self.service._handle_progress_update(
                    task_id,
                    {
                        "status": self.service.progress_mapper.get_current_stage(),
                        "progress": self.service.progress_mapper.get_current_progress(),
                        "heartbeat": True,
                        "log": "Background task still running...",
                        "message": "Processing...",
                    },
                )
                return current_time
            return last_heartbeat

        try:
            url = str(request.get("url", ""))
            safe_logfire_info(f"Starting async crawl orchestration | url={url} | task_id={task_id}")

            if self.service.progress_tracker:
                await self.service.progress_tracker.start(
                    {"url": url, "status": "starting", "progress": 0, "log": f"Starting crawl of {url}"}
                )

            original_source_id = self.service.url_handler.generate_unique_source_id(url)
            source_display_name = self.service.url_handler.extract_display_name(url)

            async def update_mapped_progress(stage: str, stage_progress: int, message: str, **kwargs):
                overall_progress = self.service.progress_mapper.map_progress(stage, stage_progress)
                await self.service._handle_progress_update(
                    task_id,
                    {
                        "status": stage,
                        "progress": overall_progress,
                        "log": message,
                        "message": message,
                        **kwargs,
                    },
                )

            await update_mapped_progress("starting", 100, f"Starting crawl of {url}", current_url=url)
            self.service._check_cancellation()

            await update_mapped_progress(
                "analyzing", 50, f"Analyzing URL type for {url}", total_pages=1, processed_pages=0
            )

            # Detect and crawl
            crawl_results, crawl_type = await self.service.url_type_router.crawl_by_url_type(url, request)

            if self.service.progress_tracker and crawl_type:
                await self.service.progress_tracker.update(
                    status="crawling", progress=15, log=f"Processing {crawl_type} content", crawl_type=crawl_type
                )

            self.service._check_cancellation()
            last_heartbeat = await send_heartbeat_if_needed()

            if not crawl_results:
                raise ValueError("No content was crawled from the provided URL")

            await update_mapped_progress("processing", 50, "Processing crawled content")
            self.service._check_cancellation()

            async def doc_storage_callback(status: str, progress: int, message: str, **kwargs):
                if self.service.progress_tracker:
                    mapped_progress = self.service.progress_mapper.map_progress("document_storage", progress)
                    await self.service.progress_tracker.update(
                        status="document_storage", progress=mapped_progress, log=message, **kwargs
                    )

            storage_results = await self.service.doc_storage_ops.store_documents(
                crawl_results,
                request,
                crawl_type,
                original_source_id,
                doc_storage_callback,
                self.service._check_cancellation,
                source_url=url,
                source_display_name=source_display_name,
            )

            self.service._check_cancellation()
            last_heartbeat = await send_heartbeat_if_needed()

            actual_chunks_stored = storage_results.get("chunks_stored", 0)
            if storage_results["chunk_count"] > 0 and actual_chunks_stored == 0:
                error_msg = f"Failed to store documents: {storage_results['chunk_count']} chunks processed but 0 stored"
                safe_logfire_error(error_msg)
                raise Exception(error_msg)

            code_examples_count = 0
            if request.get("extract_code_examples", True) and actual_chunks_stored > 0:
                self.service._check_cancellation()
                await update_mapped_progress("code_extraction", 0, "Starting code extraction...")

                async def code_progress_callback(data: dict):
                    if self.service.progress_tracker:
                        raw_progress = data.get("progress", data.get("percentage", 0))
                        mapped_progress = self.service.progress_mapper.map_progress("code_extraction", raw_progress)
                        await self.service.progress_tracker.update(
                            status=data.get("status", "code_extraction"),
                            progress=mapped_progress,
                            log=data.get("log", "Extracting code examples..."),
                            **{k: v for k, v in data.items() if k not in ["status", "progress", "percentage", "log"]}, # 合法
                        )

                code_examples_count = await self.service.doc_storage_ops.store_code_examples(
                    crawl_results,
                    storage_results["url_to_full_document"],
                    storage_results["source_id"],
                    code_progress_callback,
                    85,
                    95,
                    self.service._check_cancellation,
                )
                self.service._check_cancellation()
                last_heartbeat = await send_heartbeat_if_needed()

            await update_mapped_progress(
                "finalization",
                50,
                "Finalizing crawl results...",
                chunks_stored=actual_chunks_stored,
                code_examples_found=code_examples_count,
            )

            await update_mapped_progress(
                "completed",
                100,
                f"Crawl completed: {actual_chunks_stored} chunks, {code_examples_count} code examples",
                chunks_stored=actual_chunks_stored,
                code_examples_found=code_examples_count,
                processed_pages=len(crawl_results),
                total_pages=len(crawl_results),
            )

            if self.service.progress_tracker:
                await self.service.progress_tracker.complete(
                    {
                        "chunks_stored": actual_chunks_stored,
                        "code_examples_found": code_examples_count,
                        "processed_pages": len(crawl_results),
                        "total_pages": len(crawl_results),
                        "sourceId": storage_results.get("source_id", ""),
                        "log": "Crawl completed successfully!",
                    }
                )

            if self.service.progress_id:
                unregister_orchestration(self.service.progress_id)

        except asyncio.CancelledError:
            safe_logfire_info(f"Crawl operation cancelled | progress_id={self.service.progress_id}")
            await self.service._handle_progress_update(
                task_id,
                {
                    "status": "cancelled",
                    "progress": -1,
                    "log": "Crawl operation was cancelled by user",
                },
            )
            if self.service.progress_id:
                unregister_orchestration(self.service.progress_id)
        except Exception as e:
            logger.error("Async crawl orchestration failed", exc_info=True)
            safe_logfire_error(f"Async crawl orchestration failed | error={str(e)}")
            error_message = f"Crawl failed: {str(e)}"
            await self.service._handle_progress_update(
                task_id, {"status": "error", "progress": -1, "log": error_message, "error": str(e)}
            )
            if self.service.progress_tracker:
                await self.service.progress_tracker.error(error_message)
            if self.service.progress_id:
                unregister_orchestration(self.service.progress_id)
