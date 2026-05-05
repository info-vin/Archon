#!/bin/bash

# 預設行數門檻為 400，可透過第一個參數自訂 (例如: ./scripts/find_large_files.sh 500)
THRESHOLD=${1:-400}

echo "🔍 正在掃描專案中超過 $THRESHOLD 行的原始碼檔案..."
echo "---------------------------------------------------"

# 排除 .git, node_modules, 虛擬環境等建置與依賴目錄
# 僅鎖定 .py, .ts, .tsx, .js, .jsx, .sql 檔案進行掃描
find . \
  -type d \( -name ".git" -o -name "node_modules" -o -name "venv" -o -name ".venv" -o -name "dist" -o -name "build" -o -name "__pycache__" -o -name "coverage" \) -prune -o \
  -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.sql" \) -print0 | \
  xargs -0 wc -l | \
  awk -v threshold="$THRESHOLD" '$1 > threshold && $2 != "total" {print $1, $2}' | \
  sort -nr | \
  awk '{printf "📄 %-5s 行 | %s\n", $1, $2}'

echo "---------------------------------------------------"
echo "✅ 掃描完成！"
echo "💡 提示：這些龐大的檔案通常是隱藏「殭屍程式碼」或技術債的最佳突破口。"
