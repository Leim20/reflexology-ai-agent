# Google Sheets API - Which Sheets Consume Most Quota (Per Message)

## Executive Summary

When you send **1 WhatsApp message**, here's which sheets are being read:

```
Per Single Message:

1. Customer Record sheet      → 1 read (get_all_values)
2. Conversation History sheet → 1 read (get_all_values)
3. Members sheet              → 0 reads (cached for 5 minutes)
4. Follow-up Campaigns sheet  → 1 read (get_all_records) - IF ENABLED
5. Follow-up Queue sheet      → 1 read (get_all_records) - IF ENABLED
6. Follow-up Log sheet        → 0 reads (write-only for this message)

TOTAL: 3-5 reads per message
```

---

## Detailed Breakdown by Handler

### Handler 1: Lead Manager (lead_manager.py)
**Processes incoming customer message**

When processing 1 customer message:

#### Read #1: Check if customer exists
```python
# File: lead_manager.py line 468 - get_lead_by_phone()
all_rows = self.sheet.get_all_values()  # 1 READ: Customer Record sheet
for row in all_rows:
    if normalize(row[1]) == normalized_phone:
        existing_lead = row
```
**Sheet**: "Customer Record"
**Cost**: 1 API read request

#### Read #2: Get conversation history
```python
# File: lead_manager.py line 566 - get_conversation_history()
all_rows = self.history_sheet.get_all_values()  # 1 READ: Conversation History
for row in all_rows:
    if normalize(row[0]) == normalized_phone:
        conversations.append(row)
```
**Sheet**: "Conversation History"
**Cost**: 1 API read request

#### Read #3: Check member info (CACHED - 0 cost)
```python
# File: lead_manager.py line 150 - _refresh_members_cache()
all_members_rows = self.members_sheet.get_all_values()  # 1 READ cached for 300 seconds
```
**Sheet**: "Members"
**Cost**: 0 API requests (cached, refreshes every 5 minutes)
**How often**: Every 300 seconds (5 minutes), not per message

**Subtotal for Lead Manager: 2 reads per message**

---

### Handler 2: Follow-up Manager (follow_up_manager.py)
**Auto-enrolls leads in follow-up campaigns**

⚠️ **ONLY IF FOLLOW-UP SYSTEM IS ENABLED**

When a lead is recorded and follow-up system is enabled:

#### Read #4: Check active campaigns
```python
# File: follow_up_manager.py line 163 - get_active_campaigns()
records = self.campaigns_sheet.get_all_records()  # 1 READ: Follow-up Campaigns sheet
```
**Sheet**: "Follow-up Campaigns"
**Cost**: 1 API read request

#### Read #5: Check if lead already enrolled
```python
# File: follow_up_manager.py line 260 - is_lead_enrolled()
records = self.queue_sheet.get_all_records()  # 1 READ: Follow-up Queue sheet
```
**Sheet**: "Follow-up Queue"
**Cost**: 1 API read request

**Subtotal for Follow-up Manager: 2 reads per message (if enabled)**

---

## Total Quota Usage Per Message

```
Scenario A: Lead Manager Only (No Follow-up)
├─ Customer Record (get_lead_by_phone)        1 read
├─ Conversation History (get_conversation)    1 read
└─ TOTAL: 2 reads per message ✅

Scenario B: Lead Manager + Follow-up Enabled
├─ Customer Record (get_lead_by_phone)        1 read
├─ Conversation History (get_conversation)    1 read
├─ Follow-up Campaigns (check active)         1 read
├─ Follow-up Queue (check enrollment)         1 read
└─ TOTAL: 4 reads per message ⚠️

Scenario C: With Background Jobs (every 15-30 min)
├─ Check_and_enroll_leads_job reads:
│  ├─ All leads                               1 read
│  ├─ Active campaigns                        1 read
│  └─ Subtotal: 2 reads per job run
│
└─ Every 15-30 minutes = ~2-4 reads per hour
```

---

## Why You Hit Quota with 1 Message

**Scenario**: You send 1 WhatsApp message with Follow-up enabled

```
Actual API Calls Made:

1. get_all_values() → Customer Record       [1 read]
2. get_all_values() → Conversation History  [1 read]
3. get_all_records() → Campaigns            [1 read]
4. get_all_records() → Queue                [1 read]
5. append_row() → Queue entry               [1 write]
6. Cache refresh (Members) if 5min expired  [0-1 read]

Total: 4-5 API calls from ONE message

If you send 15-20 messages in a minute: 60-100 API calls → HITS YOUR 60 req/min QUOTA
```

---

## The Problem Sheets (High Read Volume)

### 🔴 MOST READ: Follow-up Queue Sheet
**Why**: Checked multiple times per message
- Line 260: Check if already enrolled
- Line 281: Get pending follow-ups (background job)
- Line 326: Get next message
- Line 377: Mark follow-up as sent
- Line 467: Stop campaign for lead
- Line 503: Mark lead responded

**Total checks per message**: 2x
**Total checks per hour**: ~200+ if background jobs running

### 🔴 HIGH READ: Follow-up Campaigns Sheet
**Why**: Checked to find matching campaigns per message
- Line 163: Get active campaigns
- Line 187: Get specific campaign
- Multiple times per background job

**Total checks per message**: 1-2x
**Total checks per hour**: ~100+ if background jobs running

### 🟡 MEDIUM READ: Conversation History Sheet
**Why**: Loaded to get customer history per message
- Line 566: Get conversation history for customer

