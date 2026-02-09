"""
Booking Session Manager - MySQL-backed CRUD for booking sessions.

Replaces Redis for booking sessions to:
1. Persist sessions across server restarts
2. Enable session expiry logic (< 1h, 1-24h, > 24h)
3. Prevent hallucination by isolating booking state from conversation history

Session Expiry Logic:
- < 1 hour since last update: Auto-continue booking
- 1-24 hours since last update: Auto-continue booking
- > 24 hours since last update: Ask user if they want to continue
"""

import mysql.connector
from mysql.connector import pooling
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from utils.logger import get_logger
import json
import os

logger = get_logger(__name__)

# Connection pool for efficiency
_connection_pool = None

REQUIRED_FIELDS = [
    "customer_name",
    "customer_gender",
    "service",
    "date",
    "time",
    "therapist_gender",
    "phone",
    "pain_point",
]

CONFIRMATION_FIELDS = ["customer_name", "customer_gender", "phone", "service", "date", "time", "therapist_gender"]
BOOKING_FLOW_SEQUENCE = ["pain_point", "service", "datetime", "therapist_gender"]
GENDER_FIELDS = {"customer_gender", "therapist_gender"}


def _get_db_config() -> dict:
    """Get MySQL configuration from environment or config file."""
    # Try environment variables first
    config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'reflexology_app'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'reflexology_booking'),
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci',
        'autocommit': True,
    }

    # Try loading from config.json if password not in env
    if not config['password']:
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
            with open(config_path, 'r') as f:
                app_config = json.load(f)
                mysql_config = app_config.get('mysql', {})
                config['host'] = mysql_config.get('host', config['host'])
                config['port'] = mysql_config.get('port', config['port'])
                config['user'] = mysql_config.get('user', config['user'])
                config['password'] = mysql_config.get('password', config['password'])
                config['database'] = mysql_config.get('database', config['database'])
        except Exception as e:
            logger.warning(f"Could not load MySQL config from config.json: {e}")

    return config


def _get_connection():
    """Get a connection from the pool."""
    global _connection_pool

    if _connection_pool is None:
        config = _get_db_config()
        try:
            _connection_pool = pooling.MySQLConnectionPool(
                pool_name="booking_pool",
                pool_size=5,
                pool_reset_session=True,
                **config
            )
            logger.info("MySQL connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create MySQL connection pool: {e}")
            raise

    return _connection_pool.get_connection()


# ============================================================================
# NORMALIZATION FUNCTIONS (same as original booking_session.py)
# ============================================================================

def normalize_phone(phone: str) -> str:
    """Normalize Malaysian phone number: 011xxxxxxxx -> 6011xxxxxxxx."""
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
    """Normalize date to YYYY-MM-DD format."""
    import re
    from datetime import datetime, timedelta

    if not date_str:
        return date_str

    original = date_str
    date_str = date_str.strip().lower()
    today = datetime.now()

    # Already YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str

    # Relative dates
    if date_str in ['今天', 'today', '今日', 'hari ini']:
        return today.strftime('%Y-%m-%d')
    if date_str in ['明天', 'tomorrow', '明日', 'esok']:
        return (today + timedelta(days=1)).strftime('%Y-%m-%d')
    if date_str in ['后天', 'day after tomorrow', 'lusa']:
        return (today + timedelta(days=2)).strftime('%Y-%m-%d')

    # English month names
    MONTHS = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
        'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
        'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12,
    }
    m1 = re.match(r'([a-z]+)\s+(\d{1,2})', date_str)
    if m1 and m1.group(1) in MONTHS:
        month = MONTHS[m1.group(1)]
        day = int(m1.group(2))
        return f'{today.year}-{month:02d}-{day:02d}'
    m2 = re.match(r'(\d{1,2})\s+([a-z]+)', date_str)
    if m2 and m2.group(2) in MONTHS:
        day = int(m2.group(1))
        month = MONTHS[m2.group(2)]
        return f'{today.year}-{month:02d}-{day:02d}'

    # Chinese dates
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
    """Normalize time to HH:MM 24h format."""
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

    # "6pm" / "6 pm"
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


# ============================================================================
# SESSION CRUD OPERATIONS
# ============================================================================

