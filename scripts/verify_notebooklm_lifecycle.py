import asyncio
import os
import json
import logging
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 Starting Phase 5.11.3 Physical E2E Probe")

    with patch('src.server.services.settings_service.SettingsService.get_setting') as mock_get, \
         patch('src.server.services.settings_service.SettingsService.set_setting') as mock_set, \
         patch('src.server.services.settings_service.get_supabase_client'):
         
        from src.server.services.settings_service import SettingsService
        settings_service = SettingsService()
        
        # Test quota limit
        current_date = datetime.now().strftime("%Y-%m-%d")
        mock_get.return_value = json.dumps({"date": current_date, "count": 9})
        
        can_run = settings_service.check_and_increment_notebooklm_quota()
        assert can_run is False, "Quota limit should block execution at 10th run"
        logger.info("✅ Quota limit correctly blocks execution at 10 runs")
        
        mock_get.return_value = json.dumps({"date": current_date, "count": 8})
        can_run = settings_service.check_and_increment_notebooklm_quota()
        assert can_run is True, "Quota limit should allow 9th run"
        logger.info("✅ Quota limit correctly allows runs below 10")

    logger.info("✅ Phase 5.11.3 E2E Probe Passed!")

if __name__ == "__main__":
    asyncio.run(main())
