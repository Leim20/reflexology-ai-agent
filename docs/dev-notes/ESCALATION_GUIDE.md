# 📞 Jessica Agent - Escalation Guide

## ✅ What Was Added

### 1. **Real Conversation Examples** (7 examples in prompts)
Jessica now learns from actual Serenity Reflexology chat patterns:
- Quick booking flow
- Price inquiries with bilingual mix
- Therapist requests
- Chinese customer interactions
- Birthday promotion inquiries
- Flexible cancellations
- Late arrival accommodations

### 2. **Human Escalation Capability**
Jessica can now escalate to human contacts when needed!

---

## 📋 How Escalation Works

### **When Jessica Escalates:**
- Customer asks for information NOT in knowledge base
- Special requests requiring manager approval (e.g., group discounts)
- Complaints or service issues
- Complex membership/billing questions
- Customer specifically requests to speak with manager
- Situations requiring human judgment
- Agent cannot make a decision

### **Structured Escalation Format:**

When escalation happens, Jessica provides contact info in this **EXACT format**:

```
---
📞 **HUMAN ASSISTANCE**

**Contact Person:** [Name]
**Role:** [Position/Department]
**Staff ID:** [ID Number]
**Phone:** [Phone Number]
**WhatsApp:** [WhatsApp Number]
**Available:** [Hours/Days]
---

Our team will be happy to assist you with this matter personally😊
```

---

## 👥 Escalation Contact Roles

### **Branch Manager (MGR001)**
- **Handles:** Special requests, complaints, VIP customers, policy questions
- **Example:** Group bookings, special discounts, service complaints

### **Operations Manager (OPS001)**
- **Handles:** System issues, booking problems, service coordination
- **Example:** Technical problems, scheduling conflicts

### **Membership Coordinator (MEM001)**
- **Handles:** Membership questions, birthday promotions, points system
- **Example:** Complex birthday redemption, points inquiries

### **Customer Service Supervisor (CSS001)**
- **Handles:** General inquiries, service feedback, booking assistance
- **Example:** General questions, follow-ups, service feedback

---

## ⚠️ **IMPORTANT: Update Contact Details!**

You need to fill in the actual contact information in the knowledge base file:

**Location:** `data/knowledge_base/catalog.txt`
**Section:** `[ESCALATION_CONTACTS]`

**What to update:**
```
### Branch Manager
Name: [TO BE UPDATED - Add manager name]
WhatsApp: [TO BE UPDATED]

### Operations Manager
Name: [TO BE UPDATED - Add operations manager name]
WhatsApp: [TO BE UPDATED]

### Membership Coordinator
Name: [TO BE UPDATED - Add coordinator name]
WhatsApp: [TO BE UPDATED]

### Customer Service Supervisor
Name: [TO BE UPDATED - Add supervisor name]
WhatsApp: [TO BE UPDATED]
```

Replace the `[TO BE UPDATED]` placeholders with real:
- Names
- WhatsApp numbers
- Any other specific contact details

---

## 💬 Example Escalation Scenarios

### **Scenario 1: Special Group Discount Request**

**Customer:** "Can you give me special discount for group booking of 10 people?"

**Jessica:**
```
Thank you for considering us for your group booking! For special group
rates and discounts, let me connect you with our Branch Manager who can
provide you with the best package.

---
📞 **HUMAN ASSISTANCE**

**Contact Person:** [Manager Name]
**Role:** Branch Manager / 分行经理
**Staff ID:** MGR001
**Phone:** 03-1234 5678
**WhatsApp:** [WhatsApp number]
**Available:** Daily 10am-10pm
---

Our manager will be happy to arrange a special package for your group😊
```

### **Scenario 2: Complaint About Service**

**Customer:** "The massage I received yesterday was not satisfactory"

**Jessica:**
```
I sincerely apologize for your experience. Let me have our Branch Manager
reach out to you personally to resolve this matter.

---
📞 **HUMAN ASSISTANCE**

**Contact Person:** [Manager Name]
**Role:** Branch Manager / 分行经理
**Staff ID:** MGR001
**Phone:** 03-1234 5678
**WhatsApp:** [WhatsApp number]
**Available:** Daily 10am-10pm
---

We take service quality very seriously and will make this right for you😊
```

### **Scenario 3: Unknown Information**

**Customer:** "Do you provide lymphatic drainage massage?"

**Jessica:**
```
We specialize in reflexology (指压) and aromatherapy massage (推拿), but
not lymphatic drainage massage. Let me connect you with our Operations
Manager to discuss alternative treatments that might help.

---
📞 **HUMAN ASSISTANCE**

**Contact Person:** [Operations Manager Name]
**Role:** Operations Manager / 营运经理
**Staff ID:** OPS001
**Phone:** 03-1234 5678
**WhatsApp:** [WhatsApp number]
**Available:** Monday-Friday 10am-6pm
---

They can recommend the best treatment option for your needs😊
```

---

## 📊 Files Modified

| File | Change | Purpose |
|------|--------|---------|
| **catalog.txt** | Added `[ESCALATION_CONTACTS]` section | Contact info for escalation |
| **prompts.yaml** | Added 7 real conversation examples | Improve response patterns |
| **prompts.yaml** | Added escalation logic | When/how to escalate |
| **prompts.yaml** | Added structured format | Consistent escalation format |

---

## 🚀 Next Steps

1. ✅ **Update Contact Information**
   - Open `data/knowledge_base/catalog.txt`
   - Find `[ESCALATION_CONTACTS]` section
   - Replace `[TO BE UPDATED]` with real names and WhatsApp numbers

2. ✅ **Test Escalation**
   - Run the agent: `python -m web.app`
   - Try asking questions that should trigger escalation
   - Example: "Can I get 50% discount for group of 20?"
   - Verify structured format appears correctly

3. ✅ **Train Staff**
   - Inform managers they may receive escalation contacts
   - Ensure they know how to handle escalated customers
   - Set up notification system for escalated cases

---

## 📝 Benefits of This Setup

**✅ Consistent Format:** Every escalation follows same structured format
**✅ Clear Roles:** Customers know who they're contacting and why
**✅ Professional:** Maintains Serenity Reflexology's professional image
**✅ Trackable:** Staff IDs make it easy to track escalations
**✅ Flexible:** Easy to add/update contact persons
**✅ Bilingual:** Role titles in English and Chinese

---

## 🔧 Customization

You can customize the escalation system by:
- Adding more contact roles (e.g., Technical Support)
- Changing availability hours
- Updating phone numbers
- Adding email addresses
- Modifying the structured format template

All changes should be made in:
**`data/knowledge_base/catalog.txt`** → `[ESCALATION_CONTACTS]` section

---

**Last Updated:** 2025-11-06
**Agent Version:** 1.0 with Escalation Capability
**Status:** ✅ Escalation System Active - Update Contact Details Required
