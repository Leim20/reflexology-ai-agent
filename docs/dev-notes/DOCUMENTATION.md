# Jessica - Serenity Reflexology AI Agent
## Project Documentation

**Agent Name:** Jessica
**Business:** Serenity Reflexology (Example City Branch)
**Purpose:** WhatsApp & Web chat assistant for bookings, service inquiries, and customer support
**Based On:** Chat Agent Template (duplicated and customized)

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Prompting Strategy](#prompting-strategy)
3. [Knowledge Base Creation](#knowledge-base-creation)
4. [Escalation System](#escalation-system)
5. [VPS Deployment](#vps-deployment)
6. [Testing & Verification](#testing--verification)

---

## 🎯 Project Overview

### What We Built

A bilingual (English + Chinese) AI chat agent that:
- Handles customer bookings for reflexology services
- Answers questions about services, pricing, and membership
- Processes images, voice messages, and documents from customers
- Escalates complex issues to human staff
- Responds ONLY to business-related topics

### Key Differences from Template

| Aspect | Template | Jessica (Reflexology Agent) |
|--------|----------|----------------------------|
| Port | 5000 | 5001 |
| Agent Name | Generic | Jessica |
| Communication Style | Standard English | Bilingual Malaysian (English + Chinese) |
| Knowledge Base | Empty template | Real business data from chat histories |
| Prompts | Generic | Trained from actual customer conversations |
| Escalation | Not included | Structured human escalation system |

---

## 🧠 Prompting Strategy

### Why Chat History Analysis is Critical

**Problem:** Generic AI agents sound robotic and don't match real business communication patterns.

**Solution:** Analyze actual WhatsApp chat histories to extract:
1. **Communication patterns** - How staff really talk to customers
2. **Common phrases** - Natural language used in Malaysian context
3. **Response structure** - How to handle bookings, cancellations, inquiries
4. **Cultural context** - Bilingual mixing, use of "boss/老板", casual tone

### The Prompting Process

#### Step 1: Chat History Analysis
**Input:** 10 folders of WhatsApp chat histories
**What We Extracted:**
- Business information (services, pricing, hours)
- Real conversation patterns (bilingual mixing)
- Common customer questions and staff responses
- Booking flow patterns
- Cancellation/rescheduling approaches
- Therapist request handling

#### Step 2: Identifying Communication Patterns

**Key Patterns Found:**

**Bilingual Mixing (Critical for Malaysian Context):**
```
❌ Bad: "Yes, we have availability at 7pm."
✅ Good: "Got啊, 7pm can boss😊"

❌ Bad: "Your reservation has been confirmed."
✅ Good: "好的 没问题, already booked for you😊"
```

**Short, Casual Responses:**
```
Customer: "Got slot 7pm?"
Staff: "Got😊 how many pax？"
Customer: "2 pax"
Staff: "Foot or body massage？"
```

**Accommodating Tone:**
```
Customer: "Sorry need to cancel"
Staff: "Ok no problem😊 Thank you for informing us!"
```

#### Step 3: Creating Few-Shot Examples

**Why Few-Shot Learning?**
Instead of telling the AI "be casual and bilingual," we show actual examples.

**7 Real Conversation Examples Added:**

1. **Quick Booking Flow** - Shows natural booking progression
2. **Price Inquiry with Bilingual Mix** - Demonstrates price responses
3. **Therapist Request** - How to handle specific therapist bookings
4. **Chinese Customer** - Natural bilingual conversation
5. **Birthday Promotion Inquiry** - Membership benefit explanations
6. **Flexible Cancellation** - Accommodating response pattern
7. **Late Arrival Accommodation** - Flexible scheduling

**Example from prompts.yaml:**
```yaml
## EXAMPLE 1 - Quick Booking Flow
Customer: "Got slot 7pm? 2 pax"
Jessica: "Got😊 foot or body massage？"
Customer: "Body 90min"
Jessica: "Okay, can arrange male or female therapist？"
Customer: "Female pls"
Jessica: "Sure, done for reservation. See u at 7pm😊"
```

#### Step 4: Response Formatting Rules

**Problem Identified:** AI was giving long, dense paragraphs (hard to read in chat).

**Solution Added:**
```yaml
FORMATTING RULES:
1. Use line breaks between different topics
2. Use simple dashes (-) for bullet lists
3. Group related information together
4. Keep each paragraph to 1-2 sentences max
5. Add blank lines between sections
6. When listing prices, times, or options - ALWAYS use bullet format
```

**Before Fix:**
```
Yes, we have member promotions! During your birthday month, you can redeem a FREE 1-hour service on any day. Friends who come with you get a 20% discount. We also have a Happy Hour promotion for members: 120-minute body massage for RM159 (regular RM258) every Tuesday to Thursday from 7:00 PM to 10:00 PM.
```

**After Fix:**
```
Hi boss! Member promotions:

Birthday Month:
- FREE 1 hour massage (any day in birthday month)
- Friends get 20% discount

Happy Hour (Members only):
- Tuesday-Thursday 7-10pm
- 120min body massage: RM159 (normal RM258)

Registration is free! Want to register?😊
```

#### Step 5: File Handling Instructions

**Capabilities Added:**
- **Images:** "Got the photo boss😊" + analyze + respond
- **Voice Messages:** Auto-transcribed, respond naturally
- **Documents:** Acknowledge receipt, read content, respond or escalate

#### Step 6: Business-Only Boundaries

**Problem:** AI might answer random questions (weather, jokes, general knowledge).

**Solution Added:**
```yaml
✅ ACCEPTABLE topics:
- Bookings and appointments
- Service inquiries
- Business hours and location
- Membership and promotions

❌ OFF-TOPIC (redirect):
- Personal chat
- Random questions (weather, news, jokes)
- Spam or dummy messages

Redirect Example:
Customer: "Tell me a joke"
Jessica: "I'm here for Serenity Reflexology services boss😊 Need a massage?"
```

### Final Prompt Structure

**config/prompts.yaml sections:**

1. **Agent Identity** - Who is Jessica, her role
2. **Knowledge Base Integration** - How to use catalog.txt
3. **Real Conversation Examples** (7 examples)
4. **Bilingual Communication Style** - English + Chinese mixing patterns
5. **Response Style** - Short, casual, friendly
6. **Message Formatting** - Line breaks, bullets, structure
7. **File Handling** - Images, voice, documents
8. **Off-Topic Handling** - Business-only boundaries
9. **Price Inquiries** - NEVER mention images, provide TEXT prices
10. **Booking Responses** - Flow and confirmation patterns
11. **Escalation Logic** - When and how to escalate
12. **Service Explanations** - Simple, practical descriptions
13. **Membership Info** - Registration and benefits
14. **Operational Details** - Hours, location, policies
15. **Important Reminders** - Core principles

---

## 📚 Knowledge Base Creation

### Process Overview

**Source:** 10 WhatsApp chat history folders
**Method:** Manual extraction and structuring

### What Was Extracted

#### 1. Business Information
```
[BUSINESS_INFO]
- Business name, phone, hours, location
- Operating hours: Daily 10am-12am
- Last call session: 11:30pm
```

#### 2. Services & Pricing
```
[SERVICES_PRICING]
## FOOT MASSAGE (脚底按摩)
- 45min: RM69
- 45min foot + 15min back: RM89

## BODY MASSAGE (全身按摩 / 推拿)
- 90min: RM159 (includes free cupping/guasha/ear candling/belly candling)
- 120min: RM258 (Members: RM159 on Tue-Thu 7-10pm)
```

#### 3. Therapist System
```
[THERAPIST_SERVICES]
- Customers can request by therapist number (45, 46, 55, 58, etc.)
- Can request male or female therapists
- Track customer preferences
- Record which therapists customers liked/didn't like
```

#### 4. Membership Benefits
```
[MEMBERSHIP_BENEFITS]
Registration: FREE (name, phone, birthday, Facebook like)

Birthday Month Benefits:
- FREE 1 hour service (any day in birthday month)
- Friends get 20% discount

Happy Hour (Tue-Thu 7-10pm):
- 120min body massage: RM159 (normal RM258)
- Members only
```

#### 5. Booking Procedures
```
[BOOKING_PROCEDURES]
- Same-day bookings accepted
- Walk-ins welcome but booking recommended
- Very flexible with cancellations
- Can reschedule anytime
```

#### 6. Common Customer Questions (FAQ)
```
[COMMON_CUSTOMER_QUESTIONS]
50+ real Q&A pairs extracted from chat histories

Example:
Q: Birthday month have promo?
A: Yes! Member benefit: During your birthday month, you can redeem 1 hour FREE service on any day. All friends who come with you also get 20% discount.
```

#### 7. Customer Service Standards
```
[CUSTOMER_SERVICE_STANDARDS]
Communication Style:
- Greetings: "Hi boss / 老板"
- Confirmations: "Done for reservation / 已经帮您预约了"
- Closings: "See u later😊 / 等下见"

Response patterns from real chat histories
```

### Why Chat History is Crucial for Knowledge Base

**Traditional Approach (❌):**
- Use business website copy
- Generic service descriptions
- Formal, robotic language
- No real customer context

**Chat History Approach (✅):**
- **Real questions customers actually ask**
- **Actual language staff use to respond**
- **Cultural and linguistic nuances** (bilingual mixing)
- **Edge cases and exceptions** (late arrivals, cancellations, special requests)
- **Unstated policies** (like "ok no problem" for cancellations)
- **Customer preferences** (therapist requests, couple rooms)

**Example Benefit:**

From website:
> "We offer professional reflexology services."

From chat history:
```
Q: Can request specific therapist?
A: Yes, you can request by therapist number. We'll check if they're available and arrange for you.

Q: Can arrange male/female therapist?
A: Yes, sure. We can arrange according to your preference. Just let us know when booking.
```

The chat history reveals **how** the business actually operates, not just what services exist.

---

## 📞 Escalation System

### Why Escalation is Necessary

**AI Limitations:**
- Cannot make business decisions (special discounts, group rates)
- Cannot resolve complaints
- Cannot access real-time data (specific therapist availability today)
- Should not handle medical consultations

### Escalation Structure

#### When to Escalate

```yaml
ESCALATE when:
- Customer asks for information NOT in knowledge base
- Special requests requiring manager approval (group discounts)
- Complaints or service issues
- Complex membership or billing questions
- Customer specifically requests to speak with manager
- Situations requiring human judgment
```

#### Escalation Contacts

**4 Roles Created with Staff IDs:**

```
Branch Manager (MGR001)
- Handles: Special requests, complaints, VIP customers, policy questions
- Name: Wei Jun
- WhatsApp: 60120000000
- Available: Daily 10am-10pm

Operations Manager (OPS001)
- Handles: System issues, booking problems, service coordination
- Name: Wei Jun
- WhatsApp: 60120000000
- Available: Monday-Friday 10am-6pm

Membership Coordinator (MEM001)
- Handles: Membership questions, birthday promotions, points system
- Name: Wei Jun
- WhatsApp: 60120000000
- Available: Daily 10am-8pm

Customer Service Supervisor (CSS001)
- Handles: General inquiries, service feedback, booking assistance
- Name: Wei Jun
- WhatsApp: 60120000000
- Available: Daily 11am-11pm
```

#### Structured Escalation Format

**Every escalation uses this EXACT format:**

```
---
📞 **HUMAN ASSISTANCE**

**Contact Person:** [Name]
**Role:** [Role] / [中文角色]
**Staff ID:** [ID]
**Phone:** 03-1234 5678
**WhatsApp:** [WhatsApp Number]
**Available:** [Hours]
---

[Contextual message about why they'll help]
```

**Example:**
```
Customer: "Can I get special discount for group of 20 people?"

Jessica:
"Thank you for considering us for your group booking! For special group rates and discounts, let me connect you with our Branch Manager who can provide you with the best package.

---
📞 **HUMAN ASSISTANCE**

**Contact Person:** Wei Jun
**Role:** Branch Manager / 分行经理
**Staff ID:** MGR001
**Phone:** 03-1234 5678
**WhatsApp:** 60120000000
**Available:** Daily 10am-10pm
---

Our manager will be happy to arrange a special package for your group😊"
```

### Benefits of This System

✅ **Professional** - Consistent structured format
✅ **Clear** - Customer knows who to contact and why
✅ **Trackable** - Staff IDs make escalations traceable
✅ **Bilingual** - Role titles in English and Chinese
✅ **Appropriate** - Right person for right issue

---

## 🚀 VPS Deployment

### Server Details

**VPS Provider:** DigitalOcean
**IP Address:** your-domain.com
**OS:** Ubuntu
**Access:** SSH as root

### Step-by-Step Deployment Process

#### Step 1: Transfer Files to VPS

**From local machine:**
```bash
# Navigate to project folder
cd C:\Users\Hp\Desktop

# Create tar archive (easier for large transfer)
tar -czf reflexology-agent.tar.gz reflexology-agent/

# Transfer to VPS
scp reflexology-agent.tar.gz contact@example.com:/root/

# SSH into VPS
ssh contact@example.com

# Extract files
cd /root
tar -xzf reflexology-agent.tar.gz
```

**Alternative (transfer specific files only):**
```bash
# Transfer config files
scp "C:\Users\Hp\Desktop\reflexology-agent\config\prompts.yaml" contact@example.com:/root/reflexology-agent/config/

scp "C:\Users\Hp\Desktop\reflexology-agent\config\config.json" contact@example.com:/root/reflexology-agent/config/

# Transfer knowledge base
scp "C:\Users\Hp\Desktop\reflexology-agent\data\knowledge_base\catalog.txt" contact@example.com:/root/reflexology-agent/data/knowledge_base/
```

#### Step 2: Install Dependencies

**On VPS:**
```bash
# Navigate to project directory
cd /root/reflexology-agent

# Install Python dependencies
pip3 install -r requirements.txt

# Verify installations
pip3 list | grep -E "flask|openai|requests"
```

**Dependencies installed:**
- Flask (web server)
- OpenAI (GPT-4o API)
- Requests (HTTP client)
- PyYAML (config parsing)
- python-dotenv (environment variables)
- PyPDF2, python-docx (document processing)
- Pillow (image processing)

#### Step 3: Open Firewall Port

**Problem:** Port 5001 was blocked by UFW firewall

**Solution:**
```bash
# Check current firewall status
ufw status

# Open port 5001
ufw allow 5001/tcp

# Verify port is open
ufw status | grep 5001

# Expected output:
# 5001/tcp                   ALLOW       Anywhere
# 5001/tcp (v6)              ALLOW       Anywhere (v6)
```

#### Step 4: Create Systemd Service

**Create service file:**
```bash
nano /etc/systemd/system/reflexology-agent.service
```

**Service configuration:**
```ini
[Unit]
Description=Serenity Reflexology Agent - Jessica
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/reflexology-agent
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 -m web.app
Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=reflexology-agent

[Install]
WantedBy=multi-user.target
```

**Why systemd?**
- Auto-starts on server reboot
- Auto-restarts if crashes
- Managed logging via journalctl
- Easy start/stop/status commands

#### Step 5: Enable and Start Service

```bash
# Reload systemd to recognize new service
systemctl daemon-reload

# Enable service (auto-start on boot)
systemctl enable reflexology-agent

# Start service
systemctl start reflexology-agent

# Check status
systemctl status reflexology-agent

# Expected output:
# ● reflexology-agent.service - Serenity Reflexology Agent - Jessica
#    Loaded: loaded (/etc/systemd/system/reflexology-agent.service; enabled)
#    Active: active (running) since...
```

#### Step 6: Verify Deployment

**Check health endpoint:**
```bash
# From VPS
curl http://localhost:5001/health

# Expected JSON response:
# {
#   "status": "healthy",
#   "agent": "Jessica",
#   "role": "reflexology consultant",
#   "knowledge_base_loaded": true
# }
```

**Check from external browser:**
```
http://your-domain.com:5001
```

**View logs:**
```bash
# View last 50 lines of logs
journalctl -u reflexology-agent -n 50 --no-pager

# Follow logs in real-time
journalctl -u reflexology-agent -f

# View only errors
journalctl -u reflexology-agent -p err -n 50
```

#### Step 7: Configure WhatsApp Webhook

**Whapi Dashboard Settings:**
```
Webhook URL: https://your-domain.com
```

**Test webhook:**
```bash
# View incoming webhook logs
journalctl -u reflexology-agent -f | grep "webhook"

# Send test message from WhatsApp
# Check logs for incoming data
```

### Common VPS Commands

```bash
# Restart service after config changes
systemctl restart reflexology-agent

# Stop service
systemctl stop reflexology-agent

# Check service status
systemctl status reflexology-agent

# View recent logs
journalctl -u reflexology-agent -n 100 --no-pager

# Check if port is listening
netstat -tlnp | grep 5001

# Check running processes
ps aux | grep python

# Monitor resource usage
htop
```

### Troubleshooting

**Service won't start:**
```bash
# Check detailed error logs
journalctl -u reflexology-agent -n 100 --no-pager

# Test manually to see errors
cd /root/reflexology-agent
python3 -m web.app
```

**Port issues:**
```bash
# Check if port is already in use
lsof -i :5001

# Check firewall
ufw status | grep 5001
```

**Dependency issues:**
```bash
# Reinstall dependencies
pip3 install -r requirements.txt --force-reinstall

# Check Python version
python3 --version
```

---

## ✅ Testing & Verification

### Test Categories

#### 1. Knowledge Base Tests
- Service pricing inquiries
- Operating hours questions
- Membership benefits
- Therapist availability
- Add-on treatments (cupping, guasha)

#### 2. Persona Tests
- Bilingual communication (English + Chinese)
- Casual Malaysian tone
- Use of "boss/老板"
- Short message style
- Emoji usage

#### 3. Escalation Tests
- Special discount requests → Branch Manager
- Complaints → Branch Manager
- Unknown information → Appropriate contact
- Medical questions → Manager

#### 4. File Handling Tests
- Send image (receipt, menu, location)
- Send voice message (booking request)
- Send document (PDF, form)

#### 5. Boundary Tests
- Off-topic questions (weather, jokes) → Redirect
- Spam messages → Polite redirect
- Non-business chat → Business-only response

#### 6. Formatting Tests
- Price list responses (should use bullets)
- Long information (should use line breaks)
- Member promotions (structured format)

### Sample Test Questions

```
1. "How much for foot massage?"
   Expected: Text prices with bullets, no image mention

2. "Got any member promotion?"
   Expected: Structured response with line breaks, Birthday + Happy Hour details

3. "Tell me a joke"
   Expected: Redirect to business topics

4. "Can I get 50% discount for group of 20?"
   Expected: Escalation to Branch Manager with contact details

5. "今天有开吗?" (Are you open today?)
   Expected: Bilingual response with hours

6. [Send voice message: "I want to book massage"]
   Expected: Acknowledge voice message, ask for details

7. "What's the weather like?"
   Expected: Polite redirect to business services
```

---

## 📝 Summary

### What Makes This Agent Effective

1. **Real Conversation Training** - Based on actual chat histories, not generic templates
2. **Cultural Authenticity** - Natural bilingual Malaysian communication style
3. **Structured Knowledge** - Comprehensive business data from real customer interactions
4. **Smart Boundaries** - Business-only focus with polite redirects
5. **Human Escalation** - Seamless handoff to staff when needed
6. **Professional Formatting** - Easy-to-read responses with bullets and line breaks

### Key Files

```
reflexology-agent/
├── config/
│   ├── config.json          # Agent settings (port 5001, GPT-4o)
│   ├── prompts.yaml         # MOST IMPORTANT - All prompting logic
│   └── .env                 # API keys, webhook URL
│
├── data/knowledge_base/
│   └── catalog.txt          # All business information
│
└── web/
    └── app.py               # Flask application (runs on VPS)
```

### Maintenance

**Updating Prompts:**
```bash
# Edit locally
nano config/prompts.yaml

# Transfer to VPS
scp config/prompts.yaml contact@example.com:/root/reflexology-agent/config/

# Restart service
ssh contact@example.com
systemctl restart reflexology-agent
```

**Updating Knowledge Base:**
```bash
# Edit locally
nano data/knowledge_base/catalog.txt

# Transfer to VPS
scp data/knowledge_base/catalog.txt contact@example.com:/root/reflexology-agent/data/knowledge_base/

# Restart service
ssh contact@example.com
systemctl restart reflexology-agent
```

---

**Documentation Version:** 1.0
**Last Updated:** 2025-11-07
**Agent Status:** ✅ Deployed and Running on VPS
