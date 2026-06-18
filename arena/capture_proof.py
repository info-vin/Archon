import subprocess
import time
import os
import sys

def main():
    print("Starting Godot with UI to capture screenshot...")
    
    godot_cmd = "godot"
    if subprocess.call("command -v godot &> /dev/null", shell=True) != 0:
        godot_cmd = "/Applications/Godot.app/Contents/MacOS/Godot"
        
    cmd = [
        godot_cmd,
        "-s", "Tests/capture_ui.gd"
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    
    # Run Godot with UI (NOT headless)
    process = subprocess.Popen(cmd)
    
    # Wait for completion with timeout
    try:
        process.wait(timeout=10)
        print("Capture completed successfully!")
    except subprocess.TimeoutExpired:
        print("Godot took too long. Force killing...")
        process.kill()
        sys.exit(1)

if __name__ == "__main__":
    main()
