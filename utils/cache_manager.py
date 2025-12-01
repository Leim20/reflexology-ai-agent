"""Cache Manager Utility"""
import time
from typing import Any, Optional
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)

class CacheManager:
    def __init__(self, default_ttl: int = 60):
        self._cache = {}
        self._default_ttl = default_ttl
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "invalidations": 0, "errors": 0}
        logger.info("CACHE MANAGER INITIALIZED | TTL: %s seconds" % default_ttl)
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            self._stats["misses"] += 1
            logger.debug("CACHE MISS: %s" % key)
            return None
        entry = self._cache[key]
        if datetime.now() > entry["expires_at"]:
            del self._cache[key]
            self._stats["misses"] += 1
            return None
        self._stats["hits"] += 1
        logger.debug("CACHE HIT: %s" % key)
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl if ttl is not None else self._default_ttl
        self._cache[key] = {"value": value, "created_at": datetime.now(), "expires_at": datetime.now() + timedelta(seconds=ttl), "ttl": ttl}
        self._stats["sets"] += 1
        logger.debug("CACHE SET: %s | TTL: %ss" % (key, ttl))
    
    def invalidate(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            self._stats["invalidations"] += 1
            logger.info("CACHE INVALIDATED: %s" % key)
            return True
        return False
    
    def get_stats(self) -> dict:
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
        return {**self._stats, "total_requests": total, "hit_rate": "%.1f%%" % hit_rate, "cache_size": len(self._cache)}

global_cache = CacheManager(default_ttl=60)
logger.info("Cache Manager module loaded")
