# 🚀 Deployment Guide

**Deploy your chat agent to production (VPS/DigitalOcean)**

---

## 📋 Prerequisites

- VPS with Ubuntu 20.04+ (DigitalOcean, AWS, etc.)
- Domain name (optional but recommended)
- SSH access to your VPS
- Root or sudo privileges

---

## 🔧 Local Development Setup

### **1. Install Dependencies**

```bash
# Install Python 3.8+
python3 --version

# Install pip if not already installed
sudo apt update
sudo apt install python3-pip python3-venv

# Navigate to project
cd path/to/chat-agent-template

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### **2. Configure Agent**

```bash
# Run interactive setup
python scripts/setup_agent.py

# OR manually configure:
cp config/.env.template .env
nano .env  # Edit with your API keys
nano config/config.json  # Update placeholders
```

### **3. Add Knowledge Base**

```bash
# Edit your knowledge base
nano data/knowledge_base/catalog.txt

# Add your domain-specific content
```

### **4. Test Locally**

```bash
# Run connection tests
python scripts/test_connection.py

# Start the app
python web/app.py

# Access at: http://localhost:5000
```

---

## 🌐 VPS Deployment

### **Step 1: Prepare VPS**

```bash
# SSH into your VPS
ssh root@your-vps-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx supervisor git

# Create app user (optional but recommended)
sudo adduser chatbot
sudo usermod -aG sudo chatbot
su - chatbot
```

### **Step 2: Upload Project Files**

**Option A: Git Clone (Recommended)**

```bash
# Clone your repository
git clone https://github.com/yourusername/your-agent-repo.git
cd your-agent-repo
```

**Option B: Manual Upload**

```bash
# On your local machine:
scp -r chat-agent-template chatbot@your-vps-ip:/home/chatbot/

# On VPS:
cd /home/chatbot/chat-agent-template
```

### **Step 3: Install Dependencies on VPS**

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Install Gunicorn for production
pip install gunicorn
```

### **Step 4: Configure Environment**

```bash
# Copy and edit .env
nano .env

# Add your production values:
# - OpenAI API key
# - Whapi token
# - Production webhook URL: https://yourdomain.com/webhook/whapi
# - Flask secret key

# Update config.json if needed
nano config/config.json
```

### **Step 5: Test Application**

```bash
# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 2 web.app:app

# Test in browser: http://your-vps-ip:5000
# If working, proceed to Nginx setup
# Press Ctrl+C to stop
```

### **Step 6: Configure Nginx**

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/chatbot
```

**Add this configuration:**

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeout settings for long requests (voice processing)
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # File upload size limit
    client_max_body_size 20M;
}
```

**Enable the site:**

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### **Step 7: Setup Systemd Service**

```bash
# Create service file
sudo nano /etc/systemd/system/chatbot.service
```

**Add this configuration:**

```ini
[Unit]
Description=Chat Agent Gunicorn Service
After=network.target

[Service]
User=chatbot
Group=www-data
WorkingDirectory=/home/chatbot/chat-agent-template
Environment="PATH=/home/chatbot/chat-agent-template/venv/bin"

ExecStart=/home/chatbot/chat-agent-template/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:5000 \
    --timeout 300 \
    --access-logfile /home/chatbot/chat-agent-template/logs/access.log \
    --error-logfile /home/chatbot/chat-agent-template/logs/error.log \
    web.app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Start the service:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start chatbot

# Enable on boot
sudo systemctl enable chatbot

# Check status
sudo systemctl status chatbot
```

### **Step 8: Setup SSL (HTTPS) - Optional but Recommended**

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## 🔗 Configure WhatsApp Webhook

### **1. Get Your Webhook URL**

Your webhook URL should be:
```
https://yourdomain.com/webhook/whapi
```

### **2. Configure in Whapi Dashboard**

