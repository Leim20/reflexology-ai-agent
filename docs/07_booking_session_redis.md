# Booking Session Management (Redis)

## Overview

The Booking Session Manager handles the **stateful, multi-step booking conversation flow**. When a customer wants to book an appointment, their booking information is collected across multiple messages. This module stores the partial booking data in Redis and tracks what information is still missing.

**Source file:** `core/booking_session.py`
**Lines of code:** ~327 lines
**Dependencies:** `redis`, `utils.redis_client`, `utils.logger`

---

## What is the Purpose?

The Booking Session Manager exists to:

1. **Maintain state across messages** — Booking requires multiple pieces of information (name, date, time, service, etc.). Redis stores partial data between customer messages.

2. **Track missing fields** — The system knows what information is still needed and prompts the customer accordingly.

3. **Normalize data** — Phone numbers, dates, times, and gender values are standardized before storage.

4. **Define booking flow** — The sequence of questions (pain point → service → datetime → therapist) is defined here.

5. **Support TTL cleanup** — Sessions auto-expire after 1 hour to prevent stale data accumulation.

---

## How It Works

### Booking Flow Sequence

```
┌─────────────────────────────────────────────────────────────┐
│                    BOOKING FLOW                              │
└─────────────────────────────────────────────────────────────┘

Step 1: Pain Point (Discovery) — OPTIONAL
        ↓
        "What brings you in today? Any areas that need attention?"
        ↓
        Customer: "My shoulders are very tight"
        ↓
        [pain_point = "shoulders"]

Step 2: Service Selection — REQUIRED
        ↓
        "Based on that, I recommend our 60-min body massage..."
        ↓
        Customer: "Yes, I'll take the 60 min body massage"
        ↓
        [service = "60-min body massage"]

Step 3: Date & Time — REQUIRED
        ↓
        "When would you like to come in?"
        ↓
        Customer: "Tomorrow 3pm"
        ↓
        [date = "2026-02-14", time = "15:00"]

Step 4: Therapist Preference — REQUIRED
        ↓
        "Do you have a preference for male or female therapist?"
        ↓
        Customer: "Female please"
        ↓
        [therapist_gender = "Female"]

Step 5: Personal Info Confirmation — REQUIRED
        ↓
        "May I have your name and contact number?"
        ↓
        Customer: "I'm Alex, 0123456789"
        ↓
        [customer_name = "Alex", phone = "60123456789"]

Step 6: COMPLETE — Generate Confirmation
        ↓
        "Perfect! Your booking is confirmed: ..."
```

### Data Structure in Redis

```
Key: "booking:60123456789"
Value: {
    "customer_name": "Alex",
    "customer_gender": "Male",
    "service": "60-min body massage",
    "date": "2026-02-14",
    "time": "15:00",
    "therapist_gender": "Female",
    "phone": "60123456789",
    "pain_point": "shoulders",
    "_pain_point_asked": true,
    "_personal_info_asked": true
}
TTL: 3600 seconds (1 hour)
```

---

## Key Constants

### Required Fields

```python
REQUIRED_FIELDS = [
    "customer_name",      # Customer's name
    "customer_gender",    # Male or Female
    "service",            # Selected service (e.g., "60-min body massage")
    "date",               # YYYY-MM-DD format
    "time",               # HH:MM 24-hour format
    "therapist_gender",   # Male or Female
    "phone",              # Malaysian format (60xxxxxxxxx)
    "pain_point",         # Discovery field (not shown in confirmation)
]
```

### Confirmation Fields

Fields shown in the booking confirmation (excludes discovery fields):

```python
CONFIRMATION_FIELDS = [
    "customer_name",
    "customer_gender",
    "phone",
    "service",
    "date",
    "time",
    "therapist_gender"
]
```

### Flow Sequence

```python
BOOKING_FLOW_SEQUENCE = ["pain_point", "service", "datetime", "therapist_gender"]
```

---

## Key Functions

### 1. `get_session(session_id)` — Retrieve Booking Session

**Purpose:** Get the current booking session data for a customer.

```python
session = get_session("60123456789")
# Returns:
# {
#     "customer_name": "Alex",
#     "service": "60-min body massage",
#     "date": None,  # Not yet collected
#     ...
# }
```

### 2. `merge_session(session_id, extracted)` — Update Session

**Purpose:** Merge newly extracted fields into the existing session.

```python
extracted = {
    "date": "2026-02-14",
    "time": "15:00"
}
updated_session = merge_session("60123456789", extracted)
```

**Key behaviors:**
- Only non-null values are merged
- Phone numbers are normalized (0123... → 60123...)
- Gender values are normalized (男 → Male)
- Dates are normalized to YYYY-MM-DD
- Times are normalized to HH:MM

