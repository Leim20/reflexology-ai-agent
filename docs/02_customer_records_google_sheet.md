# Customer Records in Google Sheet

## Overview

The Customer Records feature automatically tracks and organizes every customer who interacts with the bot. Data is stored in a Google Spreadsheet via `handlers/tools/lead_manager.py` (`LeadManager` class).

The system uses a **single Google Spreadsheet** (configured in `config.json` → `lead_tracking.spreadsheet_name`) with **6 dedicated tabs (worksheets)**.

---

## Google Spreadsheet Structure

### Tab 1: `Customer Record` (Main customer profile)

| Column | Field | Description |
|--------|-------|-------------|
| A | Name | Customer's name (extracted by AI from conversation) |
| B | Phone | WhatsApp phone number (e.g., `60123456789`) |
| C | Interest | Current interest category (e.g., Booking, Inquiry, Service) |
| D | Last Visit | Date of last recorded visit (YYYY-MM-DD) |
| E | Preferences | Customer preferences extracted from conversation |
| F | Total Conversations | Count of all recorded conversations |
| G | Last Updated | Timestamp of last update |

**Auto-record trigger:** After every 3 messages in a new conversation (`auto_record_after_messages: 3` in config).

---

### Tab 2: `Conversation History`

| Column | Field | Description |
|--------|-------|-------------|
| A | Phone | WhatsApp phone number |
| B | Date | Date of conversation |
| C | Conversation Summary | AI-generated summary of the session |
| D | Interest Category | Detected category |
| E | AI Confidence | Confidence score of category detection |

Each conversation session creates one row in this tab.

---

### Tab 3: `Members`

Tracks customers enrolled in the membership/loyalty program.

| Column | Field | Description |
|--------|-------|-------------|
| A | Phone | WhatsApp phone number |
| B | Name | Member's name |
| C | Birthday | Birthday (YYYY-MM-DD) |
| D | Registration Date | Date they became a member |
| E | Points | Current loyalty points balance |
| F | Birthday Benefit Used | Whether birthday benefit was used this year |

**Note:** Members are registered via AI function call (`register_member`) when a customer asks to join the membership during chat.

---

### Tab 4: `Bookings`

Records all appointments booked through the bot.

| Column | Field | Description |
|--------|-------|-------------|
| A | Name | Customer name |
| B | Phone | WhatsApp phone number |
| C | Service | Service booked (e.g., "60-min Foot Massage") |
| D | Booking Date | Date of appointment (YYYY-MM-DD) |
| E | Booking Time | Time of appointment (HH:MM) |
| F | Therapist | Preferred therapist (if specified) |
| G | Notes | Special requests or notes |
| H | Status | Booking status (Confirmed / Cancelled / Completed) |
| I | Reminder Sent | Timestamp when reminder was sent (empty = not yet sent) |

**Auto-booking detection:** The AI automatically detects when a booking is confirmed in conversation and writes to this sheet.

---

### Tab 5: `Conversation Insights`

Stores AI analysis from each conversation — pain points and recommendations made by the AI.
This is the primary data source for the **Follow-up Feature** (warm lead detection).

| Column | Field | Description |
|--------|-------|-------------|
| A | Phone | Customer phone number (normalized, no + or spaces) |
| B | Name | Customer name |
| C | Pain Points | Health concerns mentioned by customer (e.g., "back pain", "stress") |
| D | Recommendations | Services the AI recommended to the customer |
| E | Last Updated | Timestamp of last update (YYYY-MM-DD HH:MM:SS) |

**Special values for Pain Points column:**
- `direct_booking_request` — Customer skipped discovery, asked to book directly
- `not_disclosed` — Customer did not share any health concerns

**How this sheet is populated:**
The AI calls `track_conversation_info()` after STEP 3 of the conversation framework
(after making a recommendation). It updates the existing row if the phone exists, or
creates a new row.

**Warm Lead Detection:**
`get_customer_context(phone)` checks this sheet + the Bookings sheet.
If a row exists in Conversation Insights but NO booking exists → customer is flagged
as a **warm lead** and becomes eligible for follow-up campaigns.

---

### Tab 6: `Cancellation Log`

Tracks cancellation and reschedule events with reasons and outcomes for retention analytics.

