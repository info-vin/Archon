from typing import Any

from .models import DiscoveryResultDTO, HostStatusDTO, ModelDictDTO, OllamaModel


class OllamaManifestParser:
    """Parses and aggregates Ollama model discovery results."""

    @staticmethod
    def parse_tags_response(data: dict[str, Any], instance_url: str) -> list[OllamaModel]:
        """Parses the raw JSON response from /api/tags into a list of OllamaModel."""
        models: list[OllamaModel] = []
        if "models" in data:
            for model_data in data["models"]:
                model = OllamaModel(
                    name=model_data.get("name", "unknown"),
                    tag=model_data.get("name", "unknown"),  # Ollama uses name as tag
                    size=model_data.get("size", 0),
                    digest=model_data.get("digest", ""),
                    capabilities=[],  # Will be filled by capability detection
                    instance_url=instance_url,
                )

                details = model_data.get("details", {})
                if details:
                    model.parameters = {
                        "family": details.get("family", ""),
                        "parameter_size": details.get("parameter_size", ""),
                        "quantization": details.get("quantization_level", ""),
                    }

                models.append(model)
        return models

    @staticmethod
    def aggregate_discovery_results(instance_urls: list[str], results: list[Any]) -> DiscoveryResultDTO:
        """Aggregates results from multiple instances into a single discovery dictionary."""
        all_models: list[OllamaModel] = []
        chat_models: list[ModelDictDTO] = []
        embedding_models: list[ModelDictDTO] = []
        host_status: dict[str, HostStatusDTO] = {}
        discovery_errors: list[str] = []

        for url, result in zip(instance_urls, results, strict=False):
            if isinstance(result, Exception):
                error_msg = f"Failed to discover models from {url}: {str(result)}"
                discovery_errors.append(error_msg)
                host_status[url] = {"status": "error", "error": str(result)}
            else:
                models: list[OllamaModel] = result
                all_models.extend(models)
                host_status[url] = {"status": "online", "models_count": str(len(models)), "instance_url": url}

                for model in models:
                    if "chat" in model.capabilities:
                        chat_models.append(
                            {
                                "name": model.name,
                                "instance_url": model.instance_url,
                                "size": model.size,
                                "parameters": model.parameters,
                                "context_window": model.context_window,
                                "max_context_length": model.max_context_length,
                                "base_context_length": model.base_context_length,
                                "custom_context_length": model.custom_context_length,
                                "architecture": model.architecture,
                                "format": model.format,
                                "parent_model": model.parent_model,
                                "capabilities": model.capabilities,
                            }
                        )

                    if "embedding" in model.capabilities:
                        embedding_models.append(
                            {
                                "name": model.name,
                                "instance_url": model.instance_url,
                                "dimensions": model.embedding_dimensions,
                                "size": model.size,
                                "parameters": model.parameters,
                                "context_window": model.context_window,
                                "max_context_length": model.max_context_length,
                                "base_context_length": model.base_context_length,
                                "custom_context_length": model.custom_context_length,
                                "architecture": model.architecture,
                                "format": model.format,
                                "parent_model": model.parent_model,
                                "capabilities": model.capabilities,
                            }
                        )

        # Remove duplicates (same model on multiple instances)
        unique_models: dict[str, OllamaModel] = {}
        for model in all_models:
            key = f"{model.name}@{model.instance_url}"
            unique_models[key] = model

        return {
            "total_models": len(unique_models),
            "chat_models": chat_models,
            "embedding_models": embedding_models,
            "host_status": host_status,
            "discovery_errors": discovery_errors,
            "unique_model_names": list({model.name for model in unique_models.values()}),
        }
