
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.librarian_service import LibrarianService


@pytest.mark.asyncio
async def test_librarian_style_critique_extraction():
    """
    Ensures LibrarianService can extract style rules from unstructured notes.
    """
    lib = LibrarianService()
    post_title = "The Future of AI"
    original_content = "AI is great! :joy: It helps everyone do everything fast."
    review_notes = "Stop using emojis. It looks unprofessional. Also, make it more formal."

    # Fix Patch Path: Patch the actual Client class in google.genai
    with patch("google.genai.Client") as MockGenAI:
        mock_response = MagicMock()
        mock_response.text = "- Do not use emojis in professional content.\n- Maintain a formal tone."
        MockGenAI.return_value.models.generate_content.return_value = mock_response

        with patch.object(lib, 'supabase'):
            with patch("src.server.services.librarian_service.create_embedding", new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = [0.1] * 768

                with patch("src.server.services.librarian_service.update_source_info", new_callable=AsyncMock) as mock_update:
                    source_id = await lib.archive_style_critique(
                        post_title=post_title,
                        original_content=original_content,
                        review_notes=review_notes
                    )

                    assert source_id.startswith("style-lesson-")
                    mock_update.assert_called_once()
                    # Ensure metadata reflects the expertise type
                    args, kwargs = mock_update.call_args
                    assert "style_lesson" in kwargs.get('tags', [])

@pytest.mark.asyncio
async def test_marketing_approval_triggers_learning():
    """
    Ensures process_approval calls archive_style_critique when rejected.
    """
    from src.server.api_routes.marketing_api import process_approval

    # Setup Mock Request
    mock_request = MagicMock()
    mock_request.method = "POST"
    mock_request.json = AsyncMock(return_value={"review_notes": "Too many exclamation marks!"})

    current_user = {"id": "user-123", "role": "manager"}

    with patch("src.server.api_routes.marketing_api.get_supabase_client") as mock_db:
        mock_db.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
            {"id": "blog-1", "title": "Test Blog", "content": "Hello!!!"}
        ]

        # Patch LibrarianService at the point of use in marketing_api
        with patch("src.server.services.librarian_service.LibrarianService.archive_style_critique", new_callable=AsyncMock) as mock_learn:
            await process_approval(
                item_type="blog",
                item_id="blog-1",
                action="reject",
                request=mock_request,
                current_user=current_user
            )

            # Critical: Allow event loop to process the background task
            await asyncio.sleep(0.2)

            mock_learn.assert_called_once()
            args, kwargs = mock_learn.call_args
            assert kwargs['review_notes'] == "Too many exclamation marks!"
            assert kwargs['post_title'] == "Test Blog"
