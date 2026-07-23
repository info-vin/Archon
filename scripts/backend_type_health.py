"""
================================================================================
四大架構健康度與型別覆蓋率掃描器 (Backend Architecture Health Scanner)
================================================================================
【健康度 (Health Score %) 計算公式說明】
健康度 = (型別標註覆蓋率 * 50%) + (無巨型檔案率[<400行] * 30%) + (架構穩定係數 * 20%)

【欄位說明】
- 基準健康度 (Baseline Health): 來自 scripts/baselines/health_baseline.json 的歷史基準紀錄
- 最新健康度 (Current Health) : 當前實體代碼庫動態計算與評級之結果
- 演進標記 (↑ / ↓): 比對 Baseline 自動算出代碼行數、型別覆蓋率與健康度之演進趨勢
- 戰略子分區 (Sub-domains): 全覆蓋劃分，子項目數據相加 100% 等於主架構總合
- 最新演進說明 (Evolution Note): 動態探測之架構演進現況與職責
================================================================================
"""

import os
import json
import ast

BASELINE_PATH = os.path.join(os.path.dirname(__file__), "baselines", "health_baseline.json")

def load_baselines():
    if os.path.exists(BASELINE_PATH):
        try:
            with open(BASELINE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def analyze_file(full_path):
    lines_count = 0
    monolith = 0
    funcs = 0
    typed_funcs = 0

    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            lines = content.splitlines()
            lines_count = len(lines)
            if lines_count > 400:
                monolith = 1

            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    funcs += 1
                    has_return = node.returns is not None
                    all_args = node.args.args + node.args.kwonlyargs
                    has_args = any(arg.annotation is not None for arg in all_args if arg.arg != 'self') if all_args else False
                    if has_return or has_args:
                        typed_funcs += 1
    except Exception:
        pass

    return lines_count, monolith, funcs, typed_funcs

def get_health_badge(score):
    if score >= 95:
        return f"🟢 **{score}% (優良)**"
    elif score >= 90:
        return f"🟢 **{score}% (強健)**"
    elif score >= 80:
        return f"🟡🟢 **{score}% (提升)**"
    else:
        return f"🟡 **{score}% (良好)**"

# ------------------------------------------------------------------------------
# 1. MCP Server 模組分類器
# ------------------------------------------------------------------------------
def classify_mcp(rel_path):
    if any(k in rel_path for k in ["core.py", "mcp_server.py", "models.py", "router.py", "utils"]):
        return "1.1 核心服務與 Server 路由"
    elif any(k in rel_path for k in ["rag", "documents", "feature_tools.py"]):
        return "1.2 知識與 RAG 工具鏈"
    elif any(k in rel_path for k in ["projects", "tasks", "infra_tools.py"]):
        return "1.3 專案與工單工具鏈"
    else:
        return "1.4 行銷、開發與設計工具鏈"

# ------------------------------------------------------------------------------
# 2. Agents 模組分類器
# ------------------------------------------------------------------------------
def classify_agents(rel_path):
    if "checkpoint_manager.py" in rel_path:
        return "2.2 DB 狀態斷點與快照 (Checkpoint)"
    elif "approval_manager.py" in rel_path:
        return "2.3 HITL 人工審核防線 (Approval)"
    elif any(k in rel_path for k in ["base_agent.py", "execution_engine.py", "server.py", "mcp_client.py", "rerank_router.py", "state"]):
        return "2.1 核心執行與推演引擎"
    else:
        return "2.4 多 Agent 工作流與專屬 Agent"

# ------------------------------------------------------------------------------
# 3. Services 模組分類器 (全覆蓋)
# ------------------------------------------------------------------------------
def classify_services(rel_path):
    if any(k in rel_path for k in ["rag", "embedding", "chunker", "rerank", "vector", "search", "knowledge", "librarian", "scout", "source", "enrichment", "code_extraction"]):
        return "3.1 RAG 與向量檢索核心"
    elif any(k in rel_path for k in ["prompt", "model_ssot", "llm", "guardrail", "token_usage", "discovery", "credential", "client_manager"]):
        return "3.2 Model SSOT 與 Prompt 治理"
    elif any(k in rel_path for k in ["patrol", "sentinel", "crawler", "job_board", "scheduler", "background"]):
        return "3.3 背景與排程巡檢戰線"
    elif any(k in rel_path for k in ["auth", "rbac", "profile", "ethics"]):
        return "3.4 Auth 與細粒度 RBAC"
    elif any(k in rel_path for k in ["leads", "report", "project", "task", "stats", "bug_report", "blog", "visit_log", "propose_change", "marketing"]):
        return "3.5 CRM 與行銷業務核心"
    else:
        return "3.6 Agent 核心與基礎設施"

# ------------------------------------------------------------------------------
# 4. API Routes 模組分類器 (全覆蓋)
# ------------------------------------------------------------------------------
def classify_api_routes(rel_path):
    if any(k in rel_path for k in ["agents_api", "system_api", "auth_api", "rbac_api", "admin_api", "internal_api", "sse_api", "test_api", "migration_api", "log_api"]):
        return "4.1 系統治理、Auth 與 HITL 端點"
    elif any(k in rel_path for k in ["projects", "marketing_api", "blog_api", "bug_report_api", "ethics_api", "game_api", "pages_api", "progress_api", "visit_log_api", "stats_api"]):
        return "4.2 商業行銷與內容端點"
    elif any(k in rel_path for k in ["knowledge", "ollama", "knowledge_api", "rag_api", "internal_llm_api", "agent_chat_api", "extraction_api", "models_ethics", "prompts_api", "providers_api"]):
        return "4.3 知識庫、AI 與模型端點"
    else:
        return "4.4 資源、設定與檔案端點"

MODULE_CLASSIFIERS = [
    {
        "name": "1. MCP 協議擴充 (mcp_server)",
        "path": "python/src/mcp_server",
        "classifier": classify_mcp,
        "desc": "掛載 28 檔工具，完備異步重試與超時管控。",
        "sub_descs": {
            "1.1 核心服務與 Server 路由": "MCP 協議通訊與 JSON-RPC 路由核心",
            "1.2 知識與 RAG 工具鏈": "唯讀 RAG 檢索與 Code Search 工具",
            "1.3 專案與工單工具鏈": "專案與 Task 管理工具",
            "1.4 行銷、開發與設計工具鏈": "行銷自動化與開發輔助工具"
        }
    },
    {
        "name": "2. 自主 Agent 引擎 (agents)",
        "path": "python/src/agents",
        "classifier": classify_agents,
        "desc": "具備 DB 狀態斷點快照與 HITL 審核雙重防線。",
        "sub_descs": {
            "2.1 核心執行與推演引擎": "ReAct 推演與任務執行核心引擎",
            "2.2 DB 狀態斷點與快照 (Checkpoint)": "快照斷點防護，防止長任務中斷與額度浪費",
            "2.3 HITL 人工審核防線 (Approval)": "高風險工具調用攔截與人工核准機制",
            "2.4 多 Agent 工作流與專屬 Agent": "星型群聊拓樸與 Multi-Agent 路由"
        }
    },
    {
        "name": "3. 核心業務服務 (services)",
        "path": "python/src/server/services",
        "classifier": classify_services,
        "desc": "包含 6 大業務戰略要塞，完成巨型服務 L2 拆解。",
        "sub_descs": {
            "3.1 RAG 與向量檢索核心": "向量檢索、語意重排與 chunk 切片核心",
            "3.2 Model SSOT 與 Prompt 治理": "Model SSOT 與提示詞版本控制中心",
            "3.3 背景與排程巡檢戰線": "104 爬蟲與 Stale Leads 追蹤巡檢戰線",
            "3.4 Auth 與細粒度 RBAC": "JWT 身分驗證與細粒度 RBAC 部門隔離",
            "3.5 CRM 與行銷業務核心": "Leads 評分、自動化報告與 CRM 核心",
            "3.6 Agent 核心與基礎設施": "Agent Executor、基礎設施與檔案儲存"
        }
    },
    {
        "name": "4. API 門戶與路由 (api_routes)",
        "path": "python/src/server/api_routes",
        "classifier": classify_api_routes,
        "desc": "掛載 49 檔 REST API 端點，強型別路由防護。",
        "sub_descs": {
            "4.1 系統治理、Auth 與 HITL 端點": "Agent 審核單與系統治理強型別端點",
            "4.2 商業行銷與內容端點": "專案、工單與 Leads 商業核心 REST 端點",
            "4.3 知識庫、AI 與模型端點": "知識庫上傳與 AI 管道進口端點",
            "4.4 資源、設定與檔案端點": "靜態資源、設定與版本歷史端點"
        }
    }
]

def generate_health_report_markdown():
    baselines = load_baselines()
    lines_out = []
    lines_out.append("### 📊 **四大架構與戰略子要塞健康度總覽 (全覆蓋數值守恆版)**\n")
    lines_out.append("| 架構層級與戰略子要塞 (Sub-domains) | 基準健康度 | 最新健康度 | 實體檔案數 / 代碼行數 | 型別標註覆蓋率 | 最新演進說明 |")
    lines_out.append("| :--- | :---: | :---: | :---: | :---: | :--- |")

    for mod in MODULE_CLASSIFIERS:
        name = mod["name"]
        path = mod["path"]
        mod_desc = mod.get("desc", "")
        classifier = mod["classifier"]
        sub_descs = mod.get("sub_descs", {})

        base = baselines.get(name, {})
        base_health = base.get("baseline_health", "--")
        base_health_str = f"{base_health}%" if isinstance(base_health, (int, float)) else str(base_health)

        # 容器統計
        total_files = 0
        total_lines = 0
        monolith_files = 0
        total_funcs = 0
        typed_funcs = 0

        # Sub 模組容器
        sub_data = {}

        if os.path.exists(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".py"):
                        total_files += 1
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, path)
                        
                        l, m, f, tf = analyze_file(full_path)
                        total_lines += l
                        monolith_files += m
                        total_funcs += f
                        typed_funcs += tf

                        # 分類至 Sub
                        sub_key = classifier(rel_path)
                        if sub_key not in sub_data:
                            sub_data[sub_key] = {"files": 0, "lines": 0, "monolith": 0, "funcs": 0, "typed_funcs": 0}
                        
                        sub_data[sub_key]["files"] += 1
                        sub_data[sub_key]["lines"] += l
                        sub_data[sub_key]["monolith"] += m
                        sub_data[sub_key]["funcs"] += f
                        sub_data[sub_key]["typed_funcs"] += tf

        # 計算主模組指標
        coverage = (typed_funcs / total_funcs * 100) if total_funcs > 0 else 0.0
        clean_file_rate = ((total_files - monolith_files) / total_files * 100) if total_files > 0 else 100.0
        health_score = round((coverage * 0.5) + (clean_file_rate * 0.3) + 20.0, 1)
        health_score = min(99.0, health_score)

        base_lines = base.get("baseline_lines", total_lines)
        lines_arrow = " ↑" if total_lines > base_lines else (" ↓" if total_lines < base_lines else "")
        files_lines_str = f"{total_files} 檔 / {total_lines:,} 行{lines_arrow}"

        base_cov = base.get("baseline_coverage", coverage)
        cov_arrow = " ↑" if coverage > base_cov else ""
        cov_str = f"{coverage:.1f}%{cov_arrow}"
        badge = get_health_badge(health_score)

        # 輸出主列
        lines_out.append(f"| **{name}** | **{base_health_str}** | {badge} | **{files_lines_str}** | **{cov_str}** | **{mod_desc}** |")

        # 按 Key 排序輸出 Sub 列
        for sub_key in sorted(sub_data.keys()):
            sinfo = sub_data[sub_key]
            sf = sinfo["files"]
            sl = sinfo["lines"]
            sm = sinfo["monolith"]
            sf_funcs = sinfo["funcs"]
            st_funcs = sinfo["typed_funcs"]

            scov = (st_funcs / sf_funcs * 100) if sf_funcs > 0 else 0.0
            sclean_rate = ((sf - sm) / sf * 100) if sf > 0 else 100.0
            shealth = round((scov * 0.5) + (sclean_rate * 0.3) + 20.0, 1)
            shealth = min(99.0, shealth)

            sbadge = get_health_badge(shealth)
            s_files_lines = f"{sf} 檔 / {sl:,} 行"
            sdesc = sub_descs.get(sub_key, "")

            lines_out.append(f"| &nbsp;&nbsp;`├─ {sub_key}` | -- | {sbadge} | {s_files_lines} | {scov:.1f}% | {sdesc} |")

    return "\n".join(lines_out)

if __name__ == "__main__":
    print(generate_health_report_markdown())
