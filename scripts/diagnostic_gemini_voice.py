import httpx
import json
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def diagnose():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env")
        return

    async with httpx.AsyncClient() as client:
        print("--- Step 1: Uploading ---")
        url_upload = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={api_key}"
        boundary = "diag_boundary"
        headers = {"X-Goog-Upload-Protocol": "multipart", "Content-Type": f"multipart/related; boundary={boundary}"}
        
        with open("test_voice.mp3", "rb") as f:
            audio_data = f.read()
            
        header_part = f"--{boundary}\r\nContent-Type: application/json\r\n\r\n{json.dumps({'file': {'display_name': 'test'}})}\r\n".encode()
        media_part = f"--{boundary}\r\nContent-Type: audio/mpeg\r\n\r\n".encode()
        footer_part = f"\r\n--{boundary}--\r\n".encode()
        
        body = header_part + media_part + audio_data + footer_part
        
        resp = await client.post(url_upload, content=body, headers=headers)
        if resp.status_code != 200:
            print(f"❌ Upload Failed: {resp.text}")
            return
        
        file_info = resp.json()
        file_uri = file_info['file']['uri']
        file_name = file_info['file']['name']
        print(f"✅ Uploaded! URI: {file_uri}")

        print("--- Step 2: Waiting for Processing ---")
        check_url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={api_key}"
        for i in range(5):
            await asyncio.sleep(2)
            chk = await client.get(check_url)
            state = chk.json().get("state")
            print(f"   Attempt {i+1}: State = {state}")
            if state == "ACTIVE": break

        print("--- Step 3: Transcribing ---")
        url_gen = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": "Transcribe this audio to Traditional Chinese."},
                    {"file_data": {"mime_type": "audio/mpeg", "file_uri": file_uri}}
                ]
            }]
        }
        resp_gen = await client.post(url_gen, json=payload)
        print(f"Status: {resp_gen.status_code}")
        print(f"Full Response: {resp_gen.text}")

if __name__ == "__main__":
    asyncio.run(diagnose())