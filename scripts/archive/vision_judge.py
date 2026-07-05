#!/usr/bin/env python3
"""
scripts/vision_judge.py
-----------------------
Vision Judge utility using official Google GenAI SDK and Pydantic structured outputs.
Automatically reviews E2E screenshots of Star-Topology Chat UI (WhatsApp style bubbles,
role-based avatar color coding, overlapping elements, visual distortions).

Returns:
  - Exit code 0 if visual verification passes.
  - Exit code 1 if visual verification fails or an issue is detected.
"""

import sys
import os
import argparse
import json
from pathlib import Path
from PIL import Image
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Try importing the official google-genai SDK
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ Error: 'google-genai' SDK is not installed in the current Python environment.")
    print("Please run: uv pip install google-genai or pip install google-genai")
    sys.exit(1)


class VisionJudgment(BaseModel):
    passed: bool = Field(
        ...,
        description="Whether the screenshot passes the visual sanity check (no overlapping elements, proper WhatsApp bubbles, correct avatar colors)."
    )
    issues: list[str] = Field(
        ...,
        description="List of visual layout issues or design anomalies discovered (e.g. overlap, text truncation, invalid avatar colors). Empty list if passed is True."
    )
    details: str = Field(
        ...,
        description="A detailed explanation of the visual elements observed, such as avatar roles, bubble layout, spacing, and readability."
    )


def parse_args():
    parser = argparse.ArgumentParser(description="AI Multimodal Visual UI Judge")
    parser.add_argument(
        "--image",
        required=True,
        type=str,
        help="Path to the E2E/MBT browser screenshot image (e.g. screenshot.png)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="models/gemini-3.1-flash-lite",
        help="Gemini model identifier to use (default: models/gemini-3.1-flash-lite)"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Override the default visual auditing prompt"
    )
    return parser.parse_args()


def load_api_key() -> str:
    # 1. Load dotenv from standard locations
    project_root = Path(__file__).resolve().parent.parent
    dotenv_paths = [
        project_root / ".env",
        project_root / ".env.test",
        Path.cwd() / ".env",
    ]
    for p in dotenv_paths:
        if p.exists():
            load_dotenv(p, override=True)
            break

    # 2. Get the key from environment
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY is not set in environment or any .env file.")
        print("Please check your .env file or run: export GEMINI_API_KEY=your_key")
        sys.exit(1)
    return api_key


def run_ollama_vision_judge(image_path: Path, prompt: str, model_arg: str):
    import base64
    import httpx
    
    print("🔌 OFFLINE_MODE detected. Using local Ollama for visual evaluation...")
    
    # Read and encode image to base64
    try:
        with open(image_path, "rb") as image_file:
            img_b64 = base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"❌ Error reading image for Ollama: {e}")
        sys.exit(1)
        
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    # Default to local gemma4:e4b for offline multimodal evaluation
    ollama_model = "gemma4:e4b"
    
    print(f"🚀 Sending screenshot to Ollama model '{ollama_model}' at {ollama_host}...")
    
    payload = {
        "model": ollama_model,
        "prompt": prompt + "\nRespond ONLY in the JSON format matching the schema:\n"
                  "{\n  \"passed\": bool,\n  \"issues\": [string],\n  \"details\": string\n}",
        "images": [img_b64],
        "format": "json",
        "stream": false,
        "options": {
            "temperature": 0.1
        }
    }
    
    try:
        resp = httpx.post(f"{ollama_host}/api/generate", json=payload, timeout=90.0)
        if resp.status_code != 200:
            print(f"❌ Ollama API failed with status {resp.status_code}: {resp.text}")
            sys.exit(1)
            
        result_data = resp.json()
        response_text = result_data.get("response", "")
        
        # Parse visual judgment
        judgment_dict = json.loads(response_text)
        judgment = VisionJudgment(**judgment_dict)
    except Exception as e:
        print(f"❌ Failed to execute or parse Ollama visual evaluation: {e}")
        if 'resp' in locals():
            print(f"Raw Ollama response: {resp.text}")
        sys.exit(1)
        
    print("\n" + "=" * 50)
    print("🎯 [OFFLINE VISUAL JUDGE RESULTS]")
    print("=" * 50)
    print(f"Status:  {'🟢 PASSED' if judgment.passed else '🔴 FAILED'}")
    print(f"Details: {judgment.details}\n")
 
    if judgment.issues:
        print("⚠️  [ISSUES DETECTED]:")
        for idx, issue in enumerate(judgment.issues, 1):
            print(f"  {idx}. {issue}")
    else:
        print("✅ No visual issues detected!")
    print("=" * 50)
 
    if judgment.passed:
        print("\n🟢 Local visual verification passed.")
        sys.exit(0)
    else:
        print("\n🔴 Local visual verification failed.")
        sys.exit(1)


