# Phase 5.10.8: RAG 與向量檢索核心區塊 (3.1) 型別硬化計畫 (Type Hardening Plan)

## 🎯 目標 (Goal)
將 `scripts/backend_type_health.py` 掃描器中回報的 `3.1 RAG 與向量檢索核心` 區塊健康度，從 96.2% 提升至 **100% 滿分**。
透過與 3.2 區塊相同的「實體探針」技術，我們已經精準定位出 9 個遺失型別標註的函式/方法。本次更新將專注於補齊這 9 個缺口。

## 📥 User Review Required

> [!IMPORTANT]
> 長官，此計畫為針對 3.1 區塊的 9 個缺口進行精準「外科手術」式的型別補齊。
> 同樣地，本次修改 **絕對不會** 更動任何執行期邏輯 (Runtime Logic)，符合 SSOT 與 DRY 準則。
> 請問是否同意此補充計畫？同意後，我將立即展開實體代碼修改與公證程序。

## 🔍 提案變更範圍 (Proposed Changes)

經過實體探測，以下為需要補齊型別的 9 個具體位置（分佈於 6 個檔案）：

### 1. Librarian 業務歸檔 (`librarian/business_archiver.py`)
- 內部異步閉包 `_call_gemini()`: 需補齊回傳標註 `-> Any` 或具體回應型別。

### 2. 程式碼提取儲存 (`storage/code_storage_service.py`)
- `add_code_examples(self, **kwargs: Any) -> Any`: 需補齊參數與回傳之泛型標註。
- `generate_summaries(self, blocks: Any, max_workers: Optional[int] = None, callback: Optional[Callable] = None, provider: Optional[str] = None) -> Any`: 需補齊選填參數與回傳標註。

### 3. 文件進度追蹤 (`storage/document_storage.py`)
- 內部異步閉包 `progress_wrap(msg: str, pct: int, cp: float = current_progress, bn: int = batch_num) -> None`: 需補齊回傳標註。

### 4. 網路檢索器 (`search/web_research_strategy.py` & `search/web_researcher.py`)
- `web_research_strategy.py`: 內部異步閉包 `_call_gemini() -> Any`
- `web_researcher.py`: 內部異步閉包 `_call_gemini() -> Any`

### 5. 程式碼提取器 (`code_extraction/code_extraction_service.py`)
- `_get_config(self) -> Any`: 需補齊回傳標註。

### 6. AST 處理器 (`code_extraction/logic/ast_processor.py`)
- `get_html_extraction_patterns() -> List[Dict[str, str]]`: 需補齊回傳型別。
- `get_text_extraction_patterns() -> List[Dict[str, str]]`: 需補齊回傳型別。

## 🛡️ 驗證計畫 (Verification Plan)

### 自動化測試與型別檢查 (Automated Tests)
1. **執行 `python scripts/backend_type_health.py`**：實體驗證 `3.1 RAG 與向量檢索核心` 的型別覆蓋率是否如預期躍升為 **100.0%**。
2. **執行 `uv run mypy src/server/services`**：確保本次新增的型別標註完全符合 mypy 規範。