def get_session(session_id: str) -> dict:
    """Return the current booking session dict (empty fields are None)."""
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT customer_name, customer_gender, service,
                   DATE_FORMAT(date, '%%Y-%%m-%%d') as date,
                   TIME_FORMAT(time, '%%H:%%i') as time,
                   therapist_gender, phone, pain_point,
                   pain_point_asked as _pain_point_asked,
                   personal_info_asked as _personal_info_asked,
                   status, updated_at
            FROM booking_sessions
            WHERE session_id = %s AND status = 'active'
        """, (session_id,))

        row = cursor.fetchone()
        if row:
            # Convert to expected format
            session = {field: row.get(field) for field in REQUIRED_FIELDS}
            session['_pain_point_asked'] = bool(row.get('_pain_point_asked'))
            session['_personal_info_asked'] = bool(row.get('_personal_info_asked'))
            return session

        # No session found - return empty
        return {field: None for field in REQUIRED_FIELDS}

    except Exception as e:
        logger.error(f"get_session error: {e}")
        return {field: None for field in REQUIRED_FIELDS}
    finally:
        if conn:
            conn.close()


def get_session_with_expiry_check(session_id: str) -> Tuple[dict, bool, float]:
    """
    Get session with expiry logic check.

    Returns:
        Tuple[session_dict, needs_confirmation, hours_since_update]

    Expiry Logic:
    - < 1 hour: Auto-continue
    - 1-24 hours: Auto-continue
    - > 24 hours: Ask user if they want to continue
    """
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT customer_name, customer_gender, service,
                   DATE_FORMAT(date, '%%Y-%%m-%%d') as date,
                   TIME_FORMAT(time, '%%H:%%i') as time,
                   therapist_gender, phone, pain_point,
                   pain_point_asked as _pain_point_asked,
                   personal_info_asked as _personal_info_asked,
                   status, updated_at,
                   TIMESTAMPDIFF(SECOND, updated_at, NOW()) / 3600.0 as hours_since_update
            FROM booking_sessions
            WHERE session_id = %s AND status = 'active'
        """, (session_id,))

        row = cursor.fetchone()

        if not row:
            # New session - create it
            cursor.execute("""
                INSERT INTO booking_sessions (session_id, expires_at)
                VALUES (%s, DATE_ADD(NOW(), INTERVAL 24 HOUR))
            """, (session_id,))
            conn.commit()

            return {field: None for field in REQUIRED_FIELDS}, False, 0.0

        # Existing session
        hours = float(row.get('hours_since_update', 0))
        needs_confirmation = hours > 24

        # Convert to expected format
        session = {field: row.get(field) for field in REQUIRED_FIELDS}
        session['_pain_point_asked'] = bool(row.get('_pain_point_asked'))
        session['_personal_info_asked'] = bool(row.get('_personal_info_asked'))

        # Refresh expiry if within 24 hours
        if not needs_confirmation:
            cursor.execute("""
                UPDATE booking_sessions
                SET expires_at = DATE_ADD(NOW(), INTERVAL 24 HOUR)
                WHERE session_id = %s
            """, (session_id,))
            conn.commit()

        return session, needs_confirmation, hours

    except Exception as e:
        logger.error(f"get_session_with_expiry_check error: {e}")
        return {field: None for field in REQUIRED_FIELDS}, False, 0.0
    finally:
        if conn:
            conn.close()


def merge_session(session_id: str, extracted: dict) -> dict:
    """Merge extracted fields into the session. Only overwrites non-null values."""
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor(dictionary=True)

        # First ensure session exists
        cursor.execute("""
            INSERT INTO booking_sessions (session_id, expires_at)
            VALUES (%s, DATE_ADD(NOW(), INTERVAL 24 HOUR))
            ON DUPLICATE KEY UPDATE expires_at = DATE_ADD(NOW(), INTERVAL 24 HOUR)
        """, (session_id,))

        # Build update query for non-null fields
        updates = []
        values = []
        changed = []

        for field in REQUIRED_FIELDS:
            value = extracted.get(field)
            if value is not None:
                # Normalize values
                if field == "phone":
                    value = normalize_phone(value)
                elif field in GENDER_FIELDS:
                    value = normalize_gender(value)
                elif field == "date":
                    value = normalize_booking_date(value)
                elif field == "time":
                    value = normalize_booking_time(value)

                updates.append(f"{field} = %s")
                values.append(value)
                changed.append(field)

        if updates:
            values.append(session_id)
            cursor.execute(f"""
                UPDATE booking_sessions
                SET {', '.join(updates)}, updated_at = NOW()
                WHERE session_id = %s
            """, tuple(values))
            conn.commit()

            if changed:
                logger.info("BOOKING SESSION MERGED | %s | updated: %s", session_id, changed)

        # Return updated session
        return get_session(session_id)

    except Exception as e:
        logger.error(f"merge_session error: {e}")
        return get_session(session_id)
    finally:
        if conn:
            conn.close()


def missing_fields(session_id: str) -> list:
    """Return list of required fields that are still None."""
    session = get_session(session_id)
    return [f for f in REQUIRED_FIELDS if session.get(f) is None]


