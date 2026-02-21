# Booking Workflow (Complete Flow)

## Overview

The Booking Workflow is the **end-to-end customer journey** for making an appointment. It orchestrates multiple modules (AI Engine, Date Extractor, Booking Session, Field Validator, Lead Manager) to guide customers from initial inquiry to confirmed booking.

**Files involved:**
- `web/app.py` — Main orchestration
- `core/booking_session.py` — State management (Redis)
- `core/date_extractor.py` — Date/time parsing
- `core/field_validator.py` — Two-phase validation
- `handlers/tools/lead_manager.py` — Google Sheets recording

---

## What is the Purpose?

The Booking Workflow exists to:

1. **Guide conversation naturally** — Collect booking info through natural dialogue, not a rigid form.

2. **Handle multilingual input** — Support English, Chinese, Malay, and mixed languages.

3. **Validate data progressively** — Validate each field as it's collected, not at the end.

4. **Prevent AI hallucination** — Use two-phase validation to ensure AI doesn't make up data.

5. **Record to Google Sheets** — Save confirmed bookings for staff follow-up and reminders.

---

## The Booking Flow

### 5-Step Conversation Framework

```
┌─────────────────────────────────────────────────────────────┐
│                 BOOKING FLOW OVERVIEW                        │
└─────────────────────────────────────────────────────────────┘

STEP 1: DISCOVERY (Optional)
        AI: "What brings you in today? Any areas that need attention?"
        Customer: "My shoulders are very tight from work"
        → [pain_point = "shoulders"]
        → AI can make personalized recommendation

STEP 2: SERVICE SELECTION
        AI: "Based on your shoulder tension, I recommend our 60-min
            Body Massage or 90-min Full Body treatment..."
        Customer: "I'll take the 60 min body massage"
        → [service = "60-min body massage"]

STEP 3: DATE & TIME
        AI: "When would you like to come in?"
        Customer: "明天下午3点" (tomorrow 3pm)
        → [date = "2026-02-14", time = "15:00"]

STEP 4: THERAPIST PREFERENCE
        AI: "Do you prefer a male or female therapist?"
        Customer: "Female please"
        → [therapist_gender = "Female"]

STEP 5: PERSONAL INFO CONFIRMATION
        AI: "May I have your name and contact number to confirm?"
        Customer: "I'm Alex, my number is 0123456789"
        → [customer_name = "Alex", phone = "60123456789"]

CONFIRMATION
        AI: "Perfect! Here's your booking confirmation:
            Name: Alex
            Service: 60-min Body Massage
            Date: 14 Feb 2026
            Time: 3:00 PM
            Therapist: Female

            See you tomorrow! 😊"
```

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Customer Message                            │
│           "book 明天下午3点 body massage"                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   app.py — Main Handler                      │
│                                                              │
│  1. Detect booking intent                                   │
│  2. Get current session: get_session(phone)                 │
│  3. Get next step: get_next_booking_step(phone)             │
└─────────────────────────┬───────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Date        │  │ AI Engine   │  │ Field       │
│ Extractor   │  │ (GPT-4o)    │  │ Validator   │
│             │  │             │  │             │
│ Extract:    │  │ Function    │  │ Two-phase   │
│ date, time  │  │ calling to  │  │ validation  │
│             │  │ extract     │  │             │
│             │  │ other       │  │             │
│             │  │ fields      │  │             │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│               Booking Session (Redis)                        │
│                                                              │
│  merge_session(phone, extracted_fields)                     │
│                                                              │
│  Session: {                                                 │
│    "service": "60-min body massage",                        │
│    "date": "2026-02-14",                                   │
│    "time": "15:00",                                        │
│    ...                                                      │
│  }                                                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               Check: Is booking complete?                    │
│                                                              │
│  step = get_next_booking_step(phone)                        │
│                                                              │
│  if step['step'] == 'complete':                             │
│      → Generate confirmation                                │
│      → Record to Google Sheets                              │
│      → Clear session                                        │
│  else:                                                       │
│      → AI asks for missing fields                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│          If Complete: Record to Google Sheets               │
│                                                              │
│  lead_manager.record_booking({                              │
│    name: "Alex",                                            │
│    phone: "60123456789",                                    │
│    service: "60-min body massage",                          │
│    date: "2026-02-14",                                     │
│    time: "15:00",                                          │
│    therapist: "Female"                                      │
│  })                                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Modules Involved

### 1. Booking Session (`core/booking_session.py`)
- Stores partial booking data in Redis
- Tracks what fields are collected/missing
- Controls flow sequence

### 2. Date Extractor (`core/date_extractor.py`)
- Parses "明天下午3点" → date="2026-02-14", time="15:00"
- Multilingual support
- Free parsing with AI fallback

