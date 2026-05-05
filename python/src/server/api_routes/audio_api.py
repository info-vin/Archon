import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..auth.dependencies import get_current_user
from ..services.prompt_service import prompt_service
from ..services.text_to_speech_service import text_to_speech_service

router = APIRouter(prefix="/api/audio", tags=["audio"])

class TTSRequest(BaseModel):
    text: str
    scene: str = "marketing_pitch"  # e.g., "marketing_pitch", "commander_briefing"
    voice: str | None = None

@router.post("/generate")
async def generate_audio_stream(request: TTSRequest, current_user: dict = Depends(get_current_user)):
    """
    Generates TTS audio and returns it as a streaming WAV response.
    """
    prompt_name = f"tts_{request.scene}"

    # 1. Fetch template from PromptManager
    template = prompt_service.get_prompt(prompt_name)
    # Default fallback if prompt is missing
    if not template or template == "You are a helpful AI assistant.":
        template = "{text}"

    # 2. Format with text
    try:
        final_text = template.format(text=request.text)
    except KeyError:
        # If template doesn't have {text}, just append it
        final_text = template + "\n" + request.text

    # 3. Determine Voice Actor
    voice = request.voice
    if not voice:
        # Default voice mapping
        voice = "Charon" if request.scene == "commander_briefing" else "Puck"

    # 4. Call TTS Service
    success, result = await text_to_speech_service.generate_audio(final_text, voice_name=voice)

    if not success:
        raise HTTPException(status_code=500, detail=str(result))

    # 5. Return as In-Memory Streaming Response
    return StreamingResponse(
        io.BytesIO(result),
        media_type="audio/wav",
        headers={
            "Content-Disposition": "inline; filename=\"speech.wav\""
        }
    )
