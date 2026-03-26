"""
MCP Server for Archon (Microservices Version)

This is the MCP server that uses HTTP calls to other services
instead of importing heavy dependencies directly. This significantly reduces
the container size from 1.66GB to ~150MB.

Modules:
- RAG Module: RAG queries, search, and source management via HTTP
- Project Module: Task and project management via HTTP
- Health & Session: Local operations

Note: Crawling and document upload operations are handled directly by the
API service and frontend, not through MCP tools.
"""

import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import Core Infrastructure (Phase 4.6.20 Slimming)
from server.config.logfire_config import setup_logfire
from src.mcp_server.core import (
    GLOBAL_TOOL_REGISTRY,
    get_tool_schema,
    lifespan,
)

# Load environment variables from the project root .env file
project_root = Path(__file__).resolve().parent.parent
dotenv_path = project_root / ".env"
load_dotenv(dotenv_path, override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

server_host = "0.0.0.0"
mcp_port = os.getenv("ARCHON_MCP_PORT", "8051")
server_port = int(mcp_port)

# Initialize the main FastMCP server
try:
    logger.info("🏗️ MCP SERVER INITIALIZATION:")
    logger.info("   Server Name: archon-mcp-server")

    mcp = FastMCP(
        "archon-mcp-server",
        description="MCP server for Archon - uses HTTP calls to other services",
        instructions="", # Defined below
        lifespan=lifespan,
        host=server_host,
        port=server_port,
    )
    logger.info("✓ FastMCP server instance created successfully")

except Exception as e:
    logger.error(f"✗ Failed to create FastMCP server: {e}")
    logger.error(traceback.format_exc())
    raise


# Define MCP instructions for Claude Code and other clients
MCP_INSTRUCTIONS = """
# Archon MCP Server Instructions

## 🚨 CRITICAL RULES (ALWAYS FOLLOW)
1. **Task Management**: ALWAYS use Archon MCP tools for task management.
   - Combine with your local TODO tools for granular tracking

2. **Research First**: Before implementing, use rag_search_knowledge_base and rag_search_code_examples
3. **Task-Driven Development**: Never code without checking current tasks first

## 🎯 Targeted Documentation Search

When searching specific documentation (very common!):
1. **Get available sources**: `rag_get_available_sources()` - Returns list with id, title, url
2. **Find source ID**: Match user's request to source title (e.g., "PydanticAI docs" -> find ID)
3. **Filter search**: `rag_search_knowledge_base(query="...", source_id="src_xxx", match_count=5)`

Examples:
- User: "Search the Supabase docs for vector functions"
  1. Call `rag_get_available_sources()`
  2. Find Supabase source ID from results (e.g., "src_abc123")
  3. Call `rag_search_knowledge_base(query="vector functions", source_id="src_abc123")`

- User: "Find authentication examples in the MCP documentation"
  1. Call `rag_get_available_sources()`
  2. Find MCP docs source ID
  3. Call `rag_search_code_examples(query="authentication", source_id="src_def456")`

IMPORTANT: Always use source_id (not URLs or domain names) for filtering!

## 📋 Core Workflow

### Task Management Cycle
1. **Get current task**: `list_tasks(task_id="...")`
2. **Search/List tasks**: `list_tasks(query="auth", filter_by="status", filter_value="todo")`
3. **Mark as doing**: `manage_task("update", task_id="...", status="doing")`
4. **Research phase**:
   - `rag_search_knowledge_base(query="...", match_count=5)`
   - `rag_search_code_examples(query="...", match_count=3)`
5. **Implementation**: Code based on research findings
6. **Mark for review**: `manage_task("update", task_id="...", status="review")`
7. **Get next task**: `list_tasks(filter_by="status", filter_value="todo")`

### Consolidated Task Tools (Optimized ~2 tools from 5)
- `list_tasks(query=None, task_id=None, filter_by=None, filter_value=None, per_page=10)`
  - list + search + get in one tool
  - Search with keyword query parameter (optional)
  - task_id parameter for getting single task (full details)
  - Filter by status, project, or assignee
  - **Optimized**: Returns truncated descriptions and array counts (lists only)
  - **Default**: 10 items per page (was 50)
- `manage_task(action, task_id=None, project_id=None, ...)`
  - **Consolidated**: create + update + delete in one tool
  - action: "create" | "update" | "delete"
  - Examples:
    - `manage_task("create", project_id="p-1", title="Fix auth")`
    - `manage_task("update", task_id="t-1", status="doing")`
    - `manage_task("delete", task_id="t-1")`

## 🏗️ Project Management

### Project Tools
- `list_projects(project_id=None, query=None, page=1, per_page=10)`
  - List all projects, search by query, or get specific project by ID
- `manage_project(action, project_id=None, title=None, description=None, github_repo=None)`
  - Actions: "create", "update", "delete"

### Document Tools
- `list_documents(project_id, document_id=None, query=None, document_type=None, page=1, per_page=10)`
  - List project documents, search, filter by type, or get specific document
- `manage_document(action, project_id, document_id=None, title=None, document_type=None, content=None, ...)`
  - Actions: "create", "update", "delete"

## 🔍 Research Patterns

### CRITICAL: Keep Queries Short and Focused!
Vector search works best with 2-5 keywords, NOT long sentences or keyword dumps.

✅ GOOD Queries (concise, focused):
- `rag_search_knowledge_base(query="vector search pgvector")`
- `rag_search_code_examples(query="React useState")`
- `rag_search_knowledge_base(query="authentication JWT")`
- `rag_search_code_examples(query="FastAPI middleware")`

❌ BAD Queries (too long, unfocused):
- `rag_search_knowledge_base(query="how to implement vector search with pgvector in PostgreSQL for semantic similarity matching with OpenAI embeddings")`
- `rag_search_code_examples(query="React hooks useState useEffect useContext useReducer useMemo useCallback")`

### Query Construction Tips:
- Extract 2-5 most important keywords from the user's request
- Focus on technical terms and specific technologies
- Omit filler words like "how to", "implement", "create", "example"
- For multi-concept searches, do multiple focused queries instead of one broad query

## 📊 Task Status Flow
`todo` → `doing` → `review` → `done`
- Only ONE task in 'doing' status at a time
- Use 'review' for completed work awaiting validation
- Mark tasks 'done' only after verification

## 📝 Task Granularity Guidelines

### Project Scope Determines Task Granularity

**For Feature-Specific Projects** (project = single feature):
Create granular implementation tasks:
- "Set up development environment"
- "Install required dependencies"
- "Create database schema"
- "Implement API endpoints"
- "Add frontend components"
- "Write unit tests"
- "Add integration tests"
- "Update documentation"

**For Codebase-Wide Projects** (project = entire application):
Create feature-level tasks:
- "Implement user authentication feature"
- "Add payment processing system"
- "Create admin dashboard"
"""
mcp.instructions = MCP_INSTRUCTIONS


# Discovery endpoint for Agents (Phase 4.6.19)
@mcp.tool()
async def list_tools() -> str:
    """Dynamically list all registered MCP tools using official FastMCP API."""
    try:
        tools = await mcp.list_tools()
        formatted_tools = []
        for tool in tools:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": get_tool_schema(tool)
                }
            })

        return json.dumps({
            "success": True,
            "tools": formatted_tools,
            "count": len(formatted_tools),
            "timestamp": datetime.now().isoformat()
        }, indent=2)
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# Direct RPC Bridge for Agents (Phase 4.6.19)
# This enables standard HTTP POST calls to tools, avoiding 406 Not Acceptable.
@mcp.custom_route("/rpc", methods=["POST"])
async def mcp_rpc_handler(request: Request) -> Response:
    """Handle standard JSON-RPC requests via POST."""
    global GLOBAL_TOOL_REGISTRY
    try:
        body = await request.json()
        method_name = body.get("method")
        params = body.get("params", {})

        # 1. Discovery handling (Fast path using Worker-local Registry)
        if method_name == "list_tools":
            # FAIL-SAFE A: Try disk cache first (most reliable across processes)
            tools_cache = "/tmp/mcp_tools.json"
            if os.path.exists(tools_cache):
                try:
                    with open(tools_cache) as f:
                        cached = json.load(f)
                        if cached:
                            logger.info(f"✅ [PID {os.getpid()}] Discovery: Serving {len(cached)} tools from disk cache")
                            return JSONResponse({"jsonrpc": "2.0", "result": cached, "id": body.get("id")})
                except Exception:
                    pass

            # FAIL-SAFE B: If registry is empty, try live fetch in this process
            if not GLOBAL_TOOL_REGISTRY:
                logger.warning(f"⚠️ [PID {os.getpid()}] Registry empty, triggering fail-safe live fetch")
                raw_tools = mcp._tool_manager.list_tools()
                GLOBAL_TOOL_REGISTRY = [{
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description or "",
                        "parameters": get_tool_schema(t)
                    }
                } for t in raw_tools]

            return JSONResponse({"jsonrpc": "2.0", "result": GLOBAL_TOOL_REGISTRY, "id": body.get("id")})

        # 2. Tool execution via official API (Handles ctx injection automatically)
        logger.info(f"RPC Call: [PID {os.getpid()}] Executing tool '{method_name}' via official call_tool API")
        try:
            raw_result = await mcp.call_tool(method_name, params)
        except Exception as tool_err:
            return JSONResponse({"error": {"code": -32603, "message": f"Tool execution failed: {str(tool_err)}"}}, status_code=500)

        # 3. Physical Serialization & Unwrapping
        processed_result: Any = []
        if isinstance(raw_result, list):
            for item in raw_result:
                if hasattr(item, "model_dump"):
                    dump = item.model_dump()
                    # Unwrap TextContent for standard JSON-RPC clients
                    processed_result.append(dump.get("text", "") if dump.get("type") == "text" else dump)
                else:
                    processed_result.append(str(item))
        else:
            processed_result = str(raw_result)

        return JSONResponse({"jsonrpc": "2.0", "result": processed_result, "id": body.get("id")})
    except Exception as e:
        logger.error(f"RPC Bridge Failed: {e}", exc_info=True)
        return JSONResponse({"error": {"code": -32603, "message": str(e)}}, status_code=500)


