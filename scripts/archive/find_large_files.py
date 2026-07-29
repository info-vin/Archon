#!/usr/bin/env python3
import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Scan project files for large source code files.")
    parser.add_argument("threshold", type=int, nargs="?", default=400, help="Line count threshold")
    args = parser.parse_args()

    threshold = args.threshold
    print(f"🔍 正在掃描專案中超過 {threshold} 行的原始碼檔案...")
    print("---------------------------------------------------")

    excluded_dirs = {".git", "node_modules", "venv", ".venv", "dist", "build", "__pycache__", "coverage"}
    allowed_extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".sql"}

    large_files = []

    for root, dirs, files in os.walk("."):
        # Modify dirs in-place to prune excluded directories
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in allowed_extensions:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        line_count = sum(1 for _ in f)
                    if line_count > threshold:
                        large_files.append((line_count, filepath))
                except Exception as e:
                    print(f"⚠️  無法讀取檔案 {filepath}: {e}")

    large_files.sort(key=lambda x: x[0], reverse=True)

    for lines, filepath in large_files:
        print(f"📄 {lines:<5} 行 | {filepath}")

    print("---------------------------------------------------")
    print("✅ 掃描完成！")
    print("💡 提示：這些龐大的檔案通常是隱藏「殭屍程式碼」或技術債的最佳突破口。")

if __name__ == "__main__":
    main()
