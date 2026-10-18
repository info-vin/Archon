import pytest

from src.server.services.ollama.discovery.capability_patterns import (
    _map_details_to_model,
    enrich_model_capabilities_logic,
)
from src.server.services.ollama.discovery.manifest_parser import OllamaManifestParser
from src.server.services.ollama.discovery.models import (
    OllamaModel,
    OllamaModelDetailsDTO,
)


def test_parse_tags_response():
    data = {
        "models": [
            {
                "name": "llama3:latest",
                "size": 4000000000,
                "digest": "abc12345",
                "details": {
                    "family": "llama",
                    "parameter_size": "8B",
                    "quantization_level": "Q4_0",
                },
            },
            {
                "name": "nomic-embed-text:latest",
                "size": 270000000,
                "digest": "def67890",
            },
        ]
    }
    instance_url = "http://localhost:11434"
    models = OllamaManifestParser.parse_tags_response(data, instance_url)

    assert len(models) == 2
    assert models[0].name == "llama3:latest"
    assert models[0].parameters == {
        "family": "llama",
        "parameter_size": "8B",
        "quantization": "Q4_0",
    }
    assert models[1].name == "nomic-embed-text:latest"


@pytest.mark.asyncio
async def test_enrich_model_capabilities_logic():
    models = [
        OllamaModel(
            name="nomic-embed-text:latest",
            tag="nomic-embed-text:latest",
            size=270000000,
            digest="def67890",
            capabilities=[],
        ),
        OllamaModel(
            name="llama3:latest",
            tag="llama3:latest",
            size=4000000000,
            digest="abc12345",
            capabilities=[],
        ),
    ]

    enriched = await enrich_model_capabilities_logic(
        service_instance=None,
        models=models,
        instance_url="http://localhost:11434",
        fetch_details=False,
    )

    assert len(enriched) == 2
    assert "embedding" in enriched[0].capabilities
    assert enriched[0].embedding_dimensions == 768

    assert "chat" in enriched[1].capabilities
    assert "function_calling" in enriched[1].capabilities


def test_map_details_to_model():
    model = OllamaModel(
        name="llama3:latest",
        tag="llama3:latest",
        size=4000000000,
        digest="abc12345",
        capabilities=["chat"],
    )

    details: OllamaModelDetailsDTO = {
        "context_window": 8192,
        "max_context_length": 8192,
        "architecture": "llama",
        "parameter_count": 8000000000,
        "family": "llama",
        "capabilities": ["tools"],
    }

    _map_details_to_model(model, details)

    assert model.context_window == 8192
    assert model.architecture == "llama"
    assert model.parameter_count == 8000000000
    assert "tools" in model.capabilities


def test_aggregate_discovery_results():
    m1 = OllamaModel(
        name="llama3:latest",
        tag="llama3:latest",
        size=4000000000,
        digest="abc12345",
        capabilities=["chat"],
        instance_url="http://localhost:11434",
    )

    m2 = OllamaModel(
        name="nomic-embed-text:latest",
        tag="nomic-embed-text:latest",
        size=270000000,
        digest="def67890",
        capabilities=["embedding"],
        embedding_dimensions=768,
        instance_url="http://localhost:11434",
    )

    urls = ["http://localhost:11434"]
    results = [[m1, m2]]

    res = OllamaManifestParser.aggregate_discovery_results(urls, results)

    assert res["total_models"] == 2
    assert len(res["chat_models"]) == 1
    assert len(res["embedding_models"]) == 1
    assert res["host_status"]["http://localhost:11434"]["status"] == "online"
    assert "llama3:latest" in res["unique_model_names"]
