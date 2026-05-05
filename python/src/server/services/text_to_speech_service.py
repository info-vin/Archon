import io
import wave

from google import genai
from google.genai import types

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
        The audio bytes are packaged into a valid WAV format suitable for browser playback.
        """
        try:
            api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
            if not api_key:
                logger.warning("TTS failed: No valid API key found.")
                return False, "API Key missing."

            client = genai.Client(api_key=api_key)

            # The dedicated TTS model
            model_name = SYSTEM_MODELS.get("TTS_MODEL", "models/gemini-3.1-flash-tts-preview").split("/")[-1]

            logger.info(f"Generating TTS audio. Voice: {voice_name}. Text length: {len(text)} characters.")

            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                )
            )

            response = await client.aio.models.generate_content(
                model=model_name,
                contents=text,
                config=config
            )

            if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
                return False, "No audio generated."
                
            # Log token usage for ROI calculation
            if response.usage_metadata:
                token_usage_service.log_usage(
                    model=model_name,
                    prompt_tokens=response.usage_metadata.prompt_token_count,
                    completion_tokens=response.usage_metadata.candidates_token_count,
                    total_tokens=response.usage_metadata.total_token_count,
                    agent_name="Librarian_TTS"
                )

            for part in response.candidates[0].content.parts:
                # Check for inline_data that contains audio (the model returns raw PCM)
                if part.inline_data and part.inline_data.data:
                    raw_audio = part.inline_data.data

                    # Package Raw PCM into WAV format in memory
                    wav_io = io.BytesIO()
                    with wave.open(wav_io, 'wb') as wf:
                        wf.setnchannels(1)          # Mono
                        wf.setsampwidth(2)          # 16-bit
                        wf.setframerate(24000)      # 24kHz
                        wf.writeframes(raw_audio)

                    wav_bytes = wav_io.getvalue()
                    return True, wav_bytes

            return False, "No audio part found in the response."
        except Exception as e:
            logger.error(f"TTS generation failed: {str(e)}")
            raise e  # Let retry_with_backoff handle it; if it exhausts retries it will propagate

# Singleton export
text_to_speech_service = TextToSpeechService()
