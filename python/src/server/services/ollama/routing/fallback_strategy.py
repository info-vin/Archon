from src.server.config.logfire_config import get_logger
from src.server.services.embeddings.multi_dimensional_embedding_service import multi_dimensional_embedding_service

logger = get_logger(__name__)

class FallbackStrategy:
    """Handles fallback routing strategies for embeddings."""

    @staticmethod
    def get_fallback_dimensions_and_column(model_name: str) -> tuple[int, str]:
        """Get fallback dimensions and target column based on model mapping."""
        dimensions = multi_dimensional_embedding_service.get_dimension_for_model(model_name)
        target_column = multi_dimensional_embedding_service.get_embedding_column_name(dimensions)

        logger.info(f"Model mapping: {model_name} -> {dimensions}D -> {target_column}")

        return dimensions, target_column
