import os
import sys
from dotenv import dotenv_values
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
env_vars = dotenv_values(env_path)
api_key = env_vars.get("GOOGLE_API_KEY")

if not api_key:
    print("API Key not found")
    sys.exit(1)
try:
    from google import genai
    client = genai.Client(api_key=api_key)
    for model in client.models.list():
        if "gemini" in model.name:
            print(model.name)
except Exception as e:
    print(f"Error: {e}")