**Total checks per message**: 1x
**Total checks per hour**: Same as message count (50-100)

### 🟡 MEDIUM READ: Customer Record Sheet
**Why**: Loaded to find if customer exists per message
- Line 468: Check if customer exists
- Line 836: Get all leads (for follow-up job)

**Total checks per message**: 1x
**Total checks per hour**: Same as message count (50-100)

### 🟢 LOW READ: Members Sheet
**Why**: Cached for 5 minutes
- Line 161: Refresh members cache (every 300 seconds)

**Total checks per hour**: 12 times/hour (every 5 minutes)

---

## Optimization Ranking

### Highest Impact: Disable Follow-up System
**Current Cost**: 2 extra reads per message
**New Cost**: 0 reads per message
**Savings**: 50% reduction in quota usage

```
Before: 4-5 reads/msg → 60 reads/min at 15 msgs/min
After:  2 reads/msg  → 30 reads/min at 15 msgs/min
```

### High Impact: Cache Follow-up Sheets
**Current Cost**: Read every message
**New Cost**: Read once per 5 minutes
**Savings**: 90% reduction in follow-up sheet reads

```
Before: 100+ reads/hour for campaigns + queue
After:  24 reads/hour (once every 5 min per sheet)
```

### Medium Impact: Combine Conversation History + Customer Lookup
**Current Cost**: 2 separate get_all_values() calls
**New Cost**: 1 combined get_all_values() call
**Savings**: 50% reduction (1 read instead of 2)

---

## Quick Optimization: Disable Follow-up Features

If you're hitting quota limits, the fastest fix is:

### Option 1: Disable Follow-up System Completely
**File**: `config/config.json`
```json
{
  "lead_tracking": {
    "enabled": false    // ← Change this to false
  }
}
```

**Impact**:
- Eliminates 2 reads per message
- Saves ~50% of quota usage
- Follow-up campaigns stop processing

### Option 2: Disable Only Auto-Enrollment
**File**: Edit `web/app.py` around line 376
```python
# Comment out this line in check_and_enroll_leads_job():
# stats = follow_up_manager.check_and_enroll_leads(lead_manager)
```

**Impact**:
- Still processes follow-ups manually
- Saves 1-2 reads per hour from background jobs
- Saves 10-15% quota

### Option 3: Cache Follow-up Campaigns & Queue (Advanced)
Add caching to follow_up_manager.py similar to lead_manager:
```python
def get_active_campaigns(self):
    # Check cache first
    cached = self.cache_manager.get("active_campaigns")
    if cached:
        return cached

    # Fetch from sheets if not cached
    records = self.campaigns_sheet.get_all_records()  # 1 read
    self.cache_manager.set("active_campaigns", records, ttl=600)  # 10 min cache
    return records
```

**Impact**:
- Reduces campaigns reads from 100+/hour to 6/hour
- Saves ~94% on campaigns sheet reads
- Requires code change

---

## Your Real Situation Analysis

**You said**: "Send 1 message but hit quota"

This happens when:

### Scenario 1: Multiple Messages in Quick Succession
```
Send 15 messages in 1 minute:
├─ 15 messages × 4 reads each = 60 reads
└─ HITS 60 req/min quota exactly
```

### Scenario 2: Background Job Runs at Same Time
```
Send 5 messages (5 min):
├─ 5 messages × 4 reads = 20 reads
├─ Background job runs simultaneously = 2 reads
├─ All happen within same minute window
└─ 20-22 reads in that minute (within safe zone)

BUT if background jobs check sheets 10+ times/min:
├─ 5 messages × 4 = 20 reads
├─ Jobs × 10 = 10 reads
└─ 30 reads total (50% of quota)
```

### Scenario 3: Follow-up Queue Polling Too Frequently
```python
# If process_pending_followups_job runs every 1-5 minutes:
Every minute, if jobs align:
├─ Message processing × 2 reads
├─ Job polling queue × 1 read
├─ Job polling campaigns × 1 read
└─ Can easily hit 30-40 reads in 1 minute peak
```

---

## Recommended Configuration for 60 req/min Quota

### Conservative (Most Safe)
```json
{
  "lead_tracking": {
    "enabled": false  // Disable follow-up
  }
}
```
**Result**: 2 reads/msg, can handle 30 msgs/min safely

### Balanced (Safe + Features)
```json
{
  "lead_tracking": {
    "enabled": true,
    "auto_record_after_messages": 3
  }
}
// Plus add caching to follow_up_manager.py
```
**Result**: 4 reads/msg with caching, can handle 15 msgs/min safely

### Aggressive (All Features)
```json
{
  "lead_tracking": {
    "enabled": true
  }
}
// Keep as-is, monitor quota closely
```
**Result**: 4-5 reads/msg, can handle 12-15 msgs/min max

---

## Summary: Sheet Read Frequency

| Sheet | Per Message | Per Hour (50 msgs) | Per Hour (Job Runs) | Priority to Cache |
|-------|-------------|-------------------|-------------------|------------------|
| Customer Record | 1 read | 50 reads | 70 reads | HIGH |
| Conversation History | 1 read | 50 reads | 50 reads | HIGH |
| Follow-up Campaigns | 1 read | 50 reads | 60+ reads | **CRITICAL** |
| Follow-up Queue | 1 read | 50 reads | 100+ reads | **CRITICAL** |
| Members | 0 reads* | 12 reads | 12 reads | LOW (already cached) |

*Members are cached for 300 seconds

