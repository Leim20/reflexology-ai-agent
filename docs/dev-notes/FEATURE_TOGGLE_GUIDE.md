# Google Sheets Feature Toggles - Configuration Guide

This guide explains what each feature toggle does and how much quota you save by disabling it.

## Current Configuration Location
**File**: `config/config.json`
**Section**: `google_sheets_features`

---

## Feature 1: Follow-up System
**Config Key**: `follow_up_system`
**Status**: Enabled (true/false to toggle)

### What It Does
- Auto-enrolls customers in follow-up campaigns
- Tracks pending follow-up messages
- Logs all follow-up messages sent
- Provides analytics on campaign performance

### Google Sheets Involved
1. Follow-up Campaigns sheet - Gets list of active campaigns
2. Follow-up Queue sheet - Checks if customer already enrolled, adds new entries
3. Follow-up Sent Log sheet - Records sent messages
4. Follow-up Analytics sheet - Tracks performance metrics

### API Quota Impact
```
Per Customer Message (with Follow-up enabled):
├─ Check active campaigns        → 1 API read
├─ Check if lead already enrolled → 1 API read
├─ Add to follow-up queue        → 1 API write
└─ TOTAL: 2 reads + 1 write per message

Example: 15 messages/min × 2 reads = 30 API reads/min
Without this feature: Saves 30 API reads/min
```

### When To Disable
- You don't need automated follow-up campaigns
- Manual follow-up system is sufficient
- You're hitting quota limits (429 errors)

### Impact of Disabling
- ✅ Saves 2 API reads per message
- ✅ Saves ~50% of total API quota usage
- ❌ Auto follow-up campaigns stop working
- ❌ Follow-up queue system is disabled
- ⚠️ Manual follow-up tracking still available

### How to Disable
```json
{
  "google_sheets_features": {
    "follow_up_system": {
      "enabled": false
    }
  }
}
```

---

## Feature 2: Membership System
**Config Key**: `membership_system`
**Status**: Enabled (true/false to toggle)

### What It Does
- Loads all member data at startup and caches it
- Checks membership status for each customer
- Tracks loyalty points
- Manages birthday promotions
- Validates members for special pricing

### Google Sheets Involved
1. Members sheet - Customer membership details, points, birthday info

### API Quota Impact
```
Per Customer Message (with Membership enabled):
├─ Check member cache           → 0 API reads (if cached)
└─ Refresh member cache every 5 min → 1 API read

Example: 50 messages/min = 0 reads (cached), every 5 min = 1 read
Without this feature: Saves 1 API read every 5 minutes
Total savings: ~12 API reads per hour
```

### When To Disable
- You don't have a membership program
- You don't need loyalty points tracking
- You don't need birthday promotions
- You're hitting quota limits

### Impact of Disabling
- ✅ Saves 1 API read every 5 minutes (~12/hour)
- ✅ Small but consistent quota savings
- ❌ Member status checking disabled
- ❌ Loyalty points system disabled
- ❌ Birthday promotions disabled
- ⚠️ You can still greet customers by name if stored elsewhere

### How to Disable
```json
{
  "google_sheets_features": {
    "membership_system": {
      "enabled": false
    }
  }
}
```

---

## Feature 3: Conversation History
**Config Key**: `conversation_history`
**Status**: Enabled (true/false to toggle)

### What It Does
- Stores all customer conversations in Google Sheets
- Retrieves conversation history for each customer
- Provides context for AI responses
- Maintains conversation records for audit/reference

### Google Sheets Involved
1. Conversation History sheet - All messages and responses

### API Quota Impact
```
Per Customer Message (with Conversation History enabled):
├─ Get conversation history    → 1 API read
├─ Save new message            → 1 API write
└─ TOTAL: 1 read + 1 write per message

Example: 50 messages/min × 1 read = 50 API reads/min
Without this feature: Saves 50 API reads per minute
This is ~83% of your total quota!
```

### When To Disable
- You don't need conversation history
- You're storing conversations elsewhere (database)
- You're hitting quota limits
- Customer context isn't important for responses

### Impact of Disabling
- ✅ Saves 1 API read per message
- ✅ Saves up to 50% of total quota usage (depending on message volume)
- ❌ No conversation history stored
- ❌ AI won't have previous context
- ❌ No audit trail of communications
- ⚠️ Responses will be less personalized

### How to Disable
```json
{
  "google_sheets_features": {
    "conversation_history": {
      "enabled": false
    }
  }
}
```

---

## Feature 4: Lead Tracking
**Config Key**: `lead_tracking`
**Status**: Enabled (true/false to toggle)

### What It Does
- Tracks all customer interactions
- Records customer names, phone, interests
- Updates last visit dates
- Maintains customer profile information
- Used by follow-up system to know who to contact

### Google Sheets Involved
1. Customer Record sheet - All customer details and interaction history

### API Quota Impact
```
Per Customer Message (with Lead Tracking enabled):
├─ Check if customer exists    → 1 API read
├─ Update customer record      → 1 API write
└─ TOTAL: 1 read + 1 write per message

Example: 50 messages/min × 1 read = 50 API reads/min
Without this feature: Saves 50 API reads per minute
```

