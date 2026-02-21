# Broadcast Feature

## Overview

The Broadcast Feature allows staff to schedule and send bulk WhatsApp messages to a list of recipients. Everything is managed through Google Sheets — staff adds recipients and schedules messages in the sheet, and the system auto-sends at the specified date and time.

**Source file:** `handlers/tools/broadcast_manager.py`  
**Scheduler job:** `web/app.py` — `check_and_send_broadcasts_job()`  
**Google Sheet:** Same spreadsheet as the main system (3 dedicated tabs)

---

## How It Works

### Step-by-Step Flow

1. **Staff adds recipients** to the `Broadcast Recipients` sheet (Name + Phone + Status=Active).

2. **Staff creates a broadcast** in the `Scheduled Broadcasts` sheet with:
   - A title, message text (or `image_url|caption` for image messages)
   - Scheduled Date and Time
   - Target List (usually `all` or a specific group)
   - Status = `Pending`

3. **Scheduler checks every 1 minute** via `check_and_send_broadcasts_job()`.  
   Finds broadcasts where:
   - Status = `Pending`
   - Scheduled Date/Time has passed (i.e., it is now time to send)

4. **System sends to each recipient** in the Recipients list:
   - 60-second delay between each message (to avoid spam detection)
   - Retries up to 10 times with exponential backoff if send fails
   - Supports both text and image messages

5. **Delivery is logged** to `Broadcast Logs` sheet per recipient.

6. **Broadcast status updated** to `Sent` with sent timestamp and count.

---

## Google Sheets Structure

### Tab: Broadcast Recipients

List of customers/phones to receive broadcasts.

| Column | Field | Description |
|--------|-------|-------------|
| A | Name | Recipient name |
| B | Phone | WhatsApp phone number |
| C | Status | Active or Inactive |
| D | Added Date | When they were added |
| E | Notes | Optional notes |

Only recipients with Status = `Active` will receive broadcasts.

---

### Tab: Scheduled Broadcasts

Staff creates rows here to schedule broadcasts.

| Column | Field | Description |
|--------|-------|-------------|
| A | Broadcast ID | Unique ID (e.g., BROADCAST001) |
| B | Title | Internal label for the broadcast |
| C | Message | Message text OR `image_url|caption` for image |
| D | Schedule Date | Date to send (YYYY-MM-DD) |
| E | Schedule Time | Time to send (HH:MM) |
| F | Target List | `all` or group name |
| G | Status | Pending, Sending, Sent, Failed |
| H | Sent Count | How many recipients received it |
| I | Created Date | When the row was created |
| J | Sent Date | When broadcast was completed |

**Image message format in Message column:**
```
https://drive.google.com/file/d/FILE_ID/view|Your caption here
```
The system detects the pipe character `|` to split URL from caption.

---

### Tab: Broadcast Logs

One row per recipient per broadcast — full delivery audit trail.

| Column | Field | Description |
|--------|-------|-------------|
| A | Broadcast ID | Which broadcast |
| B | Title | Broadcast title |
| C | Phone | Recipient phone |
| D | Name | Recipient name |
| E | Sent Time | When message was sent |
| F | Delivery Status | Sent, Failed |
| G | Message Type | text or image |
| H | Retry Count | Number of retries needed |
| I | Response Text | Any error message if failed |

---

## Message Types

### Text Message
Simply enter the message text in the Message column.

Example:
```
Hi! Serenity Reflexology is offering 20% off all services this weekend.
Book now: 03-1234 5678
```

### Image Message (with caption)
Format: `image_url|caption_text`

Supported image sources:
- **Google Drive**: Provide the sharing URL or file ID. The system automatically downloads and converts to base64 for WhatsApp.
- **Direct URL**: Any public image URL ending in .jpg, .jpeg, .png, .gif, .webp

Example:
```
https://drive.google.com/file/d/1abc123.../view|Check out our new promotion! 🎉
```

---

## Retry Behavior

| Setting | Value |
|---------|-------|
| Max retry attempts | 10 |
| Initial retry delay | 2 seconds |
| Max retry delay | 60 seconds |
| Backoff | Exponential (doubles each retry) |
| Delay between recipients | 60 seconds |

If all 10 retries fail, the send is marked `Failed` in the Broadcast Logs.

---

## Scheduler Registration

Defined in `web/app.py` `init_app()`:

```python
scheduler.add_job(
    func=check_and_send_broadcasts_job,
    trigger='interval',
    minutes=1,
    id='check_broadcasts',
    name='Check and send scheduled broadcasts',
    replace_existing=True
)
```

The job is only registered if both `broadcast_manager` and `whatsapp_handler` are initialized successfully at startup.

---

## Key Methods

| Method | Location | Description |
|--------|----------|-------------|
| `BroadcastManager.__init__()` | `broadcast_manager.py` | Initializes 3 Sheets tabs |
| `check_and_send_broadcasts_job()` | `web/app.py` line ~900 | Main scheduler job |
| `get_pending_broadcasts()` | `broadcast_manager.py` | Finds broadcasts ready to send |
| `get_active_recipients()` | `broadcast_manager.py` | Returns all Active recipients |
| `send_broadcast()` | `broadcast_manager.py` | Sends to all recipients with retry |
| `log_delivery()` | `broadcast_manager.py` | Writes to Broadcast Logs tab |
| `download_google_drive_image()` | `broadcast_manager.py` | Downloads Drive image as base64 |

---

## Setup Script

Run once to create the 3 broadcast tabs in the spreadsheet:
```
cd /root/reflexology-agent(token-optimized)
python3 scripts/setup_broadcast_sheets.py
```

---

## Configuration

In `config/config.json` (under `google_sheets_features`):
```json
"broadcast_system": {
    "enabled": true
}
```

The broadcast system uses the same spreadsheet as the lead tracking system (same `spreadsheet_name` from `lead_tracking` config). It shares the Google Service Account credentials.

---

## Important Notes

- **Anti-spam**: The 60-second delay between recipients is mandatory to avoid WhatsApp spam detection and account bans.
- **Google Drive images**: The file must be set to "Anyone with the link can view" for the download to work.
- **Timing precision**: The scheduler runs every 1 minute. A broadcast scheduled for 14:00 may send between 14:00 and 14:01.
- **No duplicate sends**: Once a broadcast is marked `Sent`, the scheduler will never send it again.
