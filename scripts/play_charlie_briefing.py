import asyncio
import os
import sys

# 將 src 設為 PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'python'))

from dotenv import load_dotenv
load_dotenv("python/.env") # 舊環境變數可能在這
load_dotenv(".env") # 確保讀到最新的

async def play_charlie_briefing():
    print("📡 啟動 Agent，根據 Nexus 數據動態生成講稿中 (LLM Translation)...")
    
    # 模擬今天 Manager Nexus 抓到的數據
    mock_dashboard_data = {
        "staleLeads": 3,
        "pendingApprovals": 5,
        "activeForce": "optimal",
        "sla_reliability": 92
    }
    
    # 直接使用我們剛寫好的內部 Service (繞過 API Auth 限制，方便 CLI 測試)
    from src.server.config.model_ssot import SYSTEM_MODELS
    from src.server.services.credential_service import credential_service
    from src.server.services.prompt_service import prompt_service
    from src.server.services.text_to_speech_service import text_to_speech_service
    import json
    from google import genai
    
    # 1. 取得提示詞範本
    template = prompt_service.get_prompt("tts_commander_briefing") or "{text}"
    
    # 2. 啟動 Gemini 進行語義化轉譯
    api_key = await credential_service.get_credential("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    model_name = SYSTEM_MODELS.get("DEFAULT_TEXT", "models/gemini-3.1-flash-lite-preview").split("/")[-1]
    
    system_instruction = (
        "You are a Senior Chief of Staff translating dashboard JSON data into a fluent, "
        "natural spoken briefing script. Read the provided prompt template to understand "
        "the voice style and instructions. Must output in Traditional Chinese."
    )
    
    prompt = (
        f"=== Prompt Template ===\n{template}\n\n"
        f"=== Dashboard Data ===\n{json.dumps(mock_dashboard_data, ensure_ascii=False)}\n\n"
        "Task: Generate the final spoken script based ONLY on the dashboard data provided, "
        "adhering strictly to the style requested in the template. Output the raw text ready for TTS."
    )
    
    response = await client.aio.models.generate_content(
        model=model_name,
        contents=prompt,
        config={"system_instruction": system_instruction}
    )
    
    final_text = response.text
    print(f"\n📝 Agent 生成的動態劇本:\n{final_text}\n")
    print("🎙️ 正在送往 TTS 模型發聲 (Voice: Charon)...")
    
    # 3. 生成語音
    success, result = await text_to_speech_service.generate_audio(final_text, voice_name="Charon")
    
    if success:
        output_file = "../temp_refactor/charlie_briefing.wav"
        with open(output_file, 'wb') as f:
            f.write(result)
        print(f"✅ 成功！音檔已儲存至 {output_file}")
        print("🎵 正在為您播放...")
        os.system(f"afplay {output_file}")
    else:
        print(f"❌ 生成失敗: {result}")

if __name__ == "__main__":
    asyncio.run(play_charlie_briefing())