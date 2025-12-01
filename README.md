# 💆‍♀️ Jessica - Reflexology Chat Agent

**An AI-powered reflexology consultant providing expert guidance via WhatsApp and Web**

Version: 1.0
Created: 2025-11-06
Agent Name: Jessica
Specialty: Reflexology & Wellness

---

## 📋 Overview

Jessica is a friendly and professional reflexology consultant AI agent that helps customers understand reflexology treatments, benefits, techniques, and wellness guidance. Built on a modular chat agent template, Jessica provides accurate FAQ responses based on a comprehensive knowledge base.

**Key Capabilities:**
- ✅ Answer reflexology FAQs with accurate, helpful information
- ✅ Explain treatment benefits, techniques, and what to expect
- ✅ Provide pricing and booking information
- ✅ Process customer inquiries via WhatsApp and Web chat
- ✅ Handle file uploads (documents, images, voice messages)
- ✅ Multi-language support (English, Bahasa Melayu, Chinese)
- ✅ Maintain conversation history for personalized responses

---

## 🎯 What Jessica Does

### **Reflexology Guidance**
- Explains what reflexology is and how it works
- Describes different treatment types (foot, hand, full body)
- Answers common questions about reflexology
- Provides information about treatment benefits
- Explains reflexology techniques and principles

### **Treatment Information**
- Details about session duration and what to expect
- Treatment pricing and package options
- Booking information and appointment scheduling
- Location, hours, and contact details
- Preparation tips for first-time clients

### **Professional Boundaries**
- Emphasizes reflexology as complementary therapy
- Refers customers to healthcare professionals for medical concerns
- Does not make medical diagnoses or health guarantees
- Provides accurate information from knowledge base only

---

## 🚀 Quick Start

### **Running Jessica Locally**

```bash
# 1. Navigate to the project folder
cd reflexology-agent

# 2. Install dependencies (if not already installed)
pip install -r requirements.txt

# 3. Verify environment variables in .env file
cat .env

# 4. Update knowledge base with your reflexology content
nano data/knowledge_base/catalog.txt

# 5. Run the agent
python web/app.py
```

### **Access Points**
- **Web Chat:** http://localhost:5001
- **Health Check:** http://localhost:5001/health
- **WhatsApp:** Configure webhook at http://your-vps-ip:5001/webhook/whapi

---

## 📁 Project Structure

```
reflexology-agent/
├── config/
│   ├── config.json          # Jessica's configuration (name, role, port)
│   ├── prompts.yaml         # Reflexology-specific system prompts
│   └── .env.template        # Environment variables template
│
├── core/                    # Core functionality
│   ├── ai_engine.py        # OpenAI integration
│   ├── conversation_manager.py
│   └── validator.py
│
├── handlers/               # Request handlers
│   ├── whatsapp_handler.py
│   ├── web_handler.py
│   └── tools/             # File processing (images, docs, voice)
│
├── data/
│   └── knowledge_base/
│       └── catalog.txt    # ⚠️ FILL WITH YOUR REFLEXOLOGY CONTENT
│
├── web/
│   └── app.py            # Flask application (runs on port 5001)
│
└── logs/                 # Application logs (auto-created)
```

---

## ⚙️ Configuration

### **Agent Settings** (config/config.json)
```json
{
  "agent": {
    "name": "Jessica",
    "role": "reflexology consultant",
    "description": "Friendly reflexology consultant providing expert guidance..."
  },
  "platforms": {
    "web": {
      "port": 5001  // Different from template (5000)
    }
  }
}
```

### **Environment Variables** (.env)
```bash
OPENAI_API_KEY=sk-proj-...          # Same as template
WHAPI_API_TOKEN=Ro10XvLAumv5m9...   # Same as template
WHAPI_CHANNEL_ID=60120000000        # Same as template
WEBHOOK_URL=https://your-domain.com  # Updated port
```

---

## 📚 Knowledge Base Setup

### **⚠️ IMPORTANT: Fill In Your Reflexology Content**

The knowledge base template is located at:
```
data/knowledge_base/catalog.txt
```

**Sections to complete:**
1. **[TREATMENTS]** - Your reflexology treatment offerings
2. **[BENEFITS]** - Health and wellness benefits
3. **[PRICING]** - Treatment prices and packages
4. **[FAQ]** - Frequently asked questions
5. **[BOOKING_INFO]** - Location, hours, contact, booking policy
6. **[TECHNIQUES]** - Reflexology techniques and methods
7. **[HEALTH_CONDITIONS]** - Conditions reflexology may help with

**Example Format:**
```
[TREATMENTS]
Name: Foot Reflexology Treatment
Duration: 60 minutes
Benefits: Stress relief, improved circulation
Price: RM 88
Description: Comprehensive foot reflexology session...
```

---

## 🔌 Platform Integration

### **Web Chat**
- Automatically enabled
- Access at: http://localhost:5001 (local) or http://your-ip:5001 (VPS)
- Clean, mobile-friendly interface

