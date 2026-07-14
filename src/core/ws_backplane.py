import logging
import asyncio
import redis.asyncio as redis
from typing import Callable, Awaitable

from src.core.config import settings

logger = logging.getLogger(__name__)

class RedisPubSubBackplane:
    """
    Redis Pub/Sub Backplane for WebSocket Scaling.
    Allows multi-user event broadcasting across horizontally scaled FastAPI pods.
    """
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.pubsub = self.redis.pubsub()
        self.subscriptions = {}
        self._listener_task = None

    async def start(self):
        """Starts the background listener task for Redis messages."""
        self._listener_task = asyncio.create_task(self._listen())
        logger.info("Redis Pub/Sub Backplane started.")

    async def _listen(self):
        """Listens to all subscribed channels and routes messages to callbacks."""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    data = message["data"]
                    if channel in self.subscriptions:
                        for callback in self.subscriptions[channel]:
                            try:
                                await callback(data)
                            except Exception as e:
                                logger.error(f"Error in Pub/Sub callback for channel {channel}: {e}")
        except Exception as e:
            logger.error(f"Redis listener encountered an error: {e}")

    async def subscribe(self, channel: str, callback: Callable[[str], Awaitable[None]]):
        """Subscribes a WebSocket connection callback to a Redis channel."""
        if channel not in self.subscriptions:
            self.subscriptions[channel] = []
            await self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to Redis channel: {channel}")
            
        self.subscriptions[channel].append(callback)

    async def unsubscribe(self, channel: str, callback: Callable[[str], Awaitable[None]]):
        """Removes a WebSocket connection callback from a Redis channel."""
        if channel in self.subscriptions:
            if callback in self.subscriptions[channel]:
                self.subscriptions[channel].remove(callback)
            if not self.subscriptions[channel]:
                await self.pubsub.unsubscribe(channel)
                del self.subscriptions[channel]
                logger.info(f"Unsubscribed from Redis channel: {channel}")

    async def publish(self, channel: str, message: str):
        """Publishes a message to all FastAPI nodes listening on the channel."""
        await self.redis.publish(channel, message)

# Singleton instance
pubsub_backplane = RedisPubSubBackplane()