| Column | Field | Description |
|--------|-------|-------------|
| A | Phone | Customer phone number (normalized) |
| B | Name | Customer name (auto-fetched from Bookings sheet) |
| C | Original Date | Original booking date that was cancelled |
| D | Original Time | Original booking time that was cancelled |
| E | Reason | Cancellation reason code (see below) |
| F | Outcome | What happened after cancellation (see below) |
| G | Notes | Additional context or notes |
| H | Timestamp | When the cancellation was logged (YYYY-MM-DD HH:MM:SS) |

**Reason values (column E):**
- `busy` — Customer has something else to do
- `health` — Customer is not feeling well
- `budget` — Budget or money concern
- `reschedule` — Customer wants a different time
- `other` — Other reasons

**Outcome values (column F):**
- `rescheduled` — Customer changed to a new date/time
- `cancelled` — Booking fully cancelled, no rebooking

**How this sheet is populated:**
When a customer asks to cancel, the AI uses a retention-focused approach:
1. Asks caring questions about the reason
2. Offers alternatives if appropriate (e.g., reschedule for `busy`, later date for `health`)
3. Calls `log_cancellation_reason()` automatically after the conversation
4. Writes the reason and outcome to this sheet

---

## How Customer Records Are Created / Updated

### Automatic Flow

```
Customer sends message #3 in conversation
        │
        ▼
LeadManager.update_customer_record(phone, name, interest, summary)
        │
        ├── Customer exists?  ──YES──► Update: interest, last_updated, total_conversations
        │                               
        └── NO ──► Create new row: name, phone, interest, last_updated, total_conversations=1
```

### Interest Categorization

The AI analyzes the conversation and assigns one of these interest categories:
- `Booking` — Customer wants to make an appointment
- `Inquiry` — General questions about services/prices
- `Membership` — Asking about membership benefits
- `Complaint` — Service feedback
- `Returning Customer` — Has visited before

If `use_ai_analysis: true` (config), GPT-4o-mini is called to extract and classify the customer's intent.

---

## How Members Are Registered

When a customer says *"I want to register as a member"* in chat:

1. AI calls the `register_member` function (defined in `web/app.py`).
2. System collects name, birthday from conversation.
3. Writes to `Members` tab.
4. Replies with confirmation and loyalty points balance.

---

## How Bookings Are Recorded

### Automatic Detection
The system (`auto_detect_and_record_booking()` in `web/app.py`) scans every AI response for booking confirmation patterns (e.g., *"confirmed your booking for..."*) and automatically writes to the `Bookings` tab.

### Manual Function Call
If auto-detection misses a booking, the AI explicitly calls the `record_booking` function.

Both methods write: Name, Phone, Service, Date, Time, Therapist, Notes, Status = `Confirmed`.

---

## Cache Behavior

`LeadManager` uses `CacheManager` (TTL: 300 seconds) for all Google Sheets reads:

- Member lookups: **pre-cached on startup** (all members loaded into RAM)
- Customer records: cached for 5 minutes per phone number
- Bookings: read fresh each time (reminder-critical)

This reduces Google Sheets API usage by ~80–90%.

---

## Setup Scripts

| Script | Purpose |
|--------|---------|
| `scripts/setup_booking_sheet.py` | Create/initialize `Bookings` tab |
| `scripts/setup_members_sheet.py` | Create/initialize `Members` tab |
| `scripts/setup_conversation_insights_sheet.py` | Create/initialize `Conversation Insights` tab |
| `scripts/setup_cancellation_log_sheet.py` | Create/initialize `Cancellation Log` tab |
| `scripts/google_sheets_writer.py` | Utility for direct sheet writes |

---

## Configuration

In `config/config.json`:
```json
"lead_tracking": {
    "enabled": true,
    "credentials_file": "config/<PUT_YOUR_GOOGLE_PROJECT_ID_HERE>-c123857bd130.json",
    "spreadsheet_name": "YOUR_GOOGLE_SHEET_ID",
    "auto_record_after_messages": 3,
    "use_ai_analysis": true,
    "log_lead_recording": true
}
```

- `credentials_file`: Google Service Account JSON key (must have Sheets + Drive access)
- `spreadsheet_name`: Can be spreadsheet name, full URL, or spreadsheet ID
- `auto_record_after_messages`: How many messages before first auto-record
- `use_ai_analysis`: Use AI to classify interest category (vs. keyword matching)

