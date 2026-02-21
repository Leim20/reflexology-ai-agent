# Cache Manager (Redis-Backed Caching)

## Overview

The Cache Manager is a **Redis-backed caching utility** that reduces API calls to external services (especially Google Sheets). It stores frequently accessed data with automatic TTL (Time-To-Live) expiration.

**Location:** `utils/cache_manager.py`
**Lines of code:** ~74 lines
**Dependencies:** Redis, `utils/redis_client.py`, `utils/logger.py`

---

## What is the Purpose?

The Cache Manager exists to:

1. **Reduce API Calls** — Cache Google Sheets data to avoid quota limits.

2. **Improve Response Time** — Serve cached data instantly (0ms vs 500ms+).

3. **Prevent Rate Limiting** — Stay under Google Sheets 60 requests/minute quota.

4. **Save Costs** — Fewer API calls = lower usage costs.

5. **Handle Traffic Spikes** — Cache absorbs repeated requests.

---

## How It Works

### Cache Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Request                             │
│              "Get member info for 60123456789"              │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Cache Manager                               │
│                                                              │
│  cache.get("member:60123456789")                            │
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │                   CACHE HIT?                     │        │
│  │                                                  │        │
│  │  YES → Return cached data (0ms)                 │        │
│  │        stats["hits"] += 1                       │        │
│  │                                                  │        │
│  │  NO  → Continue to source                       │        │
│  │        stats["misses"] += 1                     │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────┬───────────────────────────────────┘
                          │ CACHE MISS
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 Google Sheets API                            │
│                                                              │
│  1. Fetch data from Google Sheets                           │
│  2. Store in cache with TTL                                 │
│  3. Return data                                             │
│                                                              │
│  cache.set("member:60123456789", data, ttl=300)             │
└─────────────────────────────────────────────────────────────┘
```

---

## The CacheManager Class

### Initialization

```python
class CacheManager:
    def __init__(self, default_ttl: int = 60):
        """
        Initialize Cache Manager with Redis backend.

        Args:
            default_ttl: Default time-to-live in seconds (default: 60)
        """
        self._default_ttl = default_ttl
        self._redis = get_redis_client()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "invalidations": 0,
            "errors": 0
        }
        logger.info(f"CACHE MANAGER INITIALIZED (Redis) | TTL: {default_ttl} seconds")
```

### Key Prefix

All cache keys are prefixed to avoid collisions:

```python
CACHE_PREFIX = "cache:"

# Example keys:
# "cache:member:60123456789"
# "cache:all_members"
# "cache:bookings:60123456789"
```

---

## Key Methods

### 1. get() — Retrieve from Cache

```python
def get(self, key: str) -> Optional[Any]:
    """
    Get value from cache.

    Args:
        key: Cache key (without prefix)

    Returns:
        Cached value or None if not found
    """
    try:
        raw = self._redis.get(f"{CACHE_PREFIX}{key}")
    except Exception as e:
        logger.error(f"CACHE GET ERROR: {e} | key={key}")
        self._stats["errors"] += 1
        return None

    if raw is None:
        self._stats["misses"] += 1
        logger.debug(f"CACHE MISS: {key}")
        return None

    self._stats["hits"] += 1
    logger.debug(f"CACHE HIT: {key}")

    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw
```

**Usage:**

```python
cache = CacheManager(default_ttl=300)

# Get from cache
member = cache.get("member:60123456789")

if member is None:
    # Cache miss - fetch from source
    member = fetch_from_google_sheets(phone)
    cache.set("member:60123456789", member)
```

---

### 2. set() — Store in Cache

```python
def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
    """
    Store value in cache with TTL.

    Args:
        key: Cache key (without prefix)
        value: Value to cache (will be JSON serialized)
        ttl: Time-to-live in seconds (uses default if not specified)
    """
    ttl = ttl if ttl is not None else self._default_ttl

    try:
        serialized = json.dumps(value)
        self._redis.set(f"{CACHE_PREFIX}{key}", serialized, ex=ttl)
    except Exception as e:
        logger.error(f"CACHE SET ERROR: {e} | key={key}")
        self._stats["errors"] += 1
        return

    self._stats["sets"] += 1
    logger.debug(f"CACHE SET: {key} | TTL: {ttl}s")
```

**Usage:**

```python
# Store with default TTL (300 seconds)
cache.set("member:60123456789", member_data)

# Store with custom TTL (10 minutes)
cache.set("all_members", all_members, ttl=600)

# Store with short TTL (30 seconds)
cache.set("temp_data", data, ttl=30)
```

---

### 3. invalidate() — Remove from Cache

```python
def invalidate(self, key: str) -> bool:
    """
    Remove key from cache.

    Use after data changes to ensure fresh data on next request.

    Args:
        key: Cache key to invalidate

    Returns:
        True if key was deleted, False if key didn't exist
    """
    try:
        deleted = self._redis.delete(f"{CACHE_PREFIX}{key}")
    except Exception as e:
        logger.error(f"CACHE INVALIDATE ERROR: {e} | key={key}")
        self._stats["errors"] += 1
        return False

    if deleted:
        self._stats["invalidations"] += 1
        logger.info(f"CACHE INVALIDATED: {key}")
        return True

    return False
```

**Usage:**

```python
# After updating a member's info
lead_manager.update_member(phone, new_data)

# Invalidate cache so next request gets fresh data
cache.invalidate(f"member:{phone}")
cache.invalidate("all_members")
```

---

### 4. get_stats() — Cache Statistics

```python
def get_stats(self) -> dict:
    """
    Get cache statistics.

    Returns:
        dict with hits, misses, sets, invalidations, hit_rate, etc.
    """
    total = self._stats["hits"] + self._stats["misses"]
    hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0

    try:
        cache_size = self._redis.dbsize()
    except Exception:
        cache_size = -1

    return {
        **self._stats,
        "total_requests": total,
        "hit_rate": f"{hit_rate:.1f}%",
        "cache_size": cache_size
    }
