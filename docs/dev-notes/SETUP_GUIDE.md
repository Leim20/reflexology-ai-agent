# 🚀 Quick Setup Guide

**Get your chat agent running in 5 minutes!**

---

## ⚡ Quick Start

### **Step 1: Install Dependencies** (2 minutes)

```bash
# Navigate to project
cd "path/to/Duplicate agent template"

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### **Step 2: Run Setup Wizard** (2 minutes)

```bash
python scripts/setup_agent.py
```

**You'll be asked for:**
- Agent name (e.g., "ShopBot")
- Agent role (e.g., "clothing shop assistant")
- OpenAI API key (from https://platform.openai.com/api-keys)
- WhatsApp settings (optional)

### **Step 3: Add Your Knowledge** (1 minute)

```bash
# Edit the knowledge base
notepad data/knowledge_base/catalog.txt  # Windows
nano data/knowledge_base/catalog.txt     # Mac/Linux
```

Add your products, FAQs, or domain knowledge.

### **Step 4: Run the Agent!**

```bash
python web/app.py
```

✅ **Done!** Open http://localhost:5000 in your browser.

---

## 🔍 Verify Everything Works

```bash
# Run connection tests
python scripts/test_connection.py
```

This checks:
- ✅ Environment variables
- ✅ Configuration files
- ✅ Python dependencies
- ✅ OpenAI API connection
- ✅ Whapi API connection (if configured)

---

## 📝 Manual Setup (Alternative)

If you prefer manual configuration:

### **1. Create .env file**

```bash
cp config/.env.template .env
```

Edit `.env` and add:

```
OPENAI_API_KEY=sk-proj-your-key-here
WHAPI_API_TOKEN=your-whapi-token
WHAPI_CHANNEL_ID=60123456789
WEBHOOK_URL=http://localhost:5000/webhook/whapi
FLASK_SECRET_KEY=generate-with-python-secrets
```

### **2. Update config.json**

Edit `config/config.json` and replace placeholders:
- `{{AGENT_NAME}}` → Your agent name
- `{{AGENT_ROLE}}` → Agent's role
- `{{AGENT_DESCRIPTION}}` → Description

### **3. Add Knowledge Base**

Edit `data/knowledge_base/catalog.txt` with your content.

---

## 🎯 What You Can Do

### **Web Chat**
- Access: http://localhost:5000
- Upload images, documents, voice messages
- Chat with AI assistant
- Export conversation history

### **WhatsApp Integration**
1. Set up webhook in Whapi dashboard
2. Point to: `http://your-server/webhook/whapi`
3. Send messages to your WhatsApp number
4. Bot responds automatically!

---

## 📂 Project Structure

```
Duplicate agent template/
├── config/           # Configuration files
│   ├── config.json   # Main config (edit placeholders!)
│   ├── .env.template # Copy to .env and fill in
│   └── prompts.yaml  # System prompts
│
├── data/
│   └── knowledge_base/
│       └── catalog.txt  # ← Add your knowledge here!
│
├── web/
│   └── app.py        # ← Main application (run this!)
│
└── scripts/
    ├── setup_agent.py      # Setup wizard
    └── test_connection.py  # Connection tester
```

---

## 🐛 Common Issues

### **"OPENAI_API_KEY not configured"**
- Run `python scripts/setup_agent.py`
- OR manually edit `.env` file

### **"Knowledge base not loaded"**
- Edit `data/knowledge_base/catalog.txt`
- Add content after the `[CATALOG]` marker

### **"ModuleNotFoundError"**
```bash
pip install -r requirements.txt
```

### **WhatsApp webhook not working**
- Use public URL (not localhost)
- Enable HTTPS for production
- Check Whapi dashboard webhook settings

---

## 🚀 Next Steps

### **For Production Deployment:**
See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- VPS setup (DigitalOcean, AWS, etc.)
- Nginx configuration
- SSL/HTTPS setup
- Systemd service
- Monitoring & logs

### **For Customization:**
- Edit `config/prompts.yaml` - Customize AI behavior
- Edit `config/config.json` - Change model, temperature, etc.
- Edit `data/knowledge_base/catalog.txt` - Update knowledge

### **For Creating New Agents:**
1. Copy entire folder
2. Run `python scripts/setup_agent.py`
3. Update knowledge base
4. Deploy!

---

## 📖 Full Documentation

- [README.md](README.md) - Complete overview
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Technical details

---

## ✅ Success Checklist

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Setup wizard completed (`python scripts/setup_agent.py`)
- [ ] `.env` file created with API keys
- [ ] Knowledge base added to `catalog.txt`
- [ ] Connection tests passed (`python scripts/test_connection.py`)
- [ ] Web app running (`python web/app.py`)
- [ ] Tested in browser (http://localhost:5000)
- [ ] WhatsApp webhook configured (optional)

---

**🎉 You're all set! Happy chatting!**

Need help? Check the logs in `logs/` directory for debugging.
