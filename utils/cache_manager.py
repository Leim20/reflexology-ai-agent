"""Cache Manager Utility - Redis-backed cache with TTL"""
import json
from typing import Any, Optional
from utils.logger import get_logger
from utils.redis_client import get_redis_client

logger = get_logger(__name__)

CACHE_PREFIX = "cache:"


class CacheManager:
    def __init__(self, default_ttl: int = 60):
        self._default_ttl = default_ttl
        self._redis = get_redis_client()
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "invalidations": 0, "errors": 0}
        logger.info("CACHE MANAGER INITIALIZED (Redis) | TTL: %s seconds" % default_ttl)

    def get(self, key: str) -> Optional[Any]:
        try:
            raw = self._redis.get(f"{CACHE_PREFIX}{key}")
        except Exception as e:
            logger.error("CACHE GET ERROR: %s | key=%s" % (e, key))
            self._stats["errors"] += 1
            return None
        if raw is None:
            self._stats["misses"] += 1
            logger.debug("CACHE MISS: %s" % key)
            return None
        self._stats["hits"] += 1
        logger.debug("CACHE HIT: %s" % key)
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl if ttl is not None else self._default_ttl
        try:
            serialized = json.dumps(value)
            self._redis.set(f"{CACHE_PREFIX}{key}", serialized, ex=ttl)
        except Exception as e:
            logger.error("CACHE SET ERROR: %s | key=%s" % (e, key))
            self._stats["errors"] += 1
            return
        self._stats["sets"] += 1
        logger.debug("CACHE SET: %s | TTL: %ss" % (key, ttl))

    def invalidate(self, key: str) -> bool:
        try:
            deleted = self._redis.delete(f"{CACHE_PREFIX}{key}")
        except Exception as e:
            logger.error("CACHE INVALIDATE ERROR: %s | key=%s" % (e, key))
            self._stats["errors"] += 1
            return False
        if deleted:
            self._stats["invalidations"] += 1
            logger.info("CACHE INVALIDATED: %s" % key)
            return True
        return False

    def get_stats(self) -> dict:
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
        try:
            cache_size = self._redis.dbsize()
        except Exception:
            cache_size = -1
        return {**self._stats, "total_requests": total, "hit_rate": "%.1f%%" % hit_rate, "cache_size": cache_size}


global_cache = CacheManager(default_ttl=60)
logger.info("Cache Manager module loaded (Redis backend)")
