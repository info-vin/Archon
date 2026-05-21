"""
Threading Service for Archon (Facade)
"""

import asyncio
import gc
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Any

from ..config.logfire_config import get_logger
from ..utils.rate_limiter import RateLimitConfig, RateLimiter
from .shared_constants import ProcessingMode
from .threading.dispatcher import MemoryAdaptiveDispatcher
from .threading.metrics import SystemMetrics, get_system_metrics

logfire_logger = get_logger("threading")


class ThreadingConfig:
    """Configuration for threading behavior"""

    base_workers: int = 4
    max_workers: int = 16
    memory_threshold: float = 0.8
    cpu_threshold: float = 0.9
    batch_size: int = 15
    yield_interval: float = 0.1
    health_check_interval: float = 30


class ThreadingService:
    """Main threading service that coordinates all threading operations"""

    def __init__(
        self,
        threading_config: ThreadingConfig | None = None,
        rate_limit_config: RateLimitConfig | None = None,
    ):
        self.config = threading_config or ThreadingConfig()
        self.rate_limiter = RateLimiter(rate_limit_config or RateLimitConfig())
        self.memory_dispatcher = MemoryAdaptiveDispatcher(self.config)

        # Thread pools for different workload types
        self.cpu_executor = ThreadPoolExecutor(max_workers=self.config.max_workers, thread_name_prefix="archon-cpu")
        self.io_executor = ThreadPoolExecutor(max_workers=self.config.max_workers * 2, thread_name_prefix="archon-io")

        self._running = False
        self._health_check_task: asyncio.Task[None] | None = None

    async def start(self):
        if self._running:
            return
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logfire_logger.info("Threading service started", extra={"config": self.config.__dict__})

    async def stop(self):
        if not self._running:
            return
        self._running = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        self.cpu_executor.shutdown(wait=True)
        self.io_executor.shutdown(wait=True)
        logfire_logger.info("Threading service stopped")

    async def run_cpu_intensive(self, func: Callable, *args, **kwargs) -> Any:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.cpu_executor, func, *args, **kwargs)

    async def run_io_bound(self, func: Callable, *args, **kwargs) -> Any:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.io_executor, func, *args, **kwargs)

    async def batch_process(
        self,
        items: list[Any],
        process_func: Callable,
        mode: ProcessingMode = ProcessingMode.CPU_INTENSIVE,
        progress_callback: Callable | None = None,
    ) -> list[Any]:
        return await self.memory_dispatcher.process_with_adaptive_concurrency(
            items, process_func, mode, progress_callback
        )

    @asynccontextmanager
    async def rate_limited_operation(self, estimated_tokens: int = 8000, progress_callback: Callable | None = None):
        async with self.rate_limiter.semaphore:
            can_proceed = await self.rate_limiter.acquire(estimated_tokens, progress_callback)
            if not can_proceed:
                raise Exception("Rate limit exceeded")

            start_time = time.time()
            try:
                yield
            finally:
                duration = time.time() - start_time
                logfire_logger.debug(
                    "Rate limited operation completed",
                    extra={"duration": duration, "tokens": estimated_tokens},
                )

    def get_system_metrics(self) -> SystemMetrics:
        return get_system_metrics()

    async def _health_check_loop(self):
        while self._running:
            try:
                metrics = get_system_metrics()
                logfire_logger.info(
                    "System health check",
                    extra={
                        "memory_percent": metrics.memory_percent,
                        "cpu_percent": metrics.cpu_percent,
                        "available_memory_gb": metrics.available_memory_gb,
                        "active_threads": metrics.active_threads,
                    },
                )

                if metrics.memory_percent > 90:
                    gc.collect()
                    try:
                        from .log_service import log_service

                        log_service.create_log_entry(
                            {
                                "project_name": "system-resource",
                                "gemini_response": f"CRITICAL: Memory usage at {metrics.memory_percent}%",
                                "user_input": "Automatic Health Check",
                            }
                        )
                    except Exception:
                        pass

                if metrics.cpu_percent > 95:
                    try:
                        from .log_service import log_service

                        log_service.create_log_entry(
                            {
                                "project_name": "system-resource",
                                "gemini_response": f"CRITICAL: CPU usage at {metrics.cpu_percent}%",
                                "user_input": "Automatic Health Check",
                            }
                        )
                    except Exception:
                        pass

                await asyncio.sleep(self.config.health_check_interval)
            except Exception as e:
                logfire_logger.error("Health check failed", extra={"error": str(e)})
                await asyncio.sleep(self.config.health_check_interval)


_threading_service: ThreadingService | None = None


def get_threading_service() -> ThreadingService:
    global _threading_service
    if _threading_service is None:
        _threading_service = ThreadingService()
    return _threading_service


async def start_threading_service() -> ThreadingService:
    service = get_threading_service()
    await service.start()
    return service


async def stop_threading_service():
    global _threading_service
    if _threading_service:
        await _threading_service.stop()
        _threading_service = None
