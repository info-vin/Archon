import time
from typing import Any

from src.server.config.logfire_config import get_logger

from .capability_tester import get_model_details_logic
from .models import OllamaModel

logger = get_logger(__name__)

# PERFORMANCE: Pre-compiled tuples to prevent redundant allocations inside the loop
EMBEDDING_PATTERNS = (
    "embed",
    "embedding",
    "bge-",
    "e5-",
    "sentence-",
    "arctic-embed",
    "nomic-embed",
    "mxbai-embed",
    "snowflake-arctic-embed",
    "gte-",
    "stella-",
)

CHAT_PATTERNS = (
    "phi",
    "qwen",
    "llama",
    "mistral",
    "gemma",
    "deepseek",
    "codellama",
    "orca",
    "vicuna",
    "wizardlm",
    "solar",
    "mixtral",
    "chatglm",
    "baichuan",
    "yi",
    "zephyr",
    "openchat",
    "starling",
    "nous-hermes",
)

FUNCTION_CALLING_PATTERNS = ("qwen", "llama3", "phi3", "mistral")
STRUCTURED_OUTPUT_PATTERNS = ("llama", "phi", "gemma")
UNKNOWN_EMBEDDING_PATTERNS = ("embed", "embedding", "vector")


async def enrich_model_capabilities_logic(
    service_instance,
    models: list[OllamaModel],
    instance_url: str,
    fetch_details: bool = False,
) -> list[OllamaModel]:
    """Pattern-match and enrich model capabilities from Ollama API."""
    start_time = time.time()
    enriched_models = []
    unknown_models = []

    for model in models:
        model_name_lower = model.name.lower()

        is_embedding_model = any(pattern in model_name_lower for pattern in EMBEDDING_PATTERNS)

        if is_embedding_model:
            model.capabilities = ["embedding"]
            if "nomic" in model_name_lower:
                model.embedding_dimensions = 768
            elif "bge" in model_name_lower:
                model.embedding_dimensions = 1024 if "large" in model_name_lower else 768
            elif "e5" in model_name_lower:
                model.embedding_dimensions = 1024 if "large" in model_name_lower else 768
            elif "arctic" in model_name_lower:
                model.embedding_dimensions = 1024
            else:
                model.embedding_dimensions = 768
            logger.debug(f"Pattern-matched embedding model {model.name}")
            enriched_models.append(model)
        else:
            if any(pattern in model_name_lower for pattern in CHAT_PATTERNS):
                model.capabilities = ["chat"]
                if any(p in model_name_lower for p in FUNCTION_CALLING_PATTERNS):
                    model.capabilities.extend(["function_calling", "structured_output"]) # 合法
                elif any(p in model_name_lower for p in STRUCTURED_OUTPUT_PATTERNS):
                    model.capabilities.append("structured_output")

                if fetch_details:
                    try:
                        detailed_info = await get_model_details_logic(model.name, instance_url)
                        if detailed_info:
                            _map_details_to_model(model, detailed_info)
                    except Exception as e:
                        logger.debug(f"Could not get details for {model.name}: {e}")
                enriched_models.append(model)
            else:
                unknown_models.append(model)

    if unknown_models:
        for model in unknown_models:
            model.capabilities = ["chat"]
            model_name_lower = model.name.lower()
            if any(h in model_name_lower for h in UNKNOWN_EMBEDDING_PATTERNS):
                model.capabilities = ["embedding"]
                model.embedding_dimensions = 768
            enriched_models.append(model)

    logger.info(f"Model enrichment complete for {instance_url} in {time.time() - start_time:.2f}s")
    return enriched_models


def _map_details_to_model(model: OllamaModel, info: dict[str, Any]):
    """Internal helper to map /api/show dict to OllamaModel object."""
    model.context_window = info.get("context_window")
    model.max_context_length = info.get("max_context_length")
    model.base_context_length = info.get("base_context_length")
    model.custom_context_length = info.get("custom_context_length")
    model.architecture = info.get("architecture")
    model.block_count = info.get("block_count")
    model.attention_heads = info.get("attention_heads")
    model.format = info.get("format")
    model.parent_model = info.get("parent_model")
    model.family = info.get("family")
    model.parameter_size = info.get("parameter_size")
    model.quantization = info.get("quantization")
    model.parameter_count = info.get("parameter_count")
    model.file_type = info.get("file_type")
    model.quantization_version = info.get("quantization_version")
    model.basename = info.get("basename")
    model.size_label = info.get("size_label")
    model.license = info.get("license")
    model.finetune = info.get("finetune")
    model.embedding_dimension = info.get("embedding_dimension")

    api_caps = info.get("capabilities", [])
    if api_caps:
        model.capabilities = list(set(model.capabilities + api_caps))

    if info.get("parameters"):
        if model.parameters:
            model.parameters.update(info["parameters"])
        else:
            model.parameters = info["parameters"]