def main():
    args = parse_args()
    image_path = Path(args.image)

    if not image_path.exists():
        print(f"❌ Error: Image file not found: {image_path}")
        sys.exit(1)

    # Set up the default verification prompt specifically tuned for Star-Topology multi-agent chat
    default_prompt = (
        "You are an Elite QA Visual Automation Judge. Analyze the provided browser screenshot of "
        "the Multi-Agent Star-Topology Chat UI. Verify if it meets our strict visual and logical "
        "design specifications:\n\n"
        "1. WhatsApp-Style Chat History Layout:\n"
        "   - Inspect if message bubbles (chat bubbles) are clean, fully visible, and properly styled.\n"
        "   - Ensure there is NO OVERLAPPING TEXT, cut-off words, or visual distortions in any of the bubbles.\n\n"
        "2. Role-Based Avatar Color Coding:\n"
        "   - Identify different agent/user avatars (Supervisor, Librarian, AI Developer, User, etc.).\n"
        "   - Check if their color matches their respective role or permissions correctly (e.g. Supervisor avatar has its designated accent color, user has its fallback, etc.).\n"
        "   - Verify that all active avatars are clearly rendered without layout glitches.\n\n"
        "Perform a rigorous audit and return your findings in the requested structured JSON schema."
    )
    prompt = args.prompt if args.prompt else default_prompt

    # OFFLINE_MODE check
    offline_mode = os.environ.get("OFFLINE_MODE", "false").lower() == "true"
    if offline_mode:
        run_ollama_vision_judge(image_path, prompt, args.model)
        return

    # Clean up model name to remove redundant prefixes if any
    model_name = args.model
    if model_name.startswith("models/"):
        model_name = model_name.split("/")[-1]

    # Load API key and initialize Google GenAI Client
    api_key = load_api_key()
    print(f"🔑 Loaded GEMINI_API_KEY successfully. Initializing Google GenAI Client...")
    client = genai.Client(api_key=api_key)

    # Load screenshot image
    try:
        image = Image.open(image_path)
        print(f"🖼️ Loaded screenshot: '{image_path}' ({image.width}x{image.height} px)")
    except Exception as e:
        print(f"❌ Error loading image: {e}")
        sys.exit(1)

    print(f"🚀 Submitting image to {model_name} for visual audit...")

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=[image, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VisionJudgment,
                temperature=0.1  # Highly deterministic
            )
        )
    except Exception as e:
        print(f"❌ Gemini API Call crashed: {e}")
        print("Please check your GEMINI_API_KEY or connection.")
        sys.exit(1)

    try:
        judgment_data = json.loads(response.text)
        judgment = VisionJudgment(**judgment_data)
    except Exception as e:
        print(f"❌ Error parsing structured response from Gemini: {e}")
        print(f"Raw Response: {response.text}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("🎯 [VISUAL JUDGE RESULTS]")
    print("=" * 50)
    print(f"Status:  {'🟢 PASSED' if judgment.passed else '🔴 FAILED'}")
    print(f"Details: {judgment.details}\n")

    if judgment.issues:
        print("⚠️  [ISSUES DETECTED]:")
        for idx, issue in enumerate(judgment.issues, 1):
            print(f"  {idx}. {issue}")
    else:
        print("✅ No visual issues detected!")
    print("=" * 50)

    # Return exit code based on judgment
    if judgment.passed:
        print("\n🟢 Visual verification passed physically.")
        sys.exit(0)
    else:
        print("\n🔴 Visual verification failed due to the issues listed above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
