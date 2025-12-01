# DEPLOYMENT INSTRUCTIONS - 20-Conversation Memory System

## Files to Upload to VPS

### NEW FILES:
1. `handlers/tools/lead_manager.py` - Lead manager module with memory system
2. `config/<PUT_YOUR_GOOGLE_PROJECT_ID_HERE>-c123857bd130.json` - Google credentials

### MODIFIED FILES:
1. `config/config.json` - Added lead_tracking & memory configuration
2. `web/app.py` - Integrated memory system into WhatsApp webhook

---

## Deployment Steps

### Step 1: Install Dependencies on VPS

SSH into your VPS:
```bash
ssh contact@example.com
```

Navigate to project directory:
```bash
cd /root/reflexology-agent
```

Install required libraries:
```bash
pip install gspread google-auth
```

### Step 2: Upload Files via WinSCP

**Option A: Upload NEW files**
1. Open WinSCP
2. Connect to: your-domain.com
3. Navigate to: /root/reflexology-agent/
4. Upload these files:

   - **NEW**: `handlers/tools/lead_manager.py`
     - Local: `C:\Users\Hp\Desktop\reflexology-agent\handlers\tools\lead_manager.py`
     - Remote: `/root/reflexology-agent/handlers/tools/lead_manager.py`

   - **NEW**: `config/<PUT_YOUR_GOOGLE_PROJECT_ID_HERE>-c123857bd130.json`
     - Local: `C:\Users\Hp\Desktop\reflexology-agent\config\<PUT_YOUR_GOOGLE_PROJECT_ID_HERE>-c123857bd130.json`
     - Remote: `/root/reflexology-agent/config/<PUT_YOUR_GOOGLE_PROJECT_ID_HERE>-c123857bd130.json`

   - **MODIFIED**: `config/config.json`
     - Local: `C:\Users\Hp\Desktop\reflexology-agent\config\config.json`
     - Remote: `/root/reflexology-agent/config/config.json`

   - **MODIFIED**: `web/app.py`
     - Local: `C:\Users\Hp\Desktop\reflexology-agent\web\app.py`
     - Remote: `/root/reflexology-agent/web/app.py`

### Step 3: Restart Service

SSH into VPS:
```bash
ssh contact@example.com
```

Restart the reflexology agent service:
```bash
systemctl restart reflexology-agent
```

Check service status:
```bash
systemctl status reflexology-agent
```

Expected output:
```
● reflexology-agent.service - Serenity Reflexology WhatsApp Agent
   Loaded: loaded
   Active: active (running)
```

### Step 4: Check Logs for Memory System Initialization

View recent logs:
```bash
journalctl -u reflexology-agent -n 50 --no-pager
```

Look for these lines:
```
✓ Lead Manager initialized
   Spreadsheet: YOUR_GOOGLE_SHEET_ID
   Customer Sheet: Customer Record
   History Sheet: Conversation History
   Column Mapping: Name→A, Phone→B, Interest→C, LastVisit→D, Preferences→E, TotalConvs→F, LastUpdated→G
```

If you see errors, check:
```bash
journalctl -u reflexology-agent -n 100 | grep -i error
```

### Step 5: Test with Real WhatsApp Messages

Send test messages from WhatsApp to your bot:

**Test Scenario 1: Simple Inquiry (Should NOT record - less than 3 messages)**
```
You: "Hi"
Bot: "Hi boss! How can I help?"
```
→ Check logs: Should see "Skipping lead recording - only 2 messages"

**Test Scenario 2: Full Conversation - NEW CUSTOMER (SHOULD record - 3+ messages)**
```
You: "Hi"
Bot: "Hi boss! How can I help?"
You: "What's your price for foot massage?"
Bot: [Provides pricing]
You: "Ok thanks"
Bot: [Responds]
```
→ Check logs: Should see "🆕 New customer - no previous memory found"
→ Check logs: Should see "📊 AUTOMATIC LEAD TRACKING & MEMORY UPDATE"
→ Check Google Sheet "Customer Record": Should see your phone number and data in new row
→ Check Google Sheet "Conversation History": Should see conversation summary saved

**Test Scenario 3: Returning Customer (Should RECOGNIZE and UPDATE memory)**
```
(Send messages again from same number - NEXT DAY)
You: "Hi, I want to book body massage"
Bot: [Should say "Welcome back!" and reference previous interest]
```
→ Check logs: Should see "💭 RETURNING CUSTOMER DETECTED"
→ Check logs: Should see customer memory (Total Conversations, Last Visit, etc.)
→ Check logs: Should see "Memory context added"
→ Bot should acknowledge you as returning customer
→ Check Google Sheet "Customer Record": Should UPDATE existing row (Total Conversations incremented)
→ Check Google Sheet "Conversation History": Should add NEW row for this conversation

**Test Scenario 4: Multiple Conversations (Memory builds up)**
```
(Continue chatting over several days)
Day 1: Ask about foot massage
Day 2: Ask about body massage
Day 3: Ask about therapist preference
Day 4: Book appointment
```
→ Each conversation should be saved to "Conversation History" sheet
→ Bot should show better personalization over time
→ "Customer Record" sheet shows total conversation count increasing
→ Preferences field should auto-populate based on conversations

### Step 6: Monitor Logs During Testing

