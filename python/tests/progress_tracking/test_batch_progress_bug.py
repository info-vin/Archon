"""
Test for batch progress bug where progress jumps to 100% prematurely.

This test ensures that when document_storage completes (100% of its stage),
the overall progress maps correctly and doesn't contaminate future stages.
"""

import asyncio
import pytest

from src.server.services.crawling.progress_mapper import ProgressMapper
from src.server.utils.progress.progress_tracker import ProgressTracker


class TestBatchProgressBug:
    """Test that batch progress doesn't jump to 100% prematurely."""

    @pytest.mark.asyncio
    async def test_document_storage_completion_maps_correctly(self):
        """Test that document_storage at 100% maps to 30% overall, not 100%."""
        mapper = ProgressMapper()
        progress_values = []

        # Document storage (10-30) progresses from 0 to 100%
        for i in range(0, 101, 20):
            mapped = mapper.map_progress("document_storage", i)
            progress_values.append(mapped)

            if i == 0:
                assert mapped == 10, f"document_storage at 0% should map to 10%, got {mapped}%"
            elif i == 100:
                assert mapped == 30, f"document_storage at 100% should map to 30%, got {mapped}%"
            else:
                assert 10 <= mapped <= 30, f"document_storage at {i}% should be between 10-30%, got {mapped}%"

        assert mapper.last_overall_progress == 30, "After document_storage completes, overall should be 30%"

        # Code extraction (30-95) starts at 30%
        code_start = mapper.map_progress("code_extraction", 0)
        assert code_start == 30, f"code_extraction at 0% should map to 30%, got {code_start}%"

        # 50% of code_extraction -> 30 + 0.5 * (95-30) = 62.5 -> 62
        code_mid = mapper.map_progress("code_extraction", 50)
        assert code_mid == 62, f"code_extraction at 50% should map to 62%, got {code_mid}%"

        code_end = mapper.map_progress("code_extraction", 100)
        assert code_end == 95, f"code_extraction at 100% should map to 95%, got {code_end}%"

    @pytest.mark.asyncio
    async def test_progress_tracker_prevents_raw_value_contamination(self):
        """Test that ProgressTracker doesn't allow raw progress values to contaminate state."""
        tracker = ProgressTracker("test-progress-123", "crawl")
        await tracker.start({"url": "https://example.com"})

        # document_storage stage starts at 10
        await tracker.update("document_storage", 10, "Starting document storage")
        assert tracker.state["progress"] == 10

        await tracker.update("document_storage", 20, "Processing batches")
        assert tracker.state["progress"] == 20

        await tracker.update("document_storage", 30, "Document storage complete")
        assert tracker.state["progress"] == 30

        logs = tracker.state.get("logs", [])
        if logs:
            last_log = logs[-1]
            assert last_log["progress"] == 30, f"Log should have progress=30, got {last_log['progress']}"

        await tracker.update("code_extraction", 30, "Starting code extraction")
        assert tracker.state["progress"] == 30, "Progress should stay at 30% when code_extraction starts"

        await tracker.update("code_extraction", 62, "Extracting code examples")
        assert tracker.state["progress"] == 62

        await tracker.update("code_extraction", 70, "More extraction", raw_progress=100, fake_status="fake")
        assert tracker.state["progress"] == 70, "Progress should remain at 70%"
        assert tracker.state["status"] == "code_extraction", "Status should remain code_extraction"
        assert tracker.state.get("raw_progress") != 70, "raw_progress can be stored but shouldn't affect progress"

    @pytest.mark.asyncio
    async def test_batch_processing_progress_sequence(self):
        """Test realistic batch processing sequence to ensure no premature 100%."""
        mapper = ProgressMapper()
        tracker = ProgressTracker("test-batch-123", "crawl")
        await tracker.start({"url": "https://example.com/sitemap.xml"})

        total_pages = 20
        # Crawling phase (2-5%)
        for page in range(1, total_pages + 1):
            progress = (page / total_pages) * 100
            mapped = mapper.map_progress("crawling", progress)
            await tracker.update("crawling", mapped, f"Crawled {page}/{total_pages} pages")
            assert mapped <= 5, f"Crawling progress should not exceed 5%, got {mapped}%"

        # Document storage phase (10-30%) - process in 5 batches
        total_batches = 5
        for batch in range(1, total_batches + 1):
            progress = (batch / total_batches) * 100
            mapped = mapper.map_progress("document_storage", progress)
            await tracker.update("document_storage", mapped, f"Batch {batch}/{total_batches}")
            assert 10 <= mapped <= 30, f"Document storage should be 10-30%, got {mapped}%"

            if batch == 4:
                assert mapped < 30, f"Batch 4/{total_batches} should not be at 30% yet, got {mapped}%"

        final_doc_progress = tracker.state["progress"]
        assert final_doc_progress == 30, f"After document storage, should be at 30%, got {final_doc_progress}%"

        # Code extraction phase (30-95%)
        code_batches = 10
        for batch in range(1, code_batches + 1):
            progress = (batch / code_batches) * 100
            mapped = mapper.map_progress("code_extraction", progress)
            await tracker.update("code_extraction", mapped, f"Code batch {batch}/{code_batches}")
            assert 30 <= mapped <= 95, f"Code extraction should be 30-95%, got {mapped}%"

        # Finalization (95-100%)
        finalize_mapped = mapper.map_progress("finalization", 50)
        await tracker.update("finalization", finalize_mapped, "Finalizing")
        assert 95 <= finalize_mapped <= 100, f"Finalization should be 95-100%, got {finalize_mapped}%"

        complete_mapped = mapper.map_progress("completed", 100)
        await tracker.update("completed", complete_mapped, "Completed")
        assert complete_mapped == 100, "Only 'completed' stage should reach 100%"

        logs = tracker.state.get("logs", [])
        for i, log in enumerate(logs[:-1]):
            assert log["progress"] < 100, f"Log {i} shows premature 100%: {log}"

        if logs:
            assert logs[-1]["progress"] == 100, "Final log should be 100%"


if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v"]))