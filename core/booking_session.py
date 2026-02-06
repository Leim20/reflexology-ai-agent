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

# Fields to show in booking confirmation (excludes discovery fields like pain_point)
CONFIRMATION_FIELDS = ["customer_name", "customer_gender", "phone", "service", "date", "time", "therapist_gender"]

# Sequential flow order for collecting booking info
BOOKING_FLOW_SEQUENCE = ["pain_point", "service", "datetime", "therapist_gender"]

_redis = None

GENDER_FIELDS = {"customer_gender", "therapist_gender"}


def normalize_phone(phone: str) -> str:
    """Normalize Malaysian phone number: 011xxxxxxxx → 6011xxxxxxxx."""
    cleaned = phone.replace("-", "").replace(" ", "").replace("+", "")
    if cleaned.startswith("0"):
        cleaned = "60" + cleaned[1:]
    return cleaned


def normalize_gender(value: str) -> str:
    """Normalize gender to Male/Female for storage."""
    v = value.strip().lower()
    if "男" in v or v == "male":
        return "Male"
    if "女" in v or v == "female":
        return "Female"
    return value


def normalize_booking_date(date_str: str) -> str:
    """Normalize date to YYYY-MM-DD format (Layer 2 safety net)."""
    import re
    from datetime import datetime, timedelta

    if not date_str:
        return date_str

    original = date_str
    date_str = date_str.strip().lower()
    today = datetime.now()

    # Already YYYY-MM-DD — pass through
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str

    # Relative dates
    if date_str in ['今天', 'today', '今日', 'hari ini']:
        return today.strftime('%Y-%m-%d')
    if date_str in ['明天', 'tomorrow', '明日', 'esok']:
        return (today + timedelta(days=1)).strftime('%Y-%m-%d')
    if date_str in ['后天', 'day after tomorrow', 'lusa']:
        return (today + timedelta(days=2)).strftime('%Y-%m-%d')

    # English month names: "february 16" / "16 february" / "feb 16"
    MONTHS = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
        'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
        'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12,
    }
    # "february 16" or "feb 16"
    m1 = re.match(r'([a-z]+)\s+(\d{1,2})', date_str)
    if m1 and m1.group(1) in MONTHS:
        month = MONTHS[m1.group(1)]
        day = int(m1.group(2))
        return f'{today.year}-{month:02d}-{day:02d}'
    # "16 february" or "16 feb"
    m2 = re.match(r'(\d{1,2})\s+([a-z]+)', date_str)
    if m2 and m2.group(2) in MONTHS:
        day = int(m2.group(1))
        month = MONTHS[m2.group(2)]
        return f'{today.year}-{month:02d}-{day:02d}'

    # Chinese: 2025年12月28日 or 12月28日
    cn_full = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
    if cn_full:
        y, m, d = cn_full.groups()
        return f'{y}-{m.zfill(2)}-{d.zfill(2)}'
    cn_short = re.match(r'(\d{1,2})月(\d{1,2})日', date_str)
    if cn_short:
        m, d = cn_short.groups()
        return f'{today.year}-{m.zfill(2)}-{d.zfill(2)}'

    logger.warning("normalize_booking_date: could not parse '%s', returning as-is", original)
    return original


def normalize_booking_time(time_str: str) -> str:
    """Normalize time to HH:MM 24h format (Layer 2 safety net)."""
    import re

    if not time_str:
        return time_str

    original = time_str
    time_str = time_str.strip()

    # Already HH:MM
    if re.match(r'^\d{1,2}:\d{2}$', time_str):
        h, m = time_str.split(':')
        return f'{int(h):02d}:{m}'

    # "6:00 PM" / "3:10 AM"
    pm_match = re.match(r'(\d{1,2}):(\d{2})\s*(PM|AM)', time_str, re.IGNORECASE)
    if pm_match:
        h, m, period = pm_match.groups()
        h = int(h)
        if period.upper() == 'PM' and h != 12:
            h += 12
        elif period.upper() == 'AM' and h == 12:
            h = 0
        return f'{h:02d}:{m}'

    # "6pm" / "6 pm" / "6am" / "6 am" (no colon)
    bare_match = re.match(r'(\d{1,2})\s*(pm|am)', time_str, re.IGNORECASE)
    if bare_match:
        h, period = bare_match.groups()
        h = int(h)
        if period.upper() == 'PM' and h != 12:
            h += 12
        elif period.upper() == 'AM' and h == 12:
            h = 0
        return f'{h:02d}:00'

    # Chinese: 下午3点10分 / 晚上8点
    cn_match = re.match(r'(上午|下午|晚上|早上)?(\d{1,2})[点时](?:(\d{1,2})分?)?', time_str)
    if cn_match:
        period, h, m = cn_match.groups()
        h = int(h)
        m = int(m) if m else 0
        if period in ['下午', '晚上'] and h < 12:
            h += 12
        return f'{h:02d}:{m:02d}'

    logger.warning("normalize_booking_time: could not parse '%s', returning as-is", original)
    return original


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
            if field == "phone":
                value = normalize_phone(value)
            elif field in GENDER_FIELDS:
                value = normalize_gender(value)
            elif field == "date":
                value = normalize_booking_date(value)
            elif field == "time":
                value = normalize_booking_time(value)
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

    # Step 5: Confirm personal info (name, gender, phone)
    # Always ask even if already known - for verification
    personal_info_asked = session.get('_personal_info_asked', False)
    if not personal_info_asked:
        missing = []
        for f in ("customer_name", "customer_gender", "phone"):
            if not session.get(f):
                missing.append(f)
        return {
            "step": "personal_info",
            "missing": missing,
            "session": session
        }

    # All essential booking fields complete
    return {
        "step": "complete",
        "missing": [],
        "session": session
    }


def mark_personal_info_asked(session_id: str) -> None:
    """Mark that personal info confirmation has been asked."""
    r = _get_redis()
    raw = r.get(_key(session_id))
    if raw:
        session = json.loads(raw)
    else:
        session = {field: None for field in REQUIRED_FIELDS}

    session['_personal_info_asked'] = True
    r.set(_key(session_id), json.dumps(session), ex=BOOKING_TTL)
    logger.info("BOOKING SESSION | %s | personal_info_asked marked", session_id)


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
