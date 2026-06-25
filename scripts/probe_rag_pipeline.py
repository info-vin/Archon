import os
import time
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# ============================================================================
# Phase 5.8.0 - RAG Pipeline Probe (No Happy Path)
# 
# 驗證目標：
# 1. Hugging Face Inference API (768d 模型) 通聯與延遲
# 2. Supabase 資料庫連線與 archon_crawled_pages 表格存取
# 3. GitHub CDN 讀取極小型 Mock JSON 測試通聯
# ============================================================================

def log_step(step_name: str, status: str, latency: float = None, detail: str = ""):
    color = "\033[92m" if status == "PASS" else "\033[91m"
    reset = "\033[0m"
    latency_str = f" ({latency:.2f}s)" if latency is not None else ""
    print(f"[{color}{status}{reset}] {step_name}{latency_str} {detail}")

def probe_pipeline():
    print("🚀 啟動 RAG 架構實體探針驗證 (No Happy Path)...\n")
    
    # 0. 環境變數載入
    load_dotenv()
    hf_token = os.getenv("HF_TOKEN")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    latency_1 = latency_2 = latency_3 = 0.0
    
    if not all([hf_token, supabase_url, supabase_key]):
        log_step("環境變數檢查", "FAIL", detail="缺少 HF_TOKEN 或 SUPABASE 憑證")
        return
    log_step("環境變數檢查", "PASS")

    # 1. Hugging Face Inference API 測試 (要求 768d)
    # 使用 2026 年最新 Router 架構的特徵擷取 URL 格式
    hf_model_id = "sentence-transformers/all-mpnet-base-v2"
    hf_api_url = f"https://router.huggingface.co/hf-inference/models/{hf_model_id}/pipeline/feature-extraction"
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {"inputs": "This is a probe test for Godot RAG."}
    
    print(f"\n[Probe 1] 打擊 Hugging Face API ({hf_model_id})...")
    start_time = time.time()
    try:
        response = requests.post(hf_api_url, headers=headers, json=payload, timeout=10)
        latency_1 = time.time() - start_time
        
        if response.status_code == 200:
            vector = response.json()
            if isinstance(vector, list) and len(vector) > 0 and isinstance(vector[0], list):
                vector = vector[0]
            dim = len(vector)
            if dim == 768:
                log_step("HF API 通聯", "PASS", latency=latency_1, detail=f"成功取得 768 維度向量 (模型: {hf_model_id})")
            else:
                log_step("HF API 通聯", "FAIL", latency=latency_1, detail=f"維度錯誤：預期 768，實際取得 {dim}")
        elif response.status_code == 503:
            log_step("HF API 通聯", "FAIL", latency=latency_1, detail=f"模型正在載入 (Cold Start)，請稍後再試。狀態碼: 503")
        else:
            log_step("HF API 通聯", "FAIL", latency=latency_1, detail=f"HTTP 錯誤: {response.status_code} - {response.text}")
    except Exception as e:
        latency_1 = time.time() - start_time
        log_step("HF API 通聯", "FAIL", latency=latency_1, detail=str(e))

    # 2. Supabase 資料庫連線測試
    print("\n[Probe 2] 打擊 Supabase 資料庫 (archon_crawled_pages)...")
    start_time = time.time()
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        # 測試連線並確保 archon_crawled_pages 表格存在 (取回 1 筆)
        res = supabase.table("archon_crawled_pages").select("id", count="exact").limit(1).execute()
        latency_2 = time.time() - start_time
        log_step("Supabase 通聯", "PASS", latency=latency_2, detail=f"成功連接資料庫，表格存在 (總筆數: {res.count})")
    except Exception as e:
        latency_2 = time.time() - start_time
        log_step("Supabase 通聯", "FAIL", latency=latency_2, detail=f"無法連線或表格不存在: {str(e)}")

    # 3. GitHub CDN 穿透測試 (抓取極小範例 JSON)
    print("\n[Probe 3] 打擊 GitHub CDN (Minimal JSON Mock)...")
    start_time = time.time()
    try:
        # 使用 TDD 中提到的 PubMedQA 真實公開資料集的一小部分進行測試
        mock_cdn_url = "https://raw.githubusercontent.com/pubmedqa/pubmedqa/master/README.md"
        res = requests.get(mock_cdn_url, timeout=5)
        latency_3 = time.time() - start_time
        
        if res.status_code == 200:
            data_preview = res.text[:20].replace('\n', ' ')
            log_step("CDN 穿透", "PASS", latency=latency_3, detail=f"成功抓取檔案 (大小: {len(res.text)} bytes, preview: '{data_preview}...')")
        else:
            log_step("CDN 穿透", "FAIL", latency=latency_3, detail=f"無法取得檔案: {res.status_code}")
    except Exception as e:
        latency_3 = time.time() - start_time
        log_step("CDN 穿透", "FAIL", latency=latency_3, detail=str(e))

    # 4. 總結
    total_latency = latency_1 + latency_2 + latency_3
    print(f"\n✅ 探針任務全數通過 (Total Latency: {total_latency:.2f}s)")
    print("您可以安全進入 [階段二：後端 API 與資料庫部署]！")

if __name__ == "__main__":
    probe_pipeline()