### **WhatsApp (via Whapi)**
1. Webhook already configured in .env file
2. Set webhook in Whapi dashboard: `https://your-domain.com`
3. Customers can message via WhatsApp
4. Jessica responds with reflexology guidance

---

## 🧪 Testing

```bash
# Test API connections
python scripts/test_connection.py

# Check health endpoint
curl http://localhost:5001/health

# View logs
tail -f logs/ChatAgent_*.log

# View error logs only
tail -f logs/ChatAgent_errors_*.log
```

---

## 💬 Example Conversations

**Customer:** "What is reflexology?"
**Jessica:** "Great question! ✨

Reflexology is a complementary therapy that involves applying pressure to specific points on the feet, hands, or ears. These points correspond to different organs and systems in the body...

Would you like to know more about a specific treatment? 😊"

**Customer:** "How much for foot reflexology?"
**Jessica:** "Here's our pricing for foot reflexology! 👣

Foot Reflexology (60 min): RM 88
First-time Package: RM 78
Package of 5 sessions: RM 400

Would you like to book a session? 😊"

---

## 📊 Logging

All activity is logged in the `logs/` directory:
- `ChatAgent_YYYYMMDD.log` - All logs (DEBUG level)
- `ChatAgent_errors_YYYYMMDD.log` - Errors only

**Log format:**
```
2025-11-06 15:30:45 | INFO | core.ai_engine.generate_response:145 | Processing reflexology question...
```

---

## 🚢 Deployment

### **VPS Deployment (DigitalOcean, etc.)**

See `DEPLOYMENT.md` for detailed instructions.

**Quick deployment:**
```bash
# 1. Install Gunicorn
pip install gunicorn

# 2. Run with Gunicorn
gunicorn --bind 0.0.0.0:5001 --workers 2 web.app:app

# 3. Set up systemd service (see DEPLOYMENT.md)
```

**Important:** Update Whapi webhook URL to your VPS IP with port 5001

---

## 🔧 Customization

### **Update Treatment Information**
Edit `data/knowledge_base/catalog.txt` with your:
- Treatment offerings and descriptions
- Pricing and packages
- Booking information
- FAQs specific to your practice

### **Change Agent Personality**
Edit `config/prompts.yaml` to adjust:
- Tone and communication style
- Response formatting
- Professional boundaries
- Language preferences

### **Modify Settings**
Edit `config/config.json` to change:
- Agent name and role
- AI model and parameters
- Port number
- Feature flags

---

## 🐛 Troubleshooting

### **Agent gives incorrect information**
- Check if knowledge base is loaded: visit `/health` endpoint
- Review logs: `logs/ChatAgent_*.log`
- Verify `data/knowledge_base/catalog.txt` has your content

### **Port 5001 already in use**
- Change port in `config/config.json`
- Update webhook URL in `.env`
- Update Whapi webhook settings

### **WhatsApp not responding**
- Verify webhook URL is publicly accessible
- Check Whapi dashboard for webhook status
- Review logs for incoming webhook data
- Ensure port 5001 is open on your VPS

### **Missing OpenAI responses**
- Check OpenAI API key in `.env`
- Review error logs: `logs/ChatAgent_errors_*.log`
- Verify API quota/billing on OpenAI platform

---

## 📝 Next Steps

### **1. Complete Knowledge Base** ⚠️
Fill in your reflexology content in:
```
data/knowledge_base/catalog.txt
```

### **2. Test Locally**
```bash
python web/app.py
# Visit http://localhost:5001
```

### **3. Deploy to VPS**
- Follow `DEPLOYMENT.md` instructions
- Update Whapi webhook URL
- Test WhatsApp integration

### **4. Add PDFs (Optional)**
Place reflexology guides, brochures in:
```
data/knowledge_base/documents/
```

---

## ⚠️ Important Reminders

1. **Knowledge Base:** Fill in `data/knowledge_base/catalog.txt` with your content
2. **Port Number:** This agent uses port **5001** (not 5000)
3. **Webhook URL:** Update Whapi webhook to use port 5001
4. **Medical Disclaimer:** Jessica emphasizes reflexology is complementary therapy
5. **Professional Boundaries:** Jessica refers medical concerns to healthcare professionals

---

## 📄 Configuration Summary

| Setting | Value |
|---------|-------|
| Agent Name | Jessica |
| Role | Reflexology Consultant |
| Port | 5001 |
| OpenAI Key | ✅ Same as template |
| WHAPI Token | ✅ Same as template |
| Webhook URL | https://your-domain.com |
| Knowledge Base | data/knowledge_base/catalog.txt (⚠️ Update this!) |

---

## 🤝 Support

For issues:
1. Check logs in `logs/` directory
2. Review `DEPLOYMENT.md` for deployment issues
3. Verify configuration in `config/` directory
4. Test connections: `python scripts/test_connection.py`

---

**Built with ❤️ using the Chat Agent Template**
**Specialized for reflexology consultation and wellness guidance**
