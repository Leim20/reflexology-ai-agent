# Follow-up Feature

## Overview

The Follow-up Feature automatically sends scheduled WhatsApp follow-up messages to leads who haven't booked, haven't responded, or showed interest but didn't convert. It operates as a **campaign-based system** managed entirely through Google Sheets and runs on a background scheduler.

**Source file:**   
**Queue logic:**   
**Scheduler jobs:** 

---

## Architecture: Minimal Quota Mode (4-Job Pipeline)

The system uses a 4-job pipeline designed to minimize Google Sheets API quota usage.



Result: ~44 Google Sheets API calls per hour (vs. ~200+ without this design).

---

## Google Sheets Structure

The system uses 4 tabs in the same Google Spreadsheet:

### Tab: Follow-up Campaigns

Defines each campaign with messages and timing.

| Column | Field | Description |
|--------|-------|-------------|
| A | Campaign ID | Unique ID (e.g., CAMP001) |
| B | Campaign Name | Human-readable name |
| C | Target Condition | Trigger condition (see conditions below) |
| D | Message 1 | First message text |
| E | Message 2 | Second message text |
| F | Message 3 | Third message text |
| G | Gap Hours 1->2 | Hours to wait before Message 2 |
| H | Gap Hours 2->3 | Hours to wait before Message 3 |
| I | Status | active or inactive |
| J | Total Sent | Count of total sends |
| K | Created Date | When campaign was created |

---

### Tab: Follow-up Queue

Tracks which customer is in which campaign stage.

| Column | Field | Description |
|--------|-------|-------------|
| A | Phone | Customer phone number |
| B | Campaign ID | Which campaign they are in |
| C | Current Message | Next message to send (1, 2, or 3) |
| D | Next Send Time | Scheduled datetime for next message |
| E | Status | Pending, Queued, Sent, Completed, Responded, Stopped |
| F | Enrolled Date | When they were enrolled |
| G | Last Sent Date | When last message was sent |
| H | Messages Sent | Count of messages sent so far |

---

### Tab: Follow-up Sent Log

Audit log of every message sent.

| Column | Field | Description |
|--------|-------|-------------|
| A | Phone | Customer phone |
| B | Campaign ID | Campaign |
| C | Campaign Name | Campaign name |
| D | Message Number | Which message (1/2/3) |
| E | Message Text | Actual message content sent |
| F | Sent Time | When it was sent |
| G | Response Received | Yes / No / Failed |
| H | Response Time | When customer responded |
| I | Response Text | Customer response (first 100 chars) |

---

### Tab: Follow-up Analytics

Aggregated statistics per campaign.

| Column | Field |
|--------|-------|
| A | Campaign ID |
| B | Campaign Name |
| C | Total Enrolled |
| D | Message 1 Sent |
| E | Message 2 Sent |
| F | Message 3 Sent |
| G | Responses Received |
| H | Conversions |
| I | Response Rate |
| J | Conversion Rate |
| K | Last Updated |

---

## Trigger Conditions

Leads are automatically enrolled in campaigns based on these conditions:

| Condition Code | Triggers when... |
|----------------|-----------------|
| no_response_24_hours | Customer has not interacted in 24+ hours |
| no_response_72_hours | Customer has not interacted in 72+ hours |
| no_response_168_hours | Customer has not interacted in 7+ days |
| no_booking_72_hours | Showed booking interest but no booking in 72+ hours |
| no_booking_168_hours | Showed booking interest but no booking in 7+ days |
| no_purchase_after_visit | Visited in last 30 days but no purchase recorded |
| new_lead | Customer has had 2 or fewer conversations total |
| warm_lead_24h | Got AI recommendation but no booking — 24h later |
| warm_lead_48h | Got AI recommendation but no booking — 48h later |
| warm_lead_72h | Got AI recommendation but no booking — 72h later |

Each campaign has exactly ONE Target Condition. A lead can be enrolled in multiple campaigns if they meet multiple conditions.

---

## Message Personalization

Campaign messages support dynamic placeholders:

| Placeholder | Replaced with |
|-------------|--------------|
| {name} | Customer name (from Conversation Insights or Customer Record) |
| {pain_points} | Customer health concerns (e.g., back pain) |
| {recommendations} | Services the AI previously recommended |

If placeholder data is unavailable, graceful fallbacks are applied automatically.

---

## Auto-Stop Behavior

When a customer replies to any message (via WhatsApp):

1. FollowUpManager.mark_lead_responded(phone, response_text) is called
2. All Pending or Sent queue entries for that phone are set to Responded
3. No further follow-up messages are sent to that customer
4. The Sent Log is updated with the response text and time

---

## Status Lifecycle



---

## Key Classes and Methods

| Class / Method | Location | Description |
|----------------|----------|-------------|
| FollowUpManager.__init__() | follow_up_manager.py | Connects to Sheets, initializes 4 tabs |
| check_and_enroll_leads() | follow_up_manager.py | Scans all leads, auto-enrolls matching conditions |
| get_pending_followups() | follow_up_manager.py | Gets queue entries ready to send |
| get_next_message() | follow_up_manager.py | Gets message text with personalization |
| mark_followup_sent() | follow_up_manager.py | Updates queue + log after send |
| mark_lead_responded() | follow_up_manager.py | Stops all campaigns for a phone |
| batch_update_queue() | follow_up_manager.py | Batch write multiple queue updates |
| FollowupMessageQueue | utils/followup_queue.py | Thread-safe in-memory RAM queue |
| check_and_enroll_leads_job() | web/app.py | APScheduler job: enroll |
| check_and_queue_followups_job() | web/app.py | APScheduler job: check timing |
| throttled_send_followup_job() | web/app.py | APScheduler job: send |
| flush_batch_updates_job() | web/app.py | APScheduler job: flush writes |

---

## Configuration

In config/config.json:

    google_sheets_features: {
        follow_up_system: {
            enabled: true
        }
    }

To disable follow-up entirely: set enabled to false. This saves ~2 Google Sheets API reads per inbound message.

---

## Setup

Run this script once to create the 4 follow-up tabs in the spreadsheet:

    cd /root/reflexology-agent(token-optimized)
    python3 scripts/setup_followup_sheets.py
