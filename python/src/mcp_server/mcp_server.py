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
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from mcp.server.fastmcp import FastMCP

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import Core Infrastructure (Phase 4.6.20 Slimming)
from src.mcp_server.core import (
    get_tool_schema,
    lifespan,
)
from src.mcp_server.router import register_custom_routes
from src.server.config.logfire_config import setup_logfire

# Load environment variables from the project root .env file by searching upwards
load_dotenv(find_dotenv(), override=True)

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

# Load instructions from external markdown file (Phase 5.4.1 Slimming)
instructions_path = Path(__file__).parent / "mcp_instructions.md"
MCP_INSTRUCTIONS = ""
try:
    if instructions_path.exists():
        MCP_INSTRUCTIONS = instructions_path.read_text(encoding="utf-8")
        logger.info("✓ Loaded MCP instructions from mcp_instructions.md")
    else:
        logger.warning(f"⚠️ Instructions file not found at {instructions_path}")
except Exception as e:
    logger.error(f"Failed to load MCP instructions: {e}")


# Initialize the main FastMCP server with physical instruction alignment
try:
    logger.info("🏗️ MCP SERVER INITIALIZATION:")
    logger.info("   Server Name: archon-mcp-server")

    mcp = FastMCP(
        "archon-mcp-server",
        instructions=MCP_INSTRUCTIONS,  # Correct way to pass instructions
        lifespan=lifespan,
        host=server_host,
        port=server_port,
    )
    logger.info("✓ FastMCP server instance created successfully")

except Exception as e:
    logger.error(f"✗ Failed to create FastMCP server: {e}")
    logger.error(traceback.format_exc())
    raise

# Register custom routing (Discovery, RPC Bridge, Sessions)
register_custom_routes(mcp)


# Import and register modules
def register_modules():
    """Register all MCP tool modules."""
    logger.info("🔧 Registering MCP tool modules...")
    modules_registered = 0

    try:
        from src.mcp_server.features.infra_tools import register_infra_tools

        register_infra_tools(mcp)
        modules_registered += 1
        logger.info("✓ Infrastructure tools registered")
    except Exception as e:
        logger.error(f"✗ Failed to register infra tools: {e}")

    try:
        from src.mcp_server.features.rag import register_rag_tools

        register_rag_tools(mcp)
        modules_registered += 1
        logger.info("✓ RAG module registered (HTTP-based)")
    except Exception as e:
        logger.error(f"✗ Error registering RAG module: {e}")

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

    try:
        from src.mcp_server.features.feature_tools import register_feature_tools

        register_feature_tools(mcp)
        modules_registered += 1
        logger.info("✓ Feature tools registered")
    except Exception as e:
        logger.error(f"✗ Failed to register feature tools: {e}")

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
        formatted = [
            {
                "type": "function",
                "function": {"name": t.name, "description": t.description or "", "parameters": get_tool_schema(t)},
            }
            for t in tools
        ]
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
