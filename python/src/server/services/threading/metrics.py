"""
Threading Metrics Submodule
"""

import threading
import time
from dataclasses import dataclass, field

import psutil


@dataclass
class SystemMetrics:
    """Current system performance metrics"""

    memory_percent: float
    cpu_percent: float
    available_memory_gb: float
    active_threads: int
    timestamp: float = field(default_factory=time.time)


def get_system_metrics() -> SystemMetrics:
    """Get current system performance metrics"""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=None)
    active_threads = threading.active_count()

    return SystemMetrics(
        memory_percent=memory.percent,
        cpu_percent=cpu_percent,
        available_memory_gb=memory.available / (1024**3),
        active_threads=active_threads,
    )
