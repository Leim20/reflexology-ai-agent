# Booking Function Tools

## Overview

The Booking Tools are **3 OpenAI function calling tools** that handle the complete booking lifecycle — from progressive field collection to final confirmation and date/time validation.

**Location:** `web/app.py` (lines 1147-1330)
**Tools:** `update_booking_fields`, `record_booking`, `validate_booking_datetime`
**Dependencies:** `core/booking_session.py` (Redis), `handlers/tools/lead_manager.py`

---

## What is the Purpose?

The Booking Tools exist to:

1. **Progressive Field Collection** — Save booking info as customer provides it, not all at once.

2. **Prevent Data Loss** — Fields are saved to Redis immediately, surviving disconnections.

3. **Validate Before Confirming** — Check date/time validity before showing confirmation.

4. **Record to Google Sheets** — Save confirmed bookings for staff follow-up.

5. **Support Rescheduling** — Update existing bookings instead of creating duplicates.

---

## The 3 Booking Tools

| Tool | When Called | Purpose |
|------|-------------|---------|
| `update_booking_fields` | During booking flow | Save fields progressively to Redis |
| `validate_booking_datetime` | Before showing preview | Check date/time is valid |
| `record_booking` | After confirmation | Save to Google Sheets |

---

## Tool 1: update_booking_fields

### Purpose

Save booking information **as the customer provides it** during the conversation. Called immediately when customer mentions any booking-related info.

### Function Definition

```python
def get_update_booking_fields_function_definition():
    return {
        "type": "function",
        "function": {
            "name": "update_booking_fields",
            "description": (
                "Save booking information provided by the customer during the booking flow. "
                "Call this IMMEDIATELY whenever the customer provides any booking-related info "
                "(pain point, service choice, date, time, therapist preference, name, gender, phone). "
                "You may set multiple fields in one call if the customer provides several at once. "
                "IMPORTANT: Resolve contextual references before calling. If the customer says "
                "'就这个吧' (this one) after you recommended a service, pass the actual service name."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pain_point": {
                        "type": "string",
                        "description": "Customer's pain point (e.g. '肩膀酸痛', 'lower back pain')"
                    },
                    "service": {
                        "type": "string",
                        "description": "Service name and duration (e.g. '90分钟足部按摩')"
                    },
                    "date": {
                        "type": "string",
                        "description": "Booking date in YYYY-MM-DD format"
                    },
                    "time": {
                        "type": "string",
                        "description": "Booking time in HH:MM 24-hour format"
                    },
                    "therapist_gender": {
                        "type": "string",
                        "description": "Must be 'Male' or 'Female'"
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Customer's name"
                    },
                    "customer_gender": {
                        "type": "string",
                        "description": "Must be 'Male' or 'Female'"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Phone number. Use 'this_number' if using WhatsApp number."
                    }
                },
                "required": []  # All optional - save whatever is provided
            }
        }
    }
```

### Handler Implementation

```python
def handle_update_booking_fields_function_call(
    function_args: dict,
    phone: str,
    whatsapp_phone: str
) -> dict:
    """Handle update_booking_fields function call from AI"""

    logger.info("="*80)
    logger.info("HANDLING UPDATE_BOOKING_FIELDS FUNCTION CALL")
    logger.info("="*80)

    # Extract fields from AI arguments
    fields_to_update = {}

    # Map AI arguments to session fields
    field_mapping = {
        'pain_point': 'pain_point',
        'service': 'service',
        'date': 'date',
        'time': 'time',
        'therapist_gender': 'therapist_gender',
        'customer_name': 'customer_name',
        'customer_gender': 'customer_gender',
        'phone': 'phone'
    }

    for ai_field, session_field in field_mapping.items():
        value = function_args.get(ai_field)
        if value:
            fields_to_update[session_field] = value

    # Handle 'this_number' sentinel for phone
    if fields_to_update.get('phone') == 'this_number':
        fields_to_update['phone'] = whatsapp_phone

    # Normalize gender fields
    if 'therapist_gender' in fields_to_update:
        fields_to_update['therapist_gender'] = normalize_gender(
            fields_to_update['therapist_gender']
        )

    if 'customer_gender' in fields_to_update:
        fields_to_update['customer_gender'] = normalize_gender(
            fields_to_update['customer_gender']
        )

    # Merge into Redis session
    if fields_to_update:
        merge_booking_session(phone, fields_to_update)
        logger.info(f"Saved fields: {list(fields_to_update.keys())}")

    # Get current session state
    session = get_booking_session(phone)
    next_step = get_next_booking_step(phone)

    return {
        'success': True,
        'saved_fields': list(fields_to_update.keys()),
        'current_session': session,
        'next_step': next_step['step'],
        'missing_fields': next_step['missing']
    }
```

