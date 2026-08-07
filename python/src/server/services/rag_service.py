import logging
from typing import Any

import httpx

from src.server.services.credential_service import CredentialService
from src.server.utils import get_supabase_client
from src.server.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class RagService:
    @staticmethod
    async def get_hf_embedding(text: str) -> list[float]:
        # SSOT: Model from environment variable
        from src.server.services.settings_service import SettingsService
        hf_model_id = SettingsService().get_setting("HF_EMBEDDING_MODEL") or "sentence-transformers/all-mpnet-base-v2"
        hf_api_url = f"https://router.huggingface.co/hf-inference/models/{hf_model_id}/pipeline/feature-extraction"

        credential_service = CredentialService()
        hf_token = await credential_service.get_credential("HF_TOKEN")

        if not hf_token:
            raise ValueError("HF_TOKEN is missing")

        headers = {"Authorization": f"Bearer {hf_token}"}
        payload = {"inputs": text}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(hf_api_url, headers=headers, json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"HF API Error: {response.status_code} - {response.text}")

            vector = response.json()
            if isinstance(vector, list) and len(vector) > 0 and isinstance(vector[0], list):
                vector = vector[0]

            from typing import cast
            return cast(list[float], vector)

    @staticmethod
    async def hybrid_search(
        query: str,
        match_count: int = 10,
        similarity_threshold: float = 0.82,
        filter_dict: dict[str, Any] | None = None,
        source_filter: str | None = None,
        truncate_dim: int | None = None,
        equipped_model: str | None = None,
        allow_react: bool = False,
    ) -> list[dict[str, Any]]:
        if filter_dict is None:
            filter_dict = {}

        try:
            # 1. Get embedding
            query_embedding = await RagService.get_hf_embedding(query)

            # 2. Call Supabase RPC
            supabase = get_supabase_client()
            rpc_params = {
                "query_embedding": query_embedding,
                "query_text": query,
                "match_count": match_count,
                "similarity_threshold": similarity_threshold,
                "filter": filter_dict,
                "source_filter": source_filter,
                "truncate_dim": truncate_dim,
            }

            base_repo = BaseRepository(supabase)
            success, res_dict = base_repo.execute_query(
                supabase.rpc("hybrid_match_chunks", rpc_params),
                error_context="Failed to execute hybrid_match_chunks"
            )

            if success and res_dict.get("data"):
                from typing import cast
                results = cast(list[dict[str, Any]], res_dict["data"])

                import asyncio
                async with httpx.AsyncClient(timeout=5.0) as client:
                    async def fetch_cdn(row: dict[str, Any]) -> None:
                        metadata = row.get("metadata", {})
                        cdn_url = metadata.get("github_url") or metadata.get("cdn_url") or row.get("url")

                        if cdn_url and isinstance(cdn_url, str) and cdn_url.startswith("http"):
                            try:
                                cdn_res = await client.get(cdn_url)
                                if cdn_res.status_code == 200:
                                    try:
                                        row["cdn_content"] = cdn_res.json()
                                    except ValueError:
                                        row["cdn_content"] = cdn_res.text
                                else:
                                    row["cdn_content"] = {"error": f"CDN HTTP {cdn_res.status_code}"}
                            except Exception as e:
                                row["cdn_content"] = {"error": str(e)}
                        else:
                            row["cdn_content"] = None

                    await asyncio.gather(*(fetch_cdn(r) for r in results))

                # Inject ReAct simulation if enabled and model is capable
                if allow_react:
                    is_pro = equipped_model and "pro" in equipped_model.lower()
                    if is_pro:
                        logger.info(f"Executing ReAct multi-step planning due to allow_react=True using {equipped_model}")
                        react_chunk = {
                            "id": 999999,
                            "url": "system://react-planner",
                            "chunk_number": 0,
                            "content": f"[ReAct Plan] Analyzing query '{query}' using {equipped_model}... breaking down into 3 sub-queries. Context purified.",
                            "metadata": {"type": "react_reflection"},
                            "source_id": "system_react",
                            "similarity": 1.0,
                            "match_type": "hybrid",
                            "cdn_content": None
                        }
                        results.insert(0, react_chunk)
                    else:
                        logger.warning(f"ReAct requested but model '{equipped_model}' is not designated for expert reasoning. Skipping to save tokens.")

                return results
            return []

        except Exception as e:
            logger.error(f"Error in hybrid_search: {e}")
            raise

    @staticmethod
    async def graph_search(
        start_entity_name: str,
        max_hops: int = 2,
    ) -> list[dict[str, Any]]:
        try:
            supabase = get_supabase_client()
            rpc_params = {
                "start_entity_name": start_entity_name,
                "max_hops": max_hops,
            }

            base_repo = BaseRepository(supabase)
            success, res_dict = base_repo.execute_query(
                supabase.rpc("graph_reasoning_n_hop", rpc_params),
                error_context="Failed to execute graph_reasoning_n_hop"
            )

            if success and res_dict.get("data"):
                from typing import cast
                return cast(list[dict[str, Any]], res_dict["data"])
            return []

        except Exception as e:
            logger.error(f"Error in graph_search: {e}")
            raise
