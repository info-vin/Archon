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
import threading
import time
import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Import Logfire configuration
from server.config.logfire_config import mcp_logger, setup_logfire
from server.services.mcp_service_client import get_mcp_service_client
from server.services.mcp_session_manager import get_session_manager

# Load environment variables from the project root .env file
project_root = Path(__file__).resolve().parent.parent
dotenv_path = project_root / ".env"
load_dotenv(dotenv_path, override=True)

# Configure logging FIRST before any imports that might use it
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/tmp/mcp_server.log", mode="a")
        if os.path.exists("/tmp")
        else logging.NullHandler(),
    ],
)
logger = logging.getLogger(__name__)

def get_tool_schema(tool: Any) -> dict:
    """Safely extract tool schema regardless of FastMCP version."""
    if hasattr(tool, "inputSchema"):
        return tool.inputSchema
    if hasattr(tool, "parameters"):
        return tool.parameters
    if hasattr(tool, "model_dump"):
        return tool.model_dump().get("inputSchema", {})
    return {}

# Global initialization lock and flag
_initialization_lock = threading.Lock()
_initialization_complete = False
_shared_context = None

server_host = "0.0.0.0"  # Listen on all interfaces

# Require ARCHON_MCP_PORT to be set
mcp_port = os.getenv("ARCHON_MCP_PORT")
if not mcp_port:
    raise ValueError(
        "ARCHON_MCP_PORT environment variable is required. "
        "Please set it in your .env file or environment. "
        "Default value: 8051"
    )
server_port = int(mcp_port)


@dataclass
class ArchonContext:
    """
    Context for MCP server.
    No heavy dependencies - just service client for HTTP calls.
    """

    service_client: Any
    health_status: dict | None = None
    startup_time: float | None = None

    def __post_init__(self):
        if self.health_status is None:
            self.health_status = {
                "status": "healthy",
                "api_service": False,
                "agents_service": False,
                "last_health_check": None,
            }
        if self.startup_time is None:
            self.startup_time = time.time()


async def perform_health_checks(context: ArchonContext):
    """Perform health checks on dependent services via HTTP."""
    try:
        # Check dependent services
        service_health = await context.service_client.health_check()

        if context.health_status is not None:
            context.health_status["api_service"] = service_health.get("api_service", False)
            context.health_status["agents_service"] = service_health.get("agents_service", False)

            # Overall status
            all_critical_ready = context.health_status["api_service"]

            context.health_status["status"] = "healthy" if all_critical_ready else "degraded"
            context.health_status["last_health_check"] = datetime.now().isoformat()

            if not all_critical_ready:
                logger.warning(f"Health check failed: {context.health_status}")
            else:
                logger.info("Health check passed - dependent services healthy")

    except Exception as e:
        logger.error(f"Health check error: {e}")
        if context.health_status is not None:
            context.health_status["status"] = "unhealthy"
            context.health_status["last_health_check"] = datetime.now().isoformat()


# GLOBAL REGISTRY FOR AGENTS (Phase 4.6.19)
GLOBAL_TOOL_REGISTRY = []

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[ArchonContext]:
    """
    Lifecycle manager - ensures tools are registered in the correct process.
    """
    global _initialization_complete, _shared_context, GLOBAL_TOOL_REGISTRY

    # Quick check without lock
    if _initialization_complete and _shared_context:
        logger.info(f"♻️ [PID {os.getpid()}] Reusing existing context")
        yield _shared_context
        return

    # Acquire lock for initialization
    with _initialization_lock:
        if _initialization_complete and _shared_context:
            yield _shared_context
            return

        logger.info(f"🚀 [PID {os.getpid()}] Starting MCP server...")

        try:
            get_session_manager()
            service_client = get_mcp_service_client()
            context = ArchonContext(service_client=service_client)
            await perform_health_checks(context)

            # --- PHYSICAL REGISTRY POPULATION (Phase 4.6.19) ---
            raw_tools = mcp._tool_manager.list_tools()
            GLOBAL_TOOL_REGISTRY = [{
                "type": "function",
                "function": {
                    "name": t.name, 
                    "description": t.description or "", 
                    "parameters": get_tool_schema(t)
                }
            } for t in raw_tools]
            logger.info(f"✅ [PID {os.getpid()}] PHYSICAL REGISTRY FINALIZED: {len(GLOBAL_TOOL_REGISTRY)} tools")


            _shared_context = context
            _initialization_complete = True
            yield context

        except Exception as e:
            logger.error(f"💥 Critical error in lifespan setup: {e}")
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

