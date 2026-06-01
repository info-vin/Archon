import io
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from google import genai
from pydantic import BaseModel

from ..auth.dependencies import get_current_user
from ..config.model_ssot import SYSTEM_MODELS
from ..services.prompt_service import prompt_service
from ..services.text_to_speech_service import text_to_speech_service

router = APIRouter(prefix="/api/audio", tags=["audio"])


class TTSRequest(BaseModel):
    text: str = ""
    scene: str = "marketing_pitch"  # e.g., "marketing_pitch", "commander_briefing"
    voice: str | None = None
    agent_data: dict | None = None


@router.post("/generate")
async def generate_audio_stream(request: TTSRequest, current_user: dict = Depends(get_current_user)):
    """
    Generates TTS audio and returns it as a streaming WAV response.
    If agent_data is provided, it uses an LLM to dynamically generate the script
    based on the scene's prompt template and the data.
    """
    prompt_name = f"tts_{request.scene}"

    # 1. Fetch template from PromptManager
    template = prompt_service.get_prompt(prompt_name)
    # Default fallback if prompt is missing
    if not template or template == "You are a helpful AI assistant.":
        template = "{text}"

    final_text = request.text

    # 2. Semantic Translation by Agent (if agent_data is present)
    if request.agent_data:
        from ..services.credential_service import credential_service

        api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential(
            "GOOGLE_API_KEY"
        )
        if not api_key:
            raise HTTPException(status_code=500, detail="No API key for semantic translation")

        client = genai.Client(api_key=api_key)
        model_name = SYSTEM_MODELS.get("DEFAULT_TEXT", "models/gemini-3.1-flash-lite").split("/")[-1]

        default_instruction = (
            "You are a Senior Chief of Staff translating dashboard JSON data into a fluent, "
            "natural spoken briefing script. Read the provided prompt template to understand "
            "the voice style and instructions."
        )
        system_instruction = prompt_service.get_prompt("CHIEF_OF_STAFF_AUDIO_BRIEFING", default=default_instruction)

        prompt = (
            f"=== Prompt Template ===\n{template}\n\n"
            f"=== Dashboard Data ===\n{json.dumps(request.agent_data, ensure_ascii=False)}\n\n"
            "Task: Generate the final spoken script based ONLY on the dashboard data provided, "
            "adhering strictly to the style requested in the template. Output the raw text ready for TTS."
        )

        try:
            response = await client.aio.models.generate_content(
                model=model_name, contents=prompt, config={"system_instruction": system_instruction}
            )
            final_text = response.text if response.text else "Failed to generate briefing."
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM translation failed: {str(e)}") from e

    else:
        # 3. Static Formatting (if no agent_data)
        try:
            final_text = template.format(text=request.text)
        except KeyError:
            # If template doesn't have {text}, just append it
            final_text = template + "\n" + request.text

    # 4. Determine Voice Actor
    voice = request.voice
    if not voice:
        # Default voice mapping
        voice = "Charon" if request.scene == "commander_briefing" else "Puck"

    # 5. Call TTS Service
    success, result = await text_to_speech_service.generate_audio(final_text, voice_name=voice)

    if not success:
        raise HTTPException(status_code=500, detail=str(result))

    # 6. Return as In-Memory Streaming Response
    return StreamingResponse(
        io.BytesIO(result), media_type="audio/wav", headers={"Content-Disposition": 'inline; filename="speech.wav"'}
    )
