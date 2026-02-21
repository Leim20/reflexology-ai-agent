# Field Validator (Two-Phase Anti-Hallucination)

## Overview

The Field Validator is a **two-phase validation system** that prevents AI hallucination when extracting booking information. It ensures that extracted fields actually came from the current message, not from conversation history.

**Location:** `core/field_validator.py`
**Lines of code:** ~383 lines
**Dependencies:** OpenAI API (GPT-4o-mini), `utils/logger.py`

---

## What is the Purpose?

The Field Validator exists to:

1. **Prevent Hallucination** — Stop AI from using old data as if it's new.

2. **Validate Current Message** — Ensure extracted values exist in the latest message.

3. **Protect Data Integrity** — Only save data the customer actually provided now.

4. **Enable Trust** — Confidently use AI extraction knowing it's verified.

5. **Reduce Errors** — Catch mistakes before they reach Google Sheets.

---

## The Hallucination Problem

### What Can Go Wrong?

```
Conversation History:
  User: "Book tomorrow 3pm"
  AI: "Got it! Tomorrow 3pm."
  User: "Actually just 60min foot massage"

Without Validation:
  AI extracts: date="tomorrow", time="3pm", service="60min foot"
  ❌ Problem: date and time came from HISTORY, not current message

With Two-Phase Validation:
  Phase 1: AI extracts all fields
  Phase 2: Validator checks current message only
  ✅ Result: Only service="60min foot" is saved
```

### Why Does This Happen?

The AI sees the **full conversation** and may confuse:
- What was said **before** vs **now**
- What was **confirmed** vs **mentioned**
- What was **changed** vs **original**

---

## How It Works

### Two-Phase Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PHASE 1: EXTRACTION                      │
│                                                              │
│  AI sees: Full conversation history                         │
│  AI extracts: date, time, service, name, phone, etc.        │
│                                                              │
│  Output: {                                                  │
│    "date": "2026-02-22",                                    │
│    "time": "15:00",                                         │
│    "service": "60min foot massage"                          │
│  }                                                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 2: VALIDATION                       │
│                                                              │
│  Validator sees: ONLY current message                       │
│  Current message: "Actually just 60min foot massage"        │
│                                                              │
│  Check each field:                                          │
│  - date "2026-02-22" → NOT in current message → REJECT      │
│  - time "15:00" → NOT in current message → REJECT           │
│  - service "60min foot" → IN current message → ACCEPT       │
│                                                              │
│  Output: {                                                  │
│    "service": "60min foot massage"                          │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Functions

### 1. validate_extracted_fields() — Main Entry Point

```python
def validate_extracted_fields(
    extracted_fields: Dict[str, str],
    current_message: str,
    session_id: str = None,
    log_to_db: bool = True
) -> Dict[str, str]:
    """
    Phase 2 Validation: Check each extracted field against ONLY the current message.

    Args:
        extracted_fields: Fields extracted by Phase 1 (with full context)
        current_message: The current user message ONLY (no history)
        session_id: For logging purposes
        log_to_db: Whether to log results

    Returns:
        Dict with only validated fields (hallucinations removed)
    """
```

**Example:**

```python
# Phase 1 extracted these fields
extracted = {
    "date": "2026-02-22",
    "time": "15:00",
    "service": "60min foot massage"
}

# Current message (what user just said)
current_message = "Actually just 60min foot massage"

# Phase 2 validation
validated = validate_extracted_fields(extracted, current_message)

# Result: Only fields found in current message
# validated = {"service": "60min foot massage"}
```

---

### 2. _batch_validate_fields() — LLM Validation

```python
def _batch_validate_fields(
    fields: Dict[str, str],
    current_message: str,
    session_id: str = None,
    log_to_db: bool = True
) -> Dict[str, str]:
    """
    Validate all fields in a single LLM call for cost efficiency.
    Uses GPT-4o-mini with JSON output.
    """
```

**The Validation Prompt:**

```python
prompt = f"""You are a validation assistant. Check if extracted data appears in the user's message.

USER MESSAGE (the ONLY source of truth):
"{current_message}"

EXTRACTED DATA TO VALIDATE:
- date: "2026-02-22" (booking date)
- time: "15:00" (booking time)
- service: "60min foot massage" (service type)

VALIDATION RULES:
1. VALID: Value appears directly OR can be clearly inferred
   - "tomorrow" in message → date "tomorrow" is VALID
   - "2pm" in message → time "14:00" is VALID (same meaning)

2. HALLUCINATED: Value does NOT appear and CANNOT be inferred
   - Message says nothing about time → time is HALLUCINATED

3. Be STRICT: When in doubt, mark as HALLUCINATED.

Respond with JSON:
{{"date": "valid", "time": "hallucinated", "service": "valid"}}"""
```

**LLM Call:**

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You validate extracted booking data. JSON only."},
        {"role": "user", "content": prompt}
    ],
    temperature=0,  # Deterministic for validation
    max_tokens=500,
    response_format={"type": "json_object"}
)
```

---

### 3. validate_booking_extraction() — Integration Helper

```python
def validate_booking_extraction(
    function_args: Dict[str, str],
    current_message: str,
    session_id: str = None,
    skip_fields: List[str] = None
) -> Dict[str, str]:
    """
    Main entry point for validating function call extraction results.

    OPTIMIZATION: Skip validation for MCQ-trusted fields (date, time, service)
    since MCQ already constrains output to valid formats.

    Args:
        function_args: Raw extraction from AI function call
        current_message: Current user message only
        session_id: For logging
        skip_fields: Fields to skip (e.g., 'message_type')

    Returns:
        Validated fields only
    """
