import os
import sys
from dotenv import dotenv_values
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
env_vars = dotenv_values(env_path)
api_key = env_vars.get("GOOGLE_API_KEY")

try:
    from google import genai
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite',
        contents='Test message.'
    )
    print("Success:", response.text)
except Exception as e:
    print(f"Error: {e}")
