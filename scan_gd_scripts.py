import os

target_dirs = [
    "archon-agency-tycoon",
    "arena",
    "archon-semantic-infiltration"
]

print(f"{'File Path':<60} | {'Lines':<6} | {'Size (KB)':<8}")
print("-" * 80)

total_files = 0
monoliths = []

for d in target_dirs:
    if not os.path.exists(d):
        continue
    for root, dirs, files in os.walk(d):
        # 忽略隱藏資料夾與 addons 避免雜訊
        dirs[:] = [dir for dir in dirs if not dir.startswith('.') and dir != 'addons']
        for file in files:
            if file.endswith(".gd"):
                filepath = os.path.join(root, file)
                size_kb = os.path.getsize(filepath) / 1024.0
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = sum(1 for line in f)
                
                total_files += 1
                
                if lines >= 400:
                    monoliths.append((filepath, lines, size_kb))
                else:
                    # 如果不到400行，但想看也可以印出來，不過為了整潔我們先印比較大的(比如 > 100行)
                    # 這裡先全部印出前20個字元縮寫方便查看
                    display_path = filepath if len(filepath) <= 58 else "..." + filepath[-55:]
                    print(f"{display_path:<60} | {lines:<6} | {size_kb:<8.2f}")

print("\n" + "=" * 80)
print(f"Total .gd files scanned: {total_files}")
print(f"Files >= 400 lines (Monoliths): {len(monoliths)}")
if monoliths:
    print("\n🚨 WARNING: Monolith Files Detected (> 400 lines) 🚨")
    for filepath, lines, size_kb in sorted(monoliths, key=lambda x: x[1], reverse=True):
        print(f"🔴 {filepath:<57} | {lines:<6} | {size_kb:<8.2f} KB")

