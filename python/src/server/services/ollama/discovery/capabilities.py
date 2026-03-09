"""
Capability Detection Engine for Ollama Discovery Service (Phase 4.6.12 Hardening)

Handles model capability testing (chat, embedding, structured output),
metadata enrichment via /api/show, and pattern matching.
"""

import time
from typing import Any, cast

import httpx

from src.server.config.logfire_config import get_logger
from src.server.services.llm_provider_service import get_llm_client

from .models import ModelCapabilities, OllamaModel

logger = get_logger(__name__)


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

        # 1. Pattern Matching Logic
        embedding_patterns = [
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
        ]
        is_embedding_model = any(
            pattern in model_name_lower for pattern in embedding_patterns
        )

        if is_embedding_model:
            model.capabilities = ["embedding"]
            if "nomic" in model_name_lower:
                model.embedding_dimensions = 768
            elif "bge" in model_name_lower:
                model.embedding_dimensions = (
                    1024 if "large" in model_name_lower else 768
                )
            elif "e5" in model_name_lower:
                model.embedding_dimensions = (
                    1024 if "large" in model_name_lower else 768
                )
            elif "arctic" in model_name_lower:
                model.embedding_dimensions = 1024
            else:
                model.embedding_dimensions = 768
            logger.debug(f"Pattern-matched embedding model {model.name}")
            enriched_models.append(model)
        else:
            chat_patterns = [
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
            ]
            if any(pattern in model_name_lower for pattern in chat_patterns):
                model.capabilities = ["chat"]
                if any(
                    p in model_name_lower for p in ["qwen", "llama3", "phi3", "mistral"]
                ):
                    model.capabilities.extend(["function_calling", "structured_output"])
                elif any(p in model_name_lower for p in ["llama", "phi", "gemma"]):
                    model.capabilities.append("structured_output")

                if fetch_details:
                    try:
                        detailed_info = await get_model_details_logic(
                            model.name, instance_url
                        )
                        if detailed_info:
                            _map_details_to_model(model, detailed_info)
                    except Exception as e:
                        logger.debug(f"Could not get details for {model.name}: {e}")
                enriched_models.append(model)
            else:
                unknown_models.append(model)

    # Fast assignment for unknown models (Performance Mode)
    if unknown_models:
        for model in unknown_models:
            model.capabilities = ["chat"]
            model_name_lower = model.name.lower()
            if any(h in model_name_lower for h in ["embed", "embedding", "vector"]):
                model.capabilities = ["embedding"]
                model.embedding_dimensions = 768
            enriched_models.append(model)

    logger.info(
        f"Model enrichment complete for {instance_url} in {time.time() - start_time:.2f}s"
    )
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


async def detect_model_capabilities_logic(
    service_instance, model_name: str, instance_url: str, optimized: bool = False
) -> ModelCapabilities:
    """Detect capabilities by testing model endpoints with caching."""
    cache_key = f"{model_name}@{instance_url}"
    if cache_key in service_instance.capability_cache:
        return cast(ModelCapabilities, service_instance.capability_cache[cache_key])

    caps = ModelCapabilities()
    try:
        if optimized:
            # Fast heuristic path
            if any(p in model_name.lower() for p in ["embed", "embedding"]):
                dims = await test_embedding_capability_fast_logic(
                    model_name, instance_url
                )
                if dims:
                    caps.supports_embedding = True
                    caps.embedding_dimensions = dims
                    service_instance.capability_cache[cache_key] = caps
                    return caps

            if await test_chat_capability_fast_logic(model_name, instance_url):
                caps.supports_chat = True
                if await test_structured_output_capability_fast_logic(
                    model_name, instance_url
                ):
                    caps.supports_structured_output = True
        else:
            # Comprehensive path
            dims = await test_embedding_capability_logic(model_name, instance_url)
            if dims:
                caps.supports_embedding = True
                caps.embedding_dimensions = dims

            if await test_chat_capability_logic(model_name, instance_url):
                caps.supports_chat = True
                if await test_function_calling_capability_logic(
                    model_name, instance_url
                ):
                    caps.supports_function_calling = True
                if await test_structured_output_capability_logic(
                    model_name, instance_url
                ):
                    caps.supports_structured_output = True

        info = await get_model_details_logic(model_name, instance_url)
        if info:
            caps.parameter_count = info.get("parameter_count")
            caps.model_family = info.get("family")
            caps.quantization = info.get("quantization")

        service_instance.capability_cache[cache_key] = caps
    except Exception as e:
        logger.warning(f"Capability detection failed for {model_name}: {e}")
        caps.supports_chat = True  # Default fallback

    return caps


