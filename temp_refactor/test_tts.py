import os
import asyncio
import wave
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 從根目錄載入環境變數
load_dotenv(".env")

async def main():
    # 根據測試結果，GEMINI_API_KEY 已過期，因此我們強制優先使用有效的 GOOGLE_API_KEY
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ 錯誤: 找不到有效的 GOOGLE_API_KEY，請確認 .env 檔案設定。")
        return
        
    client = genai.Client(api_key=api_key)
    
    print(f"🔑 使用的金鑰末五碼: ***{api_key[-5:]}")
    
    # 測試的劇本文案與導演標籤
    text = "[excited] Welcome to Archon! [normal] This is a test of the Gemini Text-to-Speech preview model."
    prompt = text
    
    print(f"🎙️ 正在傳送語音生成請求至 Gemini TTS...")
    print(f"📜 劇本內容:\n{prompt}\n")
    
    try:
        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Puck"
                    )
                )
            )
        )
        
        response = await client.aio.models.generate_content(
            model="models/gemini-3.1-flash-tts-preview",
            contents=prompt,
            config=config
        )
        
        if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
            print("❌ 錯誤: 模型未回傳任何內容。")
            return
            
        output_path = "temp_refactor/test_output.wav"
        
        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(1)          # Mono
            wf.setsampwidth(2)          # 16-bit (2 bytes)
            wf.setframerate(24000)      # 24kHz
            
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    wf.writeframes(part.inline_data.data)
                    
        print(f"✅ 成功! 語音檔已儲存至: {output_path}")
        print(f"🎵 您可以透過 macOS 內建指令播放: afplay {output_path}")
        
    except Exception as e:
        print(f"❌ API 錯誤: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
