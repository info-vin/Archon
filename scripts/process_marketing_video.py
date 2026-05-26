import argparse
import os
import shutil
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description="Process recorded WebM video into MP4 format for marketing.")
    parser.add_argument("--video", required=True, help="Path to the recorded webm video file")
    parser.add_argument("--scenario", default="marketing_demo", help="Name of the scenario for output file prefix")
    args = parser.parse_args()
    
    webm_path = args.video
    if not os.path.exists(webm_path):
        print(f"❌ Input video path does not exist: {webm_path}")
        sys.exit(1)
        
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'enduser-ui-fe', 'public', 'assets', 'videos', 'auto_demos'))
    os.makedirs(output_dir, exist_ok=True)
    
    # Use scenario name for file prefix (replace '_chat' with '_demo' for backward compatibility or just use scenario name)
    prefix = args.scenario.replace('_chat', '_demo') if args.scenario == 'marketing_chat' else args.scenario
    
    mp4_target = os.path.join(output_dir, f"{prefix}.mp4")
    webm_target = os.path.join(output_dir, f"{prefix}.webm")
    
    # 1. Convert WebM to MP4 using FFmpeg if available
    ffmpeg_available = shutil.which("ffmpeg") is not None
    
    if ffmpeg_available:
        print(f"🎬 FFmpeg detected! Converting {webm_path} to {mp4_target}...")
        try:
            # Run ffmpeg with settings that ensure compatibility
            subprocess.run([
                "ffmpeg", "-y", "-i", webm_path, 
                "-c:v", "libx264", "-pix_fmt", "yuv420p", 
                "-preset", "fast", "-crf", "23", mp4_target
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"🎉 Success! Converted video saved to: {mp4_target}")
        except Exception as e:
            print(f"⚠️ FFmpeg conversion failed: {e}. Falling back to copy...")
            shutil.copy(webm_path, webm_target)
            print(f"📂 Copied raw WebM to: {webm_target}")
    else:
        print("⚠️ FFmpeg NOT found in system path! Falling back to raw WebM copy...")
        shutil.copy(webm_path, webm_target)
        print(f"📂 Copied raw WebM to: {webm_target}")
        
    # 2. Write companion metadata text file
    txt_target = os.path.join(output_dir, f"{prefix}.txt")
    print(f"✍️ Writing metadata description to: {txt_target}...")
    
    if args.scenario == "marketing_chat":
        metadata_content = (
            "【人機協作系統操作展示：多 Agent 星環群聊】\n\n"
            "本影片展示了 Archon 人機協作工作流的實機運行過程：\n"
            "1. David Howard (Admin) 登入系統並開啟「New Task」對話框建立行銷分析任務。\n"
            "2. 將任務指派給 Supervisor Agent (f0f00000-0000-0000-0000-000000000000)。\n"
            "3. Supervisor 接收任務後，在星環群聊 (WhatsApp 風格) 中，自動召集並調度 DevBot 與 MarketBot 協作。\n"
            "4. DevBot 進行數據提取與系統日誌檢查，MarketBot 進行 Q2 漏斗數據行銷分析，多方 AI 角色在統一的對話框中實體化交談，最終產出整合行銷報告。\n"
            "此功能是 Archon 核心的「多 Agent 星環拓樸工作流」的物理體現，完全免除人工溝通斷層，實現 AI 協同開發與分析的閉環。"
        )
    else:
        metadata_content = (
            f"【自動化驗證展示：{prefix}】\n\n"
            f"本影片展示了系統 {prefix} 場景的實機自動化驗證過程，"
            "作為 E2E MBT 測試的視覺公證證據。"
        )
    
    with open(txt_target, "w", encoding="utf-8") as f:
        f.write(metadata_content)
        
    # 3. Clean up the temp recording files
    temp_dir = os.path.dirname(webm_path)
    print(f"♻️ Cleaning up temporary WebM recording files in: {temp_dir}...")
    for f in os.listdir(temp_dir):
        fp = os.path.join(temp_dir, f)
        if os.path.isfile(fp):
            try:
                os.remove(fp)
            except:
                pass
                
    # 4. Trigger seed_knowledge.py to re-index knowledge base
    print("📡 Re-indexing marketing assets into RAG database...")
    try:
        python_exe = sys.executable
        seed_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "seed_knowledge.py"))
        subprocess.run([python_exe, seed_script], check=True)
        print("✅ RAG Knowledge Base re-indexed successfully.")
    except Exception as se:
        print(f"⚠️ Failed to trigger seed_knowledge.py: {se}")

if __name__ == "__main__":
    main()
