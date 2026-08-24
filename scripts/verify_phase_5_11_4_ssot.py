import asyncio
import os
import json
import shutil
from unittest.mock import MagicMock

# Force wipe the environment variable to prove SSOT is working
if "NOTEBOOKLM_AUTH_JSON" in os.environ:
    del os.environ["NOTEBOOKLM_AUTH_JSON"]
    print("🧹 Wiped NOTEBOOKLM_AUTH_JSON from environment.")

# Set a custom isolated directory for test
os.environ["NOTEBOOKLM_DATA_DIR"] = "/tmp/archon_test_notebooklm"

from src.server.services.settings_service import SettingsService
from src.server.utils.notebooklm_auth import sync_notebooklm_session

async def test_bi_directional_sync():
    print("🚀 Starting Phase 5.11.4 Bi-Directional Sync Test...")
    
    # 1. Clean up old test data if it exists
    test_dir = "/tmp/archon_test_notebooklm"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        
    # 2. Mock Settings Service
    mock_settings = MagicMock(spec=SettingsService)
    initial_db_token = '{"cookies": ["test_initial_cookie"]}'
    
    def mock_get_setting(key, default=None):
        if key == "notebooklm_auth_json":
            return initial_db_token
        return default
        
    mock_settings.get_setting.side_effect = mock_get_setting
    
    # 3. Enter Context Manager
    async with sync_notebooklm_session(mock_settings, profile_name="test_profile") as base_dir:
        print(f"✅ Context yielded base_dir: {base_dir}")
        assert base_dir == test_dir, f"Expected {test_dir}, got {base_dir}"
        
        # Verify Pre-Run Sync (DB -> File)
        file_path = os.path.join(test_dir, "profiles", "test_profile", "storage_state.json")
        assert os.path.exists(file_path), "Pre-run DB->File sync failed, file not created."
        
        with open(file_path, "r") as f:
            content = f.read()
            assert content == initial_db_token, "File content does not match DB token!"
            
        print("✅ Pre-run Sync (DB -> File) passed!")
        
        # 4. Simulate Playwright updating the token file (Refreshing Cookie)
        print("🔄 Simulating Playwright refreshing cookies...")
        refreshed_token = '{"cookies": ["test_refreshed_cookie_v2"]}'
        with open(file_path, "w") as f:
            f.write(refreshed_token)
            
    # 5. Verify Post-Run Sync (File -> DB)
    print("✅ Context exited.")
    
    # Check if set_setting was called with the new JSON
    assert mock_settings.set_setting.called, "Post-run File->DB sync failed! set_setting was not called."
    
    # Check args
    call_args = mock_settings.set_setting.call_args[0]
    key, new_val = call_args[0], call_args[1]
    
    assert key == "notebooklm_auth_json"
    
    # The saved json might be compressed or reformatted by json.dumps, so compare parsed dicts
    assert json.loads(new_val) == json.loads(refreshed_token), f"Expected {refreshed_token}, but got {new_val}"
    
    print("✅ Post-run Sync (File -> DB) passed!")
    print("🎉 All Phase 5.11.4 SSOT & Session Hardening checks passed successfully!")

if __name__ == "__main__":
    asyncio.run(test_bi_directional_sync())