```

**MCQ-Trusted Fields:**

Some fields are trusted from MCQ (Multiple Choice Questions) extraction:

```python
mcq_trusted_fields = {'date', 'time', 'service', 'therapist_gender', 'customer_gender'}

# These skip Phase 2 validation because:
# 1. MCQ already constrains to valid enum values
# 2. Format is guaranteed (YYYY-MM-DD, HH:MM, etc.)
```

---

### 4. Quick Validators — Fast Heuristics

**Phone Validation:**

```python
def quick_validate_phone(extracted_phone: str, current_message: str) -> bool:
    """
    Quick check if phone digits appear in message.
    Runs BEFORE expensive LLM validation.
    """
    # Handle 'this_number' sentinel
    if extracted_phone == 'this_number':
        indicators = ['this number', 'same number', '这个号码', 'nombor ini']
        return any(ind in current_message.lower() for ind in indicators)

    # Extract digits and compare
    phone_digits = ''.join(c for c in extracted_phone if c.isdigit())
    message_digits = ''.join(c for c in current_message if c.isdigit())

    # Phone should appear in message (at least last 8 digits)
    if len(phone_digits) >= 8:
        return phone_digits in message_digits or phone_digits[-8:] in message_digits

    return False
```

**Date/Time Validation:**

```python
def quick_validate_date_time(extracted_value: str, current_message: str) -> bool:
    """
    Quick check for date/time patterns.
    """
    msg_lower = current_message.lower()
    value_lower = extracted_value.lower()

    # Direct match
    if value_lower in msg_lower:
        return True

    # Check relative keywords
    date_keywords = {
        'today': ['today', '今天', 'hari ini'],
        'tomorrow': ['tomorrow', '明天', 'esok'],
    }

    for key, keywords in date_keywords.items():
        if any(kw in value_lower for kw in keywords):
            if any(kw in msg_lower for kw in keywords):
                return True

    return False