### 3. `missing_fields(session_id)` — Check What's Missing

**Purpose:** Get list of fields still needed.

```python
missing = missing_fields("60123456789")
# Returns: ["date", "time", "therapist_gender"]
```

### 4. `get_next_booking_step(session_id)` — Flow Control

**Purpose:** Determine the next step in the booking flow.

```python
step_info = get_next_booking_step("60123456789")
# Returns:
# {
#     "step": "datetime",
#     "missing": ["date", "time"],
#     "session": {...}
# }
```

**Possible steps:**
- `"pain_point"` — Ask about concerns (optional)
- `"service"` — Ask for service selection
- `"datetime"` — Ask for date and time
- `"therapist_gender"` — Ask for therapist preference
- `"personal_info"` — Confirm name, gender, phone
- `"complete"` — All fields collected

### 5. `get_confirmation_summary(session_id)` — For Confirmation Message

**Purpose:** Get booking details formatted for confirmation.

```python
summary = get_confirmation_summary("60123456789")
# Returns only CONFIRMATION_FIELDS (excludes pain_point)
```

### 6. `clear_session(session_id)` — Delete Session

**Purpose:** Remove booking session after completion or cancellation.

```python
clear_session("60123456789")
```

---

## Normalization Functions

### Phone Number Normalization

```python
def normalize_phone(phone: str) -> str:
    """
    011xxxxxxxx → 6011xxxxxxxx
    0123456789  → 60123456789
    +60123456789 → 60123456789
    """
```

**Examples:**
- `"60120000000"` → `"60120000000"`
- `"0123456789"` → `"60123456789"`
- `"+60123456789"` → `"60123456789"`

### Gender Normalization

```python
def normalize_gender(value: str) -> str:
    """
    男 / male → Male
    女 / female → Female
    """
```

**Examples:**
- `"男"` → `"Male"`
- `"女的"` → `"Female"`
- `"male"` → `"Male"`

### Date Normalization

```python
def normalize_booking_date(date_str: str) -> str:
    """
    Converts various date formats to YYYY-MM-DD
    """
```

**Examples:**
- `"今天"` → `"2026-02-13"`
- `"明天"` → `"2026-02-14"`
- `"february 16"` → `"2026-02-16"`
- `"2月15号"` → `"2026-02-15"`

### Time Normalization

```python
def normalize_booking_time(time_str: str) -> str:
    """
    Converts various time formats to HH:MM (24-hour)
    """
```

**Examples:**
- `"6pm"` → `"18:00"`
- `"3:30 PM"` → `"15:30"`
- `"下午3点"` → `"15:00"`
- `"晚上8点半"` → `"20:30"`

---

## Step-by-Step: How I Built This

### Step 1: Set Up Redis Connection

```python
from utils.redis_client import get_redis_client

REDIS_PREFIX = "booking:"
BOOKING_TTL = 3600  # 1 hour

_redis = None

def _get_redis():
    global _redis
    if _redis is None:
        _redis = get_redis_client()
    return _redis

def _key(session_id: str) -> str:
    return f"{REDIS_PREFIX}{session_id}"
```

### Step 2: Define Session Storage

```python
def get_session(session_id: str) -> dict:
    r = _get_redis()
    raw = r.get(_key(session_id))
    if raw:
        return json.loads(raw)
    # Return empty session with all fields as None
    return {field: None for field in REQUIRED_FIELDS}
```

### Step 3: Implement Merge Logic

```python
def merge_session(session_id: str, extracted: dict) -> dict:
    current = get_session(session_id)
    changed = []

    for field in REQUIRED_FIELDS:
        value = extracted.get(field)
        if value is not None:
            # Apply normalizations
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

    # Save back to Redis with TTL
    r = _get_redis()
    r.set(_key(session_id), json.dumps(current), ex=BOOKING_TTL)

    if changed:
        logger.info(f"BOOKING SESSION MERGED | {session_id} | updated: {changed}")

    return current
```

### Step 4: Implement Flow Control

```python
def get_next_booking_step(session_id: str) -> dict:
    session = get_session(session_id)

    # Step 1: Pain point (optional)
    pain_point_asked = session.get('_pain_point_asked', False)
    if not session.get('pain_point') and not pain_point_asked:
        return {"step": "pain_point", "missing": ["pain_point"], "session": session}

    # Step 2: Service
    if not session.get('service'):
        return {"step": "service", "missing": ["service"], "session": session}

    # Step 3: Date and Time
    if not session.get('date') or not session.get('time'):
        missing = []
        if not session.get('date'): missing.append('date')
        if not session.get('time'): missing.append('time')
        return {"step": "datetime", "missing": missing, "session": session}

    # Step 4: Therapist preference
    if not session.get('therapist_gender'):
        return {"step": "therapist_gender", "missing": ["therapist_gender"], "session": session}

    # Step 5: Personal info
    if not session.get('_personal_info_asked'):
        missing = [f for f in ("customer_name", "customer_gender", "phone") if not session.get(f)]
        return {"step": "personal_info", "missing": missing, "session": session}

    # All complete
    return {"step": "complete", "missing": [], "session": session}
```

