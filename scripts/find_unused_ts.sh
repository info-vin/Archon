#!/bin/bash

echo "🔍 正在掃描前端目錄中可能「從未被 import」的 TypeScript 檔案..."
echo "⚠️  注意：這是一個基於字串比對的啟發式掃描，可能會有偽陽性（例如僅作為路由入口的檔案）。"
echo "---------------------------------------------------"

# 定義要掃描的目錄 (根據 Archon 專案結構)
TARGET_DIRS="archon-ui-main/src enduser-ui-fe/src"

# 檢查目錄是否存在
EXISTING_DIRS=""
for dir in $TARGET_DIRS; do
  if [ -d "$dir" ]; then
    EXISTING_DIRS="$EXISTING_DIRS $dir"
  fi
done

if [ -z "$EXISTING_DIRS" ]; then
  echo "❌ 找不到前端原始碼目錄 (archon-ui-main/src 或 enduser-ui-fe/src)。請確保在專案根目錄執行。"
  exit 1
fi

# 建立一個陣列來存放可能是孤兒的檔案
UNUSED_FILES=()

# 尋找所有 ts/tsx 檔案，排除測試檔、型別定義檔與常見的進入點
for file in $(find $EXISTING_DIRS -type f \( -name "*.ts" -o -name "*.tsx" \) \
  ! -name "*.d.ts" \
  ! -name "*.test.*" \
  ! -name "*.spec.*" \
  ! -name "main.tsx" \
  ! -name "index.ts" \
  ! -name "index.tsx" \
  ! -name "App.tsx" \
  ! -name "setupTests.ts"); do

  # 取得不含副檔名的檔案名稱 (例如 MyComponent.tsx -> MyComponent)
  BASENAME=$(basename "$file" | sed 's/\.[^.]*$//')

  # 使用 grep 搜尋是否有其他檔案包含這個名稱 (排除當前檔案自己)
  MATCH_COUNT=$(grep -rl "$BASENAME" $EXISTING_DIRS | grep -v "$file" | wc -l)

  if [ "$MATCH_COUNT" -eq 0 ]; then
    UNUSED_FILES+=("$file")
  fi
done

# 輸出結果
if [ ${#UNUSED_FILES[@]} -eq 0 ]; then
  echo "✅ 恭喜！沒有找到明顯未被使用的 TypeScript 檔案。"
else
  echo "👻 發現 ${#UNUSED_FILES[@]} 個疑似殭屍檔案（無其他原始碼引用其名稱）："
  for unused in "${UNUSED_FILES[@]}"; do
    echo "📄 $unused"
  done
fi

echo "---------------------------------------------------"
echo "💡 處置建議："
echo "1. 這些檔案可能是完全廢棄的死代碼，也可能是被 Router 動態匯入的頂層頁面。"
echo "2. 刪除前請務必執行 'cd <前端目錄> && pnpm run build' 與 'pnpm test:unit' 進行物理驗證。"
