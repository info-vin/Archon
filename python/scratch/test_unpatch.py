import asyncio

from src.server.services.text_to_speech_service import text_to_speech_service


async def main():
    try:
        from tests.conftest import _global_patches
        print("Patches found:", len(_global_patches))
        genai_patch = next((p for p in _global_patches if hasattr(p, "target") and getattr(p.target, "__name__", "") == "google.genai"), None)
        if genai_patch:
            print("Stopping genai patch...")
            genai_patch.stop()
        else:
            print("Genai patch not found!")
    except ImportError as e:
        print("Import error:", e)
        return

    # Check if we have API key
    # Need to fake db mock if we use get_credential?
    # No, get_credential falls back to os.getenv if DB returns None.
    # But wait, credential_service uses cache. Let's just set os.environ["GEMINI_API_KEY"] if not set.

    print("Testing generate_audio...")
    try:
        success, result = await text_to_speech_service.generate_audio("Hello world", "Puck")
        print("Success:", success)
        print("Result length:", len(result) if success else result)
    except Exception as e:
        print("Exception:", e)

    if genai_patch:
        genai_patch.start()

if __name__ == "__main__":
    asyncio.run(main())
