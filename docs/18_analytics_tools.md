# Analytics Function Tools

## Overview

The Analytics Tools are **3 OpenAI function calling tools** that track customer insights, conversation patterns, and booking behaviors for business analytics and follow-up optimization.

**Location:** `web/app.py` (lines 1493-1760)
**Tools:** `track_conversation_info`, `lookup_my_bookings`, `log_cancellation_reason`
**Dependencies:** `handlers/tools/lead_manager.py`, Google Sheets

---

## What is the Purpose?

The Analytics Tools exist to:

1. **Track Pain Points** — Record what issues brought customers in (for personalization).

2. **Log Recommendations** — Track which services AI recommended (for follow-up).

3. **Monitor Cancellations** — Understand why customers cancel (for improvement).

4. **Refresh Booking Data** — Allow real-time booking history queries.

5. **Enable Data-Driven Follow-ups** — Use tracked data for personalized campaigns.

---

## The 3 Analytics Tools

| Tool | When Called | Purpose |
|------|-------------|---------|
| `track_conversation_info` | After AI recommends service | Record pain points & recommendations |
| `lookup_my_bookings` | When customer needs refresh | Get latest booking history |
| `log_cancellation_reason` | After cancellation | Record why customer cancelled |

---

## Tool 1: track_conversation_info

### Purpose

Track customer **pain points and AI recommendations** after the AI makes a service recommendation. This data is used for:
- Personalized follow-ups
- Service improvement
- Marketing insights

### Function Definition

```python
def get_track_conversation_info_function_definition():
    return {
        "type": "function",
        "function": {
            "name": "track_conversation_info",
            "description": "Track customer pain points and recommendations after making a recommendation in STEP 3. Call this after you recommend a service to the customer, to record their needs and your suggestions for follow-up.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_phone": {
                        "type": "string",
                        "description": "Customer's phone number"
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Customer's name (or 'Unknown' if not provided)"
                    },
                    "pain_points": {
                        "type": "string",
                        "description": "Customer's pain points or needs. Use 'direct_booking_request' if customer skipped discovery. Use 'not_disclosed' if customer didn't share."
                    },
                    "recommendations": {
                        "type": "string",
                        "description": "The service(s) you recommended (e.g., '90分钟香薰身体按摩')"
                    }
                },
                "required": ["customer_phone", "pain_points", "recommendations"]
            }
        }
    }
```

### Handler Implementation

```python
def handle_track_conversation_info_function_call(function_args: dict) -> dict:
    """Handle track_conversation_info function call from AI"""

    logger.info("="*80)
    logger.info("HANDLING TRACK_CONVERSATION_INFO FUNCTION CALL")
    logger.info("="*80)

    customer_phone = function_args.get('customer_phone', '')
    customer_name = function_args.get('customer_name', 'Unknown')
    pain_points = function_args.get('pain_points', '')
    recommendations = function_args.get('recommendations', '')

    logger.info(f"Phone: {customer_phone}")
    logger.info(f"Name: {customer_name}")
    logger.info(f"Pain Points: {pain_points}")
    logger.info(f"Recommendations: {recommendations}")

    if not lead_manager:
        logger.error("Lead manager not initialized")
        return {
            'success': False,
            'message': 'Lead manager not available'
        }

    result = lead_manager.track_conversation_info(
        customer_phone=customer_phone,
        customer_name=customer_name,
        pain_points=pain_points,
        recommendations=recommendations
    )

    logger.info(f"Track result: {result}")
    return result
```

