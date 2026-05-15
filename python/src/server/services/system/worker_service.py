"""
Worker Service for Archon (Phase 5.1.0)
Handles DB-based task queueing and background execution to replace synchronous blocking.
"""

import asyncio
from typing import Any

from src.server.config.logfire_config import get_logger
from src.server.services.agent_service import agent_service
from src.server.services.projects.task_service import task_service
from src.server.services.system.rate_limiter import global_throttler

logger = get_logger(__name__)


class WorkerService:
    """
    Background worker that polls for 'dispatched' tasks and executes them.
    """

    def __init__(self, poll_interval_seconds: float = 5.0):
        self.poll_interval = poll_interval_seconds
        self._running = False
        self._task: asyncio.Task[Any] | None = None

    async def start(self):
        """Start the background worker loop"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"🚀 Worker Service started (poll interval: {self.poll_interval}s)")

    async def stop(self):
        """Stop the background worker loop"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Worker Service stopped")

    async def _run_loop(self):
        """Main polling loop"""
        while self._running:
            try:
                await self._process_queued_tasks()
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)

            await asyncio.sleep(self.poll_interval)

    async def _process_queued_tasks(self):
        """Fetch and execute dispatched tasks"""
        # 1. Fetch tasks with status='dispatched'
        # We use task_service.list_tasks which internally calls query_logic
        success, result = await task_service.list_tasks(status="dispatched")
        if not success or not result.get("tasks"):
            return

        tasks = result["tasks"]
        logger.info(f"📥 Worker found {len(tasks)} dispatched tasks. Processing...")

        for task in tasks:
            task_id = task["id"]
            agent_id = task.get("assignee")

            if not agent_id:
                logger.warning(f"Task {task_id} is dispatched but has no assignee. Skipping.")
                continue

            # 2. Mark as processing to prevent other workers (if any) from picking it up
            # Phase 5.1.0: Use 'processing' as a lock state
            await task_service.update_task(task_id, {"status": "processing"})

            # 3. Wait for rate limit capacity before executing
            # This replaces the sleep in the agent execution loop
            # Note: We assume 'lite' tier by default, or could deduce from agent_id
            await global_throttler.wait_for_capacity(tier="lite")

            # 4. Execute the task
            # We call run_agent_task with immediate=True to bypass enqueuing
            try:
                logger.info(f"⚙️ Worker executing task {task_id} for agent {agent_id}")
                # We need to make sure run_agent_task doesn't re-enqueue
                await agent_service.run_agent_task(task_id=task_id, agent_id=agent_id, immediate=True)
            except Exception as e:
                logger.error(f"Worker failed to execute task {task_id}: {e}")
                await task_service.update_task(task_id, {"status": "failed"})


worker_service = WorkerService()
