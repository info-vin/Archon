import logging
import os
from typing import Any

import httpx

from src.server.services.credential_service import CredentialService
from src.server.utils import get_supabase_client

logger = logging.getLogger(__name__)


class RagService:
    @staticmethod
    async def get_hf_embedding(text: str) -> list[float]:
        # SSOT: Model from environment variable
        hf_model_id = os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")
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
            }

            res = supabase.rpc("hybrid_match_chunks", rpc_params).execute()

            if hasattr(res, "data") and res.data:
                from typing import cast
                results = cast(list[dict[str, Any]], res.data)

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

                return results
            return []

        except Exception as e:
            logger.error(f"Error in hybrid_search: {e}")
            raise
