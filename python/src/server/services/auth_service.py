from typing import Any

from supabase import Client

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client
from .profile_service import ProfileService

logger = get_logger(__name__)

class AuthService:
    """
    Service for handling authentication and user management via Supabase Admin API.
    Uses SUPABASE_SERVICE_KEY for privileged operations.
    """

    def __init__(self, supabase_client: Client | None = None, profile_service: ProfileService | None = None):
        self.supabase = supabase_client or get_supabase_client()
        self.profile_service = profile_service or ProfileService(self.supabase)

    def create_user_by_admin(self, email: str, password: str, name: str, role: str, status: str = 'active') -> dict[str, Any]:
        """
        Creates a new user using the Admin API (does not log out the current user).
        Also ensures a profile is created in public.profiles.

        Args:
            email: User email.
            password: User password.
            name: User full name.
            role: EmployeeRole (e.g., 'admin', 'member').
            status: Account status.

        Returns:
            Created profile data.
        """
        try:
            logger.info(f"Admin creating user: {email} with role {role}")

            # 1. Create Auth User via Admin API
            # Note: invite=False ensures we create it directly, confirm=True auto-confirms email
            attributes = {
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {"name": name}
            }

            # Use auth.admin.create_user (GoTrue Admin API)
            user_response = self.supabase.auth.admin.create_user(attributes)

            if not user_response.user:
                raise ValueError("Failed to create auth user: No user returned.")

            user_id = user_response.user.id
            logger.info(f"Auth user created: {user_id}")

            # 2. Create Profile
            # We construct the profile object. 'avatar' is generated same as frontend did.
            profile_data = {
                "id": user_id,
                "email": email,
                "name": name,
                "role": role,
                "status": status,
                "avatar": f"https://i.pravatar.cc/150?u={user_id}"
            }

                        # Insert into public.profiles
                        # We use upsert to be safe, though create_user should ensure new ID.
                        # Fix: Simplify query chain for sync client compatibility
                        response = self.supabase.table("profiles").upsert(profile_data).execute()
                        
                        # For upsert, if we want data back, we might need to fetch it or rely on execute returning it if configured
                        if response.data:
                            logger.info(f"Profile created for: {user_id}")
                            # Return the first item if list
                            return response.data[0] if isinstance(response.data, list) and response.data else response.data
                        else:                # Fallback: If upsert returns nothing (rare), fetch it
                success, profile = self.profile_service.get_profile(user_id)
                if success and profile:
                    return profile
                raise ValueError("Profile creation failed: No data returned.")

        except Exception as e:
            logger.error(f"Error in create_user_by_admin: {e}", exc_info=True)
            raise e

    def register_user(self, email: str, password: str, name: str) -> dict[str, Any]:
        """
        Public registration.
        """
        try:
            logger.info(f"Public registration for: {email}")

            # For public registration, we use standard signUp (not admin),
            # BUT since this is server-side with Service Key, strictly speaking we are admin.
            # However, to simulate 'public' sign up, we can still use auth.sign_up
            # but that logs us in as that user on this client instance (potentially).
            # BETTER APPROACH: Use admin.create_user but with default role 'member'.

            attributes = {
                "email": email,
                "password": password,
                "email_confirm": True, # Auto-confirm for simplicity in this app context
                "user_metadata": {"name": name}
            }

            user_response = self.supabase.auth.admin.create_user(attributes)

            if not user_response.user:
                raise ValueError("Registration failed in auth.")

            user_id = user_response.user.id

                        profile_data = {
                            "id": user_id,
                            "email": email,
                            "name": name,
                            "role": "member", # Default role
                            "status": "active",
                            "avatar": f"https://i.pravatar.cc/150?u={user_id}"
                        }
            
                        response = self.supabase.table("profiles").insert(profile_data).execute()
                        
                        if response.data:
                            return response.data[0] if isinstance(response.data, list) else response.data
                        raise ValueError("Profile creation failed.")
        except Exception as e:
            logger.error(f"Error in register_user: {e}", exc_info=True)
            raise e

    def update_user_email(self, user_id: str, new_email: str) -> None:
        """
        Updates user email via Admin API.
        """
        try:
            logger.info(f"Updating email for {user_id} to {new_email}")

            # 1. Update Auth
            self.supabase.auth.admin.update_user_by_id(user_id, {"email": new_email})

            # 2. Update Profile
            self.supabase.table("profiles").update({"email": new_email}).eq("id", user_id).execute()

        except Exception as e:
            logger.error(f"Error updating email: {e}", exc_info=True)
            raise e
