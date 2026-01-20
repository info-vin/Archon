import os
import sys
from pathlib import Path

def verify():
    project_root = Path(__file__).resolve().parent.parent
    logo_path = project_root / "enduser-ui-fe" / "public" / "logo-eciton.svg"
    
    print(f"🔍 Verifying brand asset at: {logo_path}")
    
    # 1. Check if file exists
    if not logo_path.exists():
        print("❌ Error: logo-eciton.svg not found!")
        sys.exit(1)
    
    # 2. Read content
    with open(logo_path, "r") as f:
        content = f.read()
    
    # 3. Validate content
    has_svg = "<svg" in content
    has_animate = "<animate" in content
    has_eciton_colors = "#00f2ff" in content or "#a855f7" in content
    
    if has_svg and has_animate and has_eciton_colors:
        print("✅ Success: DevBot output verified (Dynamic SVG with ECITON palette).")
    else:
        print("❌ Error: File exists but content validation failed!")
        print(f"SVG: {has_svg}, Animate: {has_animate}, Colors: {has_eciton_colors}")
        sys.exit(1)

if __name__ == "__main__":
    verify()
