import os

import pytest

from src.server.services.auth_service import AuthService
from src.server.services.blog_service import BlogService


# Skip integration tests if no real Supabase credentials
@pytest.mark.skipif(
    not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_KEY"),
    reason="Requires real Supabase credentials"
)
class TestSupabaseIntegration:

    @pytest.fixture
    def auth_service(self):
        return AuthService()

    @pytest.fixture
    def blog_service(self):
        return BlogService()

    def test_auth_service_create_user_syntax(self, auth_service):
        """
        Verifies that the Supabase client syntax for creating users is correct.
        We don't actually want to spam the auth user database, so we might just
        test the profile insertion part if possible, or create a dummy user and clean it up.

        However, the specific error 'SyncQueryRequestBuilder object has no attribute select'
        happens during the DB query construction/execution.
        """
        # For safety in this test environment, we'll try a simpler table operation
        # that mimics the problematic syntax to confirm the fix.
        # The error was: table(...).upsert(...).select().single().execute()

        # We'll try to query public.profiles with the corrected syntax
        # Using a deterministic UUID for cleanup
        dummy_id = "00000000-0000-0000-0000-000000000000"
        
        try:
            # Let's try to upsert a dummy profile (id must be valid uuid)
            profile_data = {
                "id": dummy_id,
                "email": "integration_test@example.com",
                "name": "Integration Test",
                "role": "member",
                "status": "active"
            }

            # This is the line we expect to fail if syntax is wrong
            # Corrected syntax: .upsert(data).execute()
            response = auth_service.supabase.table("profiles").upsert(profile_data).execute()

            assert response is not None
            # assert response.data is not None # Data might be None if no returning

        except AttributeError as e:
            pytest.fail(f"Supabase client syntax error: {e}")
        except Exception as e:
            # Ignore other errors (like row constraints) as we just want to verify client syntax
            print(f"Operational error (expected): {e}")
        
        finally:
            # Cleanup - Always run this block
            try:
                print(f"Cleaning up test profile {dummy_id}")
                auth_service.supabase.table("profiles").delete().eq("id", dummy_id).execute()
            except Exception as cleanup_error:
                print(f"Failed to cleanup test data: {cleanup_error}")

    def test_blog_service_update_syntax(self, blog_service):
        """
        Verifies the update syntax for blog posts.
        """
        dummy_id = "00000000-0000-0000-0000-000000000000"
        
        try:
            # Dummy update
            update_data = {"title": "Updated Title"}

            # This line caused "SyncFilterRequestBuilder object has no attribute select"
            # Corrected syntax: .update(data).eq(id).execute()
            blog_service.supabase.table("blog_posts").update(update_data).eq("id", dummy_id).execute()

        except AttributeError as e:
            pytest.fail(f"Supabase client syntax error: {e}")
        except Exception:
            # We expect it might fail to find the row, but not AttributeError on the client
            pass
        
        # No cleanup needed for blog service test as it doesn't create data, only attempts update on non-existent row