### Conversation Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Customer: "My shoulders have been really stiff lately"    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  AI: "For shoulder stiffness, I recommend our              │
│       90-minute Body Massage with aromatherapy.            │
│       Would you like to book?"                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  AI calls: track_conversation_info(                         │
│      customer_phone="60123456789",                          │
│      customer_name="Unknown",                               │
│      pain_points="shoulders stiff, tension",                │
│      recommendations="90-minute Body Massage with aroma"    │
│  )                                                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Saved to Google Sheets: Conversation Insights              │
│                                                              │
│  | Phone       | Date       | Pain Points      | Rec       │
│  |-------------|------------|------------------|-----------|│
│  | 60123456789 | 2026-02-21 | shoulders stiff  | 90min body│
└─────────────────────────────────────────────────────────────┘
```

### Google Sheets: Conversation Insights Tab

| Column | Field | Example |
|--------|-------|---------|
| A | Phone | 60123456789 |
| B | Name | Unknown |
| C | Date | 2026-02-21 |
| D | Pain Points | shoulders stiff, tension |
| E | Recommendations | 90-minute Body Massage |
| F | Booked | Yes/No |

---

## Tool 2: lookup_my_bookings

### Purpose

**Refresh customer booking history** when they mention their data seems outdated. This is a secure tool that only returns the current sender's bookings.

### Function Definition

```python
def get_lookup_my_bookings_function_definition():
    return {
        "type": "function",
        "function": {
            "name": "lookup_my_bookings",
            "description": "Refresh customer booking data. Only use if: (1) customer says info seems wrong, (2) customer mentions a recent booking not shown, or (3) customer explicitly asks to check again. Booking history is already pre-loaded.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
```

### Handler Implementation

```python
def handle_lookup_my_bookings(sender: str) -> dict:
    """
    Handle lookup_my_bookings function call

    Security: Uses sender's phone only, not user input
    """
    logger.info("="*80)
    logger.info("HANDLING LOOKUP_MY_BOOKINGS FUNCTION CALL")
    logger.info("="*80)
    logger.info(f"Phone: {sender}")

    if not lead_manager:
        return {
            'success': False,
            'message': 'Booking system not available'
        }

    # Normalize phone
    normalized_phone = sender.replace('@s.whatsapp.net', '')

    # Get bookings
    result = lead_manager.get_bookings(normalized_phone)

    if result.get('success') and result.get('count', 0) > 0:
        bookings = result['bookings']

        # Separate upcoming and past
        today = datetime.now().date()
        upcoming = []
        past = []

        for b in bookings:
            try:
                booking_date = datetime.strptime(
                    b.get('Booking Date', ''),
                    '%Y-%m-%d'
                ).date()

                if booking_date >= today:
                    upcoming.append(b)
                else:
                    past.append(b)
            except:
                past.append(b)

        return {
            'success': True,
            'upcoming_count': len(upcoming),
            'past_count': len(past),
            'upcoming': upcoming[:5],  # Limit to 5 most recent
            'past': past[:3]
        }
    else:
        return {
            'success': True,
            'upcoming_count': 0,
            'past_count': 0,
            'message': 'No bookings found'
        }
```

### Pre-loaded vs Refresh

Booking history is **pre-loaded** when conversation starts:

```python
def pre_fetch_customer_bookings(phone: str) -> dict:
    """Pre-fetch booking data for session context"""
    # Called once at conversation start
    # Data included in system prompt
    ...
```

`lookup_my_bookings` is only needed when:
- Customer says "that doesn't look right"
- Customer made a booking in another channel
- Customer explicitly asks to "check again"

---

## Tool 3: log_cancellation_reason

### Purpose

**Log why a customer cancelled** their booking. This data helps:
- Identify common cancellation reasons
- Improve service offerings
- Follow up appropriately

### Function Definition

```python
def get_log_cancellation_reason_function_definition():
    return {
        "type": "function",
        "function": {
            "name": "log_cancellation_reason",
            "description": "Log the reason when a customer cancels or reschedules. Call AFTER the cancellation conversation is complete.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_phone": {
                        "type": "string",
                        "description": "Customer phone number"
                    },
                    "original_booking_date": {
                        "type": "string",
                        "description": "The original date that was cancelled (YYYY-MM-DD)"
                    },
                    "original_booking_time": {
                        "type": "string",
                        "description": "The original time that was cancelled"
                    },
                    "cancellation_reason": {
                        "type": "string",
                        "enum": ["busy", "health", "budget", "reschedule", "other"],
                        "description": "Reason: busy (有事), health (身体不舒服), budget (预算), reschedule (改时间), other"
                    },
                    "outcome": {
                        "type": "string",
                        "enum": ["rescheduled", "cancelled"],
                        "description": "Outcome: rescheduled (changed to new time) or cancelled (fully cancelled)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Brief notes about what happened (optional)"
                    }
                },
                "required": ["customer_phone", "cancellation_reason", "outcome"]
            }
        }
    }
```

### Handler Implementation

```python
def handle_log_cancellation_reason_function_call(
    function_args: dict,
    whatsapp_phone: str = None
) -> dict:
    """Handle the log_cancellation_reason function call"""

    logger.info("="*80)
    logger.info("LOGGING CANCELLATION REASON")
    logger.info("="*80)

    try:
        customer_phone = function_args.get("customer_phone") or whatsapp_phone
        original_date = function_args.get("original_booking_date", "")
        original_time = function_args.get("original_booking_time", "")
        reason = function_args.get("cancellation_reason", "other")
        outcome = function_args.get("outcome", "cancelled")
        notes = function_args.get("notes", "")

        # Normalize phone
        if customer_phone:
            customer_phone = ''.join(filter(str.isdigit, customer_phone))

        logger.info(f"Phone: {customer_phone}")
        logger.info(f"Original Date: {original_date}")
        logger.info(f"Reason: {reason}")
        logger.info(f"Outcome: {outcome}")
        logger.info(f"Notes: {notes}")

        if not lead_manager:
            return {"success": False, "message": "Lead manager not available"}

        result = lead_manager.log_cancellation_reason(
            customer_phone=customer_phone,
            original_booking_date=original_date,
            original_booking_time=original_time,
            cancellation_reason=reason,
            outcome=outcome,
            notes=notes
        )

        return result

    except Exception as e:
        logger.error(f"Error logging cancellation: {e}")
        return {"success": False, "message": str(e)}
