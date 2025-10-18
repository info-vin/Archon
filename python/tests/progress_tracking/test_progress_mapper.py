"""
Tests for ProgressMapper
"""

import pytest

from src.server.services.crawling.progress_mapper import ProgressMapper


class TestProgressMapper:
    """Test suite for ProgressMapper"""

    def test_initialization(self):
        """Test ProgressMapper initialization"""
        mapper = ProgressMapper()
        
        assert mapper.last_overall_progress == 0
        assert mapper.current_stage == "starting"
        
    def test_map_progress_basic(self):
        """Test basic progress mapping"""
        mapper = ProgressMapper()
        
        # Starting stage (0-1%)
        progress = mapper.map_progress("starting", 50)
        assert progress == 0
        
        # Analyzing stage (1-2%)
        progress = mapper.map_progress("analyzing", 50)
        assert progress == 2  # 1 + (50% of 1) = 1.5 -> 2
        
        # Crawling stage (2-5%)
        progress = mapper.map_progress("crawling", 50)
        assert progress == 4  # 2 + (50% of 3) = 3.5 -> 4
        
    def test_progress_never_goes_backwards(self):
        """Test that progress never decreases"""
        mapper = ProgressMapper()
        
        # Move to 50% of crawling (2-5%) = 4%
        progress1 = mapper.map_progress("crawling", 50)
        assert progress1 == 4
        
        # Try to go back to analyzing (1-2%) - should stay at 4%
        progress2 = mapper.map_progress("analyzing", 100)
        assert progress2 == 4  # Should not go backwards
        
        # Can move forward to document_storage (10-30%)
        progress3 = mapper.map_progress("document_storage", 50)
        assert progress3 == 20  # 10 + (50% of 20) = 20
        
    def test_completion_handling(self):
        """Test completion status handling"""
        mapper = ProgressMapper()
        
        # Jump straight to completed
        progress = mapper.map_progress("completed", 0)
        assert progress == 100
        
        # Any percentage at completed should be 100
        progress = mapper.map_progress("completed", 50)
        assert progress == 100
        
    def test_error_handling(self):
        """Test error status handling"""
        mapper = ProgressMapper()
        
        # Error should return -1
        progress = mapper.map_progress("error", 50)
        assert progress == -1
        
    def test_unknown_stage(self):
        """Test handling of unknown stages"""
        mapper = ProgressMapper()
        
        # Set some initial progress
        mapper.map_progress("crawling", 50) # sets progress to 4
        current = mapper.last_overall_progress
        assert current == 4
        
        # Unknown stage should maintain current progress
        progress = mapper.map_progress("unknown_stage", 50)
        assert progress == current
        
    def test_stage_ranges(self):
        """Test all defined stage ranges"""
        mapper = ProgressMapper()
        
        # Verify ranges are correctly defined with new balanced values
        assert mapper.STAGE_RANGES["starting"] == (0, 1)
        assert mapper.STAGE_RANGES["analyzing"] == (1, 2)
        assert mapper.STAGE_RANGES["crawling"] == (2, 5)
        assert mapper.STAGE_RANGES["processing"] == (5, 8)
        assert mapper.STAGE_RANGES["source_creation"] == (8, 10)
        assert mapper.STAGE_RANGES["document_storage"] == (10, 30)
        assert mapper.STAGE_RANGES["code_extraction"] == (30, 95)
        assert mapper.STAGE_RANGES["finalization"] == (95, 100)
        assert mapper.STAGE_RANGES["completed"] == (100, 100)
        
        # Upload-specific stages
        assert mapper.STAGE_RANGES["reading"] == (0, 5)
        assert mapper.STAGE_RANGES["extracting"] == (5, 10)
        assert mapper.STAGE_RANGES["chunking"] == (10, 15)
        assert mapper.STAGE_RANGES["creating_source"] == (15, 20)
        assert mapper.STAGE_RANGES["summarizing"] == (20, 30)
        assert mapper.STAGE_RANGES["storing"] == (30, 100)
        
    def test_calculate_stage_progress(self):
        """Test calculating percentage within a stage"""
        mapper = ProgressMapper()
        
        # 5 out of 10 = 50%
        progress = mapper.calculate_stage_progress(5, 10)
        assert progress == 50.0
        
        # 0 out of 10 = 0%
        progress = mapper.calculate_stage_progress(0, 10)
        assert progress == 0.0
        
        # 10 out of 10 = 100%
        progress = mapper.calculate_stage_progress(10, 10)
        assert progress == 100.0
        
        # Handle division by zero
        progress = mapper.calculate_stage_progress(5, 0)
        assert progress == 0.0
        
    def test_map_batch_progress(self):
        """Test batch progress mapping"""
        mapper = ProgressMapper()
        
        # Batch 1 of 5 in document_storage stage (range 10-30)
        # Stage progress = ((1-1)/5)*100 = 0%
        # Mapped = 10 + (0/100 * 20) = 10
        progress = mapper.map_batch_progress("document_storage", 1, 5)
        assert progress == 10
        
        # Batch 3 of 5
        # Stage progress = ((3-1)/5)*100 = 40%
        # Mapped = 10 + (40/100 * 20) = 10 + 8 = 18
        progress = mapper.map_batch_progress("document_storage", 3, 5)
        assert progress == 18
        
        # Batch 5 of 5
        # Stage progress = ((5-1)/5)*100 = 80%
        # Mapped = 10 + (80/100 * 20) = 10 + 16 = 26
        progress = mapper.map_batch_progress("document_storage", 5, 5)
        assert progress == 26
        
    def test_map_with_substage(self):
        """Test mapping with substage information"""
        mapper = ProgressMapper()
        
        # Currently just uses main stage
        # document_storage (10-30) at 50% -> 10 + (50/100 * 20) = 20
        progress = mapper.map_with_substage("document_storage", "embeddings", 50)
        assert progress == 20
        
    def test_reset(self):
        """Test resetting the mapper"""
        mapper = ProgressMapper()
        
        # Set some progress
        mapper.map_progress("document_storage", 50) # -> 20
        assert mapper.last_overall_progress == 20
        assert mapper.current_stage == "document_storage"
        
        # Reset
        mapper.reset()
        assert mapper.last_overall_progress == 0
        assert mapper.current_stage == "starting"
        
    def test_get_current_stage(self):
        """Test getting current stage"""
        mapper = ProgressMapper()
        
        assert mapper.get_current_stage() == "starting"
        
        mapper.map_progress("crawling", 50)
        assert mapper.get_current_stage() == "crawling"
        
        mapper.map_progress("code_extraction", 50)
        assert mapper.get_current_stage() == "code_extraction"
        
    def test_get_current_progress(self):
        """Test getting current progress"""
        mapper = ProgressMapper()
        
        assert mapper.get_current_progress() == 0
        
        mapper.map_progress("crawling", 50) # -> 4
        assert mapper.get_current_progress() == 4
        
        # code_extraction (30-95) at 50% -> 30 + (50/100 * 65) = 30 + 32.5 = 62.5 -> 62
        mapper.map_progress("code_extraction", 50)
        assert mapper.get_current_progress() == 62
        
    def test_get_stage_range(self):
        """Test getting stage range"""
        mapper = ProgressMapper()
        
        assert mapper.get_stage_range("starting") == (0, 1)
        assert mapper.get_stage_range("code_extraction") == (30, 95)
        assert mapper.get_stage_range("unknown") == (0, 100)  # Default range
        
    def test_realistic_crawl_sequence(self):
        """Test a realistic crawl progress sequence"""
        mapper = ProgressMapper()
        
        # Starting (0-1)
        assert mapper.map_progress("starting", 0) == 0
        assert mapper.map_progress("starting", 100) == 1
        
        # Analyzing (1-2)
        assert mapper.map_progress("analyzing", 0) == 1
        assert mapper.map_progress("analyzing", 100) == 2
        
        # Crawling (2-5)
        assert mapper.map_progress("crawling", 0) == 2
        assert mapper.map_progress("crawling", 33) == 3  # 2 + (33% of 3) = 2.99 -> 3
        assert mapper.map_progress("crawling", 66) == 4  # 2 + (66% of 3) = 3.98 -> 4
        assert mapper.map_progress("crawling", 100) == 5
        
        # Processing (5-8)
        assert mapper.map_progress("processing", 0) == 5
        assert mapper.map_progress("processing", 100) == 8
        
        # Source creation (8-10)
        assert mapper.map_progress("source_creation", 0) == 8
        assert mapper.map_progress("source_creation", 100) == 10
        
        # Document storage (10-30)
        assert mapper.map_progress("document_storage", 0) == 10
        assert mapper.map_progress("document_storage", 50) == 20  # 10 + (50% of 20) = 20
        assert mapper.map_progress("document_storage", 100) == 30
        
        # Code extraction (30-95)
        assert mapper.map_progress("code_extraction", 0) == 30
        assert mapper.map_progress("code_extraction", 25) == 46  # 30 + (25% of 65) = 46.25 -> 46
        assert mapper.map_progress("code_extraction", 50) == 62  # 30 + (50% of 65) = 62.5 -> 62
        assert mapper.map_progress("code_extraction", 75) == 79  # 30 + (75% of 65) = 78.75 -> 79
        assert mapper.map_progress("code_extraction", 100) == 95
        
        # Finalization (95-100)
        assert mapper.map_progress("finalization", 0) == 95
        assert mapper.map_progress("finalization", 100) == 100
        
        # Completed
        assert mapper.map_progress("completed", 0) == 100
