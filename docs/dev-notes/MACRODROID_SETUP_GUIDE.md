# MacroDroid Setup Guide - Outbound Lead Tracking

This guide explains how to configure MacroDroid to automatically track leads when you send WhatsApp messages to callers.

---

## 📋 Overview

**What this does:**
1. Customer calls your business phone
2. MacroDroid detects the call and gets caller's number
3. MacroDroid sends a prefilled WhatsApp message to the caller
4. **NEW:** MacroDroid notifies your chat agent system
5. Lead is recorded in Google Sheets immediately (even if customer doesn't respond)

---

## 🔧 MacroDroid Configuration

### Step 1: Create a New Macro

1. Open MacroDroid app
2. Tap the **+** button to create a new macro
3. Name it: **"Call to WhatsApp Lead Tracker"**

---

### Step 2: Add Trigger - Incoming Call

1. Tap **Add Trigger**
2. Select **Phone → Incoming Call**
3. Configure:
   - **Call Type:** Any / All Calls
   - **Contact:** Any Contact (to capture all callers)
4. Tap **OK**

---

### Step 3: Add Action 1 - Extract Caller Information

1. Tap **Add Action**
2. Select **Variables → Set Variable**
3. Create these variables:

**Variable 1: caller_number**
- Type: String
- Value: `{clnum}` (MacroDroid magic text for caller number)

**Variable 2: caller_name**
- Type: String
- Value: `{clname}` (MacroDroid magic text for caller name)

**Variable 3: call_time**
- Type: String
- Value: `{datetime}` (MacroDroid magic text for current timestamp)

---

### Step 4: Add Action 2 - Send WhatsApp Message (Whapi)

1. Tap **Add Action**
2. Select **Connectivity → HTTP Request**
3. Configure:

**HTTP Request Settings:**
```
Method: POST
URL: https://gate.whapi.cloud/messages/text
```

**Headers:**
```
Authorization: Bearer YOUR_WHAPI_TOKEN
Content-Type: application/json
```
*(Replace `YOUR_WHAPI_TOKEN` with your actual Whapi API token)*

**Body (JSON):**
```json
{
  "to": "{lv=caller_number}",
  "body": "Thank you for calling! We'll get back to you as soon as possible. In the meantime, feel free to let us know how we can help you today."
}
```

**Timeout:** 10 seconds

**Notes:**
- `{lv=caller_number}` references the variable we created earlier
- Customize the message text to match your business needs
- Make sure the phone number format matches WhatsApp's requirements (e.g., +60123456789)

---

### Step 5: ⭐ Add Action 3 - Notify Chat Agent (NEW)

1. Tap **Add Action**
2. Select **Connectivity → HTTP Request**
3. Configure:

**HTTP Request Settings:**
```
Method: POST
URL: http://YOUR_SERVER_IP:5000/api/track-outbound
```
*(Replace `YOUR_SERVER_IP` with your actual server IP or domain)*

**Examples:**
- Local server: `http://192.168.1.100:5000/api/track-outbound`
- Cloud server: `http://your-domain.com/api/track-outbound`
- Ngrok tunnel: `http://abc123.ngrok.io/api/track-outbound`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "phone": "{lv=caller_number}",
  "name": "{lv=caller_name}",
  "call_time": "{lv=call_time}",
  "message": "Thank you for calling! We'll get back to you as soon as possible."
}
```

**Timeout:** 10 seconds

**Store Response in Variable (Optional):**
- Enable this to debug
- Variable name: `api_response`

---

### Step 6: (Optional) Add Notification for Debugging

1. Tap **Add Action**
2. Select **Notifications → Notify**
3. Configure:

**Title:** Lead Tracked
**Text:**
```
Caller: {lv=caller_name}
Number: {lv=caller_number}
Response: {lv=api_response}
```

This will show a notification confirming the lead was tracked.

---

### Step 7: Add Constraints (Optional but Recommended)

To prevent the macro from running during off-hours:

1. Tap **Add Constraint**
2. Select **Time/Date → Day of Week**
3. Select: Monday - Friday (or your business days)
4. Tap **OK**

Then add another:

1. Tap **Add Constraint**
2. Select **Time/Date → Time**
3. Set: 9:00 AM - 6:00 PM (or your business hours)
4. Tap **OK**

---

## 📱 Complete Macro Flow

Your final macro should look like this:

```
┌─────────────────────────────────────────┐
│ TRIGGER: Incoming Call                  │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ ACTION 1: Set Variable                  │
│   caller_number = {clnum}               │
│   caller_name = {clname}                │
│   call_time = {datetime}                │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ ACTION 2: HTTP POST → Whapi             │
│   Send WhatsApp message to caller       │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ ACTION 3: HTTP POST → Chat Agent        │
│   Notify system to track lead           │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ ACTION 4: Show Notification (optional)  │
│   Confirm lead was tracked              │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ CONSTRAINTS (optional):                 │
│   - Business days only                  │
│   - Business hours only                 │
└─────────────────────────────────────────┘
```

---

## 🧪 Testing Your Macro

### Test 1: Local Test (without actual call)

1. Open the macro in MacroDroid
2. Tap the **Test Actions** button (play icon)
3. MacroDroid will execute all actions manually
4. Check:
   - Did WhatsApp message send?
   - Did you see the notification?
   - Check Google Sheets - is the lead recorded?

### Test 2: Real Call Test

1. Call your business number from a different phone
2. Hang up after 1-2 rings
3. Check:
   - Did you receive a WhatsApp message?
   - Check MacroDroid logs (Menu → Log)
   - Check your chat agent logs
   - Check Google Sheets for the new lead

---

## 🔍 Troubleshooting

### Issue 1: Whapi Message Not Sending

**Symptoms:** WhatsApp message doesn't arrive

**Solutions:**
- Verify your Whapi API token is correct
- Check Whapi dashboard for API limits/errors
- Ensure phone number format is correct (+60123456789)
- Check MacroDroid logs for HTTP errors

### Issue 2: Lead Not Recorded in Google Sheets

**Symptoms:** Lead doesn't appear in Customer Record sheet

**Solutions:**
- Check server logs: `C:\Users\Hp\Desktop\reflexology-agent\logs\`
- Verify server URL is correct and accessible
- Test endpoint manually using test script:
  ```bash
  python scripts/test_track_outbound.py
  ```
- Ensure lead tracking is enabled in config:
  ```json
  {
    "lead_tracking": {
      "enabled": true
    }
  }
  ```

### Issue 3: HTTP Request Times Out

**Symptoms:** MacroDroid shows "Request timeout"

**Solutions:**
- Increase timeout to 15-20 seconds
- Check server is running: `http://YOUR_SERVER_IP:5000/health`
- Verify firewall allows incoming connections
- If using cloud server, check security group rules