Open a second terminal and watch logs in real-time:
```bash
ssh contact@example.com
journalctl -u reflexology-agent -f
```

This will show live logs as customers message the bot.

---

## Verification Checklist

After deployment, verify:

- [ ] Service is running: `systemctl status reflexology-agent`
- [ ] No errors in logs: `journalctl -u reflexology-agent -n 100 | grep -i error`
- [ ] Lead Manager initialized with both sheets in logs
- [ ] Test WhatsApp message received response
- [ ] After 3+ messages, lead recorded in "Customer Record" sheet
- [ ] Conversation summary saved in "Conversation History" sheet
- [ ] Data in correct columns (Customer Record: Name→A, Phone→B, Interest→C, LastVisit→D, Preferences→E, TotalConvs→F, LastUpdated→G)
- [ ] Returning customer shows "RETURNING CUSTOMER DETECTED" in logs
- [ ] Memory context injected into AI prompt
- [ ] Duplicate phone number updates existing row (doesn't create new)
- [ ] Conversation count increments with each conversation
- [ ] Preferences auto-populate from conversations

---

## Troubleshooting

### Issue: "Spreadsheet not found"
- Check that Google Drive API is enabled
- Verify sheet is shared with: <PUT_YOUR_GOOGLE_CLIENT_EMAIL_HERE>

### Issue: "402 Payment Required" (Whapi)
- Add credits to Whapi Cloud account
- Not a code issue - billing issue

### Issue: "Module not found: gspread"
- Run: `pip install gspread google-auth` on VPS

### Issue: Lead not recording
- Check logs for minimum message count: needs 3+ messages
- Verify lead_tracking.enabled is true in config.json
- Check for errors in logs

---

## Expected Log Output (Success)

### NEW CUSTOMER (First Time)
```
🆕 New customer - no previous memory found
================================================================================
📊 AUTOMATIC LEAD TRACKING & MEMORY UPDATE
================================================================================
Customer: John Doe (60123456789)
Using AI to analyze conversation...
AI categorized interest as: Booking - body massage 90min
Recording lead with interest: Booking - body massage 90min
✅ Lead created successfully (Row 3)
   Name: John Doe
   Phone: 60123456789
   Interest: Booking - body massage 90min
Updating customer memory...
Summary: Customer inquired about 90-minute body massage and wanted to book for weekend
✅ Conversation saved to history sheet
Extracting customer preferences...
Preferences found: 90min body massage, weekend slots
✅ Preferences updated in Customer Record
✅ Conversation count updated: 1
================================================================================
```

### RETURNING CUSTOMER (Second Time)
```
Checking for customer memory...
================================================================================
💭 RETURNING CUSTOMER DETECTED
================================================================================
Name: John Doe
Total Conversations: 1
Last Visit: 2025-11-09
Current Interest: Booking - body massage 90min
Preferences: 90min body massage, weekend slots
Conversation History: 1 records
================================================================================
Injecting customer memory into AI context...
Memory context added (450 chars)
[AI generates personalized response: "Welcome back, John! I see you were interested in 90-minute body massage..."]
✅ WhatsApp message sent successfully
================================================================================
📊 AUTOMATIC LEAD TRACKING & MEMORY UPDATE
================================================================================
Customer: John Doe (60123456789)
✅ Lead updated successfully (Row 3)
Updating customer memory...
Summary: Customer confirmed booking for body massage on Saturday
✅ Conversation saved to history sheet
✅ Conversation count updated: 2
================================================================================
```

---

## Memory System Configuration

The memory system is fully configurable via `config.json`:

```json
"memory": {
  "enabled": true,
  "max_conversations_stored": 20,
  "max_conversations_retrieved": 20,
  "save_conversation_summary": true,
  "extract_preferences": true,
  "tiered_detail": {
    "recent_detailed": 3,      // Most recent 3 conversations: Full detail
    "medium_detail": 10,        // Conversations 4-10: Medium detail
    "brief_mention": 20         // Conversations 11-20: Brief mention
  }
}
```

**Configuration Options:**
- `enabled`: Enable/disable entire memory system
- `max_conversations_stored`: Max conversations to keep in history (default: 20)
- `max_conversations_retrieved`: Max to retrieve for memory context (default: 20)
- `save_conversation_summary`: Auto-save conversation summaries (default: true)
- `extract_preferences`: Auto-extract customer preferences (default: true)
- `tiered_detail`: Configure memory detail levels for token optimization

---

## Post-Deployment

After successful deployment:
1. Delete test rows from both Google Sheets (if not already deleted)
2. Monitor logs for 24 hours to see memory system in action
3. Check both sheets daily:
   - "Customer Record" sheet for customer summary data
   - "Conversation History" sheet for detailed conversation logs
4. Use data for follow-up, personalization, and marketing
5. Observe AI responses becoming more personalized over time

---

## Rollback (If Needed)

If something goes wrong, you can disable the memory system without removing code:

Edit config.json on VPS:
```bash
nano /root/reflexology-agent/config/config.json
```

**Option 1: Disable memory only (keep lead tracking)**
```json
"memory": {
  "enabled": false,  // ← Change to false
}
```

**Option 2: Disable everything (lead tracking + memory)**
```json
"lead_tracking": {
  "enabled": false,  // ← Change to false
}
```

Then restart:
```bash
systemctl restart reflexology-agent
```
