import httpx
import asyncio
import os

async def run_test():
    base_url = "http://localhost:8181/api"
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        # 1. Login (Get Dev Token)
        print("🔑 Getting Dev Token...")
        try:
            resp = await client.post(f"{base_url}/auth/dev-token", json={"password": "qwer45tyuiop"})
            if resp.status_code != 200:
                print(f"❌ Login failed: {resp.text}")
                return
            token = resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Token acquired.")
        except Exception as e:
            print(f"❌ Connection failed. Is backend running? Error: {e}")
            return

        # 2. Upload Audio
        print("🎙️ Uploading audio (mocking Alice's Visit)...")
        # Check root and current dir
        test_file = "test_voice.mp3"
        if not os.path.exists(test_file):
            test_file = "../test_voice.mp3"
            
        if not os.path.exists(test_file):
            print(f"❌ Test file not found in current or parent dir!")
            return

        with open(test_file, "rb") as f:
            files = {"audio_file": ("test_voice.mp3", f, "audio/mpeg")}
            data = {
                "latitude": "25.0330",
                "longitude": "121.5654",
                "location_address": "Taipei 101, Taiwan"
            }
            
            try:
                resp = await client.post(f"{base_url}/visit-logs/", headers=headers, data=data, files=files)
                
                if resp.status_code == 200:
                    result = resp.json()
                    print("\n✅ SUCCESS! Visit Log Created:")
                    print(f"   ID: {result['id']}")
                    print(f"   Summary: {result['summary']}")
                    print(f"   Tasks Extracted: {len(result['follow_up_tasks'])}")
                    print(f"   Transcript Preview: {result['voice_transcript'][:100]}...")
                else:
                    print(f"❌ API Error ({resp.status_code}): {resp.text}")

            except httpx.ReadTimeout:
                print("❌ Timeout waiting for Gemini response (Processing took too long).")
            except Exception as e:
                print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())