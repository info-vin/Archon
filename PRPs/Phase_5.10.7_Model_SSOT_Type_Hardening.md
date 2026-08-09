# Phase 5.10.7: Model SSOT & Prompt 治理區塊 (3.2) 型別硬化計畫 (Type Hardening Plan)

## 🎯 目標 (Goal)
將 `scripts/backend_type_health.py` 掃描器中回報的 `3.2 Model SSOT 與 Prompt 治理` 區塊健康度，從 90.8% 提升至 **100% 滿分**。
此計畫將精準補齊剩餘 13 個遺失型別標註的函式/方法，不造新輪子、不擴大範圍，嚴格遵守 SSOT 與 DRY 原則。

## 📥 User Review Required

> [!IMPORTANT]
> 長官，此計畫為針對上述 13 個缺口進行精準「外科手術」式的型別補齊 (Type Hinting)。
> 本次修改 **絕對不會** 更動任何執行期邏輯 (Runtime Logic)，也不會新增任何新腳本，完全遵守 SSOT 與 DRY 準則。
> 請問是否同意此計畫？同意後，我將立即展開實體代碼修改與公證程序。

## 🔍 提案變更範圍 (Proposed Changes)

以下為需要補齊型別的 13 個具體位置（分佈於 5 個檔案）：

### python/src/server/services/token_usage_service.py
- 內部異步閉包 `_log_to_db()`: 需補齊回傳標註 `-> None`
- 內部異步閉包 `_fetch_data()`: 需補齊回傳標註 `-> List[Dict[str, Any]]`

### python/src/server/services/client_manager.py
- 動態代理方法 `_robust_execute(self, *args: Any, **kwargs: Any) -> Any`: 需補齊參數與回傳之泛型標註。

### python/src/server/services/llm/clients.py
- `_get_optimal_ollama_instance(instance_type: Optional[str] = None, use_embedding: bool = False, override: Optional[str] = None) -> str`: 需補齊選填參數與字串回傳標註。

### python/src/server/services/llm/base.py
- `create(self, *args: Any, **kwargs: Any) -> Any` (需補齊兩處多載宣告)
- `close(self) -> None` (需補齊回傳)
- `aclose(self) -> None` (需補齊回傳)
- `__getattr__(self, name: str) -> Any` (需補齊兩處多載宣告)
- 內部閉包 `_execute_on_ollama() -> Any` (需補齊回傳)

### python/src/server/services/discovery/models.py
- `__post_init__(self) -> None` (需補齊回傳)

### python/src/server/services/discovery/__init__.py
- `close() -> None` (或 `async def close() -> None`，需補齊回傳)

## 🛡️ 驗證計畫 (Verification Plan)

### 自動化測試與型別檢查 (Automated Tests)
1. **執行 `python scripts/backend_type_health.py`**：實體驗證 `3.2 Model SSOT 與 Prompt 治理` 的分數是否如預期從 90.8% 躍升為 **100%**。
2. **執行 `uv run mypy src/server/services`**：確保本次新增的型別標註完全符合 mypy 的靜態型別檢查規範，沒有引發新的型別衝突。