### 3. Field Validator (`core/field_validator.py`)
- Two-phase validation (AI proposes → system verifies)
- Validates service names against catalog
- Validates date/time formats
- Prevents hallucination

### 4. AI Engine (`core/ai_engine.py`)
- Generates natural conversation
- Extracts fields via function calling
- Provides recommendations based on pain points

### 5. Lead Manager (`handlers/tools/lead_manager.py`)
- Records confirmed bookings to Google Sheets
- Sends booking notification to staff
- Triggers reminder scheduling

---

## Step-by-Step Implementation

### Step 1: Detect Booking Intent

```python
BOOKING_KEYWORDS = [
    "book", "booking", "appointment", "reserve", "schedule",
    "预约", "预订", "订", "tempah",
    "tomorrow", "today", "monday", ...
]

def has_booking_intent(message: str) -> bool:
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in BOOKING_KEYWORDS)
```

### Step 2: Check Current Booking State

```python
from core.booking_session import get_session, get_next_booking_step

def handle_booking_message(phone: str, message: str):
    # Get current session
    session = get_session(phone)

    # Get next step
    step_info = get_next_booking_step(phone)
    current_step = step_info['step']
    missing_fields = step_info['missing']

    if current_step == 'complete':
        # All fields collected - confirm booking
        return generate_confirmation(phone)
    else:
        # Still collecting - process message and ask for missing
        return process_and_continue(phone, message, current_step, missing_fields)
```

### Step 3: Extract Fields from Message

```python
from core.date_extractor import extract_datetime
from core.booking_session import merge_session

def process_and_continue(phone, message, current_step, missing_fields):
    extracted = {}

    # Extract date/time if needed
    if 'date' in missing_fields or 'time' in missing_fields:
        dt_result = extract_datetime(message)
        if dt_result['date']:
            extracted['date'] = dt_result['date']
        if dt_result['time']:
            extracted['time'] = dt_result['time']

    # Use AI to extract other fields via function calling
    ai_extracted = extract_with_ai(message, current_step)
    extracted.update(ai_extracted)

    # Merge into session
    if extracted:
        merge_session(phone, extracted)

    # Generate AI response for next step
    return generate_next_prompt(phone)
```

### Step 4: AI Function Calling for Field Extraction

```python
UPDATE_BOOKING_TOOL = {
    "type": "function",
    "function": {
        "name": "update_booking_fields",
        "description": "Update booking fields extracted from customer message",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string"},
                "service": {"type": "string"},
                "date": {"type": "string", "format": "YYYY-MM-DD"},
                "time": {"type": "string", "format": "HH:MM"},
                "therapist_gender": {"type": "string", "enum": ["Male", "Female"]}
            }
        }
    }
}

def extract_with_ai(message, current_step):
    # Build prompt based on current step
    prompt = f"Extract booking fields from: '{message}'. Current step: {current_step}"

    result = ai_engine.generate_response(
        messages=[{"role": "user", "content": prompt}],
        tools=[UPDATE_BOOKING_TOOL],
        tool_choice="auto"
    )

    if result.get('tool_calls'):
        args = json.loads(result['tool_calls'][0]['function']['arguments'])
        return args

    return {}
```

### Step 5: Two-Phase Validation

```python
from core.field_validator import validate_service, validate_datetime

def validate_extracted_fields(extracted: dict, knowledge_base: str) -> dict:
    validated = {}

    # Validate service against catalog
    if 'service' in extracted:
        is_valid = validate_service(extracted['service'], knowledge_base)
        if is_valid:
            validated['service'] = extracted['service']
        else:
            logger.warning(f"Invalid service: {extracted['service']}")

    # Validate date format
    if 'date' in extracted:
        is_valid = validate_datetime(extracted['date'], 'date')
        if is_valid:
            validated['date'] = extracted['date']

    return validated
```

### Step 6: Generate Confirmation

```python
from core.booking_session import get_confirmation_summary, clear_session

def generate_confirmation(phone: str) -> str:
    summary = get_confirmation_summary(phone)

    confirmation = f"""✅ Booking Confirmed!

📋 Booking Details:
- Name: {summary['customer_name']}
- Phone: {summary['phone']}
- Service: {summary['service']}
- Date: {summary['date']}
- Time: {summary['time']}
- Therapist: {summary['therapist_gender']}

📍 Location: Serenity Reflexology
2, 51-G, Jalan Contoh 1, Downtown, 40000 Example City

See you soon! 😊"""

    # Record to Google Sheets
    lead_manager.record_booking(summary)

    # Clear session
    clear_session(phone)

    # Send notification to staff
    notify_staff_new_booking(summary)

    return confirmation
```

### Step 7: Record to Google Sheets

