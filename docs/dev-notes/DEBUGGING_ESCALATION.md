# 🔍 Escalation System Debug Logging Guide

## Overview
Comprehensive logging has been added to track every step of the escalation process to help identify and solve any issues.

---

## Log Locations

### **VPS Logs:**
```bash
# View live logs
journalctl -u reflexology-agent -f

# View recent logs
journalctl -u reflexology-agent -n 100

# Search for escalation events
journalctl -u reflexology-agent | grep -i escalation

# Search for specific customer
journalctl -u reflexology-agent | grep "60123456789"
```

### **Log Files:**
- Main logs: `logs/app.log`
- Escalation tracking: `logs/escalations.log`
- Error logs: `logs/error.log`

---

## What the Logs Show

### **1. WhatsApp Webhook Data Extraction**

When a customer sends a message, you'll see:

```
📋 EXTRACTED WEBHOOK DATA:
   from: 60123456789
   from_name: 'John Tan' (empty=False)
   message_id: p.w30M7fgwWD4XwHu
   type: text
   message preview: Can I get discount for 25 people?...
```

**Look for:**
- ✅ `from_name` has a value → Customer name will be included
- ❌ `from_name: ''` (empty=True) → Customer name will default to phone number

---

### **2. Escalation Detection Trigger**

When AI decides to escalate, you'll see:

```
================================================================================
🚨 ESCALATION DETECTED IN WHATSAPP AI RESPONSE!
================================================================================

📋 ESCALATION TRIGGER DATA:
   Message ID: p.w30M7fgwWD4XwHu
   Escalation ID: whatsapp_60123456789_p.w30M7fgwWD4XwHu
   Already escalated count: 3
```

**Look for:**
- Message ID → Unique ID for this specific message
- Escalation ID → Combined ID to prevent duplicates
- Already escalated count → How many escalations have been sent today

---

### **3. Duplicate Check**

**If duplicate:**
```
⏭️ DUPLICATE ESCALATION DETECTED - SKIPPING
   Message ID: p.w30M7fgwWD4XwHu
   This message was already escalated
================================================================================
```

**If new escalation:**
```
✓ New escalation - proceeding...

👤 CUSTOMER INFO EXTRACTED:
   Sender (phone): 60123456789
   from_name field: 'John Tan'
   Final customer_name: 'John Tan'
   Final customer_phone: '60123456789'
   User message: 'Can I get discount for 25 people?...'
   User message length: 42 chars
```

**Look for:**
- `from_name field` → What was in the webhook
- `Final customer_name` → What will be sent to manager
- `User message` → MUST match what customer typed (not AI response!)

---

### **4. Escalation Type Determination**

```
🎯 ESCALATION TYPE DETERMINED: special_request
   AI response contains: ["i'll forward", 'branch manager']
```

**Escalation types and routing:**
- `special_request` / `complaint` / `vip_customer` → Branch Manager
- `system_issue` / `booking_problem` → Operations Manager
- `membership` → Membership Coordinator
- `general` → Customer Service Supervisor

---

### **5. Escalation Tool Execution**

```
================================================================================
🚨 ESCALATING TO HUMAN
================================================================================
📋 ESCALATION DETAILS:
   Customer Name: 'John Tan' (length: 8 chars)
   Customer Phone: '60123456789'
   Escalation Type: 'special_request'
   Platform: 'whatsapp'
   Reason: 'WhatsApp inquiry - Can I get discount for 25 people?'
   Customer Message Preview: 'Can I get discount for 25 people?...'
   Customer Message Length: 42 chars

🔍 Finding manager for escalation type: 'special_request'
✓ Manager found: Alex (Branch Manager / 分行经理)
   Manager Phone: 60120000000

📝 Formatting escalation message...
   Formatted message length: 356 chars

📤 Sending escalation to manager: 60120000000
```

**Look for:**
- Customer Name length → If 0, it's empty
- Customer Message → MUST match customer's actual message
- Manager Phone → Verify correct manager receiving it

---

### **6. Sending Result**

**If successful:**
```
✅ ESCALATION SENT SUCCESSFULLY!
   To: Alex (Branch Manager / 分行经理)
   Phone: 60120000000
   Message ID: wamid.HBgLNjAxMjM0NTY3ODkVAgARGBI5MTE4QzM4...
   From Customer: John Tan (60123456789)
   Platform: whatsapp
📄 Logging escalation to file: logs/escalations.log
================================================================================
```

**If failed:**
```
❌ FAILED TO SEND ESCALATION MESSAGE!
   Error: Failed to send message via WhatsApp
   Details: {'success': False, 'error': 'Invalid phone number format'}
================================================================================
```

---

### **7. Web App Confirmation**