# Import and register modules
def register_modules():
    """Register all MCP tool modules."""
    logger.info("🔧 Registering MCP tool modules...")
    modules_registered = 0

    # Infrastructure & Monitoring (Phase 4.6.20 Slimming)
    try:
        from src.mcp_server.features.infra_tools import register_infra_tools
        register_infra_tools(mcp)
        modules_registered += 1
        logger.info("✓ Infrastructure tools registered")
    except Exception as e:
        logger.error(f"✗ Failed to register infra tools: {e}")

    # RAG
    try:
        from src.mcp_server.features.rag import register_rag_tools
        register_rag_tools(mcp)
        modules_registered += 1
        logger.info("✓ RAG module registered (HTTP-based)")
    except Exception as e:
        logger.error(f"✗ Error registering RAG module: {e}")

    # Projects & Tasks
    try:
        from src.mcp_server.features.projects import register_project_tools
        register_project_tools(mcp)
        modules_registered += 1
        logger.info("✓ Project tools registered")
    except Exception as e:
        logger.error(f"✗ Failed to register project tools: {e}")

    try:
        from src.mcp_server.features.tasks import register_task_tools
        register_task_tools(mcp)
        modules_registered += 1
        logger.info("✓ Task tools registered")
    except Exception as e:
        logger.error(f"✗ Failed to register task tools: {e}")

    # Feature Management
    try:
        from src.mcp_server.features.feature_tools import register_feature_tools
        register_feature_tools(mcp)
        modules_registered += 1
        logger.info("✓ Feature tools registered")
    except Exception as e:
        logger.error(f"✗ Failed to register feature tools: {e}")

    # Developer, Marketing, Design
    try:
        from src.mcp_server.features.developer import register_developer_tools
        register_developer_tools(mcp)
        modules_registered += 1
        logger.info("✓ Developer tools registered")
    except Exception as e:
        logger.error(f"✗ Failed to register developer tools: {e}")

    try:
        from src.mcp_server.features.marketing import register_marketing_tools
        register_marketing_tools(mcp)
        modules_registered += 1
        logger.info("✓ Marketing tools registered")
    except Exception as e:
        logger.error(f"✗ Failed to register marketing tools: {e}")

    try:
        from src.mcp_server.features.design import register_design_tools
        register_design_tools(mcp)
        modules_registered += 1
        logger.info("✓ Design tools registered")
    except Exception as e:
        logger.error(f"✗ Failed to register design tools: {e}")

    # Document Management
    try:
        from src.mcp_server.features.documents import register_document_tools
        register_document_tools(mcp)
        modules_registered += 1
        logger.info("✓ Document tools registered")
    except Exception as e:
        logger.error(f"✗ Failed to register document tools: {e}")

    try:
        from src.mcp_server.features.documents import register_version_tools
        register_version_tools(mcp)
        modules_registered += 1
        logger.info("✓ Version tools registered")
    except Exception as e:
        logger.error(f"✗ Failed to register version tools: {e}")

    logger.info(f"📦 Total modules registered: {modules_registered}")
    if modules_registered == 0:
        raise RuntimeError("No MCP modules available")

    # PHYSICAL PERSISTENCE (Phase 4.6.19)
    try:
        tools = mcp._tool_manager.list_tools()
        formatted = [{"type": "function", "function": {"name": t.name, "description": t.description or "", "parameters": get_tool_schema(t)}} for t in tools]
        with open("/tmp/mcp_tools.json", "w") as f:
            json.dump(formatted, f)
        logger.info(f"✅ PHYSICAL TOOLS PERSISTED: {len(formatted)} tools saved to /tmp/mcp_tools.json")
    except Exception as e:
        logger.error(f"Failed to persist physical tools: {e}")


# Register all modules
try:
    register_modules()
except Exception as e:
    logger.error(f"💥 Critical error during module registration: {e}")
    raise


def main():
    """Main entry point for the MCP server."""
    try:
        setup_logfire(service_name="archon-mcp-server")
        logger.info("🚀 Starting Archon MCP Server")
        logger.info(f"   URL: http://{server_host}:{server_port}/mcp")
        mcp.run(transport="streamable-http")
    except Exception as e:
        logger.error(f"💥 Fatal error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
