"""Booking Session Manager - Redis-backed CRUD for booking sessions"""
import json
from typing import Optional
from utils.redis_client import get_redis_client
from utils.logger import get_logger

logger = get_logger(__name__)

BOOKING_TTL = 3600  # 1 hour auto-cleanup
REDIS_PREFIX = "booking:"

REQUIRED_FIELDS = [
    "customer_name",
    "customer_gender",
    "service",
    "date",
    "time",
    "therapist_gender",
    "phone",
]

_redis = None


def _get_redis():
    global _redis
    if _redis is None:
        _redis = get_redis_client()
    return _redis


def _key(session_id: str) -> str:
    return f"{REDIS_PREFIX}{session_id}"


def get_session(session_id: str) -> dict:
    """Return the current booking session dict (empty fields are None)."""
    r = _get_redis()
    raw = r.get(_key(session_id))
    if raw:
        return json.loads(raw)
    return {field: None for field in REQUIRED_FIELDS}


def merge_session(session_id: str, extracted: dict) -> dict:
    """Merge extracted fields into the session. Only overwrites non-null values."""
    current = get_session(session_id)
    changed = []
    for field in REQUIRED_FIELDS:
        value = extracted.get(field)
        if value is not None:
            current[field] = value
            changed.append(field)
    r = _get_redis()
    r.set(_key(session_id), json.dumps(current), ex=BOOKING_TTL)
    if changed:
        logger.info("BOOKING SESSION MERGED | %s | updated: %s", session_id, changed)
    return current


def missing_fields(session_id: str) -> list:
    """Return list of required fields that are still None."""
    session = get_session(session_id)
    return [f for f in REQUIRED_FIELDS if session.get(f) is None]


def clear_session(session_id: str) -> None:
    """Delete the booking session from Redis."""
    r = _get_redis()
    r.delete(_key(session_id))
    logger.info("BOOKING SESSION CLEARED | %s", session_id)
