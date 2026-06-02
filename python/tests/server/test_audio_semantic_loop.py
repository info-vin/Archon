import os

import pytest
from google import genai
from google.genai import types

from src.server.config.model_ssot import SYSTEM_MODELS
from src.server.services.credential_service import credential_service


@pytest.mark.integration
@pytest.mark.asyncio
async def test_audio_semantic_loop_live(client):
    """
    Live Integration Test for TTS Audio Generation and Semantic Validation.
    """
    from tests.conftest import _global_patches
    genai_patch = next((p for p in _global_patches if hasattr(p, "target") and getattr(p.target, "__name__", "") == "google.genai"), None)

    if genai_patch:
        genai_patch.stop()

    try:
        import respx
        # Allow pass-through for real API calls during live test
        respx.route(host__regex=r".*generativelanguage\.googleapis\.com").pass_through()

        # 1. Fetch live API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            api_key = await credential_service.get_credential("GEMINI_API_KEY")

        if not api_key or api_key == "fake-api-key":
            pytest.skip("Skipping live integration test: GEMINI_API_KEY not found in environment or DB")

        # 2. Define the input text
        input_text = "The operational parameters of the Archon defense system are currently optimal."

        # 3. Call the FastAPI TTS generation endpoint
        try:
            response = client.post("/api/audio/generate", json={
                "text": input_text,
                "scene": "commander_briefing",
                "voice": "Charon"
            })

            # 4. Verify basic HTTP and WAV parameters
            assert response.status_code == 200
            assert response.headers.get("content-type") == "audio/wav"

            audio_bytes = response.content
            assert len(audio_bytes) > 100
            assert audio_bytes.startswith(b"RIFF")
            assert b"WAVEfmt" in audio_bytes

            # 5. Connect to live Gemini and transcribe the generated audio
            genai_client = genai.Client(api_key=api_key)

            # We pack the audio bytes directly into a Part object
            audio_part = types.Part.from_bytes(
                data=audio_bytes,
                mime_type="audio/wav"
            )

            model_name = SYSTEM_MODELS["DEFAULT_TEXT"].split("/")[-1]

            # Generate content using the audio part to transcribe the text
            res = genai_client.models.generate_content(
                model=model_name,
                contents=[
                    audio_part,
                    "Transcribe this audio precisely. Return ONLY the transcribed text. Do not add comments or explanations."
                ]
            )
        except Exception as e:
            err_msg = str(e)
            if any(msg in err_msg for msg in ["leaked", "PERMISSION_DENIED", "API key was reported as leaked", "API_KEY_INVALID", "500 INTERNAL"]):
                pytest.skip(f"Skipping live integration test: API key/Upstream issue ({e})")
            raise

        transcription = res.text
        assert transcription is not None
        transcription_lower = transcription.lower()

        # 6. Assert semantic keywords are present in the audio transcription
        assert any(word in transcription_lower for word in ["operational", "parameters", "archon", "defense", "system", "optimal"])
    finally:
        if genai_patch:
            genai_patch.start()