### Example Flow

```
Customer: "I want to book tomorrow 3pm, body massage"
    ↓
AI calls: update_booking_fields(
    date="2026-02-22",
    time="15:00",
    service="body massage"
)
    ↓
Handler: merge_booking_session(phone, {
    'date': '2026-02-22',
    'time': '15:00',
    'service': 'body massage'
})
    ↓
Returns: {
    'success': True,
    'saved_fields': ['date', 'time', 'service'],
    'next_step': 'therapist_gender',
    'missing_fields': ['therapist_gender', 'customer_name', ...]
}
    ↓
AI: "Great! Would you prefer a male or female therapist?"
```

---

## Tool 2: validate_booking_datetime

### Purpose

Check if a booking date and time is valid **before showing the confirmation** to the customer. Prevents past dates and too-soon bookings.

### Function Definition

```python
def get_validate_booking_datetime_function_definition():
    return {
        "type": "function",
        "function": {
            "name": "validate_booking_datetime",
            "description": "Validate if a booking date and time is valid (not in the past). Call this BEFORE showing booking preview to user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_date": {
                        "type": "string",
                        "description": "The booking date in YYYY-MM-DD format"
                    },
                    "booking_time": {
                        "type": "string",
                        "description": "The booking time in HH:MM format (24-hour)"
                    }
                },
                "required": ["booking_date", "booking_time"]
            }
        }
    }
```

### Handler Implementation

```python
def validate_booking_datetime(booking_date: str, booking_time: str) -> dict:
    """Validate if booking datetime is not in the past"""
    from datetime import datetime
    import pytz

    try:
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        now = datetime.now(malaysia_tz)

        # Parse the booking datetime
        booking_datetime_str = f"{booking_date} {booking_time}"
        booking_dt = datetime.strptime(booking_datetime_str, "%Y-%m-%d %H:%M")
        booking_dt = malaysia_tz.localize(booking_dt)

        # Check if in the past
        if booking_dt < now:
            return {
                "valid": False,
                "error": "past_datetime",
                "message": f"The requested time ({booking_date} {booking_time}) is in the past.",
                "current_time": now.strftime("%Y-%m-%d %H:%M")
            }

        # Check if too soon (less than 30 minutes)
        minutes_until = (booking_dt - now).total_seconds() / 60
        if minutes_until < 30:
            return {
                "valid": False,
                "error": "too_soon",
                "message": f"Please book at least 30 minutes in advance.",
                "current_time": now.strftime("%Y-%m-%d %H:%M")
            }

        return {
            "valid": True,
            "message": f"The requested time ({booking_date} {booking_time}) is valid.",
            "current_time": now.strftime("%Y-%m-%d %H:%M")
        }

    except ValueError as e:
        return {
            "valid": False,
            "error": "invalid_format",
            "message": f"Invalid date/time format. Use YYYY-MM-DD and HH:MM."
        }
```

### Validation Rules

| Check | Condition | Error |
|-------|-----------|-------|
| Past datetime | `booking_dt < now` | "Time is in the past" |
| Too soon | `< 30 minutes` | "Book at least 30 min ahead" |
| Invalid format | Parse fails | "Use YYYY-MM-DD and HH:MM" |

---

## Tool 3: record_booking

### Purpose

Save a **confirmed booking** to Google Sheets after all fields are collected and the customer confirms. Also supports rescheduling existing bookings.

### Function Definition

```python
def get_record_booking_function_definition():
    return {
        "type": "function",
        "function": {
            "name": "record_booking",
            "description": "Record a confirmed booking to Bookings sheet. ONLY call AFTER sending confirmation message. For RESCHEDULE: include original_booking_date to update existing booking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Customer's name"
                    },
                    "customer_gender": {
                        "type": "string",
                        "description": "Must be 'Male' or 'Female'"
                    },
                    "customer_phone": {
                        "type": "string",
                        "description": "Customer's phone number"
                    },
                    "booking_date": {
                        "type": "string",
                        "description": "NEW date in YYYY-MM-DD format"
                    },
                    "booking_time": {
                        "type": "string",
                        "description": "Time of appointment"
                    },
                    "service": {
                        "type": "string",
                        "description": "Service type and duration"
                    },
                    "therapist_gender": {
                        "type": "string",
                        "description": "Must be 'Male' or 'Female'"
                    },
                    "original_booking_date": {
                        "type": "string",
                        "description": "ONLY for RESCHEDULE: The original date to update"
                    }
                },
                "required": ["customer_name", "customer_gender", "customer_phone",
                            "booking_date", "booking_time", "service", "therapist_gender"]
            }
        }
    }
```

### Handler Implementation

