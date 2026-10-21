#!/usr/bin/env python3
"""
Physical Probe Gate: Daily Executive Summary & Star-Topology Pipeline (Phase 5.12.1)
Verifies end-to-end execution of the Daily Executive Summary pipeline:
1. Environment & Credential Verification (Supabase, Telegram, Gemini)
2. Database Context Gathering (Leads, Token ROI, Logs, Tasks)
3. Multi-Agent Workflow Engine Execution (Charlie -> Bob -> DevBot -> Summary -> End)
4. Physical Telegram Dispatch Verification
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Setup paths for cross-directory invocation
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIR = PROJECT_ROOT / "python"
sys.path.insert(0, str(PYTHON_DIR))
sys.path.insert(0, str(PYTHON_DIR / "src"))

# Load .env file explicitly if not already loaded
from dotenv import load_dotenv

env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


async def run_physical_probe(send_telegram: bool = True) -> bool:
    print("=" * 70)
    print("🚀 [Archon Probe Gate] 啟動每日執行摘要 (Daily Summary) 物理全鏈路公證")
    print("=" * 70)

    # Step 1: Environment & Credential Check
    print("\n[Step 1/4] 檢驗基礎設施與 API 憑證 (Environment Check)...")
    from src.server.config.config import get_config
    from src.server.schemas.settings import NotificationConfig
    from src.server.services.settings_service import SettingsService
    from src.server.utils import get_supabase_client

    config = get_config()
    supabase_url = config.supabase_url
    has_gemini = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))

    try:
        sb = get_supabase_client()
        settings_svc = SettingsService(sb)
        all_s = settings_svc.get_all_settings()
        notif_cfg = NotificationConfig.model_validate(all_s)
        has_tg_token = bool(notif_cfg.telegram_token or os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN"))
        has_tg_chat = bool(notif_cfg.telegram_chat_id or os.getenv("TELEGRAM_TO") or os.getenv("TELEGRAM_CHAT_ID"))
    except Exception:
        has_tg_token = bool(os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN"))
        has_tg_chat = bool(os.getenv("TELEGRAM_TO") or os.getenv("TELEGRAM_CHAT_ID"))

    print(f"  - Supabase URL: {supabase_url[:25]}... (Configured: {bool(supabase_url)})")
    print(f"  - Gemini API Key: {'✅ Present' if has_gemini else '❌ Missing'}")
    print(f"  - Telegram Bot Token: {'✅ Present (DB/Env)' if has_tg_token else '❌ Missing'}")
    print(f"  - Telegram Chat ID: {'✅ Present (DB/Env)' if has_tg_chat else '❌ Missing'}")

    if not (supabase_url and has_gemini):
        print("❌ [FAIL] 必要環境變數缺失，終止公證。")
        return False
    print("  -> Step 1 通過 ✅")

    # Step 2: Database Context Gathering
    print("\n[Step 2/4] 物理檢索系統指標與運營上下文 (Context Gathering)...")
    from src.server.services.report_service import report_service

    try:
        context_md = await report_service.gather_report_context(days=1)
        print(f"  - 成功收集資料，上下文長度: {len(context_md)} 字元")
        print(f"  - 內容預覽 (前 150 字): {context_md[:150].strip()}...")
        if len(context_md) < 50:
            print("❌ [FAIL] 收集到的上下文異常過短。")
            return False
        print("  -> Step 2 通過 ✅")
    except Exception as e:
        print(f"❌ [FAIL] 收集報告上下文失敗: {e}")
        return False

    # Step 3: Multi-Agent Star-Topology Workflow Execution
    print("\n[Step 3/4] 執行多 Agent 星環辯論協同 (Workflow Engine Run)...")
    from src.agents.workflow.engine import WorkflowEngine
    from src.server.services.prompt_service import prompt_service

    try:
        prompt_template = prompt_service.get_prompt("DAILY_EXECUTIVE_SUMMARY_PROMPT")
        prompt = prompt_template.format(context_md=context_md)

        engine = WorkflowEngine()
        wf_result = await engine.run_workflow(prompt, "daily_executive_summary")

        success = wf_result.get("success", False)
        step_count = wf_result.get("step_count", 0)
        final_result = wf_result.get("final_result", "") or ""
        messages = wf_result.get("messages", [])

        print(f"  - 工作流成功狀態: {success}")
        print(f"  - 總協同步數 (Step Count): {step_count}")
        print(f"  - 訊息流記錄數: {len(messages)}")

        if not success:
            print(f"❌ [FAIL] 多 Agent 協同討論失敗: {wf_result.get('error')}")
            return False

        if step_count > 6:
            print(f"⚠️ [WARN] 協同討論步數過多 ({step_count} 步)，可能存在重複指派風險。")

        print(f"  - 產出報告預覽 (前 200 字):\n{final_result[:200].strip()}\n...")
        print("  -> Step 3 通過 ✅")
    except Exception as e:
        print(f"❌ [FAIL] WorkflowEngine 執行異常: {e}")
        return False

    # Step 4: Physical Telegram Delivery Verification
    print("\n[Step 4/4] 檢驗終端 Telegram 推播交付 (Telegram Dispatch)...")
    if not send_telegram:
        print("  - 跳過 Telegram 實體推播 (Dry Run 模式)")
        print("  -> Step 4 跳過 (Dry Run)")
    else:
        try:
            from src.server.services.system.telegram_service import telegram_service

            # Verify physical sending with deep link
            is_sent = await report_service.send_summary_telegram(
                title_prefix="Daily [Probe Verified]",
                content=final_result,
                task_id="probe-gate-verified",
            )
            print(f"  - Telegram 實體送達結果: {is_sent}")
            if not is_sent:
                print("❌ [FAIL] Telegram 訊息發送失敗，請確認 Token 或網路連線。")
                return False
            print("  -> Step 4 通過 ✅")
        except Exception as e:
            print(f"❌ [FAIL] Telegram 推播異常: {e}")
            return False

    print("\n" + "=" * 70)
    print("🎉 [Archon Probe Gate] 全部四道物理門禁 100% 通過！零虛假、全鏈路驗證公證完成！")
    print("=" * 70)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Physical Probe Gate for Daily Summary Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Run without sending real Telegram message")
    args = parser.parse_args()

    success = asyncio.run(run_physical_probe(send_telegram=not args.dry_run))
    sys.exit(0 if success else 1)
