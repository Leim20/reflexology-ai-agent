# 📊 VPS Monitoring Guide

Complete guide for monitoring your Jessica Reflexology chatbot on VPS.

---

## 🚀 Quick Start

After SSHing into your VPS:

```bash
# Navigate to project
cd /root/reflexology-agent  # or your project path

# Make scripts executable (first time only)
chmod +x scripts/*.sh

# Run quick status check
bash scripts/quick_status.sh
```

---

## 📋 Available Monitoring Scripts

### 1. **Quick Status** (`quick_status.sh`)
**Purpose**: Fast overview of system health
**Runtime**: ~1 second
**Use when**: You want a quick check

```bash
bash scripts/quick_status.sh
```

**Output**:
- ✅/❌ Application running status
- ✅/❌ Health check status
- ✅/❌ Debug mode status (security check)
- 📊 CPU and RAM usage
- ⚠️ Recent error count

---

### 2. **Full VPS Monitor** (`monitor_vps.sh`)
**Purpose**: Comprehensive system analysis
**Runtime**: ~5-10 seconds
**Use when**: You want detailed diagnostics

```bash
bash scripts/monitor_vps.sh
```

**Output includes**:
- 📊 System resources (CPU, RAM, Disk, Uptime)
- 🤖 Application status (service, processes, ports)
- 💚 Health check endpoint response
- ⚙️ Configuration validation (debug mode, logging level)
- 📝 Recent logs (last 10 lines)
- 🚨 Recent errors (last 5 errors)
- 📞 Escalation history
- 💬 WhatsApp connectivity test
- 📊 Google Sheets integration status
- 🌐 Network & firewall status
- ⏰ Scheduled jobs activity
- 📋 Summary with issue count

**Example output**:
```
==========================================
🔍 JESSICA CHATBOT - VPS MONITORING
==========================================

📊 SYSTEM RESOURCES
CPU Usage: 15%
RAM: 45% (500MB / 1024MB)
Disk: 30% used

🤖 APPLICATION STATUS
✅ Service is running
Port 5001: Listening

💚 HEALTH CHECK
✅ Health endpoint: OK (200)

⚙️ CONFIGURATION CHECK
✅ FLASK_DEBUG=False
Logging Level: INFO

📋 SUMMARY
✅ All checks passed! System is healthy.
```

---

### 3. **Live Monitor** (`monitor_live.sh`)
**Purpose**: Real-time continuous monitoring
**Runtime**: Continuous (updates every 5 seconds)
**Use when**: You want to watch system in real-time

```bash
bash scripts/monitor_live.sh
```

**Press Ctrl+C to stop**

**Shows (refreshed every 5 seconds)**:
- Service status
- CPU & Memory usage
- Active processes
- Port 5001 status
- Last 3 log entries
- Recent error count
- Active conversations count

Perfect for:
- Watching deployments
- Debugging issues
- Monitoring during high traffic

---

### 4. **Log Viewer** (`view_logs.sh`)
**Purpose**: Interactive log viewing
**Runtime**: Instant
**Use when**: You need to check logs

```bash
# Watch live logs (default)
bash scripts/view_logs.sh
bash scripts/view_logs.sh live

# View error logs only
bash scripts/view_logs.sh errors

# View escalation logs
bash scripts/view_logs.sh escalations

# View today's activity
bash scripts/view_logs.sh today

# List all log files
bash scripts/view_logs.sh all

# View WhatsApp activity only
bash scripts/view_logs.sh whatsapp

# View Google Sheets activity
bash scripts/view_logs.sh google
```

**Examples**:

Watch incoming messages in real-time:
```bash
bash scripts/view_logs.sh live
```

Check if there are any errors:
```bash
bash scripts/view_logs.sh errors
```

See recent escalations:
```bash
bash scripts/view_logs.sh escalations
```

---

### 5. **Alert Checker** (`check_alerts.sh`)
**Purpose**: Check for critical issues
**Runtime**: ~2-3 seconds
**Use when**: You want to check for problems

```bash
bash scripts/check_alerts.sh
```

**Checks for**:
- ❌ Application not running
- ❌ Health endpoint failure
- ❌ Debug mode enabled (security risk)
- ⚠️ High disk usage (>80%)
- ⚠️ High memory usage (>80%)
- ⚠️ Recent errors (>10 in 30 minutes)
- ❌ Port 5001 not listening
- ⚠️ Large log files (>100MB)

**Exit codes**:
- `0` = All good
- `1` = Alerts found

**Perfect for**: Adding to cron jobs for automated monitoring

---

## 🔄 Automated Monitoring (Cron Jobs)

Set up automatic monitoring:

```bash
# Edit crontab
crontab -e

# Add these lines:

# Check for alerts every 5 minutes
*/5 * * * * cd /root/reflexology-agent && bash scripts/check_alerts.sh >> logs/monitoring.log 2>&1

# Full health check every hour
0 * * * * cd /root/reflexology-agent && bash scripts/monitor_vps.sh >> logs/hourly_health.log 2>&1

# Clean old logs daily (keep last 7 days)
0 2 * * * find /root/reflexology-agent/logs -name "*.log" -mtime +7 -delete
```

---

## 📈 Common Monitoring Scenarios

### **Scenario 1: App is down**