```

---

## Validation Flow

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│            Customer Message: "60min foot massage"           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: AI Extraction (with full conversation)            │
│                                                              │
│  Extracted: {                                               │
│    "date": "2026-02-22",      ← From history                │
│    "time": "15:00",           ← From history                │
│    "service": "60min foot"    ← From current message        │
│  }                                                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  validate_booking_extraction()                               │
│                                                              │
│  1. Separate MCQ-trusted vs needs-validation                │
│     MCQ trusted: date, time, service (skip Phase 2)         │
│     Needs validation: phone, customer_name (if any)         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Quick Validators (Fast Heuristics)                          │
│                                                              │
│  - quick_validate_phone() → Digits in message?              │
│  - quick_validate_date_time() → Keywords match?             │
│                                                              │
│  Passed: Skip LLM call (save cost)                          │
│  Failed: Continue to LLM validation                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  LLM Validation (GPT-4o-mini)                               │
│                                                              │
│  For remaining fields:                                      │
│  - Ask LLM to check if each value is in current message    │
│  - Returns: {"field": "valid"} or {"field": "hallucinated"} │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Final Result                                                │
│                                                              │
│  Validated fields only: {                                   │
│    "service": "60min foot"                                  │
│  }                                                          │
│                                                              │
│  Rejected (hallucinated): date, time                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Field Descriptions

The validator knows what each field represents:

```python
FIELD_DESCRIPTIONS = {
    "service": "massage/reflexology service type (foot massage, body massage, cupping)",
    "date": "booking date (tomorrow, 3月1日, March 1, 2026-03-01)",
    "time": "booking time (2pm, 下午3点, 14:00)",
    "therapist_gender": "preferred therapist gender (male/female/男/女)",
    "customer_name": "customer's name",
    "customer_gender": "customer's gender (male/female/男/女)",
    "phone": "phone number",
    "pain_point": "body pain or health concern mentioned"
}
```

These descriptions help the LLM understand what to validate.

---

## Integration in app.py

```python
from core.field_validator import validate_booking_extraction

# After AI extracts fields via function calling
function_args = {
    "date": "2026-02-22",
    "time": "15:00",
    "service": "60min foot massage"
}

# Validate against current message only
validated = validate_booking_extraction(
    function_args=function_args,
    current_message=customer_message,
    session_id=phone
)

# Only save validated fields
if validated:
    merge_booking_session(phone, validated)
```

---

## Logging Output

```
============================================================
PHASE 2 VALIDATION - Anti-Hallucination Check
   Session: 60123456789
   Current message: Actually just 60min foot massage...
   Fields to validate: ['date', 'time', 'service']
============================================================
   MCQ TRUSTED: date='2026-02-22' (skipping Phase 2)
   MCQ TRUSTED: time='15:00' (skipping Phase 2)
   MCQ TRUSTED: service='60min foot massage' (skipping Phase 2)
   Validated fields: ['date', 'time', 'service']
   Rejected fields: set()
```

Or when hallucination is detected:

```
   HALLUCINATION DETECTED: date='2026-02-22' not in current message
   HALLUCINATION DETECTED: time='15:00' not in current message
   Validated fields: ['service']
   Rejected fields: {'date', 'time'}
```

---

## Configuration

### Validation Rules

| Rule | Behavior |
|------|----------|
| VALID | Value appears or can be clearly inferred |
| HALLUCINATED | Value not in current message |
| STRICT | When in doubt, mark as hallucinated |

### MCQ-Trusted Fields

| Field | Reason for Trust |
|-------|------------------|
| `date` | MCQ constrains to valid date formats |
| `time` | MCQ constrains to HH:MM format |
| `service` | MCQ matches against service catalog |
| `therapist_gender` | MCQ constrains to Male/Female enum |
| `customer_gender` | MCQ constrains to Male/Female enum |

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| All fields rejected | LLM too strict | Check prompt wording |
| Hallucination passed | LLM too lenient | Lower temperature to 0 |
| Slow validation | Too many fields | Use quick validators first |
| API errors | OpenAI issues | Add retry logic |

### Debug Checklist

1. Check current_message is correct (not full history)
2. Verify extracted_fields has values
3. Look for HALLUCINATION DETECTED in logs
4. Check LLM response is valid JSON

---

## Summary

The Field Validator provides **anti-hallucination protection**:

- **Two-phase approach** — Extract first, validate second
- **Current message only** — Ignores conversation history
- **Quick validators** — Fast heuristics before LLM
- **MCQ trust** — Skip validation for format-constrained fields
- **Strict by default** — Reject when uncertain

This ensures only **real, current data** is saved to the booking session.