# Initialize the main FastMCP server with fixed configuration
try:
    logger.info("🏗️ MCP SERVER INITIALIZATION:")
    logger.info("   Server Name: archon-mcp-server")
    logger.info("   Description: MCP server using HTTP calls")

    mcp = FastMCP(
        "archon-mcp-server",
        description="MCP server for Archon - uses HTTP calls to other services",
        instructions=MCP_INSTRUCTIONS,
        lifespan=lifespan,
        host=server_host,
        port=server_port,
    )
    logger.info("✓ FastMCP server instance created successfully")

except Exception as e:
    logger.error(f"✗ Failed to create FastMCP server: {e}")
    logger.error(traceback.format_exc())
    raise


# Discovery endpoint for Agents (Phase 4.6.19)
@mcp.tool()
async def list_tools() -> str:
    """Dynamically list all registered MCP tools using official FastMCP API."""
    try:
        # Physical Discovery: Use the official async API (v1.12.2)
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
                except Exception: pass

            # FAIL-SAFE B: If registry is empty, try live fetch in this process
            if not GLOBAL_TOOL_REGISTRY:
                logger.warning(f"⚠️ [PID {os.getpid()}] Registry empty, triggering fail-safe live fetch")
                raw_tools = mcp._tool_manager.list_tools()
                GLOBAL_TOOL_REGISTRY = [{
                    "type": "function",
                    "function": {"name": t.name, "description": t.description or "", "parameters": get_tool_schema(t)}
                } for t in raw_tools]
            
            return JSONResponse({"jsonrpc": "2.0", "result": GLOBAL_TOOL_REGISTRY, "id": body.get("id")})

        # 2. Tool execution via official API (Handles ctx injection automatically)
        logger.info(f"RPC Call: [PID {os.getpid()}] Executing tool '{method_name}' via official call_tool API")
        try:
            raw_result = await mcp.call_tool(method_name, params)
        except Exception as tool_err:
            return JSONResponse({"error": {"code": -32603, "message": f"Tool execution failed: {str(tool_err)}"}}, status_code=500)

        # 3. Physical Serialization & Unwrapping
        processed_result = []
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


# Custom route for session tracking
@mcp.custom_route("/sessions", methods=["GET"])
async def get_sessions(request: Request) -> Response:
    """Get active session count from FastMCP internal state."""
    active_sessions = 0
    try:
        # Access FastMCP internal session manager state if available
        # The session manager is lazy-loaded, but since we are handling a request,
        # it should be initialized.
        if hasattr(mcp, "session_manager"):
            # Access the internal _server_instances dict which tracks active connections
            # Note: This is accessing internal state, but it's the only way to get real counts
            if hasattr(mcp.session_manager, "_server_instances"):
                active_sessions = len(mcp.session_manager._server_instances)
    except Exception as e:
        logger.error(f"Failed to get active sessions: {e}")

    return JSONResponse({"active_sessions": active_sessions})


# Health check endpoint
@mcp.tool()
async def health_check(ctx: Context) -> str:
    """
    Check health status of MCP server and dependencies.

    Returns:
        JSON with health status, uptime, and service availability
    """
    try:
        # Try to get the lifespan context
        context = getattr(ctx.request_context, "lifespan_context", None)

        if context is None:
            # Server starting up
            return json.dumps({
                "success": True,
                "status": "starting",
                "message": "MCP server is initializing...",
                "timestamp": datetime.now().isoformat(),
            })

        # Server is ready - perform health checks
        if hasattr(context, "health_status") and context.health_status:
            await perform_health_checks(context)

            return json.dumps({
                "success": True,
                "health": context.health_status,
                "uptime_seconds": time.time() - context.startup_time,
                "timestamp": datetime.now().isoformat(),
            })
        else:
            return json.dumps({
                "success": True,
                "status": "ready",
                "message": "MCP server is running",
                "timestamp": datetime.now().isoformat(),
            })

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return json.dumps({
            "success": False,
            "error": f"Health check failed: {str(e)}",
            "timestamp": datetime.now().isoformat(),
        })