```

### Cancellation Reasons

| Reason Code | Chinese | English | Description |
|-------------|---------|---------|-------------|
| `busy` | 有事/临时不得空 | Busy | Schedule conflict |
| `health` | 身体不舒服/生病 | Health | Not feeling well |
| `budget` | 预算/钱 | Budget | Financial concerns |
| `reschedule` | 改时间 | Reschedule | Just changing time |
| `other` | 其他原因 | Other | Other reasons |

### Outcomes

| Outcome | Description |
|---------|-------------|
| `rescheduled` | Customer booked new time |
| `cancelled` | Booking fully cancelled |

### Google Sheets: Cancellation Log Tab

| Column | Field | Example |
|--------|-------|---------|
| A | Phone | 60123456789 |
| B | Original Date | 2026-02-21 |
| C | Original Time | 15:00 |
| D | Reason | busy |
| E | Outcome | rescheduled |
| F | Notes | Changed to next week |
| G | Logged At | 2026-02-20 14:30 |

---

## LeadManager Integration

### track_conversation_info Method

```python
def track_conversation_info(
    self,
    customer_phone: str,
    customer_name: str,
    pain_points: str,
    recommendations: str
) -> dict:
    """Save conversation insights to Google Sheets"""

    if not self.conversation_insights_sheet:
        return {'success': False, 'message': 'Insights sheet not found'}

    date = datetime.now().strftime('%Y-%m-%d')

    row = [
        customer_phone,
        customer_name,
        date,
        pain_points,
        recommendations,
        'No'  # Booked status (updated later)
    ]

    self.conversation_insights_sheet.append_row(row)

    return {
        'success': True,
        'message': 'Conversation info tracked'
    }
```

### log_cancellation_reason Method

```python
def log_cancellation_reason(
    self,
    customer_phone: str,
    original_booking_date: str,
    original_booking_time: str,
    cancellation_reason: str,
    outcome: str,
    notes: str = ""
) -> dict:
    """Log cancellation reason to Google Sheets"""

    if not self.cancellation_log_sheet:
        return {'success': False, 'message': 'Cancellation log sheet not found'}

    logged_at = datetime.now().strftime('%Y-%m-%d %H:%M')

    row = [
        customer_phone,
        original_booking_date,
        original_booking_time,
        cancellation_reason,
        outcome,
        notes,
        logged_at
    ]

    self.cancellation_log_sheet.append_row(row)

    return {
        'success': True,
        'message': 'Cancellation reason logged'
    }
```

---

## Analytics Use Cases

### 1. Pain Point Analysis

```
Query: What are the most common pain points?

Result:
1. Shoulder/neck tension - 45%
2. Lower back pain - 30%
3. Leg fatigue - 15%
4. General relaxation - 10%

Action: Create targeted promotions for shoulder massage
```

### 2. Cancellation Analysis

```
Query: Why do customers cancel?

Result:
1. Busy/schedule conflict - 50%
2. Health reasons - 20%
3. Reschedule (not actual cancel) - 20%
4. Budget - 5%
5. Other - 5%

Action: Implement flexible rescheduling policy
```

### 3. Recommendation Effectiveness

```
Query: Which recommended services lead to bookings?

Result:
1. 90-min Body Massage - 70% conversion
2. 60-min Foot Reflexology - 65% conversion
3. 120-min Full Body - 40% conversion

Action: Push 90-min Body Massage more in recommendations
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Insights not saved | Sheet not found | Run setup script |
| Wrong phone format | Not normalized | Clean phone in handler |
| Missing data | AI didn't call tool | Check tool description |
| Duplicate entries | Called multiple times | Add deduplication |

### Debug Logging

```
================================================================================
HANDLING TRACK_CONVERSATION_INFO FUNCTION CALL
================================================================================
Phone: 60123456789
Name: Unknown
Pain Points: shoulders stiff, work stress
Recommendations: 90-minute Body Massage with aromatherapy
Track result: {'success': True, 'message': 'Conversation info tracked'}
================================================================================
```

---

## Summary

The 3 Analytics Tools provide **business intelligence**:

- **`track_conversation_info`** — Capture pain points & recommendations
- **`lookup_my_bookings`** — Secure booking history refresh
- **`log_cancellation_reason`** — Understand why customers cancel

Data flows to Google Sheets for:
- Follow-up campaign targeting
- Service improvement insights
- Marketing optimization
- Customer retention analysis

This enables **data-driven decision making** for the business.