### Issue 4: Wrong Phone Number Format

**Symptoms:** Lead recorded but phone number is malformed

**Solutions:**
- Check MacroDroid's `{clnum}` format
- May need to add country code manually:
  ```json
  "phone": "+60{lv=caller_number}"
  ```
- Or remove leading zeros:
  ```json
  "phone": "+60{lv=caller_number:substring(1)}"
  ```

---

## 📊 What Gets Recorded

When MacroDroid sends the notification, the following lead data is recorded in Google Sheets:

**Customer Record Sheet:**
- **Name:** Caller name from phone contacts (or "Unknown")
- **Phone:** Caller's phone number
- **Interest:** "Phone call - sent auto-response (no reply yet)"
- **Last Visit:** Date of the call
- **Preferences:** (empty initially)
- **Total Conversations:** 0 (until they respond)
- **Last Updated:** Current timestamp

**Status:**
- If customer later responds → Interest updated automatically by AI
- If customer never responds → Remains as "no reply yet" (cold lead)

---

## 🎯 Advanced Configuration

### Custom Message Based on Time

You can customize the WhatsApp message based on time of day:

1. Add **IF** condition before Action 2
2. Check **Time → Current Hour**
3. Use different messages:
   - Morning: "Good morning! Thank you for calling..."
   - Evening: "Thank you for your call! We'll respond tomorrow morning..."

### Multiple Phone Numbers

If you have multiple business lines:

1. Add **IF** condition in trigger
2. Check **Phone → Phone Number**
3. Send different messages for different lines
4. Include line identifier in API payload:
   ```json
   {
     "phone": "{lv=caller_number}",
     "name": "{lv=caller_name}",
     "source": "Main Line"
   }
   ```

### Integration with CRM

You can enhance the payload with more data:

```json
{
  "phone": "{lv=caller_number}",
  "name": "{lv=caller_name}",
  "call_time": "{lv=call_time}",
  "call_duration": "{calldur}",
  "call_type": "Missed",
  "source": "Phone Call",
  "message": "Your prefilled message"
}
```

---

## ✅ Checklist

Before deploying to production:

- [ ] MacroDroid macro created and configured
- [ ] Whapi API token added and tested
- [ ] Server URL configured correctly
- [ ] Test call completed successfully
- [ ] Lead appears in Google Sheets
- [ ] Constraints added (business hours)
- [ ] Notification added for debugging
- [ ] Logs checked for errors
- [ ] Documentation updated with your specific settings

---

## 📞 Support

If you encounter issues:

1. Check MacroDroid logs: Menu → Log
2. Check server logs: `reflexology-agent/logs/`
3. Run test script: `python scripts/test_track_outbound.py`
4. Test endpoint manually with curl:
   ```bash
   curl -X POST http://localhost:5000/api/track-outbound \
     -H "Content-Type: application/json" \
     -d '{"phone":"+60123456789","name":"Test User"}'
   ```

---

## 🎉 You're Done!

Your system will now automatically track all callers who receive your WhatsApp auto-response, even if they never reply. No more lost leads! 🚀
