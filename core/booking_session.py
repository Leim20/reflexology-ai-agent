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
    "pain_point",  # Discovery field - not shown in confirmation
]

# Fields to show in booking confirmation (excludes discovery fields)
CONFIRMATION_FIELDS = ["service", "date", "time", "therapist_gender"]

# Sequential flow order for collecting booking info
BOOKING_FLOW_SEQUENCE = ["pain_point", "service", "datetime", "therapist_gender"]

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


def mark_pain_point_asked(session_id: str) -> None:
    """Mark that pain_point question has been asked (for skip logic)."""
    r = _get_redis()
    raw = r.get(_key(session_id))
    if raw:
        session = json.loads(raw)
    else:
        session = {field: None for field in REQUIRED_FIELDS}

    session['_pain_point_asked'] = True
    r.set(_key(session_id), json.dumps(session), ex=BOOKING_TTL)
    logger.info("BOOKING SESSION | %s | pain_point_asked marked", session_id)


def get_next_booking_step(session_id: str) -> dict:
    """
    Return the next booking step based on priority sequence.

    Flow: pain_point → service → datetime → therapist_gender → complete

    Pain point is OPTIONAL - if asked once and user didn't answer, skip to service.

    Returns:
        dict: {"step": "step_name", "missing": ["field1", ...], "session": {...}}
    """
    session = get_session(session_id)

    # Step 1: Pain point (discovery question) - OPTIONAL
    # Skip if: already answered OR already asked once
    pain_point_asked = session.get('_pain_point_asked', False)
    if not session.get('pain_point') and not pain_point_asked:
        return {
            "step": "pain_point",
            "missing": ["pain_point"],
            "session": session
        }

    # Step 2: Service selection
    if not session.get('service'):
        return {
            "step": "service",
            "missing": ["service"],
            "session": session
        }

    # Step 3: Date and Time (both needed together)
    if not session.get('date') or not session.get('time'):
        missing = []
        if not session.get('date'):
            missing.append('date')
        if not session.get('time'):
            missing.append('time')
        return {
            "step": "datetime",
            "missing": missing,
            "session": session
        }

    # Step 4: Therapist gender preference
    if not session.get('therapist_gender'):
        return {
            "step": "therapist_gender",
            "missing": ["therapist_gender"],
            "session": session
        }

    # All essential booking fields complete
    return {
        "step": "complete",
        "missing": [],
        "session": session
    }


def get_confirmation_summary(session_id: str) -> dict:
    """
    Get booking details for confirmation message.
    Only returns CONFIRMATION_FIELDS (excludes discovery fields like pain_point).
    """
    session = get_session(session_id)
    return {field: session.get(field) for field in CONFIRMATION_FIELDS}


def clear_session(session_id: str) -> None:
    """Delete the booking session from Redis."""
    r = _get_redis()
    r.delete(_key(session_id))
    logger.info("BOOKING SESSION CLEARED | %s", session_id)
