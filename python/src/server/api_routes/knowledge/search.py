"""
Knowledge Search API Hardened - Secure RAG and keyword search.
Enforces authentication for all knowledge retrieval operations.
"""

from fastapi import APIRouter, Depends, HTTPException

from src.server.api_routes.knowledge.schemas import RagQueryRequest
from src.server.config.logfire_config import safe_logfire_error
from src.server.services.search.rag_service import RAGService
from src.server.utils import get_supabase_client

from ...auth.dependencies import get_current_user

router = APIRouter()

@router.post("/knowledge-items/search")
async def search_knowledge_items(request: RagQueryRequest, current_user: dict = Depends(get_current_user)):
    """Search for relevant knowledge items using vector similarity."""
    try:
        service = RAGService(get_supabase_client())
        metadata_filter = {"source_id": request.source_ids[0]} if request.source_ids else None
        return await service.search_documents(
            query=request.query,
            match_count=request.limit,
            filter_metadata=metadata_filter
        )
    except Exception as e:
        safe_logfire_error(f"Failed to search knowledge items | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/rag/query")
async def perform_rag_query(request: RagQueryRequest, current_user: dict = Depends(get_current_user)):
    """Perform a full RAG query combining retrieval and generation."""
    try:
        service = RAGService(get_supabase_client())
        success, result = await service.perform_rag_query(
            query=request.query,
            source=request.source_ids[0] if request.source_ids else None,
            match_count=request.limit
        )
        if success:
            return {**result, "success": True}
        raise HTTPException(status_code=500, detail=str(result.get("error")))
    except Exception as e:
        safe_logfire_error(f"Failed to perform RAG query | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/rag/code-examples")
async def search_code_examples(request: RagQueryRequest, current_user: dict = Depends(get_current_user)):
    """Search specifically for code examples within the knowledge base."""
    try:
        service = RAGService(get_supabase_client())
        success, result = await service.search_code_examples_service(
            query=request.query,
            source_id=request.source_ids[0] if request.source_ids else None,
            match_count=request.limit
        )
        if success:
            return result
        raise HTTPException(status_code=500, detail=str(result.get("error")))
    except Exception as e:
        safe_logfire_error(f"Failed to search code examples | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/code-examples")
async def search_code_examples_simple(request: RagQueryRequest, current_user: dict = Depends(get_current_user)):
    """Backward compatible alias for searching code examples. Calls Service directly to avoid recursion."""
    service = RAGService(get_supabase_client())
    success, result = await service.search_code_examples_service(
        query=request.query,
        source_id=request.source_ids[0] if request.source_ids else None,
        match_count=request.limit
    )
    if success:
        return result
    raise HTTPException(status_code=500, detail=str(result.get("error")))