```
✅ WHATSAPP ESCALATION SUCCESSFUL!
   Sent to: Alex
   Timestamp: 2025-11-07T14:30:45.123456
   Added to escalated_messages set (total: 4)
================================================================================
```

---

## Common Issues and What to Look For

### **Issue 1: Empty Customer Name**

**Logs show:**
```
from_name: '' (empty=True)
Final customer_name: '60123456789'
Customer Name: '60123456789' (length: 11 chars)
```

**Cause:** Customer hasn't set WhatsApp display name
**Solution:** This is normal, falls back to phone number

---

### **Issue 2: Wrong Customer Message**

**Logs show:**
```
User message: 'Wow, that's a big group! I'll forward this to...'
Customer Message Preview: 'Wow, that's a big group! I'll forward this...'
```

**Cause:** AI response being sent instead of customer's original message
**Solution:** Check that `user_message` variable contains customer's message, not AI's

---

### **Issue 3: Spam/Duplicate Escalations**

**Logs show:**
```
Already escalated count: 15
⏭️ DUPLICATE ESCALATION DETECTED - SKIPPING
```

**Cause:** Deduplication working correctly
**Solution:** This is expected behavior, duplicates are being prevented

---

### **Issue 4: Escalation Tool Not Available**

**Logs show:**
```
⚠️ Escalation tool not available for WhatsApp!
   Check if escalation_tool was initialized properly
```

**Cause:** Escalation tool failed to initialize
**Solution:** Check earlier logs for initialization errors:
```bash
journalctl -u reflexology-agent | grep "Escalation Tool"
```

Should see: `✓ Escalation Tool initialized`

---

### **Issue 5: Wrong Manager Receiving**

**Logs show:**
```
🎯 ESCALATION TYPE DETERMINED: general
✓ Manager found: Customer Service Supervisor
```

**Cause:** AI response doesn't mention specific role (branch manager, etc.)
**Solution:** Check AI prompt keywords:
- "branch manager" → special_request
- "operations manager" → system_issue
- "membership coordinator" → membership

---

## Step-by-Step Debugging Process

### **When an escalation fails:**

1. **Check webhook extraction:**
   ```bash
   journalctl -u reflexology-agent | grep "EXTRACTED WEBHOOK DATA" -A 5
   ```
   Verify `from` and `from_name` are present

2. **Check escalation detection:**
   ```bash
   journalctl -u reflexology-agent | grep "ESCALATION DETECTED" -A 20
   ```
   Verify customer info was extracted correctly

3. **Check customer message:**
   ```bash
   journalctl -u reflexology-agent | grep "Customer Message Preview"
   ```
   Must show customer's original text, not AI's response

4. **Check sending result:**
   ```bash
   journalctl -u reflexology-agent | grep "ESCALATION SENT"
   ```
   Look for success/failure message

5. **Check escalation log file:**
   ```bash
   tail -f logs/escalations.log
   ```
   See tracking of all escalations

---

## Log Level Configuration

Current log level: **DEBUG** (set in `config/config.json`)

```json
{
  "logging": {
    "level": "DEBUG",  // Shows all detailed logs
    "log_dir": "logs",
    "enable_console": true,
    "enable_file": true
  }
}
```

**Log levels:**
- DEBUG → Everything (very detailed)
- INFO → Normal operations
- WARNING → Potential issues
- ERROR → Failures

---

## Quick Debug Commands

```bash
# Watch live escalations
journalctl -u reflexology-agent -f | grep -i "escalat"

# See today's escalations
grep "$(date +%Y-%m-%d)" logs/escalations.log

# Count escalations today
grep "$(date +%Y-%m-%d)" logs/escalations.log | wc -l

# Find specific customer's escalations
grep "60123456789" logs/escalations.log

# Check for errors in last hour
journalctl -u reflexology-agent --since "1 hour ago" | grep -i error

# See escalation tool initialization
journalctl -u reflexology-agent --since today | grep "Escalation Tool"
```

---

## Escalation Log File Format

`logs/escalations.log` contains one line per escalation:

```
2025-11-07 14:30:45 | Type: special_request | Customer: John Tan (60123456789) | Reason: WhatsApp inquiry - Can I get discount for 25 people? | Manager: Alex (60120000000) | Platform: whatsapp
```

**Fields:**
- Timestamp
- Escalation Type
- Customer Name (Phone)
- Reason
- Manager Name (Phone)
- Platform

---

## Next Steps

1. Deploy updated files to VPS
2. Restart service: `systemctl restart reflexology-agent`
3. Test with a real WhatsApp message
4. Watch logs: `journalctl -u reflexology-agent -f`
5. Verify escalation received by manager
6. Check `logs/escalations.log` for tracking entry

---

**Updated:** 2025-11-07
**Status:** ✅ Debug logging implemented
