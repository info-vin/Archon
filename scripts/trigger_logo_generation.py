import asyncio
import os
import sys
from pathlib import Path

# Add python/src to path so we can import the tool
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "python" / "src"))

from mcp_server.features.design.logo_tool import GenerateBrandAssetTool

async def main():
    print("🤖 DevBot activated for task: [REBRAND] Implement Project Eciton Identity")
    
    # 1. Initialize Tool
    tool = GenerateBrandAssetTool(style="eciton")
    
    # 2. Execute Generation (Thinking)
    print("🎨 Generating asset with style='eciton'...")
    svg_content = await tool.execute()
    
    # 3. Write Output (Acting)
    output_path = project_root / "enduser-ui-fe" / "public" / "logo-eciton.svg"
    print(f"💾 Writing asset to {output_path}...")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write(svg_content)
        
    print("✅ Task Completed: Logo asset deployed.")

if __name__ == "__main__":
    asyncio.run(main())
