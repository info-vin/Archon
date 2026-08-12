# Phase 5.10.11 Docker Dependency Locking

## 背景 (Background)
在 2026/08/11 的開發中，因為修改了 `Dockerfile.server` 觸發了無快取重建。由於先前的 Dockerfile (`Dockerfile.server` 與 `Dockerfile.mcp`) 皆未綁定 `uv.lock`，導致 `uv pip install` 抓取了 PyPI 上最新的 `mcp` 套件 (1.27.1)。
新版 `mcp` 移除了 `fastmcp` 模組，引發了致命的 `ModuleNotFoundError: No module named 'mcp.server.fastmcp'` 崩潰，導致 MCP 伺服器無法啟動。

## 決策與修復 (Decisions and Fixes)
1. **拒絕樂觀路徑 (No Optimistic Paths)**: 最初考慮使用 `uv sync` 來鎖定版本，但 `uv sync` 會將環境預設生成至 `/build/.venv` (或是需要繁瑣的環境變數覆蓋)，會改變原本 `/venv` 的實體路徑結構，有可能破壞 Playwright 或 Python 的 Shebang 綁定。
2. **導入 uv export (Defensive Design)**: 我們採用了絕對防禦路徑。透過複製 `uv.lock`，並使用 `uv export --format requirements-txt --no-hashes > requirements.txt`，接著透過原生的 `uv pip install -r requirements.txt` 來安裝。此舉確保在「完全不改變 Docker 環境結構與任何虛擬環境路徑」的前提下，達成 100% 依賴鎖定。
3. **全面修復 (Comprehensive Fix)**: 對 `Dockerfile.server` 與 `Dockerfile.mcp` 皆進行了硬化處理，防止類似未鎖定的依賴安裝問題再次發生。

## 驗證 (Verification)
透過撰寫與執行 `scratch/verify_mcp_fix.sh`，在全新無快取建置後，公證了 MCP 容器順利輸出 `Starting MCP Server on port 8051`，徹底清除了 `ModuleNotFoundError` 威脅。