### When To Disable
- You don't need to track customer interactions
- You're storing customer data elsewhere
- You're hitting quota limits
- You don't need customer profiles

### Impact of Disabling
- ✅ Saves 1 API read per message
- ✅ Saves up to 50% of total quota usage
- ❌ No customer profiles maintained
- ❌ No interaction history tracked
- ❌ Follow-up system won't work (depends on this data)
- ❌ No way to identify repeat customers
- ⚠️ Lost ability to personalize responses

### How to Disable
```json
{
  "google_sheets_features": {
    "lead_tracking": {
      "enabled": false
    }
  }
}
```

---

## Quota Savings Summary

| Feature | Quota Cost | Impact When Disabled |
|---------|-----------|----------------------|
| Follow-up System | 2 reads/msg | -2 reads per message |
| Membership System | 1 read/300s | -12 reads per hour |
| Conversation History | 1 read/msg | -1 read per message |
| Lead Tracking | 1 read/msg | -1 read per message |

---

## Recommended Scenarios

### Scenario A: Stay Safe (Recommended)
```json
{
  "follow_up_system": { "enabled": true },
  "membership_system": { "enabled": true },
  "conversation_history": { "enabled": true },
  "lead_tracking": { "enabled": true }
}
```
**Quota Usage**: 4-5 reads per message
**Safe For**: Up to 15 messages/min (with 60 req/min quota)
**Features**: All features enabled

---

### Scenario B: Disable Follow-up (Safer)
```json
{
  "follow_up_system": { "enabled": false },
  "membership_system": { "enabled": true },
  "conversation_history": { "enabled": true },
  "lead_tracking": { "enabled": true }
}
```
**Quota Usage**: 2-3 reads per message
**Safe For**: Up to 30 messages/min (with 60 req/min quota)
**Features**: No auto follow-up, but keep customer tracking
**Savings**: 50% reduction in API calls

---

### Scenario C: Minimal (Most Safe)
```json
{
  "follow_up_system": { "enabled": false },
  "membership_system": { "enabled": false },
  "conversation_history": { "enabled": true },
  "lead_tracking": { "enabled": true }
}
```
**Quota Usage**: 2 reads per message
**Safe For**: Up to 30 messages/min (with 60 req/min quota)
**Features**: Just conversation + lead tracking
**Savings**: 60% reduction in API calls

---

### Scenario D: Google Sheets Disabled (Most Aggressive)
```json
{
  "follow_up_system": { "enabled": false },
  "membership_system": { "enabled": false },
  "conversation_history": { "enabled": false },
  "lead_tracking": { "enabled": false }
}
```
**Quota Usage**: 0 reads per message
**Safe For**: Unlimited message volume
**Features**: No Google Sheets features
**Savings**: 100% reduction in API calls
**Trade-off**: No customer data stored in sheets

---

## How To Apply Changes

1. **Edit the configuration file**
   ```bash
   nano config/config.json
   ```

2. **Find the `google_sheets_features` section**

3. **Change `"enabled": true` to `"enabled": false`** for any features you want to disable

4. **Save the file** (Ctrl+X, Y, Enter in nano)

5. **Restart the service**
   ```bash
   systemctl restart reflexology-agent01
   ```

6. **Check logs to confirm**
   ```bash
   tail -50 logs/app.log | grep -i "feature\|disabled\|enabled"
   ```

---

## Monitoring Impact

After disabling a feature, check your API quota usage:

```bash
# Watch current quota usage
watch -n 5 'tail -20 logs/app.log | grep -i "quota\|api.*read"'

# Or use the quota tracker
python quota_tracker.py
```

You should see:
- ✅ Lower API read counts in logs
- ✅ Quota percentage dropping (if it was high)
- ✅ Fewer "getting..." log messages for disabled features

---

## Questions & Troubleshooting

**Q: Can I disable features temporarily to test?**
A: Yes! Just change the config and restart. No data loss - all sheets remain intact.

**Q: What if I disable a feature and then want to re-enable it?**
A: Just change `"enabled": false` back to `"enabled": true` and restart.

**Q: Will disabling features break anything?**
A: No. Disabled features are simply skipped. The system continues to work normally.

**Q: Which feature should I disable first?**
A: Start with `follow_up_system` if you don't need automated follow-ups. It saves the most quota (2 reads per message).

**Q: Can I disable multiple features at once?**
A: Yes! Disable as many as you don't need. The savings stack up.

---

## Your Current Status

**All features enabled** ✅
- Follow-up System: Enabled
- Membership System: Enabled
- Conversation History: Enabled
- Lead Tracking: Enabled

**Current quota usage**: 4-5 reads per message
**Current safe capacity**: ~15 messages per minute (with 60 req/min quota)
**Safety margin**: 8x (plenty of headroom)

If you're hitting quota errors (429), try disabling `follow_up_system` first for fastest improvement.