def mark_pain_point_asked(session_id: str) -> None:
    """Mark that pain_point question has been asked (for skip logic)."""
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO booking_sessions (session_id, pain_point_asked, expires_at)
            VALUES (%s, TRUE, DATE_ADD(NOW(), INTERVAL 24 HOUR))
            ON DUPLICATE KEY UPDATE pain_point_asked = TRUE
        """, (session_id,))
        conn.commit()

        logger.info("BOOKING SESSION | %s | pain_point_asked marked", session_id)

    except Exception as e:
        logger.error(f"mark_pain_point_asked error: {e}")
    finally:
        if conn:
            conn.close()


def mark_personal_info_asked(session_id: str) -> None:
    """Mark that personal info confirmation has been asked."""
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO booking_sessions (session_id, personal_info_asked, expires_at)
            VALUES (%s, TRUE, DATE_ADD(NOW(), INTERVAL 24 HOUR))
            ON DUPLICATE KEY UPDATE personal_info_asked = TRUE
        """, (session_id,))
        conn.commit()

        logger.info("BOOKING SESSION | %s | personal_info_asked marked", session_id)

    except Exception as e:
        logger.error(f"mark_personal_info_asked error: {e}")
    finally:
        if conn:
            conn.close()


def get_next_booking_step(session_id: str) -> dict:
    """
    Return the next booking step based on priority sequence.

    Flow: pain_point -> service -> datetime -> therapist_gender -> complete
    """
    session = get_session(session_id)

    # Step 1: Pain point (discovery question) - OPTIONAL
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

    # Step 3: Date and Time
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

    # Step 5: Confirm personal info
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


def get_confirmation_summary(session_id: str) -> dict:
    """Get booking details for confirmation message."""
    session = get_session(session_id)
    return {field: session.get(field) for field in CONFIRMATION_FIELDS}


def clear_session(session_id: str) -> None:
    """Mark booking session as completed (archives to history)."""
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor(dictionary=True)

        # Get current session for archiving
        cursor.execute("""
            SELECT * FROM booking_sessions WHERE session_id = %s
        """, (session_id,))
        row = cursor.fetchone()

        if row:
            # Archive to history
            cursor.execute("""
                INSERT INTO booking_session_history (
                    session_id, customer_name, customer_gender, service,
                    date, time, therapist_gender, phone, pain_point,
                    final_status, session_created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'completed', %s)
            """, (
                row['session_id'], row['customer_name'], row['customer_gender'],
                row['service'], row['date'], row['time'], row['therapist_gender'],
                row['phone'], row['pain_point'], row['created_at']
            ))

            # Delete from active sessions
            cursor.execute("""
                DELETE FROM booking_sessions WHERE session_id = %s
            """, (session_id,))

            conn.commit()

        logger.info("BOOKING SESSION CLEARED | %s", session_id)

    except Exception as e:
        logger.error(f"clear_session error: {e}")
    finally:
        if conn:
            conn.close()


def reset_session_for_new_booking(session_id: str) -> None:
    """
    Reset session for a new booking after > 24h expiry.
    Archives old session and creates fresh one.
    """
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor(dictionary=True)

        # Get current session for archiving
        cursor.execute("""
            SELECT * FROM booking_sessions WHERE session_id = %s
        """, (session_id,))
        row = cursor.fetchone()

        if row:
            # Archive to history as expired
            cursor.execute("""
                INSERT INTO booking_session_history (
                    session_id, customer_name, customer_gender, service,
                    date, time, therapist_gender, phone, pain_point,
                    final_status, session_created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'expired', %s)
            """, (
                row['session_id'], row['customer_name'], row['customer_gender'],
                row['service'], row['date'], row['time'], row['therapist_gender'],
                row['phone'], row['pain_point'], row['created_at']
            ))

            # Delete old session
            cursor.execute("""
                DELETE FROM booking_sessions WHERE session_id = %s
            """, (session_id,))

        # Create fresh session
        cursor.execute("""
            INSERT INTO booking_sessions (session_id, expires_at)
            VALUES (%s, DATE_ADD(NOW(), INTERVAL 24 HOUR))
        """, (session_id,))

        conn.commit()
        logger.info("BOOKING SESSION RESET FOR NEW BOOKING | %s", session_id)

    except Exception as e:
        logger.error(f"reset_session_for_new_booking error: {e}")
    finally:
        if conn:
            conn.close()


def continue_existing_session(session_id: str) -> dict:
    """
    User chose to continue existing > 24h session.
    Just refresh the expiry and return the session.
    """
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE booking_sessions
            SET expires_at = DATE_ADD(NOW(), INTERVAL 24 HOUR),
                updated_at = NOW()
            WHERE session_id = %s
        """, (session_id,))
        conn.commit()

        logger.info("BOOKING SESSION CONTINUED | %s", session_id)
        return get_session(session_id)

    except Exception as e:
        logger.error(f"continue_existing_session error: {e}")
        return get_session(session_id)
    finally:
        if conn:
            conn.close()


# ============================================================================
# VALIDATION LOGGING (for debugging hallucination issues)
# ============================================================================

def log_field_validation(session_id: str, field_name: str, extracted_value: str,
                         validation_result: str, user_message: str, reason: str = None) -> None:
    """Log field validation result for debugging."""
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO field_validation_log
            (session_id, field_name, extracted_value, validation_result, user_message, validation_reason)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (session_id, field_name, extracted_value, validation_result, user_message, reason))
        conn.commit()

    except Exception as e:
        logger.warning(f"Failed to log field validation: {e}")
    finally:
        if conn:
            conn.close()
