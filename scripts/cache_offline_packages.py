#!/usr/bin/env python
import os
import sys
import subprocess
import argparse

PACKAGES = [
    "scipy",
    "sympy",
    "pandas",
    "numpy",
    "sentence-transformers",
]

def main():
    parser = argparse.ArgumentParser(description="Download wheels for offline package cache")
    parser.add_argument(
        "--output",
        default="offline_wheels",
        help="Directory to save downloaded wheels (default: offline_wheels)"
    )
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    print(f"📥 Starting downloading offline wheels to: {os.path.abspath(args.output)}")

    for pkg in PACKAGES:
        print(f"📦 Downloading {pkg}...")
        try:
            cmd = [sys.executable, "-m", "pip", "download", "-d", args.output, pkg]
            subprocess.run(cmd, check=True)
            print(f"✅ {pkg} downloaded successfully.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to download {pkg}: {e}", file=sys.stderr)
            sys.exit(1)

    print("🎉 All offline packages cached successfully.")

if __name__ == "__main__":
    main()