```python
def record_booking(summary: dict):
    """Write booking to Bookings tab in Google Sheets"""
    row = [
        summary['customer_name'],
        summary['phone'],
        summary['service'],
        summary['date'],
        summary['time'],
        summary['therapist_gender'],
        "",  # Notes
        "Confirmed",  # Status
        ""   # Reminder Sent
    ]

    bookings_sheet.append_row(row)
    logger.info(f"Booking recorded: {summary['phone']} for {summary['date']}")
```

---

## Handling Edge Cases

### Customer Skips Pain Point Question

```python
def handle_skip_pain_point(phone: str, message: str):
    # Customer jumps straight to "book tomorrow 3pm"
    # Mark pain point as asked (to skip)
    mark_pain_point_asked(phone)

    # Extract date/time
    dt_result = extract_datetime(message)
    if dt_result['date']:
        merge_session(phone, {'date': dt_result['date'], 'time': dt_result['time']})

    # Continue to service selection
    return "What service would you like? We have foot reflexology, body massage..."
```

### Customer Provides Multiple Fields at Once

```python
# Customer: "Book tomorrow 3pm for 60min body massage, female therapist"
# System extracts ALL fields in one go and merges them
```

### Customer Changes Mind

```python
def handle_change_request(phone: str, message: str):
    # Customer: "Actually, make it 4pm instead"
    dt_result = extract_datetime(message)
    if dt_result['time']:
        # Overwrite time in session
        merge_session(phone, {'time': dt_result['time']})

    return "Got it! I've updated your booking to 4:00 PM. Anything else?"
```

### Customer Cancels Mid-Booking

```python
def handle_cancel(phone: str):
    clear_session(phone)
    return "No problem! Your booking has been cancelled. Let me know if you'd like to book again later."
```

---

## Configuration

### Booking Fields Configuration

```json
{
    "booking": {
        "required_fields": [
            "customer_name",
            "customer_gender",
            "service",
            "date",
            "time",
            "therapist_gender",
            "phone"
        ],
        "optional_fields": [
            "pain_point",
            "notes"
        ],
        "flow_sequence": [
            "pain_point",
            "service",
            "datetime",
            "therapist_gender",
            "personal_info"
        ]
    }
}
```

### Notification Configuration

```json
{
    "booking_notification": {
        "enabled": true,
        "notify_phone": "60123456789",
        "notify_name": "Ryan"
    }
}
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Booking not completing | Field missing | Check `get_next_booking_step()` |
| Date wrong | Parsing failed | Check date_extractor logs |
| Session lost | Redis TTL expired | Extend BOOKING_TTL |
| Duplicate bookings | Session not cleared | Verify `clear_session()` called |

### Debug Checklist

1. Check Redis session: `redis-cli get "booking:60123456789"`
2. Check next step: `get_next_booking_step(phone)`
3. Check date extraction: `extract_datetime(message)`
4. Check Google Sheets: Verify row was added
5. Check logs for "BOOKING" entries

### Logging

```
BOOKING SESSION MERGED | 60123456789 | updated: ['date', 'time']
BOOKING SESSION | 60123456789 | step=therapist_gender, missing=['therapist_gender']
BOOKING COMPLETE | 60123456789 | recording to Google Sheets
BOOKING SESSION CLEARED | 60123456789
```

---

## Best Practices

### 1. Always Validate Before Storing

```python
# Validate extracted fields before merging
validated = validate_extracted_fields(extracted, knowledge_base)
merge_session(phone, validated)  # Only merge validated data
```

### 2. Handle Partial Information Gracefully

```python
# Customer says "tomorrow" without time
# Store date, ask for time
merge_session(phone, {'date': extracted_date})
return "What time would you like to come in?"
```

### 3. Confirm Before Finalizing

```python
# Always show summary before recording
summary = get_confirmation_summary(phone)
confirmation_message = format_confirmation(summary)
return confirmation_message + "\n\nPlease reply 'confirm' to finalize."
```

### 4. Send Staff Notifications

```python
def notify_staff_new_booking(summary):
    message = f"📅 New Booking!\n{summary['customer_name']}\n{summary['date']} {summary['time']}"
    whatsapp_handler.send_message(staff_phone, message)
```

---

## Summary

The Booking Workflow orchestrates **multiple modules into a seamless customer experience**:

- **5-step conversational flow**: Discovery → Service → DateTime → Therapist → Confirm
- **Multilingual date parsing**: English, Chinese, Malay support
- **Two-phase validation**: Prevents AI hallucination
- **Redis state management**: Persists across messages
- **Google Sheets recording**: Integrates with staff workflow
- **Staff notifications**: Immediate alerts for new bookings

This workflow transforms a complex booking process into a natural, human-like conversation that feels effortless for the customer.
