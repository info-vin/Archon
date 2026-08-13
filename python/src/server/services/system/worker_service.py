"""
Worker Service for Archon (Phase 5.1.0)
Handles DB-based task queueing and background execution to replace synchronous blocking.
"""

import asyncio
from typing import Any

from src.server.config.logfire_config import get_logger
from src.server.services.agent_service import agent_service
from src.server.services.projects.task_service import task_service
from src.server.services.shared_constants import TaskStatusEnum
from src.server.services.system.rate_limiter import global_throttler

logger = get_logger(__name__)


class WorkerService:
    """
    Background worker that polls for 'dispatched' tasks and executes them.
    """

    def __init__(self, max_concurrent_tasks: int = 3) -> None:
        from src.server.services.settings_service import SettingsService
        settings = SettingsService()
        self.poll_interval = float(settings.get_setting("WORKER_POLL_INTERVAL") or 5.0)
        self._running = False
        self._task: asyncio.Task[Any] | None = None
        # Phase 5.1.1 Milestone 3.2: Semaphore concurrency protection
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def start(self) -> None:
        """Start the background worker loop"""
        if self._running:
            return

        self._running = True

        # 0. Phase 5.10.5: Recover Zombie Tasks
        await self._recover_zombie_tasks()

        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            f"🚀 Worker Service started (poll interval: {self.poll_interval}s, max concurrency: {self._semaphore._value})"
        )

    async def stop(self) -> None:
        """Stop the background worker loop"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Worker Service stopped")

    async def _run_loop(self) -> None:
        """Main polling loop"""
        while self._running:
            try:
                await self._process_queued_tasks()
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)

            await asyncio.sleep(self.poll_interval)

    async def _recover_zombie_tasks(self) -> None:
        """Find stuck tasks (processing/doing) from previous interrupted runs and apply DLQ logic."""
        logger.info("🧹 Scanning for zombie tasks...")

        # Fetch both 'processing' and 'doing' statuses
        tasks_to_recover = []
        for status in [TaskStatusEnum.PROCESSING, TaskStatusEnum.DOING]:
            success, result = await task_service.list_tasks(status=status)
            if success and result.get("tasks"):
                tasks_to_recover.extend(result["tasks"])

        if not tasks_to_recover:
            return

        logger.info(f"🧟 Found {len(tasks_to_recover)} zombie tasks. Applying Reaper/DLQ pattern...")

        from src.server.services.settings_service import SettingsService
        settings = SettingsService()
        max_retries = int(settings.get_setting("WORKER_MAX_RETRIES") or 3)

        for task in tasks_to_recover:
            task_id = task["id"]
            retry_count = task.get("retry_count") or 0

            if retry_count < max_retries:
                # Automatic Retry
                new_retry_count = retry_count + 1
                desc = task.get("description", "")
                append_msg = f"\n\n[系統紀錄] 理解問題: 系統意外中斷導致任務卡死 (Zombie). 嘗試重新執行 (Attempt {new_retry_count}/3)."

                await task_service.update_task(task_id, {
                    "status": TaskStatusEnum.DISPATCHED,
                    "retry_count": new_retry_count,
                    "description": desc + append_msg
                })
                logger.warning(f"🔄 Recovered zombie task {task_id} -> dispatched (Attempt {new_retry_count}/{max_retries})")
            else:
                # Dead Letter Queue
                desc = task.get("description", "")
                append_msg = "\n\n[系統紀錄] DLQ: 任務已連續失敗或中斷 3 次，放棄自動重試。"

                await task_service.update_task(task_id, {
                    "status": TaskStatusEnum.FAILED,
                    "description": desc + append_msg
                })
                logger.error(f"💀 Zombie task {task_id} exceeded MAX_RETRIES ({max_retries}). Moved to DLQ (failed).")

    async def _process_queued_tasks(self) -> None:
        """Fetch and execute dispatched tasks"""
        # 1. Fetch tasks with status='dispatched'
        # We use task_service.list_tasks which internally calls query_logic
        success, result = await task_service.list_tasks(status="dispatched")
        if not success or not result.get("tasks"):
            return

        tasks = result["tasks"]
        logger.info(f"📥 Worker found {len(tasks)} dispatched tasks. Processing...")

        async def _execute_with_semaphore(task_id: str, agent_id: str) -> None:
            async with self._semaphore:
                from src.server.services.settings_service import SettingsService
                settings = SettingsService()
                tier = settings.get_setting("WORKER_RATE_LIMIT_TIER") or "lite"
                # 3. Wait for rate limit capacity before executing
                await global_throttler.wait_for_capacity(tier=tier)

                # 4. Execute the task
                try:
                    logger.info(f"⚙️ Worker executing task {task_id} for agent {agent_id}")
                    # We call run_agent_task with immediate=True to bypass enqueuing
                    await agent_service.run_agent_task(task_id=task_id, agent_id=agent_id, immediate=True)
                except Exception as e:
                    logger.error(f"Worker failed to execute task {task_id}: {e}")
                    await task_service.update_task(task_id, {"status": "failed"})

        for task in tasks:
            task_id = task["id"]
            agent_id = task.get("assignee")

            if not agent_id:
                logger.warning(f"Task {task_id} is dispatched but has no assignee. Skipping.")
                continue

            # 2. Mark as processing synchronously to prevent other workers from picking it up
            await task_service.update_task(task_id, {"status": TaskStatusEnum.PROCESSING})

            # Fire and forget concurrent execution bounded by the Semaphore
            asyncio.create_task(_execute_with_semaphore(task_id, agent_id))


worker_service = WorkerService()
