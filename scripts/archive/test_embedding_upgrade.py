import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv(".env")

async def list_and_test():
    api_key = os.getenv("GEMINI_API_KEY")
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    
    # 1. Fetch available models
    print("--- Fetching Available Models ---")
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://generativelanguage.googleapis.com/v1beta/models", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            embed_models = []
            for model in data.get("models", []):
                if "embedContent" in model.get("supportedGenerationMethods", []):
                    embed_models.append(model["name"].split("/")[-1])
            print(f"Available embedding models: {embed_models}")
        else:
            print("Failed to fetch models.")
            return

    # 2. Test them
    payload = {
        "content": {"parts": [{"text": "Hello, this is a test string."}]},
        "outputDimensionality": 768
    }

    for model_name in ["text-embedding-004"] + embed_models:
        print(f"\n--- Testing Model: {model_name} ---")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:embedContent"
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                dim = len(resp.json().get("embedding", {}).get("values", []))
                print(f"✅ Success! Returned Vector Dimension: {dim}")
            else:
                print(f"❌ Failed! Status: {resp.status_code}")
                # Print abbreviated error
                print(f"❌ Error: {resp.text[:200]}...")

if __name__ == "__main__":
    asyncio.run(list_and_test())
