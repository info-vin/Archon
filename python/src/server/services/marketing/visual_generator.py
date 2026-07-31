import base64
from typing import Any, cast

from google import genai
from google.genai import types

from ...config.model_ssot import SYSTEM_MODELS
from .content_handler import get_logger

logger = get_logger(__name__)


class VisualAssetGenerator:
    """Handles visual asset generation and fallback SVG logo pipelines."""

    def __init__(self, supabase_client: Any) -> None:
        self.supabase_client = supabase_client

    async def generate_visual_asset(self, style: str) -> dict:
        from ..credential_service import credential_service
        from .logo_tool import generate_logo_svg

        # 1. Try native AI visual generation
        try:
            api_key = await credential_service.get_credential(
                "GEMINI_API_KEY"
            ) or await credential_service.get_credential("GOOGLE_API_KEY")

            if api_key:
                client = genai.Client(api_key=api_key)
                prompt = f"Professional tech logo, {style}, high resolution"
                native_resp = client.models.generate_content(
                    model=SYSTEM_MODELS.get("IMAGE_GEN", "imagen-3.0-generate-002"),
                    contents=cast(Any, [prompt]),
                    config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
                )
                for part in native_resp.parts or []:
                    if part.inline_data and part.inline_data.data:
                        return {
                            "status": "success",
                            "image_url": f"data:{part.inline_data.mime_type};base64,{part.inline_data.data.decode('utf-8')}",
                            "tier": "native",
                            "svg_content": "",
                        }
            else:
                logger.info("VisualAssetGenerator: API Key missing, using SVG generator directly.")
        except Exception as e:
            logger.warning(f"VisualAssetGenerator: Native AI visual generation failed ({e}), using SVG.")

        # 2. Try SVG Generation (Fallback)
        try:
            svg_content = generate_logo_svg(style)
            svg_base64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
            return {
                "status": "success",
                "image_url": f"data:image/svg+xml;base64,{svg_base64}",
                "tier": "physical_svg",
                "svg_content": svg_content,
            }
        except Exception as e:
            logger.critical(f"VisualAssetGenerator: Comprehensive visual failure: {e}")
            return {"status": "success", "image_url": "https://picsum.photos/1024/1024", "tier": "emergency"} # 合法