1. Log in to [Whapi.cloud](https://whapi.cloud)
2. Go to your channel settings
3. Find "Webhooks" section
4. Add webhook URL: `https://yourdomain.com/webhook/whapi`
5. Enable events: `messages`
6. Save settings

### **3. Test Webhook**

```bash
# Monitor logs
tail -f logs/ChatAgent_*.log

# Send a test message to your WhatsApp number
# Check logs for incoming webhook
```

---

## 📊 Monitoring & Maintenance

### **View Logs**

```bash
# Application logs
tail -f logs/ChatAgent_$(date +%Y%m%d).log

# Error logs only
tail -f logs/ChatAgent_errors_$(date +%Y%m%d).log

# Gunicorn logs
tail -f logs/access.log
tail -f logs/error.log

# Systemd service logs
sudo journalctl -u chatbot -f
```

### **Restart Service**

```bash
# Restart application
sudo systemctl restart chatbot

# Restart Nginx
sudo systemctl restart nginx
```

### **Update Code**

```bash
# Pull latest changes
cd /home/chatbot/chat-agent-template
git pull

# Restart service
sudo systemctl restart chatbot
```

### **Check Health**

```bash
# Health check endpoint
curl http://localhost:5000/health

# Or in browser:
https://yourdomain.com/health
```

---

## 🛠️ Troubleshooting

### **Application Won't Start**

```bash
# Check service status
sudo systemctl status chatbot

# Check logs
sudo journalctl -u chatbot -n 50

# Manually run to see errors
cd /home/chatbot/chat-agent-template
source venv/bin/activate
gunicorn --bind 127.0.0.1:5000 web.app:app
```

### **502 Bad Gateway**

- Check if Gunicorn is running: `sudo systemctl status chatbot`
- Check Nginx configuration: `sudo nginx -t`
- Check firewall: `sudo ufw status`

### **WhatsApp Webhook Not Working**

1. Check webhook URL is publicly accessible
2. Verify SSL certificate is valid (use HTTPS)
3. Check logs for incoming requests
4. Test webhook manually:

```bash
curl -X POST https://yourdomain.com/webhook/whapi \
  -H "Content-Type: application/json" \
  -d '{"test": "message"}'
```

### **High Memory Usage**

```bash
# Reduce Gunicorn workers
sudo nano /etc/systemd/system/chatbot.service
# Change --workers 3 to --workers 2

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart chatbot
```

### **Knowledge Base Not Loading**

```bash
# Check file exists
ls -lh data/knowledge_base/catalog.txt

# Check file permissions
chmod 644 data/knowledge_base/catalog.txt

# Check health endpoint
curl http://localhost:5000/health | jq .knowledge_base
```

---

## 🔐 Security Best Practices

1. **Use environment variables** for secrets (never commit .env)
2. **Enable firewall:**
   ```bash
   sudo ufw allow ssh
   sudo ufw allow http
   sudo ufw allow https
   sudo ufw enable
   ```
3. **Use SSL/HTTPS** (required for WhatsApp webhooks)
4. **Limit file upload sizes** (configured in Nginx)
5. **Regular updates:**
   ```bash
   sudo apt update && sudo apt upgrade
   ```

---

## 📈 Performance Optimization

### **For High Traffic**

1. **Increase Gunicorn workers:**
   ```
   --workers (2 x CPU cores) + 1
   ```

2. **Use Redis for session storage** (optional)

3. **Enable Nginx caching** for static files

4. **Monitor with Supervisor:**
   ```bash
   sudo apt install supervisor
   ```

---

## ✅ Quick Deployment Checklist

- [ ] VPS with Ubuntu 20.04+
- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`requirements.txt`)
- [ ] `.env` file configured with production values
- [ ] Knowledge base added (`catalog.txt`)
- [ ] Nginx configured and running
- [ ] Systemd service created and running
- [ ] SSL certificate installed (if using domain)
- [ ] WhatsApp webhook configured in Whapi dashboard
- [ ] Firewall configured
- [ ] Health check endpoint returns 200
- [ ] Test message sent via WhatsApp
- [ ] Logs monitored and clean

---

**🎉 Your chat agent is now deployed and ready for production!**

For issues or questions, check the logs first:
```bash
tail -f logs/ChatAgent_*.log
```