### Step 5: Add Skip Logic for Optional Fields

```python
def mark_pain_point_asked(session_id: str) -> None:
    """Mark that pain_point question has been asked (for skip logic)."""
    r = _get_redis()
    raw = r.get(_key(session_id))
    session = json.loads(raw) if raw else {field: None for field in REQUIRED_FIELDS}
    session['_pain_point_asked'] = True
    r.set(_key(session_id), json.dumps(session), ex=BOOKING_TTL)
```

---

## Configuration

### Redis Settings (from .env)

```bash
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=          # Optional
```

### Session TTL

```python
BOOKING_TTL = 3600  # 1 hour - sessions auto-expire
```

---

## Integration Points

### Where Booking Session is Used

| Location | Function | Purpose |
|----------|----------|---------|
| `web/app.py` | `get_next_booking_step()` | Determine what to ask next |
| `web/app.py` | `merge_session()` | Save extracted fields |
| `web/app.py` | `get_confirmation_summary()` | Generate confirmation message |
| `web/app.py` | `clear_session()` | Clean up after booking |
| `core/field_validator.py` | `get_session()` | Validate against current data |

### Typical Flow in app.py

```python
# 1. Check booking status
step_info = get_next_booking_step(phone)

if step_info['step'] == 'complete':
    # All fields collected - confirm booking
    summary = get_confirmation_summary(phone)
    record_booking(summary)
    clear_session(phone)
else:
    # Still collecting - AI asks for missing fields
    missing = step_info['missing']
    # AI prompt includes: "Please ask for: {missing}"
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Session not found | Redis not connected | Check Redis is running |
| Session expired | TTL exceeded | Extend BOOKING_TTL if needed |
| Date not parsing | Format not recognized | Check normalize_booking_date() |
| Phone wrong format | Normalization failed | Check normalize_phone() |

### Debug Commands

```bash
# Check Redis is running
redis-cli ping

# View booking session
redis-cli get "booking:60123456789"

# Check TTL remaining
redis-cli ttl "booking:60123456789"

# Delete session manually
redis-cli del "booking:60123456789"

# List all booking keys
redis-cli keys "booking:*"
```

### Logging

```python
# In logs, look for:
logger.info("BOOKING SESSION MERGED | 60123456789 | updated: ['date', 'time']")
logger.info("BOOKING SESSION CLEARED | 60123456789")
```

---

## Best Practices

### 1. Always Clear Session After Completion

```python
if booking_confirmed:
    record_booking_to_sheet(summary)
    clear_session(phone)  # Prevent stale data
```

### 2. Check Session Exists Before Merge

```python
session = get_session(phone)
if not any(session.values()):
    # New booking - start fresh
    logger.info("Starting new booking session")
```

### 3. Handle TTL Expiration Gracefully

```python
step = get_next_booking_step(phone)
if step['step'] == 'pain_point' and session_seems_stale:
    # Session may have expired, start over
    clear_session(phone)
```

### 4. Log Field Changes for Debugging

The module automatically logs when fields are updated:
```
BOOKING SESSION MERGED | 60123456789 | updated: ['service', 'date', 'time']
```

---

## Data Flow Diagram

```
Customer: "I want to book tomorrow 3pm for body massage"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│               AI Engine (GPT-4o-mini)                       │
│   Extracts: date="2026-02-14", time="15:00",               │
│             service="body massage"                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    merge_session()                          │
│   1. Normalize date → "2026-02-14"                         │
│   2. Normalize time → "15:00"                              │
│   3. Update Redis key "booking:60123456789"                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 get_next_booking_step()                     │
│   Check what's missing → ["therapist_gender"]              │
│   Return: step="therapist_gender"                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
AI asks: "Do you have a preference for male or female therapist?"
```

---

## Summary

The Booking Session Manager is the **state machine** for the booking flow:

- **Redis-backed storage** for reliability and persistence
- **Multi-step flow** with defined sequence
- **Automatic normalization** of phone, date, time, gender
- **Skip logic** for optional fields (pain_point)
- **TTL-based cleanup** prevents stale sessions
- **Comprehensive logging** for debugging

This module ensures that even if a customer takes 30 minutes to complete a booking, all their information is preserved and the conversation continues seamlessly.