async def get_model_details_logic(
    model_name: str, instance_url: str
) -> dict[str, Any] | None:
    """Internal helper to get details from Ollama."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10)) as client:
            base_url = instance_url.rstrip("/").replace("/v1", "")
            show_url = f"{base_url}/api/show"
            res = await client.post(show_url, json={"name": model_name})
            if res.status_code == 200:
                data = res.json()
                details_section = data.get("details", {})
                model_info = data.get("model_info", {})

                # Context logic
                num_ctx = None
                params_raw = data.get("parameters", "")
                if params_raw:
                    for line in params_raw.split("\n"):
                        if line.strip().startswith("num_ctx"):
                            try:
                                num_ctx = int(line.split()[-1])
                            except Exception:
                                pass

                max_ctx = None
                base_ctx = None
                embed_dim = None
                for k, v in model_info.items():
                    if k.endswith(".context_length"):
                        max_ctx = v
                    elif k.endswith(".rope.scaling.original_context_length"):
                        base_ctx = v
                    elif k.endswith(".embedding_length"):
                        embed_dim = v

                current_ctx = num_ctx or base_ctx or max_ctx

                details = {
                    "family": details_section.get("family"),
                    "parameter_size": details_section.get("parameter_size"),
                    "quantization": details_section.get("quantization_level"),
                    "format": details_section.get("format"),
                    "parent_model": details_section.get("parent_model"),
                    "parameters": {
                        "family": details_section.get("family"),
                        "parameter_size": details_section.get("parameter_size"),
                        "quantization": details_section.get("quantization_level"),
                        "format": details_section.get("format"),
                    },
                    "context_window": current_ctx,
                    "max_context_length": max_ctx,
                    "base_context_length": base_ctx,
                    "custom_context_length": num_ctx,
                    "architecture": model_info.get("general.architecture"),
                    "embedding_dimension": embed_dim,
                    "parameter_count": model_info.get("general.parameter_count"),
                    "capabilities": data.get("capabilities", []),
                    "block_count": next(
                        (
                            v
                            for k, v in model_info.items()
                            if any(
                                x in k
                                for x in ["block_count", "num_layers", ".n_layer"]
                            )
                        ),
                        None,
                    ),
                    "attention_heads": next(
                        (
                            v
                            for k, v in model_info.items()
                            if ".attention.head_count" in k or ".n_head" in k
                        ),
                        None,
                    ),
                }
                return details
    except Exception:
        pass
    return None


async def test_embedding_capability_logic(
    model_name: str, instance_url: str
) -> int | None:
    """Internal helper to test embedding capability."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10)) as client:
            res = await client.post(
                f"{instance_url.rstrip('/')}/api/embeddings",
                json={"model": model_name, "prompt": "test"},
            )
            if res.status_code == 200:
                emb = res.json().get("embedding", [])
                if emb:
                    return len(emb)
    except Exception:
        pass
    return None


async def test_chat_capability_logic(model_name: str, instance_url: str) -> bool:
    """Internal helper to test chat capability."""
    try:
        async with get_llm_client(provider="ollama") as client:
            client.base_url = f"{instance_url.rstrip('/')}/v1"
            res = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
                timeout=10,
            )
            return bool(res.choices)
    except Exception:
        return False


async def test_function_calling_capability_logic(
    model_name: str, instance_url: str
) -> bool:
    """Internal helper to test function calling."""
    try:
        async with get_llm_client(provider="ollama") as client:
            client.base_url = f"{instance_url.rstrip('/')}/v1"
            res = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Time?"}],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "get_time",
                            "description": "time",
                            "parameters": {"type": "object", "properties": {}},
                        },
                    }
                ],
                max_tokens=10,
                timeout=8,
            )
            return hasattr(res.choices[0].message, "tool_calls") and bool(
                res.choices[0].message.tool_calls
            )
    except Exception:
        return False


async def test_structured_output_capability_logic(
    model_name: str, instance_url: str
) -> bool:
    """Internal helper to test structured output."""
    try:
        async with get_llm_client(provider="ollama") as client:
            client.base_url = f"{instance_url.rstrip('/')}/v1"
            res = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "JSON ok? {\"a\":1}"}],
                max_tokens=20,
                timeout=8,
                temperature=0,
            )
            return "{" in (res.choices[0].message.content or "")
    except Exception:
        return False


async def test_embedding_capability_fast_logic(
    model_name: str, instance_url: str
) -> int | None:
    """Fast version of embedding test."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5)) as client:
            res = await client.post(
                f"{instance_url.rstrip('/')}/api/embeddings",
                json={"model": model_name, "prompt": "t"},
            )
            if res.status_code == 200:
                emb = res.json().get("embedding", [])
                if emb:
                    return len(emb)
    except Exception:
        pass
    return None


async def test_chat_capability_fast_logic(model_name: str, instance_url: str) -> bool:
    """Fast version of chat test."""
    try:
        async with get_llm_client(provider="ollama") as client:
            client.base_url = f"{instance_url.rstrip('/')}/v1"
            res = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "H"}],
                max_tokens=1,
                timeout=5,
            )
            return bool(res.choices)
    except Exception:
        return False


async def test_structured_output_capability_fast_logic(
    model_name: str, instance_url: str
) -> bool:
    """Fast version of structured output test."""
    try:
        async with get_llm_client(provider="ollama") as client:
            client.base_url = f"{instance_url.rstrip('/')}/v1"
            res = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "JSON: {}"}],
                max_tokens=5,
                timeout=5,
            )
            return "{" in (res.choices[0].message.content or "")
    except Exception:
        return False
