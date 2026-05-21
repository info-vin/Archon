from src.server.config.logfire_config import get_logger

logger = get_logger(__name__)


class VectorNormalization:
    """Handles logic related to embedding dimensions, padding, and performance scoring."""

    DIMENSION_COLUMNS = {768: "embedding_768", 1024: "embedding_1024", 1536: "embedding_1536", 3072: "embedding_3072"}
    INDEX_PREFERENCES = {
        768: "ivfflat",
        1024: "ivfflat",
        1536: "ivfflat",
        3072: "hnsw",
    }

    @classmethod
    def get_target_column(cls, dimensions: int) -> str:
        """Get the appropriate database column for the given dimensions."""
        if dimensions in cls.DIMENSION_COLUMNS:
            return cls.DIMENSION_COLUMNS[dimensions]

        if dimensions <= 768:
            logger.warning(f"Dimensions {dimensions} ≤ 768, using embedding_768 with padding")
            return "embedding_768"
        elif dimensions <= 1024:
            logger.warning(f"Dimensions {dimensions} ≤ 1024, using embedding_1024 with padding")
            return "embedding_1024"
        elif dimensions <= 1536:
            logger.warning(f"Dimensions {dimensions} ≤ 1536, using embedding_1536 with padding")
            return "embedding_1536"
        else:
            logger.warning(f"Dimensions {dimensions} > 1536, using embedding_3072 (may truncate)")
            return "embedding_3072"

    @classmethod
    def get_optimal_index_type(cls, dimensions: int) -> str:
        """Get the optimal index type for the given dimensions."""
        return cls.INDEX_PREFERENCES.get(dimensions, "hnsw")

    @classmethod
    def calculate_performance_score(cls, dimensions: int) -> float:
        """Calculate performance score for embedding dimensions."""
        if dimensions in cls.DIMENSION_COLUMNS:
            base_score = 1.0
        else:
            base_score = 0.7  # Penalize non-standard dimensions

        if dimensions <= 1536:
            index_bonus = 0.0
        else:
            index_bonus = -0.1

        if dimensions == 1536:
            dimension_bonus = 0.1
        elif dimensions == 768:
            dimension_bonus = 0.05
        else:
            dimension_bonus = 0.0

        final_score = max(0.0, min(1.0, base_score + index_bonus + dimension_bonus))
        logger.debug(f"Performance score for {dimensions}D: {final_score}")
        return final_score