# Session management endpoint
@mcp.tool()
async def session_info(ctx: Context) -> str:
    """
    Get current and active session information.

    Returns:
        JSON with active sessions count and server uptime
    """
    try:
        session_manager = get_session_manager()

        # Build session info
        session_info_data = {
            "active_sessions": session_manager.get_active_session_count(),
            "session_timeout": session_manager.timeout,
        }

        # Add server uptime
        context = getattr(ctx.request_context, "lifespan_context", None)
        if context and hasattr(context, "startup_time"):
            session_info_data["server_uptime_seconds"] = time.time() - context.startup_time

        return json.dumps({
            "success": True,
            "session_management": session_info_data,
            "timestamp": datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Session info failed: {e}")
        return json.dumps({
            "success": False,
            "error": f"Failed to get session info: {str(e)}",
            "timestamp": datetime.now().isoformat(),
        })


# Import and register modules
def register_modules():
    """Register all MCP tool modules."""
    logger.info("🔧 Registering MCP tool modules...")

    modules_registered = 0

    # Import and register RAG module (HTTP-based version)
    try:
        from src.mcp_server.features.rag import register_rag_tools

        register_rag_tools(mcp)
        modules_registered += 1
        logger.info("✓ RAG module registered (HTTP-based)")
    except ImportError as e:
        logger.warning(f"⚠ RAG module not available: {e}")
    except Exception as e:
        logger.error(f"✗ Error registering RAG module: {e}")
        logger.error(traceback.format_exc())

    # Import and register all feature tools - separated and focused

    # Project Management Tools
    try:
        from src.mcp_server.features.projects import register_project_tools

        register_project_tools(mcp)
        modules_registered += 1
        logger.info("✓ Project tools registered")
    except ImportError as e:
        # Module not found - this is acceptable in modular architecture
        logger.warning(f"⚠ Project tools module not available (optional): {e}")
    except (SyntaxError, NameError, AttributeError) as e:
        # Code errors that should not be ignored
        logger.error(f"✗ Code error in project tools - MUST FIX: {e}")
        logger.error(traceback.format_exc())
        raise  # Re-raise to prevent running with broken code
    except Exception as e:
        # Unexpected errors during registration
        logger.error(f"✗ Failed to register project tools: {e}")
        logger.error(traceback.format_exc())
        # Don't raise - allow other modules to register

    # Task Management Tools
    try:
        from src.mcp_server.features.tasks import register_task_tools

        register_task_tools(mcp)
        modules_registered += 1
        logger.info("✓ Task tools registered")
    except ImportError as e:
        logger.warning(f"⚠ Task tools module not available (optional): {e}")
    except (SyntaxError, NameError, AttributeError) as e:
        logger.error(f"✗ Code error in task tools - MUST FIX: {e}")
        logger.error(traceback.format_exc())
        raise
    except Exception as e:
        logger.error(f"✗ Failed to register task tools: {e}")
        logger.error(traceback.format_exc())

    # Document Management Tools
    try:
        from src.mcp_server.features.documents import register_document_tools

        register_document_tools(mcp)
        modules_registered += 1
        logger.info("✓ Document tools registered")
    except ImportError as e:
        logger.warning(f"⚠ Document tools module not available (optional): {e}")
    except (SyntaxError, NameError, AttributeError) as e:
        logger.error(f"✗ Code error in document tools - MUST FIX: {e}")
        logger.error(traceback.format_exc())
        raise
    except Exception as e:
        logger.error(f"✗ Failed to register document tools: {e}")
        logger.error(traceback.format_exc())

    # Version Management Tools
    try:
        from src.mcp_server.features.documents import register_version_tools

        register_version_tools(mcp)
        modules_registered += 1
        logger.info("✓ Version tools registered")
    except ImportError as e:
        logger.warning(f"⚠ Version tools module not available (optional): {e}")
    except (SyntaxError, NameError, AttributeError) as e:
        logger.error(f"✗ Code error in version tools - MUST FIX: {e}")
        logger.error(traceback.format_exc())
        raise
    except Exception as e:
        logger.error(f"✗ Failed to register version tools: {e}")
        logger.error(traceback.format_exc())

    # Feature Management Tools
    try:
        from src.mcp_server.features.feature_tools import register_feature_tools

        register_feature_tools(mcp)
        modules_registered += 1
        logger.info("✓ Feature tools registered")
    except ImportError as e:
        logger.warning(f"⚠ Feature tools module not available (optional): {e}")
    except (SyntaxError, NameError, AttributeError) as e:
        logger.error(f"✗ Code error in feature tools - MUST FIX: {e}")
        logger.error(traceback.format_exc())
        raise
    except Exception as e:
        logger.error(f"✗ Failed to register feature tools: {e}")
        logger.error(traceback.format_exc())

    # Developer Tools (Smart Git, File Ops, etc.)
    try:
        from src.mcp_server.features.developer import register_developer_tools

        register_developer_tools(mcp)
        modules_registered += 1
        logger.info("✓ Developer tools registered")
    except ImportError as e:
        logger.warning(f"⚠ Developer tools module not available (optional): {e}")
    except (SyntaxError, NameError, AttributeError) as e:
        logger.error(f"✗ Code error in developer tools - MUST FIX: {e}")
        logger.error(traceback.format_exc())
        raise
    except Exception as e:
        logger.error(f"✗ Failed to register developer tools: {e}")
        logger.error(traceback.format_exc())

    # Marketing Tools (Job Search, etc.)
    try:
        from src.mcp_server.features.marketing import register_marketing_tools

        register_marketing_tools(mcp)
        modules_registered += 1
        logger.info("✓ Marketing tools registered")
    except ImportError as e:
        logger.warning(f"⚠ Marketing tools module not available (optional): {e}")
    except (SyntaxError, NameError, AttributeError) as e:
        logger.error(f"✗ Code error in marketing tools - MUST FIX: {e}")
        logger.error(traceback.format_exc())
        raise
    except Exception as e:
        logger.error(f"✗ Failed to register marketing tools: {e}")
        logger.error(traceback.format_exc())

    # Design Tools (Logo Generation, etc.)
    try:
        from src.mcp_server.features.design import register_design_tools

        register_design_tools(mcp)
        modules_registered += 1
        logger.info("✓ Design tools registered")
    except ImportError as e:
        logger.warning(f"⚠ Design tools module not available (optional): {e}")
    except (SyntaxError, NameError, AttributeError) as e:
        logger.error(f"✗ Code error in design tools - MUST FIX: {e}")
        logger.error(traceback.format_exc())
        raise
    except Exception as e:
        logger.error(f"✗ Failed to register design tools: {e}")
        logger.error(traceback.format_exc())

    logger.info(f"📦 Total modules registered: {modules_registered}")

    if modules_registered == 0:
        logger.error("💥 No modules were successfully registered!")
        raise RuntimeError("No MCP modules available")

    # PHYSICAL PERSISTENCE (Phase 4.6.19)
    # Save tools to disk to survive process isolation/lazy loading
    try:
        # Use sync access here since we are in the module level init
        tools = mcp._tool_manager.list_tools()
        formatted = [{
            "type": "function",
            "function": {"name": t.name, "description": t.description or "", "parameters": get_tool_schema(t)}
        } for t in tools]
        
        with open("/tmp/mcp_tools.json", "w") as f:
            json.dump(formatted, f)
        logger.info(f"✅ PHYSICAL TOOLS PERSISTED: {len(formatted)} tools saved to /tmp/mcp_tools.json")
    except Exception as e:
        logger.error(f"Failed to persist physical tools: {e}")


# Register all modules when this file is imported
try:
    register_modules()
except Exception as e:
    logger.error(f"💥 Critical error during module registration: {e}")
    logger.error(traceback.format_exc())
    raise


def main():
    """Main entry point for the MCP server."""
    try:
        # Initialize Logfire first
        setup_logfire(service_name="archon-mcp-server")

        logger.info("🚀 Starting Archon MCP Server")
        logger.info("   Mode: Streamable HTTP")
        logger.info(f"   URL: http://{server_host}:{server_port}/mcp")

        mcp_logger.info("🔥 Logfire initialized for MCP server")
        mcp_logger.info(f"🌟 Starting MCP server - host={server_host}, port={server_port}")

        mcp.run(transport="streamable-http")

    except Exception as e:
        mcp_logger.error(f"💥 Fatal error in main - error={str(e)}, error_type={type(e).__name__}")
        logger.error(f"💥 Fatal error in main: {e}")
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 MCP server stopped by user")
    except Exception as e:
        logger.error(f"💥 Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
