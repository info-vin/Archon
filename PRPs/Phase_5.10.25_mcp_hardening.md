# Phase 5.10.25: MCP 實體防護硬化 (Topology & SSOT)

## 1. 目標 (Goal)
1. **拓樸死結修復**：修復 `archon-server` 與 `archon-mcp` 之間的容器啟動競爭條件 (Race Condition)，徹底消除 `lifespan.py` 在排程重啟時引發的 `Agent Neural Wiring FAILED` 警告。
2. **提示詞 SSOT 硬化**：將全代碼庫唯一殘留的 inline 提示詞硬編碼 (`version_control_tools.py`) 抽離並註冊至 `ALL_PROMPTS`，達成 100% 提示詞 SSOT 與 DRY。

## 2. 背景與物理事實
*   **拓樸缺陷**：經由 Python 解析 `docker-compose.yml` 實體證實，`archon-server` 服務的 `depends_on` 為 `None`。Docker 會並行啟動兩者，當 `archon-mcp` 仍在 60 秒的 `start_period` 中準備時，`archon-server` 已跑完其 30 秒的重試上限而報錯。
*   **SSOT 違規**：[`python/src/mcp_server/features/developer/version_control_tools.py`](file:///Users/vincenta/GoogleKwok022/Archon/python/src/mcp_server/features/developer/version_control_tools.py) 的 `_generate_commit_message` 函式中，硬編碼了 AI commit 生成提示詞。

## 3. 預計修改內容 (Proposed Changes)

### 3.1 基礎設施拓樸修復 (Infrastructure Topology)
#### [MODIFY] [`docker-compose.yml`](file:///Users/vincenta/GoogleKwok022/Archon/docker-compose.yml)
在 `archon-server` 區塊下新增對 `archon-mcp` 的物理健康依賴：
```yaml
    depends_on:
      archon-mcp:
        condition: service_healthy
```
> [!IMPORTANT]
> 此舉強制 Docker Compose 必須等待 `archon-mcp` 容器的 8051 port 亮綠燈後，才准許 `archon-server` 啟動，從根本上切斷 Race Condition。

### 3.2 提示詞定義 SSOT
#### [MODIFY] [`python/src/server/prompts/dev_ops_prompts.py`](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/prompts/dev_ops_prompts.py)
新增 `COMMIT_MESSAGE_GENERATOR` 提示詞模板常量：
```python
COMMIT_MESSAGE_GENERATOR = """You are a senior software engineer. Generate a concise and semantic commit message following the Conventional Commits specification based on the provided git diff.

The user provided a generic message: "{original_message}"
Please improve it to be more descriptive based on the code changes.

Git Diff:
{diff}

Instructions:
1. Use the format: <type>(<scope>): <subject>
2. Keep the subject line under 72 characters.
3. If the diff is too complex, focus on the primary change.
4. ONLY return the commit message string, no markdown, no quotes, no explanations.
"""
```

### 3.3 提示詞註冊與資料庫同步
#### [MODIFY] [`python/src/server/prompts/__init__.py`](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/prompts/__init__.py)
*   匯入 `COMMIT_MESSAGE_GENERATOR`。
*   在 `ALL_PROMPTS` 字典中新增映射：
    ```python
    "COMMIT_MESSAGE_GENERATOR": COMMIT_MESSAGE_GENERATOR,
    ```

### 3.4 動態提取提示詞
#### [MODIFY] [`python/src/mcp_server/features/developer/version_control_tools.py`](file:///Users/vincenta/GoogleKwok022/Archon/python/src/mcp_server/features/developer/version_control_tools.py)
*   引入 `from src.server.services.prompt_service import prompt_service`。
*   將原本的 inline `prompt = f"""..."""` 替換為動態獲取：
    ```python
    template = prompt_service.get_prompt("COMMIT_MESSAGE_GENERATOR")
    prompt = template.format(original_message=original_message, diff=diff[:8000])
    ```

## 4. 自動化驗證計畫 (Automated Verification)
1.  **Linter / Type Checking**: 執行 `make lint` 確保無語法與型別錯誤。
2.  **單元測試**: 執行 `make test-be` (特別是 MCP 相關測試)。
3.  **Docker 拓樸驗證**: 使用 `docker compose config` 確保 YAML 修改合法無誤。

### 3.5 爬蟲 API 記帳攔截器修復 (Token Leakage Fix)
#### [MODIFY] [`python/src/server/services/crawling/lead_evaluator.py`](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/crawling/lead_evaluator.py)
爬蟲為了高併發，繞過了 `llm_service` 直接使用原生 `genai.Client`，導致 Token 使用量未寫入資料庫，成為隱藏成本。我們需將其掛載回中介攔截器：
*   引入 `from ...services.token_usage_service import TokenUsageService`
*   在 `generate_llm_response` 方法中，從 `response.usage_metadata` 提取 Token 數，並呼叫 `TokenUsageService.log_usage` 將成本寫入 `token_usage` 表。
*   此修改能確保每日爬蟲耗費的數萬 Token 精準對帳，且不影響原有的高併發邏輯。


### 3.6 爬蟲向量過濾閾值硬化 (Threshold Adjustment)
#### [MODIFY] [`python/src/server/schemas/settings.py`](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/schemas/settings.py)
*   將 `CrawlerJobConfig` 中的 `lead_gen_similarity_threshold` 預設值由 `0.68` 調升至 `0.70`。

#### [NEW] [`migration/20260819_update_rag_threshold.sql`](file:///Users/vincenta/GoogleKwok022/Archon/migration/20260819_update_rag_threshold.sql)
*   建立資料庫遷移檔，將 `0.70` 寫入 `archon_settings`，落實 SSOT (單一事實來源) 原則：
```sql
INSERT INTO archon_settings (key, value, description) 
VALUES ('LEAD_GEN_SIMILARITY_THRESHOLD', '0.70', 'RAG Cosine Similarity Threshold for Crawler Layer 1 Filtering')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
```