```

**Usage:**

```python
stats = cache.get_stats()
print(stats)
# {
#     "hits": 150,
#     "misses": 25,
#     "sets": 30,
#     "invalidations": 10,
#     "errors": 0,
#     "total_requests": 175,
#     "hit_rate": "85.7%",
#     "cache_size": 45
# }
```

---

## Cache Key Patterns

### Recommended Key Structure

```
{entity}:{identifier}
```

| Pattern | Example | Description |
|---------|---------|-------------|
| `member:{phone}` | `member:60123456789` | Single member data |
| `all_members` | `all_members` | All members (bulk) |
| `lead_by_phone:{phone}` | `lead_by_phone:60123456789` | Customer record |
| `bookings:{phone}` | `bookings:60123456789` | Customer's bookings |
| `all_leads` | `all_leads` | All customer records |

---

## TTL Strategy

### Recommended TTL Values

| Data Type | TTL | Reason |
|-----------|-----|--------|
| Member data | 300s (5 min) | Rarely changes |
| Customer records | 300s (5 min) | Updates are infrequent |
| Bookings | 60s (1 min) | May change more often |
| All members (bulk) | 300s (5 min) | Pre-loaded cache |
| Temporary data | 30s | Short-lived |

### TTL Considerations

```
SHORT TTL (30-60s):
+ Data is more fresh
- More cache misses
- More API calls

LONG TTL (300-600s):
+ Fewer API calls
+ Better hit rate
- Data may be stale
- Need manual invalidation
```

---

## Integration in Lead Manager

```python
class LeadManager:
    def __init__(self, ...):
        # Initialize cache with 5 minute TTL
        self.cache_manager = CacheManager(default_ttl=300)

        # Pre-load members into cache on startup
        self._refresh_members_cache()

    def get_member(self, phone: str) -> dict:
        # Try cache first
        all_members = self.cache_manager.get("all_members")

        if all_members and phone in all_members:
            return all_members[phone]  # CACHE HIT

        # Cache miss - fetch from Google Sheets
        member = self._fetch_member_from_sheets(phone)

        return member

    def update_member(self, phone: str, data: dict):
        # Update in Google Sheets
        self._update_member_in_sheets(phone, data)

        # Invalidate cache
        self.cache_manager.invalidate("all_members")
        self.cache_manager.invalidate(f"member:{phone}")
```

---

## Cache Statistics Monitoring

### Log Cache Performance

```python
def log_cache_performance():
    stats = cache.get_stats()

    logger.info("="*60)
    logger.info("CACHE PERFORMANCE REPORT")
    logger.info("="*60)
    logger.info(f"   Hits: {stats['hits']}")
    logger.info(f"   Misses: {stats['misses']}")
    logger.info(f"   Hit Rate: {stats['hit_rate']}")
    logger.info(f"   Total Requests: {stats['total_requests']}")
    logger.info(f"   Cache Size: {stats['cache_size']} keys")
    logger.info(f"   Errors: {stats['errors']}")
    logger.info("="*60)
```

### Healthy Cache Metrics

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Hit Rate | > 80% | 50-80% | < 50% |
| Errors | 0 | 1-5 | > 5 |
| Cache Size | Stable | Growing | Very large |

---

## Global Cache Instance

A global instance is created for convenience:

```python
# At module level
global_cache = CacheManager(default_ttl=60)

# Use anywhere
from utils.cache_manager import global_cache

data = global_cache.get("some_key")
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| All cache misses | Redis not connected | Check Redis connection |
| Stale data | TTL too long | Reduce TTL or invalidate |
| High error rate | Redis issues | Check Redis server |
| Low hit rate | TTL too short | Increase TTL |

### Debug Commands

```python
# Check cache stats
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']}")

# Check if key exists
value = cache.get("member:60123456789")
print(f"Value: {value}")

# Force invalidation
cache.invalidate("all_members")

# Check Redis connection
redis_client = get_redis_client()
print(f"Redis ping: {redis_client.ping()}")
```

---

## Best Practices

### 1. Always Invalidate After Writes

```python
# After ANY write operation
lead_manager.update_member(phone, data)
cache.invalidate(f"member:{phone}")
cache.invalidate("all_members")
```

### 2. Use Consistent Key Naming

```python
# Good - consistent pattern
cache.get(f"member:{phone}")
cache.get(f"bookings:{phone}")

# Bad - inconsistent
cache.get(f"member_{phone}")
cache.get(f"booking-{phone}")
```

### 3. Handle Cache Failures Gracefully

```python
member = cache.get(f"member:{phone}")

if member is None:
    # Cache miss or error - fetch from source
    member = fetch_from_sheets(phone)
    # Try to cache, but don't fail if cache is down
    try:
        cache.set(f"member:{phone}", member)
    except:
        pass  # Continue without caching
```

### 4. Pre-warm Cache on Startup

```python
def _refresh_members_cache(self):
    """Load all members into cache on startup"""
    all_members = self.members_sheet.get_all_values()
    members_dict = parse_members(all_members)
    self.cache_manager.set("all_members", members_dict, ttl=300)
    logger.info(f"Pre-warmed cache with {len(members_dict)} members")
```

---

## Summary

The Cache Manager provides **fast, reliable caching**:

- **Redis-backed** — Persistent, fast, shared across workers
- **TTL expiration** — Automatic cleanup of stale data
- **Statistics tracking** — Monitor hit rate and performance
- **Simple API** — get(), set(), invalidate()
- **Error handling** — Graceful fallback on failures

This reduces Google Sheets API calls by **80-90%** and improves response times significantly.
