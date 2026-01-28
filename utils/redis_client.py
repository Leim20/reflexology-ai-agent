"""Redis Client Utility - Connection factory for Redis"""
import os
import redis
from utils.logger import get_logger

logger = get_logger(__name__)


def get_redis_client() -> redis.Redis:
    """Create and return a Redis connection using environment variables."""
    host = os.getenv("REDIS_HOST", "127.0.0.1")
    port = int(os.getenv("REDIS_PORT", 6379))
    password = os.getenv("REDIS_PASSWORD", None)

    client = redis.Redis(
        host=host,
        port=port,
        password=password,
        decode_responses=True,
    )
    logger.info("Redis client created | host=%s port=%s", host, port)
    return client