```bash
# 1. Check status
bash scripts/quick_status.sh

# 2. Check why it stopped
bash scripts/view_logs.sh errors

# 3. Check system resources
bash scripts/monitor_vps.sh

# 4. Restart if needed
sudo systemctl restart chatbot

# 5. Watch it start up
bash scripts/monitor_live.sh
```

---

### **Scenario 2: Users reporting slow responses**

```bash
# 1. Check resource usage
bash scripts/monitor_vps.sh

# 2. Watch live activity
bash scripts/monitor_live.sh

# 3. Check for errors
bash scripts/view_logs.sh errors

# 4. Check OpenAI API calls in logs
bash scripts/view_logs.sh live | grep -i "openai"
```

---

### **Scenario 3: Debug new deployment**

```bash
# Watch logs while testing
bash scripts/view_logs.sh live

# In another terminal, send test messages via WhatsApp
# Watch the logs show incoming webhooks and responses
```

---

### **Scenario 4: Check escalations**

```bash
# View all escalations
bash scripts/view_logs.sh escalations

# See escalation count
grep -c "Escalation" logs/escalations.log

# See today's escalations only
grep "$(date +%Y-%m-%d)" logs/escalations.log
```

---

### **Scenario 5: Monitor WhatsApp integration**

```bash
# Watch WhatsApp activity only
bash scripts/view_logs.sh whatsapp

# Test webhook
curl -X POST http://localhost:5001/webhook/whapi \
  -H "Content-Type: application/json" \
  -d '{"test": "message"}'

# Then check logs
bash scripts/view_logs.sh live
```

---

## 🔧 Troubleshooting

### Scripts not executing?

```bash
# Make them executable
chmod +x scripts/*.sh

# Or run with bash explicitly
bash scripts/monitor_vps.sh
```

### "Command not found" errors?

Some commands might not be installed:

```bash
# Install missing tools
sudo apt update
sudo apt install net-tools  # for netstat
sudo apt install curl       # for health checks
```

### Logs not showing?

```bash
# Check if logs directory exists
ls -la logs/

# Create if missing
mkdir -p logs

# Check log permissions
chmod 755 logs
```

### Health check failing?

```bash
# Check if app is running
systemctl status chatbot

# Check what's on port 5001
netstat -tulpn | grep 5001

# Test manually
curl -v http://localhost:5001/health
```

---

## 📊 Understanding the Metrics

### CPU Usage
- **0-30%**: Normal, healthy
- **30-70%**: Moderate, acceptable
- **70-90%**: High, investigate if sustained
- **90-100%**: Critical, performance issues likely

### Memory (RAM) Usage
- **0-50%**: Healthy
- **50-80%**: Normal under load
- **80-90%**: High, monitor closely
- **90-100%**: Critical, may cause crashes

### Disk Usage
- **0-70%**: Healthy
- **70-85%**: Should clean up soon
- **85-95%**: Urgent cleanup needed
- **95-100%**: Critical, may cause failures

### Response Times
- **<1 second**: Excellent
- **1-3 seconds**: Good
- **3-5 seconds**: Acceptable
- **>5 seconds**: Slow, investigate

---

## 🎯 Best Practices

1. **Run quick_status.sh daily** - Quick health check
2. **Run monitor_vps.sh weekly** - Full system audit
3. **Set up cron job for check_alerts.sh** - Automated monitoring
4. **Check escalation logs regularly** - Customer service quality
5. **Monitor disk space** - Prevent log files from filling disk
6. **Review error logs** - Catch issues early
7. **Keep debug mode OFF** - Security best practice
8. **Watch live during deployments** - Catch issues immediately

---

## 📞 Emergency Contacts

If monitoring shows critical issues:

1. **App down**: Check logs, restart service
2. **High resource usage**: Check for infinite loops, restart
3. **Health check failing**: Check OpenAI API key, network
4. **WhatsApp not working**: Check Whapi token, webhook URL

---

## 💡 Pro Tips

1. **Bookmark these commands in your terminal**:
   ```bash
   alias jess-status='cd /root/reflexology-agent && bash scripts/quick_status.sh'
   alias jess-monitor='cd /root/reflexology-agent && bash scripts/monitor_vps.sh'
   alias jess-logs='cd /root/reflexology-agent && bash scripts/view_logs.sh live'
   alias jess-restart='sudo systemctl restart chatbot'
   ```

2. **Watch logs from your local machine**:
   ```bash
   ssh contact@example.com 'cd /root/reflexology-agent && bash scripts/view_logs.sh live'
   ```

3. **Get status on your phone**:
   - Save these as SSH shortcuts in apps like Termius or JuiceSSH
   - Run quick checks without full SSH session

4. **Set up log rotation** to prevent disk filling:
   ```bash
   # Add to /etc/logrotate.d/reflexology-agent
   /root/reflexology-agent/logs/*.log {
       daily
       rotate 7
       compress
       missingok
       notifempty
   }
   ```

---

## 📚 Additional Resources

- **Health Endpoint**: `curl http://localhost:5001/health`
- **Service Management**: `systemctl {start|stop|restart|status} chatbot`
- **View Service Logs**: `journalctl -u chatbot -f`
- **Check Open Ports**: `netstat -tulpn` or `ss -tulpn`

---

**Happy Monitoring! 🚀**
