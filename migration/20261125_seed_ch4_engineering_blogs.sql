-- Migration: 20261125_seed_ch4_engineering_blogs.sql
-- Purpose: Publish the 5 sanitized engineering blog posts distilled from GEMINI.md Chapter 4 (2026-01 ~ 2026-10).
-- Idempotent: Uses fixed UUIDs with ON CONFLICT (id) DO UPDATE and registers in schema_migrations.

BEGIN;

INSERT INTO public.blog_posts (
    id,
    title,
    excerpt,
    content,
    author_name,
    publish_date,
    image_url,
    status,
    target_brand,
    ai_score
) VALUES
(
    'b4000001-0000-4000-8000-000000000001',
    '半夜把免費額度燒光、報告卻交白卷：我們修好 Multi-Agent 失控的三道護欄',
    '把三個 AI Agent 丟進同一個群聊後，我們收過只有 {"content": null} 的「假完成」報告，也看過單次 6.7MB 的請求瞬間打爆 429 限流。這篇文章分享我們如何花半年時間，從失控的自由對話收斂出可控、可斷點續跑的星型架構。',
    $BLOG1$# 半夜把免費額度燒光、報告卻交白卷：我們修好 Multi-Agent 失控的三道護欄

你一定遇過這種荒謬的場景：系統儀表板顯示 AI 任務「`done`（已完成）」，團隊群組也準時推播了通知——但點開報告一看，裡面只有冰冷的 `{"content": null}`。更慘的是隔天早上一查配額，兩個 Bot 在半夜的群聊裡互相客氣地「請對方補充」，一路把免費 API 額度燒得一乾二淨。

這不是模型不夠聰明，而是我們太天真地把「人類群聊」直接套在沒有煞車的多代理系統上。

---

## 開發演進時間軸（2026年1月 ～ 10月）

| 時間節點 | 演進階段 | 解決的核心問題 |
| :--- | :--- | :--- |
| **2026-01 ~ 02** | 任務系統修復與全角色閉環 | 修復任務 `assignee_id` 過濾與非同步 Context 錯亂，完成 Sales / Marketing / Manager 與 Sentinel 哨兵閉環 |
| **2026-05** | 升級星型群聊（Star Topology） | 淘汰無序自由對話，改由 Supervisor 路由並整合日、週、月報 Map-Reduce 排程 |
| **2026-07** | 斷點持久化與 HITL 防線 | 實裝 `AgentCheckpointManager` 快照落盤，高風險寫入工具強制進 `SUSPENDED_WAITING_FOR_APPROVAL` |
| **2026-09** | Oracle Payload 瘦身 | 拔除 Agent 裸寫 `select *`，改欄位投影與 JSON 遞迴截斷（`> 1,000` 字元截斷） |
| **2026-10** | 星環強制收斂與容器容災 | 實裝 4 步依序推進、強制文字收斂、3,800 字元分段與 In-Process Fallback |

---

## 一、我們踩過的兩次無效嘗試（False Starts）

剛開始遇到 Bot 互踢與報告交白卷時，我們做過兩個事後證明沒用的補丁：
1. **在 Prompt 裡苦口婆心寫「請不要重複發言」**：實測完全無效。當上下文超過一定長度，LLM 還是會忘記自己剛才說過什麼。
2. **直接把整張日誌表與文章庫餵給總結 Agent**：我們以為給越多資料越準，結果 `NexusOracleAgent` 一次撈出 **6.7MB** 原始資料，請求還沒開始推理就直接撞上 `429 Rate Limit` 整條管線卡死。

## 二、破局關鍵：限縮自由度，而不是加長 Prompt

我們決定把「自由對話」拆掉，改造成嚴格受控的**星型群聊（Star Topology）+ 斷點持久化**：

```mermaid
flowchart LR
    U["任務觸發"] --> S["Supervisor 路由"]
    S -->|"1. 4步依序推進"| W1["MarketBot / DevBot"]
    W1 -->|"Tool Call 回合"| TC{"有產出文字?"}
    TC -->|"否: 強制文字收斂"| W1
    TC -->|"是"| CP[("Checkpoint 斷點落盤")]
    CP -->|"高風險寫入"| HITL["WAITING_APPROVAL 暫停"]
    HITL -->|"人工核准"| RESUME["從斷點續跑"]
    CP -->|"一般任務"| S
    S -->|"Anti-recursion 熔斷"| END["3,800字元分頁推播"]
```

1. **強制依序推進與 Anti-recursion 防護**：在 `WORKFLOW_SUPERVISOR_DAILY` 強制 4 步推進（`marketbot -> devbot -> summary -> end`）並加入遞迴保護，根除重複指派死循環；推播點後移至 `WorkflowEngine` 產出 `final_result` 之後，解決假完成與日誌遞迴污染。
2. **資料投影與遞迴截斷**：拔除 Agent 裸寫 SQL 的權力，將欄位投影（`id, title, status`）封裝進 `BlogService` 與 `LogService`，JSON 超過 `1,000` 字元強制截斷。
3. **Checkpoint + HITL + In-Process Fallback**：每步 Action/Observation 後即快照落盤；高風險寫入工具攔截進人工審批；跨容器呼叫網路中斷時自動回退同進程 `WorkflowEngine`，並把 Map-Reduce 超時容錯放寬至 `600` 秒。

---

## 三、真實架構對比與數據驗證（As-Is vs To-Be）

| 評估維度 | 舊架構（自由群聊） | 新架構（星型 + Checkpoint） | 實質變化 | 數據來源與物理驗證方法 |
| :--- | :--- | :--- | :--- | :--- |
| **單次協同 Payload** | **6.7 MB** | **2.5 萬字元** | ⬇️ **縮減 97%**，消除 429 阻塞 | 由 `Phase 5.11.21` 物理探針實測 `gather_nexus_data` 序列化前後輸出大小 |
| **長報告推播完整度** | 舊版 **150 字元**截斷 / `null` 假完成 | **3,800 字元分段** + 頁碼注入 | 完整保留 Markdown 表格，400 解析失敗自動降純文字 | 實測 `split_message_chunks()` 分段邏輯與線上日誌追蹤推播結果 |
| **Map-Reduce 超時容錯** | 短超時頻繁中斷 | **600 秒**容錯 + `["processing", "doing"]` 回收 | 週/月報不再中途斷頭 | `task_dispatcher` 逾時回收邏輯與週/月報排程實測紀錄 |
| **高風險工具防護** | 無攔截直接執行 | **進入 `SUSPENDED_WAITING_FOR_APPROVAL`** | 容器重啟不丟進度，核准才續跑 | 透過 `AgentCheckpointManager` 狀態快照落盤與恢復端點驗證 |

---

## 四、實戰 Q&A 與具體改善方案

### Q1：Agent 回傳 `{"content": null}` 卻顯示任務完成，怎麼根治？
* **根本原因**：模型在最後一輪仍選擇呼叫 Tool（此時 `message.content` 原生為 `None`），外層流程卻把最後一次回應直接當成最終報告存檔。
* **改善方案**：
  1. 在工作節點強制設定 Tool Call 最大輪數，到達上限時將 `tool_choice` 鎖為 `"none"`，逼模型在純文字模式收斂出結論。
  2. 把外部推播（Telegram / 通知）一律移到 `WorkflowEngine` 產出非空 `final_result` **之後**，若 `final_result` 為空直接標記失敗並觸發告警，絕不發空白報告。
* **架構取捨**：會多消耗最後 1 次輕量推理成本，但能 100% 消滅靜默白卷。

### Q2：怎麼防止總結 Agent 撈爆資料庫或被上下文遞迴污染？
* **根本原因**：讓 Agent 自由組查詢或把前幾天的長篇報告原文再撈回來當日誌上下文，會造成指數級膨脹。
* **改善方案**：
  1. **Service 層強制投影**：在 `BlogService` / `LogService` 封裝固定查詢（只取 `id, title, status`），禁止 Agent 執行 `select *`。
  2. **序列化前遞迴截斷**：對傳入 Prompt 的 JSON 物件實作遞迴長度守衛，任何欄位超過 `1,000` 字元強制截斷為 `...(truncated)`，並排除自我日誌表。
* **架構取捨**：總結 Agent 會失去部分細節全文，需要深究特定文章時，再透過工具按 `id` 單筆調閱。$BLOG1$,
    'Archon 團隊',
    '2026-11-25T17:00:00+08:00',
    'https://picsum.photos/seed/archon-multi-agent/1024/1024',
    'published',
    'Archon',
    98
),
(
    'b4000001-0000-4000-8000-000000000002',
    '31.5GB 容器塞爆免費雲端硬碟？我們砍掉 84% 肥肉的 AI 瘦身實錄',
    '本地跑得好好的 RAG 系統，一上雲端就 ENOSPC 磁碟爆滿、Vite 記憶體吃到 2GB 閃退。這不是模型太強，而是「預設安裝」正在吃垮你的基礎設施。看我們如何用 22MB ONNX 與離線雙軌把映像檔砍到 5.02GB。',
    $BLOG2$# 31.5GB 容器塞爆免費雲端硬碟？我們砍掉 84% 肥肉的 AI 瘦身實錄

每個做過 RAG（檢索增強生成）的人大概都經歷過那個崩潰的下午：在自己筆電上測試一切完美，滿懷期待地執行 `docker build` 準備部署到免費雲端容器，結果終端機冷冷地吐出一行：

> `ENOSPC: no space left on device`

一查體積才嚇一跳——我們這個純文字知識庫系統，Docker 映像檔竟然胖到了 **31.5GB**！就連旁邊的前端開發伺服器，也在沒人注意的時候吃掉了 **2GB 記憶體**。

---

## 開發演進時間軸（2026年4月 ～ 8月）

| 時間節點 | 演進階段 | 解決的核心問題 |
| :--- | :--- | :--- |
| **2026-04** | x86_64 冷啟動與搜尋延遲優化 | 解決 Torch 依賴與 NumPy 載入崩潰，將熱機搜尋延遲壓低至 `2.3` 秒 |
| **2026-05** | `ENOSPC` 危機與 `OFFLINE_MODE` 雙軌 | 剃除 CUDA 依賴與快取，映像檔從 `31.5GB` 瘦身至 `5.02GB`；建立 384 維本地離線檢索 |
| **2026-06** | ONNX 重排引擎與 3-Tier 容災 | 改採 `onnxruntime` + `22MB` 微縮權重，並上線 `Gemini -> HF -> Ollama` 三級降階 |
| **2026-07** | Vite 記憶體減肥與向量截斷防護 | 注入 `NODE_OPTIONS` 壓制 Vite 記憶體（`2GB -> 350MB`），並將 `3072` 維向量安全裁切至 `768` 維 |
| **2026-08** | Build Context 與磁碟清創 | 將 `3.5GB` `ollama_data` 寫入 `.dockerignore`，釋放 `36.8GB` 磁碟快取 |

---

## 一、我們抓出的「隱形體重」元兇

拆開映像檔分層（Layer）與容器資源監控後，我們才發現業務程式碼根本沒幾 MB，剩下全是不需要的肥肉：
1. **買菜送大象的 PyTorch**：引入 `sentence-transformers` 做語意重排，預設幫你把好幾 GB 的 NVIDIA CUDA 函式庫全部裝進只有 CPU 的容器裡。
2. **未隔離的建置上下文**：`3.5GB` 的本地 `ollama_data` 目錄沒寫進 `.dockerignore`，每次打包都在空轉搬運。
3. **無上限的 Node Heap**：Vite 容器沒設 GC 門檻，記憶體一路漲到 `2GB` 直接拖垮共居服務。

## 二、破局：只留推理、不留訓練框架

```mermaid
flowchart LR
    Q["使用者查詢"] --> L1["ONNX 22MB 語意重排<br/>CPU 輕量推論"]
    Q --> R{"網路與 API 狀態"}
    R -->|"正常"| T1["Tier 1: Gemini 雲端"]
    R -->|"429 限流"| T2["Tier 2: Hugging Face"]
    R -->|"完全斷網 OFFLINE_MODE"| T3["Tier 3: 本地 Ollama + 384維嵌入"]
```

1. **用 `onnxruntime` + `22MB` 微縮權重取代 PyTorch**：放棄笨重框架，改採純推理引擎與 EAFP（`try-except`）Fail-Fast 檢查，兼容 Mock 測試並確保載入異常立刻報錯。
2. **強制 CPU-only Wheels 與 Heap 限制**：鎖定不含 CUDA 的依賴、補齊 `.dockerignore`，並於 `docker-compose.yml` 注入 `NODE_OPTIONS=--max-old-space-size=512` 強制提早 GC。
3. **建置 3-Tier 容災與 `OFFLINE_MODE` 雙軌**：在實體斷網或限流時，自動將向量降階至 `384` 維度轉接本地模型，並加上維度截斷防護（外部 `3072` 維裁切至 `768` 維防寫入崩潰）。

---

## 三、瘦身前後實測數據（As-Is vs To-Be）

| 資源與效能指標 | 瘦身前（As-Is） | 瘦身後（To-Be） | 實質改善幅度 | 數據來源與物理驗證方法 |
| :--- | :---: | :---: | :--- | :--- |
| **Docker 映像檔總體積** | **31.5 GB** | **5.02 GB** | ⬇️ **狂砍 84.1%** | 依 `05-29` `docker images` 建置實測比對（剃除 CUDA 與快取後量測） |
| **建置快取與 Context 清理** | 含 `3.5 GB` 未排除模型 | 排除 `ollama_data` | 釋放 **36.8 GB** 磁碟快取 | 依 `08-12` `.dockerignore` 更新與 `docker system prune` 輸出紀錄 |
| **語意重排模型體積** | PyTorch + CUDA 巨獸依賴 | **22 MB**（ONNX） | 消除容器依賴死鎖 | 依 `06-22` ONNX 微縮權重實體檔案大小與 EAFP 單元測試驗證 |
| **Vite 開發記憶體佔用** | **2.0 GB** | **350 MB** | ⬇️ **下降 82.5%** | 依 `07-24` 於 `docker-compose.yml` 注入 `NODE_OPTIONS=512` 後容器監控比對 |
| **熱機搜尋與離線韌性** | 斷網即全線報錯 | 熱機 **2.3 秒** / **384 維**離線 | 斷網 100% 存活 | 依 `04-15` 搜尋基準測試與 `05-30` 實體斷網 `OFFLINE_MODE` 測試公證 |

---

## 四、實戰 Q&A 與具體改善方案

### Q1：不想整套重寫 RAG，怎麼最快把 Python AI 容器體積砍半？
* **改善方案**：
  1. 先用 `docker history <image>` 找出超過 1GB 的罪魁禍首（通常是 `torch`、`nvidia-*` 與未忽略的模型權重）。
  2. 若容器只跑推論不跑訓練，把 `sentence-transformers` 換成 `onnxruntime` + 量化小模型（22MB），或直接改用 `--index-url https://download.pytorch.org/whl/cpu` 安裝純 CPU wheel。
  3. 務必把 `ollama_data/`、`.venv/`、快取目錄寫進 `.dockerignore`，避免建置上下文重複打包。
* **架構取捨**：純 CPU ONNX 在單次大批量（數百段）重排時會比 GPU 慢，因此需搭配「先向量取 Top-20、再進 ONNX 重排」的漏斗設計。

### Q2：免費雲端限流或離線降階時，不同嵌入模型的向量維度打架怎麼辦？
* **根本原因**：雲端模型（如 3072 維 / 768 維）與本地離線模型（384 維）維度不同，直接寫入同一張 `pgvector` 資料表會觸發維度不符報錯。
* **改善方案**：
  1. **寫入前維度防護**：針對支援 Matryoshka 的雲端模型，在寫入前統一截斷為 `768` 維度。
  2. **離線雙軌隔離**：在 `OFFLINE_MODE` 下將查詢路由至獨立的 `384` 維本地索引或降階檢索通道，避免污染主向量庫。
* **架構取捨**：需要維護一組輕量離線索引，換取斷網環境下 100% 服務存活率。$BLOG2$,
    'Archon 團隊',
    '2026-11-25T16:00:00+08:00',
    'https://picsum.photos/seed/archon-docker-slim/1024/1024',
    'published',
    'Archon',
    98
),
(
    'b4000001-0000-4000-8000-000000000003',
    '測試全綠卻線上炸裂？我們這樣拆穿 AI 寫碼的「幽靈開發」',
    '單元測試 100% 通過，合併上線卻因為資料庫欄位不存在而靜默回傳 0 筆資料。這就是 AI 時代最危險的「假綠燈」。看我們如何把核心型別覆蓋率從 39.3% 一路拉升到 99%+，建立不講人情的自動化物理門禁。',
    $BLOG3$# 測試全綠卻線上炸裂？我們這樣拆穿 AI 寫碼的「幽靈開發」

讓 AI 幫你寫 PR 真的很快——直到某天你開開心心合併了一個「測試全綠」的 PR，上線後頁面卻一片空白，靜默回傳 0 筆資料。

打開資料庫日誌一看，血壓直接飆高：AI 在服務層裡憑空幻想出了 `section_title`、`old_value` 這些**資料庫根本不存在的欄位**（PostgREST 報錯 `42703` 與 `PGRST204`）。更諷刺的是，為什麼測試沒抓到？因為測試裡的 Mock 回傳的是舊的假結構，甚至底層回傳型別已經改了，Mock 還在回傳舊格式——**單元測試親手替 Bug 戴上了綠色的面具。**

我們稱這種現象為**「幽靈開發（Ghost Development）」**。

---

## 開發演進時間軸（2026年2月 ～ 10月）

| 時間節點 | 演進階段 | 解決的核心問題 |
| :--- | :--- | :--- |
| **2026-02 ~ 03** | Zero-Mypy 與巨型檔案清零 | 拆分 4 大 > 1,000 行核心 Service，將 `RateLimiter` 優化為 `O(1)` 並建立部門 403 隔離 |
| **2026-05** | E2E 防禦與 `make audit-qa` | 禁用 `.single()` 防 HTTP 500、關閉 Recharts 動畫防 Playwright 崩潰，整合視覺與 LLM 裁判 |
| **2026-06 ~ 07** | L2 模組化與資料庫收斂 | 設定 `> 400` 行門禁，清除 83 支檔案 `_query()` 閉包，將 36 支碎片 SQL 收斂為 11 支語義檔 |
| **2026-09** | Lean 4 形式化證明與物理公證 | 修復 ARM64 環境讓 18 項 Lean 4 證明全數編譯通過，後端測試突破 724+ 項 |
| **2026-10** | 物理 Schema 對帳與規則極簡化 | 抓出 PR #656 / #654 幻覺欄位，將規則檔從 558 行壓縮至 86 行並加上 Step 11 門禁 |

---

## 一、為什麼「叫 AI 小心一點」完全沒用？

我們試過在規則檔寫長篇大論提醒 AI，結果 `.jules/*.md` 6 份檔案膨脹到 **558 行**，裡面甚至還出現 AI 自己編造的「幻覺日期」，反而污染了每次對話的上下文。

我們終於認清一件事：**靠提示詞自律沒有用，只有讓錯誤在 Commit 前直接被門禁腳本 Exit 1 退貨，才是唯一解法。**

## 二、建立三向「物理公證」防線

```mermaid
flowchart LR
    C["Code 變更"] --> G1["靜態契約: Ruff + MyPy + 禁用 .single"]
    C --> G2["SSOT 掃描: 禁硬編碼陣列 / 禁繞過 BaseRepository"]
    C --> G3["三向對帳: Code vs SQL Schema vs Dockerfile"]
    G1 & G2 & G3 -->|"全綠"| PASS["允許合併"]
    G1 & G2 & G3 -->|"任一失敗"| BLOCK["Exit 1 阻斷提交"]
```

1. **消滅 God Objects 與舊閉包**：將超過 1,000 行的巨型服務拆解為 L2 模組，設定 **> 400 行紅燈門禁**；同時清剿散落 83 支檔案的舊式 `_query()` 閉包與易引發 HTTP 500 的 `.single()` 查詢。
2. **強制型別與契約同步**：建置 `backend_type_health.py`（並修正其容器 `/app` 路徑盲區，實現宿主機與容器 100% 對齊），將強型別校驗延伸至 API DTO 與測試 Mock。
3. **三向物理對帳（`phase_audit.py`）**：自動掃描程式碼與真實 SQL Schema、比對規則檔行數上限（Step 11），不讓假綠燈過關。

---

## 三、治理前後硬數據對比（As-Is vs To-Be）

| 工程健康度指標 | 治理前（As-Is） | 治理後（To-Be） | 實質成果 | 數據來源與物理驗證方法 |
| :--- | :---: | :---: | :--- | :--- |
| **核心分區型別覆蓋率** | **39.3%** | **92.1% → 99.0%**（Auth/RBAC **100%**） | 消除容器內掃描 0 檔盲區 | 由 `scripts/backend_type_health.py` 宿主機與容器雙向實測掃描產出 |
| **AI 規則檔體積（`.jules/*.md`）** | **558 行**（含幻覺日期） | **86 行**（6 份檔案） | ⬇️ **精簡 84.6%** | 由 `scripts/phase_audit.py` Step 11 行數統計與門禁腳本自動驗證 |
| **碎片化 SQL Migration** | **36 支檔案** | **11 支語義化檔案** | 依外鍵順序整併，零冗餘 DDL | 依 `07-24` 自動化收斂腳本輸出與 `migration/` 目錄實體盤點 |
| **舊式 `_query()` 閉包殘留** | **83 支檔案** | **0 支** | 100% 收斂至 `BaseRepository` | 依 `07-30` 全域靜態掃描與 L2 架構 DRY 審計結果 |
| **自動化測試與形式化證明** | 612 項（偶發環境污染） | **828+ 項測試 + 18 項 Lean 4 證明** | 嚴格隔離沙盒，全綠通過 | 由 `make test-be` 與 `make audit-qa`（ARM64 Lean 4 工具鏈）實測通過 |

---

## 四、實戰 Q&A 與具體改善方案

### Q1：AI 常在 Service 裡寫出資料庫不存在的欄位，單元測試卻全綠，怎麼防？
* **改善方案**：
  1. **建立物理 Schema 對帳腳本**：在 CI / commit 前跑自動掃描（如 `phase_audit.py`），直接解析 `migration/*.sql` 的 `CREATE TABLE` 欄位清單，比對 Service 層 `.select(...)` / `.insert(...)` 字串，抓到不存在欄位立刻 `Exit 1`。
  2. **嚴禁測試 Mock 與回傳型別脫鉤**：修改任何 Service 方法的回傳型別（例如從 `str` 改為 `tuple`）時，強制全域搜尋並同步更新所有對應的 `mock_service.return_value`，同時在 DTO 啟用 Pydantic 嚴格校驗。
* **架構取捨**：每次增刪資料庫欄位都必須先產出 `migration/` SQL，不能在雲端 Console 偷改表結構，否則本地對帳腳本會立即阻斷。

### Q2：AI 規則檔越寫越長反而讓模型失智，該怎麼治理？
* **改善方案**：
  1. **硬性行數上限 + 自動化門禁**：把 `.jules/*.md` 壓縮至每份 ≤ 5 條核心鐵律（總計 86 行），並由 `phase_audit.py` Step 11 自動計算行數，超標直接失敗。
  2. **把「用文字勸導」改成「寫進靜態檢查」**：能用 Ruff、MyPy、AST 檢查抓出來的規範（例如禁止 `.single()`、單檔禁止 > 400 行），一律從 Prompt 規則檔移進腳本強制執行。
* **架構取捨**：前置撰寫檢查腳本需要投資工時，但從此不需靠人工 Code Review 盯低級錯誤。$BLOG3$,
    'Archon 團隊',
    '2026-11-25T15:00:00+08:00',
    'https://picsum.photos/seed/archon-quality-gate/1024/1024',
    'published',
    'Archon',
    98
),
(
    'b4000001-0000-4000-8000-000000000004',
    '漏了一個 Markdown 檔，雲端服務靜默停機 3 天！HF 單一容器踩坑實戰',
    '部署綠燈不代表服務活著。一次腳本漏打包引發的停擺，加上雲端防火牆封鎖 Telegram、同步 SDK 卡死 Event Loop 4.8 秒——這篇記錄我們如何把脆弱的雲端單一容器改造成能自癒的 24/7 基礎設施。',
    $BLOG4$# 漏了一個 Markdown 檔，雲端服務靜默停機 3 天！HF 單一容器踩坑實戰

這不是什麼高深演算法 Bug，而是一個讓人哭笑不得的運維事故：每天準時響起的 Telegram 營運早報突然消失了，而且當時檢查腳本竟然還一直亮著綠燈。

直到我們寫了一支探針直接戳雲端環境才破案：原來有人在 `Dockerfile` 加了一行 `COPY AGENTS.md`（另一次則是歸檔腳本 `cache_offline_packages.py` 移位），卻忘了同步更新 Hugging Face 的打包腳本。雲端容器就這樣卡在 `BUILD_ERROR` 靜默停擺，而本地的偽檢查還以為一切正常。

---

## 開發演進時間軸（2026年6月 ～ 10月）

| 時間節點 | 演進階段 | 解決的核心問題 |
| :--- | :--- | :--- |
| **2026-06** | HF 部署繞道與 HTTP/2 自癒 | 繞過 Git LFS 與 Secrets 非 ASCII 編碼陷阱；在 `execute_query` 加入指數退避根除斷線 |
| **2026-07** | Monolith 單一容器啟動自癒 | 修復 `deploy_to_hf.sh` 漏檔與換行粘連，加入 `sleep 5` + 5 次退避重試解決 MCP 搶跑 |
| **2026-08** | 依賴鎖定與 DNS 解耦 | 用 `uv export` 鎖定 MCP 依賴，透過 `AGENTS_SERVICE_URL=127.0.0.1` 解決單容器 DNS 解析失敗 |
| **2026-09** | Event Loop 解鎖與 Proxy 繞道 | 抓出同步呼叫阻塞 `4.8` 秒，全面改非同步；透過 Vercel Proxy 繞過防火牆並將錯誤寫入 DB |
| **2026-10** | 雙語音泡泡與 Storage 瘦身 | 實作 `24kHz` WAV 原生語音推播，加上 `14` 天 TTL 修剪釋放 `> 105MB` 過期音檔 |

---

## 一、免費單一容器裡的四個真實戰場

在 Hugging Face Spaces 這種「單一容器、單一對外埠口」的環境裡，本地開發完全不會遇到的問題會一次全冒出來：
1. **容器內進程搶跑**：同一個容器裡跑著 MCP（8051）、Agents（8052）與主服務（8181），FastAPI 啟動太快搶先連線，直接誤判 MCP 斷線。
2. **防火牆封鎖 `api.telegram.org`**：容器內直連 Telegram 永遠超時，但舊代碼沒把網路錯誤寫進資料庫，變成無聲黑洞。
3. **同步 SDK 卡死主執行緒**：`Oracle Agent` 與 `HealthService` 裡隱藏的同步呼叫，一次就阻塞 Event Loop 高達 **4.8 秒**，高併發直接 504。
4. **語音檔與雙開排程的雙重失血**：日報 `.wav` 音檔永久堆在 Storage；本機與雲端雙開或重啟時，排程時間平移甚至導致整週略過或重複執行。

## 二、破局：把「假設會通」改成「零信任自癒」

```mermaid
sequenceDiagram
    participant C as "HF 容器 (start_all.sh)"
    participant VP as "Vercel Serverless Proxy"
    participant TG as "Telegram Bot API"
    participant DB as "Supabase (LAST_RUN 鎖)"

    C->>C: "sleep 5 + 5次退避重試 (等 MCP 29 工具就緒)"
    C->>DB: "檢查 Asia/Taipei 時間閘門與 LAST_RUN_* 鎖"
    C->>VP: "優先走 Proxy 推播 (支援 24kHz WAV 語音泡泡)"
    VP->>TG: "轉發訊息 (失敗則序列化寫入重試佇列)"
```

---

## 三、基礎設施硬化前後數據對比（As-Is vs To-Be）

| 運維痛點 | 修復前（As-Is） | 修復後（To-Be） | 實測改善 | 數據來源與物理驗證方法 |
| :--- | :--- | :--- | :--- | :--- |
| **單容器啟動搶跑 & 漏檔** | MCP 誤判斷線 / `BUILD_ERROR` | `sleep 5` + 5 次重試 + 打包比對 | **29 項 MCP 工具** 200 OK 掛載 | 透過 `/api/mcp-logs` 遠端探針回傳與 `make phase-audit` Step 5 實測驗證 |
| **Event Loop 阻塞** | 同步呼叫卡死主執行緒 **4.8 秒** | 全面升級 `execute_query_async` + 資料庫索引 | 解除 504 超時，高併發穩定 | 依 `09-10 ~ 09-17` `gather_nexus_data` 耗時分析與 `test_concurrent_rag_queries` 驗證 |
| **語音檔空間膨脹** | `.wav` 永久堆積 | **14 天 TTL 自動修剪** | 單次釋放超過 **105 MB** 空間 | 依 `10-20` `prune_expired_podcast_audio(ttl_days=14)` 雲端執行清除統計 |
| **WAF 限流與雲地排程互鎖** | 寫死延遲 + 雙開重複/漏跑 | `curl_cffi` 指紋 + **60~90s 延遲** + **12 小時冷卻鎖** | 統一 `Asia/Taipei`，復原 **4 家**高潛力企業 | 依 `07-25` WAF 調整與 `10-22 ~ 10-30` `LAST_RUN_*` / 72 分門檻重算紀錄驗證 |

---

## 四、實戰 Q&A 與具體改善方案

### Q1：多服務塞進同一個單一容器（Monolith）時，怎麼根除啟動搶跑與漏檔部署失敗？
* **改善方案**：
  1. **部署前正則對帳**：在 `phase_audit.py`（Step 5.5）解析 `Dockerfile` 所有 `COPY` 路徑，自動核對打包腳本（如 `deploy_to_hf.sh`）清單，漏一個檔案就阻斷推送；並用探針真實打雲端 API 確認狀態為 `RUNNING`（非本地假綠燈）。
  2. **啟動緩衝 + 退避重試 + 環境覆蓋**：在 `start_all.sh` 加入 `sleep 5` 緩衝，Python `lifespan` 端實作 5 次指數退避重試等待子進程就緒，並透過 `ARCHON_SERVER_HOST=127.0.0.1` / `AGENTS_SERVICE_URL=http://127.0.0.1:8052` 覆蓋 Docker Compose 的跨容器 DNS 名稱。
* **架構取捨**：單容器啟動時間會多出約 5～10 秒冷啟動延遲，但能完全消除微服務搶跑斷線。

### Q2：雲端環境封鎖外部 Webhook（如 Telegram），且本機與雲端同時開機怕重複執行排程怎麼辦？
* **改善方案**：
  1. **Proxy 優先 + 失敗狀態持久化**：由 `SettingsService` 讀取 Serverless Proxy 網址（如 Vercel 轉發 `api.telegram.org`），失敗時用 `json.dumps` 連同 `parse_mode` 寫入任務重試佇列，並將異常寫入 `_log_to_db` 消除日誌盲區。
  2. **統一時區與 DB 狀態鎖**：全系統鎖定 `Asia/Taipei`，取消伺服器記憶體計時，改在資料庫寫入 `LAST_RUN_*` 與 12 小時冷卻鎖，確保本機與雲端雙開也不會重複觸發。
* **架構取捨**：所有關鍵通知與排程高度依賴資料庫鎖與 Proxy 存活，因此需搭配 `/health` 探針監控 Proxy 端點。$BLOG4$,
    'Archon 團隊',
    '2026-11-25T14:00:00+08:00',
    'https://picsum.photos/seed/archon-hf-monolith/1024/1024',
    'published',
    'Archon',
    98
),
(
    'b4000001-0000-4000-8000-000000000005',
    '為什麼我們用 Godot 4 幫 AI 系統做「數位雙生」？還自己手寫無頭測試框架！',
    '企業後台看久了都是冰冷的表格。我們用 Godot 4 把後端 Agent 變成卡牌對戰，卻在把遊戲引擎塞進 CI/CD 時撞得滿頭包——第三方測試框架太重、無頭模式看不到黑畫面死結。這篇公開我們的工程化解法。',
    $BLOG5$# 為什麼我們用 Godot 4 幫 AI 系統做「數位雙生」？還自己手寫無頭測試框架！

說實話，每天打開傳統後台看折線圖與 Token 報表，看久了真的很麻木。

為了讓整個團隊直覺感受到「每個 AI Agent 的成長與系統健康度」，我們做了一個有點瘋狂的實驗：用 **Godot 4** 打造一套「數位雙生（Digital Twin）」卡牌系統——後端真實的任務進度與經驗值，會直接變成遊戲畫面裡發光的節點、扇形手牌（`HandLayout`）與 Bezier 雷射箭頭。

好玩歸好玩，但當我們決定**「不能讓遊戲專案變成沒人敢改的技術債」**、要把 Godot 塞進跟後端一樣嚴格的 CI/CD 門禁時，現實立刻給了我們三記重拳。

---

## 開發演進時間軸（2026年6月 ～ 7月）

| 時間節點 | 演進階段 | 解決的核心問題 |
| :--- | :--- | :--- |
| **2026-06 上旬** | 捨棄 GUT 與建立卡牌 MVC | 放棄臃腫插件，自製原生 `HeadlessRunner.gd`；從塔防轉向卡牌並解耦 `GameState` 與 `MainUI` |
| **2026-06 中下旬** | 檔案減重與 GUI 截圖突破 | 強制拆分 `> 400` 行腳本，用 `preload` 取代 `class_name` 避開無頭快取錯亂，並寫 Python GUI 截圖器 |
| **2026-07 上旬** | 靜態型別硬化與消滅幽靈資料 | 100% 補齊靜態型別與縮排修復，清除 `SaveManager` 幽靈卡牌，修復 `ext_resource` 遺失崩潰 |
| **2026-07 中旬** | 高保真視覺工藝與轉場修復 | 導入透明底板卡牌、扇形手牌、`Tween` 震動回饋，並在 `TransitionVideo.tscn` 綁定 `next_scene` 消滅黑畫面 |

---

## 一、遊戲引擎進 CI/CD 的三個真實崩潰點

1. **第三方測試插件太臃腫**：一開始掛了流行的 GUT 測試框架，結果依賴龐大，在無頭環境下設定頻頻出錯，完全不符合精簡原則。
2. **動態型別的隱性炸彈**：一個 `Tab` 與 `Space` 混用、`SaveManager` 作用域丟失，甚至重構場景時不小心刪掉一行 `ext_resource`，整個 `GameBoard.tscn` 就直接解析崩潰。
3. **`--headless` 看不見的「黑畫面死結」**：無頭模式雖然能跑通邏輯，但它不渲染畫面。過場影片播完會卡死在黑畫面，純無頭測試根本發現不了！

## 二、破局：MVC 拆乾淨 + 雙軌自動公證

```mermaid
flowchart LR
    G["Godot 4 專案"] --> MVC["嚴格 MVC: GameState 與 MainUI 分離"]
    MVC --> T1["軌道 1: 原生 HeadlessRunner.gd<br/>15 項邏輯與編譯測試"]
    MVC --> T2["軌道 2: Python GUI 截圖器<br/>實體渲染與轉場動畫公證"]
    T1 & T2 --> CLEAN["測試前強制清除 user://savegame.save"]
```

1. **砍掉重插件，自製原生 `HeadlessRunner.gd`**：徹底解耦 `GameState`（Model）與 `MainUI`（View）後，我們直接用 Godot 原生 `--headless` 跑通編譯檢查與 **15 項單元/E2E 測試**，零外部依賴。
2. **用 100% 靜態型別鎖死 GDScript**：落實 `godot-4-audit` 規範，補齊靜態型別宣告、改用 `preload` 避開無頭 `class_name` 快取陷阱，並同步清理硬編碼的幽靈卡牌資料。
3. **突破無頭盲區的 GUI 截圖器**：既然 `--headless` 看不到畫面，就寫一支 Python 腳本自動啟動 GUI 視窗、等待 `MainMenu_Screenshotter.gd` 的動畫延遲與授權配樂就緒後實體截圖，並在 `TransitionVideo.tscn` 顯式綁定 `next_scene` 根除黑畫面死結。

---

## 三、改造前後品質門禁對比（As-Is vs To-Be）

| 驗證面向 | 改造前（早期原型） | 改造後（工程化數位雙生） | 物理公證方法與工具 |
| :--- | :--- | :--- | :--- |
| **測試架構** | 依賴臃腫 GUT 插件，無頭常報錯 | **原生 `HeadlessRunner.gd`** | 執行 `godot --headless -s tests/HeadlessRunner.gd` 實測通過 **15 項核心測試** |
| **GDScript 穩定度** | 動態型別，屢爆 Parse Error | **100% 靜態型別 + `preload`** | 執行 `godot --headless --build-solutions` 達成零編譯錯誤 |
| **測試環境純淨度** | 殘留存檔引發偶發幽靈失敗 | **測試前自動清空 `savegame.save`** | 每次執行前由腳本刪除 `user://savegame.save` 確保 100% 乾淨起始態 |
| **視覺與轉場驗收** | 依賴肉眼點按，偶發黑畫面 | **GUI 自動截圖 + `next_scene` 綁定** | 由 Python GUI 截圖器 + `MainMenu_Screenshotter.gd` 產出 `gem_*.png` 實體截圖驗證 |

---

## 四、實戰 Q&A 與具體改善方案

### Q1：Godot `--headless` 模式下 `class_name` 常找不到類別、測試又容易被舊存檔污染，怎麼修？
* **改善方案**：
  1. **用 `preload()` 取代無頭模式下的 `class_name` 依賴**：因為 `--headless` 常跳過編輯器級的 ClassDB 快取刷新，核心邏輯改用明確的 `const MyClass = preload("res://...")` 載入，同時強制補齊 GDScript 靜態型別，讓 `--build-solutions` 在編譯期就攔截型別與縮排錯誤。
  2. **測試前置清檔**：在執行 `HeadlessRunner.gd` 前，先以腳本物理刪除 `user://savegame.save`，杜絕上次測試殘留狀態導致的假失敗。
* **架構取捨**：`preload` 需要明確維護檔案路徑，重構目錄時須同步調整路徑字串，但能換取無頭 CI 100% 可重現性。

### Q2：無頭模式不渲染畫面，怎麼用自動化抓出「黑畫面死結」或 UI 破圖？
* **改善方案**：
  1. **雙軌分離**：純邏輯進 `GameState`（由無頭腳本跑 15 項測試）；畫面呈現與轉場交給 Python 腳本自動拉起實體 GUI 視窗，等待 `Tween` 動畫延遲後呼叫 `MainMenu_Screenshotter.gd` 擷取 Viewport 實體截圖進行視覺公證。
  2. **轉場顯式綁定**：所有影片或過場節點（如 `TransitionVideo.tscn`）強制綁定 `next_scene` 屬性，並用截圖驗證影片結束後確實進入主畫面。
* **架構取捨**：GUI 截圖軌道需要在有顯示環境（或虛擬顯示 Xvfb）的節點執行，適合放在發版前驗證而非每次存檔觸發。$BLOG5$,
    'Archon 團隊',
    '2026-11-25T13:00:00+08:00',
    'https://picsum.photos/seed/archon-godot-twin/1024/1024',
    'published',
    'Archon',
    98
)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    excerpt = EXCLUDED.excerpt,
    content = EXCLUDED.content,
    author_name = EXCLUDED.author_name,
    publish_date = EXCLUDED.publish_date,
    image_url = EXCLUDED.image_url,
    status = EXCLUDED.status,
    target_brand = EXCLUDED.target_brand,
    ai_score = EXCLUDED.ai_score,
    updated_at = NOW();

INSERT INTO public.schema_migrations (version)
VALUES ('20261125_seed_ch4_engineering_blogs')
ON CONFLICT (version) DO NOTHING;

COMMIT;
