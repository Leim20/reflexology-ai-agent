# Follow-up Campaigns Setup Guide

## Overview
This guide explains the Google Sheets structure needed for the automated follow-up system.

## Required Google Sheets Tabs

Your Google Sheet needs **4 new tabs** for the follow-up system:

### 1. Follow-up Campaigns
**Purpose:** Define your follow-up campaign templates

**Columns:**
| Column | Name | Description | Example |
|--------|------|-------------|---------|
| A | Campaign ID | Unique identifier | `FU001` |
| B | Campaign Name | Descriptive name | `3-Day No Response Follow-up` |
| C | Target Condition | Trigger condition | `no_response_72_hours` |
| D | Message 1 | First follow-up message | `Hi! Just checking if you're still interested...` |
| E | Message 2 | Second follow-up message | `We have a special offer...` |
| F | Message 3 | Third follow-up message | `Last chance to book...` |
| G | Gap Hours 1→2 | Hours between msg 1 and 2 | `48` |
| H | Gap Hours 2→3 | Hours between msg 2 and 3 | `72` |
| I | Status | Campaign status | `Active` or `Paused` |
| J | Total Sent | Counter (auto-updated) | `15` |
| K | Created Date | When campaign was created | `2024-11-17` |

**Header Row (Row 1):**
```
Campaign ID | Campaign Name | Target Condition | Message 1 | Message 2 | Message 3 | Gap Hours 1→2 | Gap Hours 2→3 | Status | Total Sent | Created Date
```

**Available Target Conditions:**
- `no_response_24_hours` - No reply for 24 hours
- `no_response_72_hours` - No reply for 3 days
- `no_response_168_hours` - No reply for 7 days
- `no_booking_72_hours` - Expressed interest but no booking in 3 days
- `no_booking_168_hours` - Expressed interest but no booking in 7 days
- `no_purchase_after_visit` - Visited but didn't purchase
- `new_lead` - All new leads (immediate follow-up)

---

### 2. Follow-up Queue
**Purpose:** Track individual leads in active campaigns (auto-managed by system)

**Columns:**
| Column | Name | Description | Example |
|--------|------|-------------|---------|
| A | Phone | Lead's phone number | `60123456789` |
| B | Campaign ID | Which campaign | `FU001` |
| C | Current Message | Message number (1, 2, or 3) | `2` |
| D | Next Send Time | When to send next message | `2024-11-17 15:30:00` |
| E | Status | Queue status | `Pending` / `Sent` / `Responded` / `Stopped` |
| F | Enrolled Date | When lead joined campaign | `2024-11-15 10:00:00` |
| G | Last Sent Date | Last message sent time | `2024-11-16 14:00:00` |
| H | Messages Sent | How many sent so far | `2` |

**Header Row (Row 1):**
```
Phone | Campaign ID | Current Message | Next Send Time | Status | Enrolled Date | Last Sent Date | Messages Sent
```

**Status Values:**
- `Pending` - Waiting to send next message
- `Sent` - Message sent, waiting for response
- `Responded` - Lead replied (campaign auto-stopped)
- `Stopped` - Campaign manually stopped
- `Completed` - All 3 messages sent

---

### 3. Follow-up Sent Log
**Purpose:** Record every follow-up message sent (analytics)

**Columns:**
| Column | Name | Description | Example |
|--------|------|-------------|---------|
| A | Phone | Lead's phone number | `60123456789` |
| B | Campaign ID | Which campaign | `FU001` |
| C | Campaign Name | Campaign name (for reference) | `3-Day No Response` |
| D | Message Number | Which message (1, 2, or 3) | `1` |
| E | Message Text | What was sent | `Hi! Just checking...` |
| F | Sent Time | When it was sent | `2024-11-17 10:00:00` |
| G | Response Received | Did they reply? | `Yes` / `No` |
| H | Response Time | When they replied | `2024-11-17 11:30:00` |
| I | Response Text | First message after follow-up | `Yes, I'm interested!` |

**Header Row (Row 1):**
```
Phone | Campaign ID | Campaign Name | Message Number | Message Text | Sent Time | Response Received | Response Time | Response Text
```

---

### 4. Follow-up Analytics
**Purpose:** Campaign performance metrics (auto-updated)

**Columns:**
| Column | Name | Description | Example |
|--------|------|-------------|---------|
| A | Campaign ID | Campaign identifier | `FU001` |
| B | Campaign Name | Campaign name | `3-Day No Response` |
| C | Total Enrolled | Leads enrolled | `25` |
| D | Message 1 Sent | How many msg 1 sent | `25` |
| E | Message 2 Sent | How many msg 2 sent | `18` |
| F | Message 3 Sent | How many msg 3 sent | `10` |
| G | Responses Received | Total replies | `12` |
| H | Conversions | Bookings/purchases | `8` |
| I | Response Rate | Percentage who replied | `48%` |
| J | Conversion Rate | Percentage who converted | `32%` |
| K | Last Updated | Last analytics update | `2024-11-17 15:00:00` |

**Header Row (Row 1):**
```
Campaign ID | Campaign Name | Total Enrolled | Message 1 Sent | Message 2 Sent | Message 3 Sent | Responses Received | Conversions | Response Rate | Conversion Rate | Last Updated
```

---

## Quick Setup Steps

### Option 1: Manual Setup
1. Open your existing Google Sheet (Customer Record sheet)
2. Create 4 new tabs with the names above
3. Add the header rows to each tab
4. You're ready to create campaigns!

### Option 2: Automatic Setup (Recommended)
The `FollowUpManager` class will automatically create these sheets if they don't exist when you first run the system.

---

## Sample Campaign

Here's an example campaign to get you started:

**Follow-up Campaigns Tab - Row 2:**
```
FU001 | 3-Day No Response Follow-up | no_response_72_hours | Hi [Name]! I noticed we chatted a few days ago about reflexology services. Are you still interested? 😊 | Hello again! We have a special promotion this week - 20% off your first session. Would you like to book? | Last chance! Our promotion ends tomorrow. Book now to save 20%: [link] | 48 | 72 | Active | 0 | 2024-11-17
```

**Translation:**
- Campaign ID: FU001
- Name: 3-Day No Response Follow-up
- Trigger: When someone doesn't respond for 72 hours
- Message 1: Sent immediately when triggered
- Message 2: Sent 48 hours after Message 1
- Message 3: Sent 72 hours after Message 2
- Status: Active (will run automatically)

---

## How It Works

1. **Lead qualifies for campaign** → System checks conditions every 5 minutes
2. **Auto-enrolled** → Lead added to Follow-up Queue
3. **Message 1 sent immediately** → Recorded in Sent Log
4. **Wait for gap period** → System waits (e.g., 48 hours)
5. **Check if lead responded** → If yes, stop campaign
6. **If no response, send Message 2** → Wait for next gap
7. **Repeat for Message 3** → Campaign completes or stops if they reply

---

## Important Notes

- **Auto-stop on response:** If a lead replies at ANY point, the campaign stops automatically
- **No duplicates:** A lead can only be in one instance of each campaign at a time
- **Manual override:** Set Status to "Paused" to stop a campaign temporarily
- **Analytics auto-update:** The system updates analytics every time a message is sent

---

## Next Steps

After setting up these sheets:
1. Configure your first campaign in the "Follow-up Campaigns" tab
2. The system will start monitoring leads automatically
3. Check "Follow-up Analytics" to see performance
4. Adjust messages and timing based on results

---

## Support

For technical issues or questions about configuration, check the main documentation or contact support.