```python
def handle_record_booking_function_call(
    function_args: dict,
    whatsapp_phone: str
) -> dict:
    """Handle record_booking function call from AI"""

    logger.info("="*80)
    logger.info("HANDLING RECORD_BOOKING FUNCTION CALL")
    logger.info("="*80)

    # Extract and normalize fields
    customer_name = function_args.get('customer_name', '')
    customer_gender = normalize_gender(function_args.get('customer_gender', ''))
    customer_phone = normalize_phone(function_args.get('customer_phone', whatsapp_phone))
    booking_date = function_args.get('booking_date', '')
    booking_time = function_args.get('booking_time', '')
    service = function_args.get('service', '')
    therapist_gender = normalize_gender(function_args.get('therapist_gender', ''))
    original_date = function_args.get('original_booking_date')  # For reschedule

    logger.info(f"Name: {customer_name}")
    logger.info(f"Phone: {customer_phone}")
    logger.info(f"Date: {booking_date}")
    logger.info(f"Time: {booking_time}")
    logger.info(f"Service: {service}")
    logger.info(f"Therapist: {therapist_gender}")
    logger.info(f"Original Date (reschedule): {original_date}")

    # Validate required fields
    if not all([customer_name, booking_date, booking_time, service]):
        return {
            'success': False,
            'message': 'Missing required booking information'
        }

    # Check if reschedule
    if original_date:
        result = lead_manager.update_booking(
            phone=customer_phone,
            original_date=original_date,
            new_date=booking_date,
            new_time=booking_time
        )
    else:
        # New booking
        result = lead_manager.record_booking(
            phone=customer_phone,
            name=customer_name,
            gender=customer_gender,
            date=booking_date,
            time=booking_time,
            service=service,
            therapist_gender=therapist_gender
        )

    if result['success']:
        # Clear booking session
        clear_booking_session(customer_phone)

        # Send notification to staff
        if config.get('booking_notification.enabled'):
            notify_staff_new_booking(result)

    return result
```

### New Booking vs Reschedule

```
NEW BOOKING:
    record_booking(
        customer_name="Alex",
        booking_date="2026-02-22",
        ...
    )
    → Creates new row in Bookings sheet

RESCHEDULE:
    record_booking(
        customer_name="Alex",
        booking_date="2026-02-25",         # New date
        original_booking_date="2026-02-22"  # Original date to find
    )
    → Updates existing row with new date
```

---

## Booking Flow Integration

### Complete Flow with All 3 Tools

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1-4: Customer provides booking info progressively     │
│                                                              │
│  Each time customer provides info:                          │
│  → AI calls update_booking_fields()                         │
│  → Fields saved to Redis                                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: All fields collected                               │
│                                                              │
│  Before showing confirmation:                               │
│  → AI calls validate_booking_datetime()                     │
│  → Check if date/time is valid                              │
│                                                              │
│  If invalid:                                                │
│  → AI asks customer for different time                      │
│                                                              │
│  If valid:                                                  │
│  → AI shows booking preview                                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 6: Customer confirms                                  │
│                                                              │
│  After customer says "ok" / "confirm":                      │
│  → AI calls record_booking()                                │
│  → Booking saved to Google Sheets                           │
│  → Session cleared                                          │
│  → Staff notified                                           │
└─────────────────────────────────────────────────────────────┘
```

### Forced Tool Choice

During booking flow, the AI is **forced** to call `update_booking_fields`:

```python
# From app.py line 3879-3885
booking_flow_steps = ["pain_point", "service", "datetime", "therapist_gender", "personal_info"]

if should_guide_flow and current_step in booking_flow_steps:
    tool_choice = {"type": "function", "function": {"name": "update_booking_fields"}}
else:
    tool_choice = "auto"
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Fields not saving | Redis connection | Check Redis is running |
| Date validation fails | Wrong format | Ensure YYYY-MM-DD and HH:MM |
| Booking not recorded | Missing fields | Check all required fields |
| Reschedule creates new | Missing original_date | Pass original_booking_date |

### Debug Logging

```
HANDLING UPDATE_BOOKING_FIELDS FUNCTION CALL
================================================================================
Function Arguments:
  date: '2026-02-22'
  time: '15:00'
  service: '90分钟足部按摩'
Saved fields: ['date', 'time', 'service']
Next step: therapist_gender
Missing: ['therapist_gender', 'customer_name', 'customer_gender', 'phone']
================================================================================
```

---

## Summary

The 3 Booking Tools work together for **complete booking lifecycle**:

- **`update_booking_fields`** — Progressive field saving to Redis
- **`validate_booking_datetime`** — Prevent past/invalid bookings
- **`record_booking`** — Final save to Google Sheets

This ensures no data is lost, all bookings are valid, and staff are notified immediately.
