# 🚨 Automatic Escalation System

## Overview

The escalation system automatically forwards customer messages to managers via WhatsApp when issues require human intervention. This is a **complete upgrade** from showing contact details to **actually sending messages** to managers.

---

## ✅ What Was Implemented

### **Files Created:**
1. **`handlers/tools/escalation.py`** - Complete escalation tool (393 lines)
2. **`test_escalation.py`** - Test script for escalation system

### **Files Modified:**
1. **`handlers/tools/__init__.py`** - Added escalation imports
2. **`config/config.json`** - Added escalation configuration section
3. **`config/prompts.yaml`** - Updated escalation instructions (web + WhatsApp)
4. **`web/app.py`** - Integrated escalation tool initialization

---

## 🔄 How It Works

### **Old System (❌):**
```
Customer: "Can I get discount for 20 people?"
Jessica: "Contact our manager at 60120000000"
Customer: [Has to manually call]
Manager: [Doesn't know about this]
```

### **New System (✅):**
```
Customer: "Can I get discount for 20 people?"

[Jessica detects escalation needed]
Jessica: "I'll forward this to our Branch Manager. They'll contact you shortly😊"

[System automatically sends to manager's WhatsApp]:
🚨 ESCALATION ALERT 🚨

Customer Information:
- Name: John Tan
- Phone: 60123456789
- Platform: WhatsApp
- Date & Time: 2025-11-07 15:30:45

Escalation Reason:
Special discount request - group booking (20 people)

Customer's Message:
"Can I get discount for 20 people?"

---
Please contact the customer at the above number.
Jessica Agent - Serenity Reflexology

[Manager receives message on WhatsApp]
[Manager contacts customer directly]
```

---

## 🛠️ Technical Implementation

### **1. Escalation Tool Class** (`handlers/tools/escalation.py`)

**Key Functions:**

```python
class EscalationTool:
    def escalate_to_human(...)
        # Main function - sends escalation to manager

    def format_escalation_message(...)
        # Formats message in standardized template

    def get_escalation_contact(...)
        # Routes to correct manager based on type

    def log_escalation(...)
        # Logs escalation for tracking
```

**Escalation Types & Routing:**
- `complaint`, `special_request`, `vip_customer` → Branch Manager
- `system_issue`, `booking_problem` → Operations Manager
- `membership`, `birthday_promotion` → Membership Coordinator
- `general` → Customer Service Supervisor

### **2. Configuration** (`config/config.json`)

```json
{
  "escalation": {
    "enabled": true,
    "log_escalations": true,
    "log_file": "logs/escalations.log",
    "contacts": {
      "branch_manager": {
        "name": "Wei Jun",
        "phone": "60120000000",
        "role": "Branch Manager / 分行经理",
        "handles": ["complaints", "special_requests", ...]
      },
      ...
    }
  }
}
```

### **3. Prompt Updates** (`config/prompts.yaml`)

**New Instructions:**
- Tell customers "I'll forward this to [role]"
- Manager will contact customer (not the other way around)
- System auto-forwards in background
- Do NOT provide manual contact details

**Example Response:**
```yaml
Customer: "Can I get discount for 20 people?"
You: "Thank you for considering us for your group booking! I'll forward your request to our Branch Manager right away. They will contact you shortly to discuss special group rates😊"
```

---

## 🔧 Technologies Used

### **No New External Tech Required! ✅**

**Existing Infrastructure:**
- **Whapi API** - Already in use for receiving messages, now also sends to managers
- **Python standard library** - datetime, logging, json (already installed)
- **Flask** - Already running web server
- **Existing handlers** - WhatsApp handler already available

**What's New:**
- **Logic flow** - Automatic forwarding
- **Code organization** - New tool in `handlers/tools/`
- **Message formatting** - Standardized escalation template
- **Contact routing** - Smart manager selection

---

## 📋 Escalation Message Format

```
🚨 ESCALATION ALERT 🚨

Customer Information:
- Name: [Customer Name]
- Phone: [Customer Phone - with country code]
- Platform: [WHATSAPP / WEB]
- Date & Time: [2025-11-07 15:30:45]

Escalation Reason:
[Specific reason why escalation is needed]

Customer's Message:
"[Original message from customer]"

---
Please contact the customer at the above number.

Jessica Agent - Serenity Reflexology
```

---

## 🧪 Testing

### **Test Script:** `test_escalation.py`

**Features:**
- Tests 3 scenarios (discount request, complaint, membership question)
- Dry-run mode (shows what would be sent without sending)
- Real send mode (actually sends to WhatsApp)
- Displays formatted messages
- Shows contact routing

**Run Test:**
```bash
# Dry run (no messages sent)
python test_escalation.py
# Choose "no" when prompted

# Real test (sends actual WhatsApp messages)
python test_escalation.py
# Choose "yes" when prompted - WARNING: Sends real messages!
```

**Test Scenarios Included:**
1. **Special Discount Request** → Branch Manager
2. **Service Complaint** → Branch Manager
3. **Membership Question** → Membership Coordinator

---

## 📊 When Escalation Triggers

