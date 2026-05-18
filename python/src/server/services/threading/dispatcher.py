"""
Memory Adaptive Dispatcher Submodule
"""
import asyncio
from collections.abc import Callable
from typing import Any

from ...config.logfire_config import get_logger
from ..shared_constants import ProcessingMode
from .metrics import SystemMetrics, get_system_metrics

logfire_logger = get_logger("threading")

class MemoryAdaptiveDispatcher:
    """Dynamically adjust concurrency based on memory usage"""

    def __init__(self, config):
        self.config = config
        self.current_workers = config.base_workers
        self.last_metrics: SystemMetrics | None = None

    def calculate_optimal_workers(self, mode: ProcessingMode = ProcessingMode.CPU_INTENSIVE) -> int:
        """Calculate optimal worker count based on system load and processing mode"""
        import psutil

        metrics = get_system_metrics()
        self.last_metrics = metrics

        # Base worker count depends on processing mode
        if mode == ProcessingMode.CPU_INTENSIVE:
            base = min(self.config.base_workers, psutil.cpu_count() or 1)
        elif mode == ProcessingMode.IO_BOUND:
            base = self.config.base_workers * 2
        elif mode == ProcessingMode.NETWORK_BOUND:
            base = self.config.base_workers
        else:
            base = self.config.base_workers

        # Adjust based on system load
        if metrics.memory_percent > self.config.memory_threshold * 100:
            workers = max(1, base // 2)
            logfire_logger.warning("High memory usage detected, reducing workers", extra={"memory_percent": metrics.memory_percent, "workers": workers})
        elif metrics.cpu_percent > self.config.cpu_threshold * 100:
            workers = max(1, base // 2)
            logfire_logger.warning("High CPU usage detected, reducing workers", extra={"cpu_percent": metrics.cpu_percent, "workers": workers})
        elif metrics.memory_percent < 50 and metrics.cpu_percent < 50:
            workers = min(self.config.max_workers, base * 2)
        else:
            workers = base

        self.current_workers = workers
        return int(workers)

    async def process_with_adaptive_concurrency(
        self,
        items: list[Any],
        process_func: Callable,
        mode: ProcessingMode = ProcessingMode.CPU_INTENSIVE,
        progress_callback: Callable | None = None,
    ) -> list[Any]:
        """Process items with adaptive concurrency control"""

        if not items:
            return []

        optimal_workers = self.calculate_optimal_workers(mode)
        semaphore = asyncio.Semaphore(optimal_workers)

        if self.last_metrics:
            logfire_logger.info("Starting adaptive processing", extra={"items_count": len(items), "workers": optimal_workers, "mode": mode, "memory_percent": self.last_metrics.memory_percent, "cpu_percent": self.last_metrics.cpu_percent})

        active_workers: dict[int, int] = {}
        completed_count = 0
        lock = asyncio.Lock()

        async def process_single(item: Any, index: int) -> Any:
            nonlocal completed_count
            worker_id = None
            async with lock:
                for i in range(1, optimal_workers + 1):
                    if i not in active_workers:
                        worker_id = i
                        active_workers[worker_id] = index
                        break

            async with semaphore:
                try:
                    if progress_callback and worker_id:
                        await progress_callback({"type": "worker_started", "worker_id": worker_id, "item_index": index, "total_items": len(items), "message": f"Worker {worker_id} processing item {index + 1}"})

                    if mode == ProcessingMode.CPU_INTENSIVE:
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(None, process_func, item)
                    else:
                        if asyncio.iscoroutinefunction(process_func):
                            result = await process_func(item)
                        else:
                            result = process_func(item)

                    async with lock:
                        completed_count += 1
                        if worker_id in active_workers:
                            del active_workers[worker_id]

                    if progress_callback:
                        await progress_callback({"type": "worker_completed", "worker_id": worker_id, "item_index": index, "completed_count": completed_count, "total_items": len(items), "message": f"Worker {worker_id} completed item {index + 1}"})

                    return result

                except Exception as e:
                    async with lock:
                        if worker_id and worker_id in active_workers:
                            del active_workers[worker_id]
                    logfire_logger.error(f"Processing failed for item {index}", extra={"error": str(e), "item_index": index})
                    return None

        tasks = [process_single(item, idx) for idx, item in enumerate(items)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful_results = []
        failed_items = []

        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                failed_items.append({"index": idx, "error": str(result)})
            elif result is None:
                failed_items.append({"index": idx, "error": "Processing returned None"})
            else:
                successful_results.append(result)

        success_rate = len(successful_results) / len(items) * 100
        log_extra = {"total_items": len(items), "successful": len(successful_results), "failed": len(failed_items), "success_rate": f"{success_rate:.1f}%", "workers_used": optimal_workers}

        if failed_items:
            log_extra["failed_items"] = failed_items
            logfire_logger.warning(f"Adaptive processing completed with {len(failed_items)} failures", extra=log_extra)
        else:
            logfire_logger.info("Adaptive processing completed successfully", extra=log_extra)

        return successful_results
