import json
import logging
from datetime import datetime

from pydantic_ai import RunContext

from src.agents.mcp_client import get_mcp_client

# Assuming RagDependencies will be imported by the agent that uses these tools.
# We will define it in rag_agent.py and import it here for type hinting.
from src.agents.rag_agent import RagDependencies

logger = logging.getLogger(__name__)


async def search_documents_tool(ctx: RunContext[RagDependencies], query: str, source_filter: str | None = None) -> str:
    """Search through documents using RAG query."""
    try:
        # Use source filter from context if not provided
        if source_filter is None:
            source_filter = ctx.deps.source_filter

        # Use MCP client to perform RAG query
        mcp_client = await get_mcp_client(agent_type="rag")
        result_json = await mcp_client.rag_search_knowledge_base(  # type: ignore
            query=query, source_id=source_filter, match_count=ctx.deps.match_count
        )

        # Parse the JSON response
        result = json.loads(result_json)

        if not result.get("success", False):
            return f"Search failed: {result.get('error', 'Unknown error')}"

        results = result.get("results", [])
        if not results:
            return "No results found for your query. Try using different search terms or removing filters."

        # Format results for display and capture citations
        formatted_results = []
        for i, res in enumerate(results, 1):
            similarity = res.get("similarity_score", res.get("similarity", 0))
            metadata = res.get("metadata", {})
            source = metadata.get("source", "Unknown")
            url = metadata.get("url", res.get("url", ""))
            content = res.get("content", "")

            # Capture physical citation
            ctx.deps.collected_citations.append(
                {
                    "index": i,
                    "source": source,
                    "url": url,
                    "similarity": similarity,
                    "snippet": content[:200] + "..." if len(content) > 200 else content,
                }
            )

            # Truncate content for LLM if too long
            llm_content = content[:500] + "..." if len(content) > 500 else content

            formatted_results.append(
                f"**Result {i}** (Relevance: {similarity:.2%})\nSource: {source}\nURL: {url}\nContent: {llm_content}\n"
            )

        return f"Found {len(results)} relevant results:\n\n" + "\n---\n".join(formatted_results)

    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return f"Error performing search: {str(e)}"


async def list_available_sources_tool(ctx: RunContext[RagDependencies]) -> str:
    """List all available sources that can be searched."""
    try:
        # Use MCP client to get available sources
        mcp_client = await get_mcp_client(agent_type="rag")
        result_json = await mcp_client.get_available_sources()

        # Parse the JSON response
        result = json.loads(result_json)

        if not result.get("success", False):
            return f"Failed to get sources: {result.get('error', 'Unknown error')}"

        sources = result.get("sources", [])
        if not sources:
            return "No sources are currently available. You may need to crawl some documentation first."

        source_list = []
        for source in sources:
            source_id = source.get("source_id", "Unknown")
            title = source.get("title", "Untitled")
            description = source.get("description", "")
            created = source.get("created_at", "")

            # Format the description if available
            desc_text = f" - {description}" if description else ""

            source_list.append(f"- **{source_id}**: {title}{desc_text} (added {created[:10]})")

        return f"Available sources ({len(sources)} total):\n" + "\n".join(source_list)

    except Exception as e:
        logger.error(f"Error listing sources: {e}")
        return f"Error retrieving sources: {str(e)}"


async def search_code_examples_tool(
    ctx: RunContext[RagDependencies], query: str, source_filter: str | None = None
) -> str:
    """Search for code examples related to the query."""
    try:
        # Use source filter from context if not provided
        if source_filter is None:
            source_filter = ctx.deps.source_filter

        # Use MCP client to search code examples
        mcp_client = await get_mcp_client(agent_type="rag")
        result_json = await mcp_client.call_tool(
            "rag_search_code_examples", query=query, source_id=source_filter, match_count=ctx.deps.match_count
        )

        # Parse the JSON response
        result = json.loads(result_json)

        if not result.get("success", False):
            return f"Code search failed: {result.get('error', 'Unknown error')}"

        examples = result.get("results", result.get("code_examples", []))
        if not examples:
            return "No code examples found for your query."

        formatted_examples = []
        for i, example in enumerate(examples, 1):
            similarity = example.get("similarity", 0)
            summary = example.get("summary", "No summary")
            code = example.get("code", example.get("code_block", ""))
            url = example.get("url", "")

            # Extract language from code block if available
            lang = "code"
            if code.startswith("```"):
                first_line = code.split("\n")[0]
                if len(first_line) > 3:
                    lang = first_line[3:].strip()

            formatted_examples.append(
                f"**Example {i}** (Relevance: {similarity:.2%})\n"
                f"Summary: {summary}\n"
                f"Source: {url}\n"
                f"```{lang}\n{code}\n```"
            )

        return f"Found {len(examples)} code examples:\n\n" + "\n---\n".join(formatted_examples)

    except Exception as e:
        logger.error(f"Error searching code examples: {e}")
        return f"Error searching code: {str(e)}"


async def refine_search_query_tool(ctx: RunContext[RagDependencies], original_query: str, context: str) -> str:
    """Refine a search query based on context to get better results."""
    try:
        # Simple query expansion based on context
        refined_parts = [original_query]

        # Add contextual keywords
        if "how" in original_query.lower():
            refined_parts.append("tutorial guide example")
        elif "what" in original_query.lower():
            refined_parts.append("definition explanation overview")
        elif "error" in original_query.lower() or "issue" in original_query.lower():
            refined_parts.append("troubleshooting solution fix")
        elif "api" in original_query.lower():
            refined_parts.append("endpoint method parameters response")

        # Add project-specific context if available
        if ctx.deps.project_id:
            refined_parts.append(f"project:{ctx.deps.project_id}")

        refined_query = " ".join(refined_parts)
        return f"Refined query: '{refined_query}' (original: '{original_query}')"

    except Exception as e:
        return f"Could not refine query: {str(e)}"


async def add_search_context_prompt(ctx: RunContext[RagDependencies]) -> str:
    source_info = f"Source Filter: {ctx.deps.source_filter}" if ctx.deps.source_filter else "No source filter"
    return f"""
**Current Search Context:**
- Project ID: {ctx.deps.project_id or "Global search"}
- {source_info}
- Max Results: {ctx.deps.match_count}
- Timestamp: {datetime.now().isoformat()}
"""
