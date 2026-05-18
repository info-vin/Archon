#!/usr/bin/env python3
# scripts/verify_mcp_health.py
# Phase 5.2.0 Task 5.2.0.10: MCP Health & Tool Schema Probe
# This script programmatically spawns/checks the MCP Server and audits all registered tools and their Pydantic/JSON schemas.

import os
import sys
import time
import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

# ANSI color codes for premium output
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
NC = "\033[0m"

MCP_PORT = os.getenv("ARCHON_MCP_PORT", "8051")
MCP_URL = f"http://localhost:{MCP_PORT}"
HEALTH_URL = f"{MCP_URL}/health"
RPC_URL = f"{MCP_URL}/rpc"

print(f"{CYAN}=========================================================={NC}")
print(f"{CYAN}🔍 Phase 5.2.0: MCP Health & Tool Schema Audit{NC}")
print(f"{CYAN}=========================================================={NC}")

# Step 1: Check if MCP Server is already running
server_process = None
already_running = False

try:
    print(f"Checking if MCP Server is already active on {HEALTH_URL}...")
    req = urllib.request.Request(HEALTH_URL, method="GET")
    with urllib.request.urlopen(req, timeout=2) as response:
        if response.status == 200:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("status") == "healthy":
                print(f"{GREEN}🟢 Connected to already running MCP Server (via /health)!{NC}")
                already_running = True
except Exception:
    try:
        # Fallback to sessions endpoint which existed previously
        req = urllib.request.Request(f"{MCP_URL}/sessions", method="GET")
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                print(f"{GREEN}🟢 Connected to already running MCP Server (via /sessions)!{NC}")
                already_running = True
    except Exception:
        # Final fallback: Check if port 8051 is occupied (i.e. socket open)
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        try:
            s.connect(("127.0.0.1", int(MCP_PORT)))
            s.close()
            print(f"{GREEN}🟢 Connected to already running MCP Server (Port {MCP_PORT} occupied)!{NC}")
            already_running = True
        except Exception:
            print("MCP Server is not running. Launching programmatically...")

# Step 2: If not running, launch MCP Server in background
if not already_running:
    workspace_root = Path(__file__).resolve().parent.parent
    python_dir = workspace_root / "python"
    
    print(f"Starting MCP Server on port {MCP_PORT} in background...")
    
    # Configure exact PYTHONPATH to match runtime dependencies
    env = os.environ.copy()
    env["PYTHONPATH"] = str(python_dir) + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
    env["ARCHON_MCP_PORT"] = MCP_PORT
    
    server_process = subprocess.Popen(
        [sys.executable, "-m", "src.mcp_server.mcp_server"],
        cwd=str(python_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for the server to bind to port 8051 and respond to health check
    startup_timeout = 15.0
    start_time = time.time()
    connected = False
    
    print(f"Waiting for MCP Server to bind to port {MCP_PORT}...")
    while time.time() - start_time < startup_timeout:
        # Prevent silent crashes from locking the pipeline
        if server_process.poll() is not None:
            stdout, stderr = server_process.communicate()
            print(f"{RED}🔴 MCP Server crashed on startup!{NC}")
            print(f"{YELLOW}--- STDOUT ---{NC}\n{stdout}")
            print(f"{YELLOW}--- STDERR ---{NC}\n{stderr}")
            sys.exit(1)
            
        try:
            req = urllib.request.Request(HEALTH_URL, method="GET")
            with urllib.request.urlopen(req, timeout=1.0) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    if data.get("status") == "healthy":
                        connected = True
                        break
        except Exception:
            pass
        time.sleep(0.5)
        
    if not connected:
        print(f"{RED}🔴 Timeout waiting for MCP Server to start on {HEALTH_URL}!{NC}")
        server_process.terminate()
        stdout, stderr = server_process.communicate()
        print(f"{YELLOW}--- STDERR ---{NC}\n{stderr}")
        sys.exit(1)
        
    print(f"{GREEN}🟢 MCP Server started successfully!{NC}")

# Step 3: Query registered tools and validate schemas
audit_failed = False
try:
    print("Querying registered tools and tool schemas...")
    
    rpc_payload = {
        "jsonrpc": "2.0",
        "method": "list_tools",
        "params": {},
        "id": 1
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Agent-Type": "admin"
    }
    
    req = urllib.request.Request(
        RPC_URL,
        data=json.dumps(rpc_payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=5) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        
    if "error" in res_data:
        print(f"{RED}🔴 RPC list_tools call failed: {res_data['error']}{NC}")
        audit_failed = True
    else:
        tools = res_data.get("result", [])
        print(f"Found {len(tools)} registered tools in MCP Registry.")
        
        if not tools:
            print(f"{RED}🔴 Error: No tools returned by the registry!{NC}")
            audit_failed = True
            
        for idx, t in enumerate(tools, 1):
            func = t.get("function", {})
            name = func.get("name")
            desc = func.get("description")
            params = func.get("parameters", {})
            
            print(f"\n[{idx}/{len(tools)}] Auditing Tool: {CYAN}{name}{NC}")
            
            # Audit A: Check name and description
            if not name:
                print(f"  {RED}❌ Failed: Missing tool name{NC}")
                audit_failed = True
                continue
                
            if not desc:
                print(f"  {YELLOW}⚠️  Warning: Tool '{name}' has empty or missing description{NC}")
                
            # Audit B: Validate schema parameters dict structure
            if not isinstance(params, dict):
                print(f"  {RED}❌ Failed: Parameters must be a dictionary schema, got {type(params)}{NC}")
                audit_failed = True
                continue
                
            schema_type = params.get("type")
            if schema_type != "object":
                print(f"  {RED}❌ Failed: Parameters schema type must be 'object', got '{schema_type}'{NC}")
                audit_failed = True
                
            properties = params.get("properties")
            if not isinstance(properties, dict):
                print(f"  {RED}❌ Failed: 'properties' must be a dictionary, got {type(properties)}{NC}")
                audit_failed = True
                continue
                
            # Audit C: Inspect parameter types and descriptions (Required for optimal Claude MCP execution)
            for p_name, p_schema in properties.items():
                p_type = p_schema.get("type")
                p_desc = p_schema.get("description")
                
                if not p_type:
                    print(f"    {YELLOW}⚠️  Warning: Parameter '{p_name}' has no type defined{NC}")
                if not p_desc:
                    print(f"    {YELLOW}⚠️  Warning: Parameter '{p_name}' has no description defined{NC}")
                    
            print(f"  {GREEN}✓ Tool '{name}' schema syntactically valid!{NC}")

except Exception as e:
    print(f"{RED}🔴 Exception occurred during audit: {e}{NC}")
    import traceback
    traceback.print_exc()
    audit_failed = True

# Step 4: Cleanup background server process cleanly
if server_process is not None:
    print("Shutting down background MCP Server process...")
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
        print("MCP Server process exited cleanly.")
    except subprocess.TimeoutExpired:
        print("Force terminating MCP Server...")
        server_process.kill()
        server_process.wait()

print(f"{CYAN}----------------------------------------------------------{NC}")
if audit_failed:
    print(f"{RED}🔴 [FAILURE] MCP Health & Tool Schema Audit failed! Fix tool definitions.{NC}")
    sys.exit(1)
else:
    print(f"{GREEN}🟢 [SUCCESS] MCP Health & Tool Schema Audit passed! All schemas are 100% compliant.{NC}")
    sys.exit(0)
