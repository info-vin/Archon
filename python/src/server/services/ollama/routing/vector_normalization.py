from src.server.config.logfire_config import get_logger
from src.server.services.embeddings.multi_dimensional_embedding_service import multi_dimensional_embedding_service

logger = get_logger(__name__)

class VectorNormalization:
    """Handles logic related to embedding dimensions, padding, and performance scoring."""

    INDEX_PREFERENCES = {
        768: "ivfflat",
        1024: "ivfflat",
        1536: "ivfflat",
        3072: "hnsw",
    }

    @classmethod
    def _get_supported_dimensions(cls) -> list[int]:
        return sorted(multi_dimensional_embedding_service.get_supported_dimensions().keys())

    @classmethod
    def get_target_column(cls, dimensions: int) -> str:
        """Get the appropriate database column for the given dimensions."""
        supported_dims = cls._get_supported_dimensions()

        if multi_dimensional_embedding_service.is_dimension_supported(dimensions):
            return multi_dimensional_embedding_service.get_embedding_column_name(dimensions)

        for supported_dim in supported_dims:
            if dimensions <= supported_dim:
                col_name = multi_dimensional_embedding_service.get_embedding_column_name(supported_dim)
                logger.warning(f"Dimensions {dimensions} <= {supported_dim}, using {col_name} with padding")
                return col_name

        max_dim = supported_dims[-1] if supported_dims else 3072
        max_col = multi_dimensional_embedding_service.get_embedding_column_name(max_dim)
        logger.warning(f"Dimensions {dimensions} > {max_dim}, using {max_col} (may truncate)")
        return max_col

    @classmethod
    def get_optimal_index_type(cls, dimensions: int) -> str:
        """Get the optimal index type for the given dimensions."""
        return cls.INDEX_PREFERENCES.get(dimensions, "hnsw")

    @classmethod
    def calculate_performance_score(cls, dimensions: int) -> float:
        """Calculate performance score for embedding dimensions."""
        if multi_dimensional_embedding_service.is_dimension_supported(dimensions):
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
