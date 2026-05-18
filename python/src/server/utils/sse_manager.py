"""
SSE Manager for Archon (Phase 5.1.0)
Handles Server-Sent Events broadcasting for real-time task updates.
"""

import asyncio
import json
from typing import Any

from src.server.config.logfire_config import get_logger

logger = get_logger(__name__)


class SSEManager:
    """
    Manages client subscriptions and broadcasts events via SSE.
    """

    def __init__(self):
        # Queues for active subscribers: {queue_id: asyncio.Queue}
        self.subscribers: dict[str, asyncio.Queue] = {}

    async def subscribe(self) -> tuple[str, asyncio.Queue]:
        """Subscribe a new client and return a unique ID and its queue"""
        import uuid
        subscriber_id = str(uuid.uuid4())
        queue: asyncio.Queue[str] = asyncio.Queue()
        self.subscribers[subscriber_id] = queue
        logger.info(f"📡 SSE Client subscribed: {subscriber_id} (Total: {len(self.subscribers)})")
        return subscriber_id, queue

    def unsubscribe(self, subscriber_id: str):
        """Remove a subscriber"""
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]
            logger.info(f"📡 SSE Client unsubscribed: {subscriber_id} (Total: {len(self.subscribers)})")

    async def broadcast(self, event_type: str, data: Any):
        """Broadcast an event to all subscribers"""
        if not self.subscribers:
            return

        # Format as SSE event string
        sse_message = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

        # Push to all queues
        for sub_id, queue in self.subscribers.items():
            try:
                await queue.put(sse_message)
            except Exception as e:
                logger.error(f"Failed to push SSE message to {sub_id}: {e}")

    async def event_generator(self, subscriber_id: str, queue: asyncio.Queue[str]):
        """Generator for StreamingResponse"""
        try:
            # Initial keep-alive or welcome message
            yield f"event: welcome\ndata: {json.dumps({'id': subscriber_id})}\n\n"

            while True:
                message = await queue.get()
                yield message
        except asyncio.CancelledError:
            self.unsubscribe(subscriber_id)
            raise


sse_manager = SSEManager()
