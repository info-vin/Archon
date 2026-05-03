"""
Capability Tester for Ollama Discovery Service.
Contains logic for actively testing model capabilities via API requests.
"""

from typing import Any

import httpx

from src.server.services.llm_provider_service import get_llm_client


async def get_model_details_logic(model_name: str, instance_url: str) -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10)) as client:
            base_url = instance_url.rstrip("/").replace("/v1", "")
            show_url = f"{base_url}/api/show"
            res = await client.post(show_url, json={"name": model_name})
            if res.status_code == 200:
                data = res.json()
                model_info = data.get("model_info", {})
                details_section = data.get("details", {})
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
                            if any(x in k for x in ["block_count", "num_layers", ".n_layer"])
                        ),
                        None,
                    ),
                    "attention_heads": next(
                        (v for k, v in model_info.items() if ".attention.head_count" in k or ".n_head" in k), None
                    ),
                }
                return details
    except Exception:
        pass
    return None


async def test_embedding_capability_logic(model_name: str, instance_url: str) -> int | None:
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10)) as client:
            res = await client.post(
                f"{instance_url.rstrip('/')}/api/embeddings", json={"model": model_name, "prompt": "test"}
            )
            if res.status_code == 200:
                emb = res.json().get("embedding", [])
                if emb:
                    return len(emb)
    except Exception:
        pass
    return None


async def test_chat_capability_logic(model_name: str, instance_url: str) -> bool:
    try:
        async with get_llm_client(provider="ollama") as client:
            client.base_url = f"{instance_url.rstrip('/')}/v1"
            res = await client.chat.completions.create(
                model=model_name, messages=[{"role": "user", "content": "Hi"}], max_tokens=1, timeout=10
            )
            return bool(res.choices)
    except Exception:
        return False


async def test_function_calling_capability_logic(model_name: str, instance_url: str) -> bool:
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
            return hasattr(res.choices[0].message, "tool_calls") and bool(res.choices[0].message.tool_calls)
    except Exception:
        return False


async def test_structured_output_capability_logic(model_name: str, instance_url: str) -> bool:
    try:
        async with get_llm_client(provider="ollama") as client:
            client.base_url = f"{instance_url.rstrip('/')}/v1"
            res = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": 'JSON ok? {"a":1}'}],
                max_tokens=20,
                timeout=8,
                temperature=0,
            )
            return "{" in (res.choices[0].message.content or "")
    except Exception:
        return False


async def test_embedding_capability_fast_logic(model_name: str, instance_url: str) -> int | None:
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5)) as client:
            res = await client.post(
                f"{instance_url.rstrip('/')}/api/embeddings", json={"model": model_name, "prompt": "t"}
            )
            if res.status_code == 200:
                emb = res.json().get("embedding", [])
                if emb:
                    return len(emb)
    except Exception:
        pass
    return None


async def test_chat_capability_fast_logic(model_name: str, instance_url: str) -> bool:
    try:
        async with get_llm_client(provider="ollama") as client:
            client.base_url = f"{instance_url.rstrip('/')}/v1"
            res = await client.chat.completions.create(
                model=model_name, messages=[{"role": "user", "content": "H"}], max_tokens=1, timeout=5
            )
            return bool(res.choices)
    except Exception:
        return False


async def test_structured_output_capability_fast_logic(model_name: str, instance_url: str) -> bool:
    try:
        async with get_llm_client(provider="ollama") as client:
            client.base_url = f"{instance_url.rstrip('/')}/v1"
            res = await client.chat.completions.create(
                model=model_name, messages=[{"role": "user", "content": "JSON: {}"}], max_tokens=5, timeout=5
            )
            return "{" in (res.choices[0].message.content or "")
    except Exception:
        return False
