#!/usr/bin/env python3
import os
import sys

def main():
    print("🔍 正在掃描前端目錄中可能「從未被 import」的 TypeScript 檔案...")
    print("⚠️  注意：這是一個基於字串比對的啟發式掃描，可能會有偽陽性（例如僅作為路由入口的檔案）。")
    print("---------------------------------------------------")

    target_dirs = ["archon-ui-main/src", "enduser-ui-fe/src"]
    existing_dirs = [d for d in target_dirs if os.path.isdir(d)]

    if not existing_dirs:
        print("❌ 找不到前端原始碼目錄 (archon-ui-main/src 或 enduser-ui-fe/src)。請確保在專案根目錄執行。")
        sys.exit(1)

    excluded_filenames = {
        "main.tsx", "index.ts", "index.tsx", "App.tsx", "setupTests.ts"
    }

    ts_files = []
    # Collect all candidate TS/TSX files
    for edir in existing_dirs:
        for root, dirs, files in os.walk(edir):
            for file in files:
                if (file.endswith(".ts") or file.endswith(".tsx")) and not file.endswith(".d.ts"):
                    if not any(x in file for x in [".test.", ".spec."]):
                        if file not in excluded_filenames:
                            ts_files.append(os.path.join(root, file))

    unused_files = []

    # Read all source files content once to make search fast
    file_contents = {}
    for edir in existing_dirs:
        for root, dirs, files in os.walk(edir):
            for file in files:
                if file.endswith((".ts", ".tsx", ".js", ".jsx", ".html", ".json")):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            file_contents[filepath] = f.read()
                    except Exception:
                        pass

    for file_path in ts_files:
        basename = os.path.splitext(os.path.basename(file_path))[0]
        match_count = 0
        for other_path, content in file_contents.items():
            if os.path.abspath(other_path) == os.path.abspath(file_path):
                continue
            if basename in content:
                match_count += 1
                break  # found reference
        
        if match_count == 0:
            unused_files.append(file_path)

    if not unused_files:
        print("✅ 恭喜！沒有找到明顯未被使用的 TypeScript 檔案。")
    else:
        print(f"發現 {len(unused_files)} 個疑似殭屍檔案（無其他原始碼引用其名稱）：")
        for unused in unused_files:
            print(f"📄 {unused}")

    print("---------------------------------------------------")
    print("💡 處置建議：")
    print("1. 這些檔案可能是完全廢棄的死代碼，也可能是被 Router 動態匯入的頂層頁面。")
    print("2. 刪除前請務必執行 'cd <前端目錄> && pnpm run build' 與 'pnpm test:unit' 進行物理驗證。")

if __name__ == "__main__":
    main()
