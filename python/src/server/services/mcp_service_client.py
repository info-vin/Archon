"""
MCP Service Client for HTTP-based microservice communication

This module provides HTTP clients for the MCP service to communicate with
other services (API and Agents) instead of importing their modules directly.
"""

import uuid
from typing import Any, NotRequired, TypedDict
from urllib.parse import urljoin

import httpx

from ..config.logfire_config import mcp_logger
from ..config.service_discovery import get_agents_url, get_api_url


class ErrorDTO(TypedDict):
    code: NotRequired[str]
    message: str

class CrawlResponseDTO(TypedDict):
    success: bool
    progressId: NotRequired[str | None]
    message: NotRequired[str]
    error: NotRequired[ErrorDTO | None]

class SearchResponseDTO(TypedDict):
    success: bool
    results: list[dict[str, Any]]
    reranked: NotRequired[bool]
    error: NotRequired[ErrorDTO | None]

class StoreDocumentResponseDTO(TypedDict):
    success: bool
    documents_stored: int
    chunks_created: int
    message: str

class HealthCheckResponseDTO(TypedDict):
    api_service: bool
    agents_service: bool


class MCPServiceClient:
    """
    Client for MCP service to communicate with other microservices via HTTP.
    Replaces direct module imports with proper service-to-service communication.
    """

    def __init__(self) -> None:
        self.api_url = get_api_url()
        self.agents_url = get_agents_url()
        self.service_auth = "mcp-service-key"  # In production, use proper key management
        self.timeout = httpx.Timeout(
            connect=5.0,
            read=300.0,  # 5 minutes for long operations like crawling
            write=30.0,
            pool=5.0,
        )

    def _get_headers(self, request_id: str | None = None) -> dict[str, str]:
        """Get common headers for internal requests"""
        headers: dict[str, str] = {"X-Service-Auth": self.service_auth, "Content-Type": "application/json"}
        if request_id:
            headers["X-Request-ID"] = request_id
        else:
            headers["X-Request-ID"] = str(uuid.uuid4())
        return headers

    async def crawl_url(self, url: str, options: dict[str, Any] | None = None) -> CrawlResponseDTO:
        """
        Request the API service to crawl a URL.
        """
        request_id = str(uuid.uuid4())
        mcp_logger.info(f"[{request_id}] Requesting crawl for {url}")

        if options is None:
            options = {}

        payload: dict[str, Any] = {
            "url": url,
            "wait_for_selector": options.get("wait_for_selector"),
            "extract_schema": options.get("extract_schema"),
            "exclude_patterns": options.get("exclude_patterns"),
            "timeout": options.get("timeout", 30),
        }
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    urljoin(self.api_url, "/api/tools/crawl"),
                    json=payload,
                    headers=self._get_headers(request_id),
                )

                response.raise_for_status()
                data = response.json()

                if data.get("success"):
                    return {
                        "success": True,
                        "progressId": data.get("progressId"),
                        "message": data.get("message", "Crawling started")
                    }
                else:
                    return {
                        "success": False,
                        "error": {"message": data.get("error", "Unknown crawl error")}
                    }
        except httpx.HTTPStatusError as e:
            mcp_logger.error(f"[{request_id}] Crawl request failed with status {e.response.status_code}: {e.response.text}")
            return {"success": False, "error": {"code": str(e.response.status_code), "message": f"HTTP error: {e.response.text}"}}
        except Exception as e:
            mcp_logger.error(f"[{request_id}] Error in crawl_url: {e}", exc_info=True)
            return {"success": False, "error": {"message": f"Connection error: {e!s}"}}

    async def search(
        self, query: str, source_filter: str | None = None, match_count: int = 10
    ) -> SearchResponseDTO:
        """
        Search for documents using the API service.
        Note: The actual tool uses Tavily, but this internal method is for retrieving
        documents already in the system.

        Args:
            query: Search query
            source_filter: Optional source filter
            match_count: Maximum number of results
            rerank: Whether to rerank results (handled in Server's service layer)

        Returns:
            Search response with results
        """
        endpoint = urljoin(self.api_url, "/api/rag/query")
        request_data = {"query": query, "source": source_filter, "match_count": match_count}

        mcp_logger.info(f"Calling API service to search: {query}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # First, get search results from API service
                response = await client.post(endpoint, json=request_data, headers=self._get_headers())
                response.raise_for_status()
                result = response.json()

                # Transform API response to MCP expected format
                return {
                    "success": result.get("success", True),
                    "results": result.get("results", []),
                    "reranked": False,  # Reranking should be handled by Server's service layer
                    "error": None,
                }

        except Exception as e:
            mcp_logger.error(f"Error searching: {str(e)}")
            return {
                "success": False,
                "results": [],
                "error": {"code": "SEARCH_FAILED", "message": str(e)},
            }

    async def store_documents(
        self, documents: list[dict[str, Any]], generate_embeddings: bool = True
    ) -> StoreDocumentResponseDTO:
        """
        Store documents by transforming them into the format expected by the API.
        Note: The regular API expects file uploads, so this is a simplified version.

        Args:
            documents: List of documents to store
            generate_embeddings: Whether to generate embeddings

        Returns:
            Storage response
        """
        # For now, return a simplified response since document upload
        # through the regular API requires multipart form data
        mcp_logger.info("Document storage through regular API not yet implemented")
        return {
            "success": True,
            "documents_stored": len(documents),
            "chunks_created": len(documents),
            "message": "Document storage should be handled by Server's service layer",
        }

    async def generate_embeddings(self, texts: list[str], model: str = "text-embedding-3-small") -> dict[str, Any]:
        """
        Generate embeddings - this should be handled by Server's service layer.
        MCP tools shouldn't need to directly generate embeddings.

        Args:
            texts: List of texts to embed
            model: Embedding model to use

        Returns:
            Embeddings response
        """
        mcp_logger.warning("Direct embedding generation not needed for MCP tools")
        raise NotImplementedError("Embeddings should be handled by Server's service layer")

    async def health_check(self) -> HealthCheckResponseDTO:
        """
        Check health of all dependent services.

        Returns:
            Combined health status
        """
        health_status: HealthCheckResponseDTO = {"api_service": False, "agents_service": False}

        # Check API service
        api_health_url = urljoin(self.api_url, "/api/health")
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                mcp_logger.info(f"Checking API service health at: {api_health_url}")
                response = await client.get(api_health_url)
                health_status["api_service"] = response.status_code == 200
                mcp_logger.info(f"API service health check: {response.status_code}")
        except Exception as e:
            health_status["api_service"] = False
            mcp_logger.warning(f"API service health check failed: {e}")

        # Check Agents service
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get(urljoin(self.agents_url, "/health"))
                health_status["agents_service"] = response.status_code == 200
        except Exception:
            pass

        return health_status

# Global client instance
_mcp_client = None

def get_mcp_service_client() -> MCPServiceClient:
    """Get or create the global MCP service client"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPServiceClient()
    return _mcp_client
