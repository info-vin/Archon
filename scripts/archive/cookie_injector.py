import os
import json
from pathlib import Path
from playwright.async_api import Browser, BrowserContext

class KeychainBypassCookieInjector:
    """
    Keychain-Bypass Cookie Injector for Playwright Python.
    Bypasses macOS/Linux OS Keychain password popups and decryption errors 
    by launching a clean non-persistent context and injecting standard JSON storage state.
    """

    DEFAULT_STATE_PATH = Path("/Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/.playwright/admin_storage_state.json")

    @staticmethod
    def get_state_path(custom_path: str = None) -> Path:
        """Resolves the physical path of the storage state JSON file."""
        if custom_path:
            p = Path(custom_path)
        else:
            p = KeychainBypassCookieInjector.DEFAULT_STATE_PATH
        
        # Fallbacks for dynamic environment resilience
        possible_paths = [
            p,
            Path("./enduser-ui-fe/.playwright/admin_storage_state.json"),
            Path("../enduser-ui-fe/.playwright/admin_storage_state.json"),
            Path("/app/enduser-ui-fe/.playwright/admin_storage_state.json")
        ]
        
        for path in possible_paths:
            if path.exists():
                return path.resolve()
        return p.resolve()

    @classmethod
    async def create_keychain_bypass_context(
        cls, 
        playwright_instance, 
        headless: bool = True, 
        state_path: str = None,
        **context_kwargs
    ) -> tuple[Browser, BrowserContext]:
        """
        Launches a standard chromium browser and injects the JSON state file.
        Completely immune to system OS keychain encryption prompts.
        """
        resolved_state = cls.get_state_path(state_path)
        
        print(f"🔑 [CookieInjector] Bypassing Keychain. Launching clean non-persistent context...")
        
        # Add basic password store flag as extra hardening layer
        browser_args = [
            '--no-sandbox', 
            '--disable-setuid-sandbox',
            '--password-store=basic',
            '--use-mock-keyring'
        ]
        
        browser = await playwright_instance.chromium.launch(
            headless=headless,
            args=browser_args
        )
        
        # Load storage state if it exists
        if resolved_state.exists():
            print(f"🍪 [CookieInjector] Injecting storage state from: {resolved_state}")
            context = await browser.new_context(
                storage_state=str(resolved_state),
                **context_kwargs
            )
        else:
            print(f"⚠️ [CookieInjector] Storage state file not found at: {resolved_state}. Launching clean context.")
            context = await browser.new_context(**context_kwargs)
            
        return browser, context

    @classmethod
    async def save_context_state(cls, context: BrowserContext, state_path: str = None):
        """Saves current cookies, localStorage, and sessionStorage back to the JSON file."""
        resolved_state = cls.get_state_path(state_path)
        resolved_state.parent.mkdir(parents=True, exist_ok=True)
        
        # Playwright's storage_state captures cookies and localStorage
        state = await context.storage_state()
        
        with open(resolved_state, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
            
        print(f"💾 [CookieInjector] Saved updated state to: {resolved_state}")
