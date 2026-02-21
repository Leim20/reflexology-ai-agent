# Reminder Feature (Booking Reminder)

## Overview

The Booking Reminder feature automatically sends a WhatsApp reminder message to customers before their scheduled appointment. It runs as a background scheduler job every 1 minute and checks for any upcoming bookings within the next 5 minutes.

**Source file:** `web/app.py` — `booking_reminder_job()` function  
**Booking data source:** `handlers/tools/lead_manager.py` — `get_upcoming_bookings_for_reminder()`  
**Google Sheet tab:** `Bookings`

---

## How It Works

### Step-by-Step Flow

1. **Scheduler triggers** `booking_reminder_job()` every 1 minute.

2. **Fetch upcoming bookings**: Calls `lead_manager.get_upcoming_bookings_for_reminder(minutes_before=5)`.  
   This reads all rows from the `Bookings` Google Sheet tab and filters for:
   - Today's date only
   - Appointment is **1 to 5 minutes away**
   - `Reminder Sent` column is empty (not yet sent)

3. **Send reminder via WhatsApp**: For each qualifying booking, the system:
   - Generates a personalized message via `get_booking_reminder_message(booking)`
   - Sends it using `whatsapp_handler.send_message(phone, message)`

4. **Mark as sent**: On successful send, calls `lead_manager.mark_reminder_sent(row)` which writes the current timestamp to column I (`Reminder Sent`) of that booking row.

5. **Prevent duplicates**: On the next scheduler run, any booking with a non-empty `Reminder Sent` column is skipped.

---

## Reminder Message Format

The reminder is bilingual (Chinese + English), personalized with the customer's name, booking time, and service:

```
Hi {name}! 温馨提醒您今天 {booking_time} 有预约 {service} 😊

地址：12, Jalan Contoh 1, Downtown, 40000 Example City, Selangor

期待您的光临～有任何问题随时联系我们！
```

If the customer's name is unknown, the greeting becomes `Hi!`.

The branch address is dynamically loaded from `config.json` → `branch_contact.address`.

---

## Reminder Window

| Setting | Value |
|---------|-------|
| Scheduler frequency | Every 1 minute |
| Reminder window | 1–5 minutes before appointment |
| Minimum advance | 1 minute |
| Maximum advance | 5 minutes (minutes_before parameter) |

**Note:** The comment in code says 30–60 minutes but the actual call uses `minutes_before=5`. The scheduler checks every minute, so the effective window is 1–5 minutes before appointment time.

---

## Google Sheets: Bookings Tab

The reminder system reads from and writes to the `Bookings` tab:

| Column | Field | Used for reminder? |
|--------|-------|--------------------|
| A | Name | Yes — personalize greeting |
| B | Phone | Yes — send WhatsApp to this number |
| C | Service | Yes — include in message |
| D | Booking Date | Yes — filter for today only |
| E | Booking Time | Yes — calculate minutes until appointment |
| F | Therapist | No |
| G | Notes | No |
| H | Status | No |
| I | Reminder Sent | Yes — checked to skip; written after send |

---

## Time Parsing

The system handles multiple time formats in the `Booking Time` column:

- `HH:MM` (e.g., `14:30`)
- `HH:MM:SS`
- `H:MM AM/PM` (e.g., `2:30 PM`)
- `HH.MM` (dot separator, converted to colon)

If the time cannot be parsed, the booking is skipped and a warning is logged.

---

## Scheduler Registration

Defined in `web/app.py` `init_app()`:

```python
scheduler.add_job(
    func=booking_reminder_job,
    trigger='interval',
    minutes=1,
    id='booking_reminder',
    name='Send booking reminders 30-60 min before appointment',
    replace_existing=True
)
```

The scheduler is an APScheduler `BackgroundScheduler` that starts automatically when the Flask app launches.

---

## Key Methods

| Method | Location | Description |
|--------|----------|-------------|
| `booking_reminder_job()` | `web/app.py` line ~842 | Main scheduler job |
| `get_upcoming_bookings_for_reminder()` | `lead_manager.py` line ~1681 | Reads Bookings sheet, filters by window |
| `get_booking_reminder_message()` | `lead_manager.py` line ~1801 | Generates personalized message text |
| `mark_reminder_sent()` | `lead_manager.py` line ~1793 | Writes timestamp to Reminder Sent column |

---

## Dependency Requirements

The reminder job only registers if both `lead_manager` and `whatsapp_handler` are initialized at startup. If either is missing (e.g., Google Sheets credentials are invalid), the job is skipped and a warning is logged:

```
⚠️  Follow-up scheduler jobs not registered (missing dependencies)
```

---

## Configuration

Reminder behavior depends on:

```json
"booking_notification": {
    "enabled": true,
    "notify_phone": "60120000000",
    "notify_name": "Ryan"
}
```

This is for staff notification (separate from customer reminder). The booking reminder to the customer uses the `whatsapp_handler` directly.

The branch address in the reminder message comes from:
```json
"branch_contact": {
    "address": "12, Jalan Contoh 1, Downtown, 40000 Example City, Selangor"
}
```
