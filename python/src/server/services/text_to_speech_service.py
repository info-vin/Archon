
from google import genai

from ..config.logfire_config import get_logger
from ..config.model_ssot import SYSTEM_MODELS
from ..services.credential_service import credential_service
from ..utils.retry_utils import retry_with_backoff

logger = get_logger(__name__)

class TextToSpeechService:
    """
    Dedicated service for generating audio using the gemini-3.1-flash-tts-preview model.
    Implements retry mechanisms to gracefully handle Free Tier rate limits.
    """

    @staticmethod
    @retry_with_backoff(max_retries=2, initial_delay=1.0)
    async def generate_audio(text: str, voice_name: str = "Puck") -> tuple[bool, bytes | str]:
        """
        Generates audio from text using Gemini TTS.
        Returns a tuple of (success_status, audio_bytes_or_error_message).
        """
        try:
            api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
            if not api_key:
                logger.warning("TTS failed: No valid API key found.")
                return False, "API Key missing."

            client = genai.Client(api_key=api_key)

            # The dedicated TTS model
            model_name = SYSTEM_MODELS.get("TTS_MODEL", "models/gemini-3.1-flash-tts-preview").split("/")[-1]

            # Combine voice director notes with the text if a specific voice style is requested
            prompt = f"[Voice style: {voice_name}]\n{text}"

            logger.info(f"Generating TTS audio. Text length: {len(text)} characters.")

            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
            )

            if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
                return False, "No audio generated."

            for part in response.candidates[0].content.parts:
                # Check for inline_data that contains audio
                if part.inline_data and part.inline_data.mime_type and "audio" in part.inline_data.mime_type:
                    data = part.inline_data.data
                    if data:
                        return True, data

            return False, "No audio part found in the response."
        except Exception as e:
            logger.error(f"TTS generation failed: {str(e)}")
            raise e  # Let retry_with_backoff handle it; if it exhausts retries it will propagate

# Singleton export
text_to_speech_service = TextToSpeechService()