**Automatic escalation happens when:**
- Customer asks for information NOT in knowledge base
- Special requests (group discounts, custom packages)
- Complaints or service issues
- Complex membership/billing questions
- Customer specifically requests manager
- Situations requiring human judgment
- Medical/health-related questions

---

## 📁 File Structure

```
reflexology-agent/
├── handlers/
│   └── tools/
│       ├── escalation.py          # ✨ NEW - Escalation tool
│       └── __init__.py             # Updated - Import escalation
│
├── config/
│   ├── config.json                 # Updated - Escalation config
│   └── prompts.yaml                # Updated - Escalation prompts
│
├── web/
│   └── app.py                      # Updated - Initialize escalation tool
│
├── logs/
│   └── escalations.log             # ✨ NEW - Auto-created escalation log
│
└── test_escalation.py              # ✨ NEW - Test script
```

---

## 🚀 Deployment to VPS

### **Files to Transfer:**

```bash
# Transfer new escalation tool
scp handlers/tools/escalation.py contact@example.com:/root/reflexology-agent/handlers/tools/

# Transfer updated files
scp handlers/tools/__init__.py contact@example.com:/root/reflexology-agent/handlers/tools/

scp config/config.json contact@example.com:/root/reflexology-agent/config/

scp config/prompts.yaml contact@example.com:/root/reflexology-agent/config/

scp web/app.py contact@example.com:/root/reflexology-agent/web/

# Transfer test script (optional)
scp test_escalation.py contact@example.com:/root/reflexology-agent/

# SSH and restart
ssh contact@example.com
cd /root/reflexology-agent
systemctl restart reflexology-agent
systemctl status reflexology-agent
```

### **Verify Deployment:**

```bash
# Check logs for escalation tool initialization
journalctl -u reflexology-agent -n 50 --no-pager | grep -i escalation

# Expected output:
# ✓ Escalation Tool initialized

# Test escalation system
python test_escalation.py
```

---

## 📝 Escalation Tracking

### **Log File:** `logs/escalations.log`

**Format:**
```
2025-11-07 15:30:45 | Type: special_request | Customer: John Tan (60123456789) | Reason: Special discount request - group booking (20 people) | Manager: Wei Jun (60120000000) | Platform: whatsapp
```

**Benefits:**
- Track how many escalations occur
- Identify common escalation reasons
- Monitor response patterns
- Audit trail for customer interactions

---

## 🎯 Key Benefits

### **For Customers:**
✅ **Faster response** - Manager notified immediately
✅ **No manual work** - Don't have to call manager themselves
✅ **Professional service** - Seamless handoff
✅ **Clear expectation** - Told "manager will contact you"

### **For Managers:**
✅ **Instant notification** - Receive WhatsApp message immediately
✅ **Complete context** - See customer info + original message
✅ **Prepared response** - Know the issue before calling
✅ **Trackable** - All escalations logged

### **For Business:**
✅ **Higher response rate** - Proactive manager outreach
✅ **Better customer satisfaction** - Faster issue resolution
✅ **Data insights** - Track escalation patterns
✅ **Professional image** - Organized escalation process

---

## 🔐 Important Notes

### **Phone Number Format:**
- Must include country code: `60120000000` (Malaysia)
- No spaces, dashes, or special characters
- Manager's number configured in `config/config.json`

### **Whapi API Requirements:**
- Same API token used for receiving AND sending messages
- No additional API setup needed
- Uses existing Whapi infrastructure

### **Customization:**
- Manager contacts: Update `config/config.json`
- Escalation types: Modify routing in `escalation.py`
- Message template: Edit `format_escalation_message()` function
- Enable/disable: Set `escalation.enabled` in config

---

## 🐛 Troubleshooting

### **Escalation not sending:**
1. Check `config/config.json` - ensure `escalation.enabled: true`
2. Check `.env` - verify `WHAPI_API_TOKEN` is set
3. Check logs: `journalctl -u reflexology-agent | grep -i escalation`
4. Verify phone numbers have country code (60...)

### **Wrong manager receiving escalations:**
- Check escalation type mapping in `escalation.py`
- Verify contact configuration in `config/config.json`
- Review escalation reason being passed

### **Message format issues:**
- Check `format_escalation_message()` in `escalation.py`
- Verify all customer info is being passed correctly
- Test with `test_escalation.py` dry-run mode

---

## 📚 Next Steps

### **Recommended:**
1. **Test the system** using `test_escalation.py` (dry-run first)
2. **Deploy to VPS** following deployment steps above
3. **Inform managers** they'll receive escalation WhatsApp messages
4. **Monitor escalation log** to track patterns
5. **Adjust routing** if needed based on manager feedback

### **Optional Enhancements:**
- Add more escalation types (e.g., "urgent", "vip")
- Create dashboard to view escalations
- Send confirmation to customer after manager contacts them
- Add escalation priority levels
- Integrate with CRM system

---

**Implementation Date:** 2025-11-07
**Status:** ✅ Fully Implemented & Ready for Testing
**Next Action:** Test locally, then deploy to VPS
