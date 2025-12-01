# VPS Deployment Instructions - Anti-Spam Update

**Deploy the updated reflexology-agent with anti-spam protection to your VPS**

Date: 2025-11-27
VPS IP: your-domain.com

---

## Pre-Deployment Checklist

Before deploying, ensure:
- [x] All anti-spam tests passed locally ✅
- [x] Flask app integration verified ✅
- [ ] VPS SSH access working
- [ ] Current app backed up on VPS

---

## Step 1: Backup Current VPS Installation

SSH into your VPS and backup:

```bash
ssh contact@example.com

# Navigate to project
cd /root/reflexology-agent

# Create backup
tar -czf reflexology-agent-backup-$(date +%Y%m%d).tar.gz .

# Move backup to safe location
mv reflexology-agent-backup-*.tar.gz /root/backups/

# Verify backup
ls -lh /root/backups/
```

---

## Step 2: Transfer Updated Files to VPS

From your local machine (Windows):

```powershell
# Navigate to project directory
cd C:\Users\Hp\Desktop\reflexology-agent

# Transfer updated files using SCP (if you have it)
# OR use SFTP client like WinSCP or FileZilla

# Files to transfer:
# - core/anti_spam.py (NEW FILE)
# - core/__init__.py (MODIFIED)
# - web/app.py (MODIFIED)
# - config/config.json (MODIFIED)
# - scripts/test_anti_spam.py (NEW FILE)
# - ANTI_SPAM_GUIDE.md (NEW FILE)
# - ANTI_SPAM_SUMMARY.md (NEW FILE)
```

**Using WinSCP or FileZilla:**
1. Connect to: `your-domain.com`
2. User: `root`
3. Navigate to: `/root/reflexology-agent/`
4. Upload the files listed above

**OR use Git** (if you have the project in Git):
```bash
# On VPS
cd /root/reflexology-agent
git pull origin main
```

---

## Step 3: Update Environment Variables (Optional)

If you want to enable webhook signature verification:

```bash
# On VPS
cd /root/reflexology-agent

# Edit .env file
nano .env

# Add this line (get secret from Whapi dashboard):
WHAPI_WEBHOOK_SECRET=your_webhook_secret_here

# Save: Ctrl+O, Enter
# Exit: Ctrl+X
```

---

## Step 4: Test Anti-Spam on VPS

Before restarting the app, test the anti-spam system:

```bash
cd /root/reflexology-agent

# Run test suite
python3 scripts/test_anti_spam.py

# Expected output:
# ALL TESTS COMPLETED SUCCESSFULLY
# The anti-spam system is working correctly!
```

If tests fail, check:
- Python modules installed: `pip3 list`
- File permissions: `ls -la core/`
- Python path: `python3 -c "import sys; print(sys.path)"`

---

## Step 5: Restart the Application

```bash
# Stop current app
sudo systemctl stop reflexology-agent

# OR if running with screen/tmux:
# screen -r reflexology
# Ctrl+C to stop
# exit

# Start the app
sudo systemctl start reflexology-agent

# OR manually:
# screen -S reflexology
# cd /root/reflexology-agent
# python3 web/app.py
# Ctrl+A, D to detach

# Verify it's running
sudo systemctl status reflexology-agent

# Check logs for anti-spam initialization
tail -f logs/ChatAgent_*.log | grep "Anti-Spam"

# Expected output:
# ✓ Anti-Spam Manager initialized
# ✓ Webhook Validator initialized (if webhook secret set)
```

---

## Step 6: Verify Anti-Spam is Active

### Test 1: Check Health Endpoint

```bash
curl http://your-domain.com:5001/health
```

### Test 2: Send Test Messages via WhatsApp

Send 15 messages rapidly to your WhatsApp bot:
- First 10: Should be delivered ✅
- Messages 11-15: Should get rate limit warning ⚠️

**Expected response:**
```
⚠️ You're sending messages too quickly. Maximum 10 messages per minute.

Please slow down and try again shortly.
```

### Test 3: Check Logs for Spam Detection

```bash
# Watch live logs
tail -f logs/ChatAgent_*.log | grep -E "SPAM|BLOCKED|Violation"

# OR check recent spam events
grep "BLOCKED\|Violation" logs/ChatAgent_$(date +%Y%m%d).log
```

---

## Step 7: Configure Whitelist (Optional)

Add your manager phone number to bypass all spam checks:

```bash
# On VPS
cd /root/reflexology-agent

# Edit config
nano config/config.json

# Find the "anti_spam" section and add to whitelist:
"whitelist": [
  "60120000000"  # Manager Alex - bypass all checks
]

# Save and restart app
sudo systemctl restart reflexology-agent
```

---

## Step 8: Monitor for 24 Hours

Keep an eye on the logs for the first 24 hours:

```bash
# Watch for spam events
tail -f logs/ChatAgent_*.log | grep -E "SPAM|BLOCKED|Violation|AUTO-BLOCKED"

# Check error logs
tail -f logs/ChatAgent_errors_*.log

# Monitor system resources
htop
# Press q to exit
```

---

## Rollback Procedure (If Issues Occur)

If something goes wrong:

```bash
# Stop the app
sudo systemctl stop reflexology-agent

# Restore from backup
cd /root
rm -rf reflexology-agent
tar -xzf backups/reflexology-agent-backup-YYYYMMDD.tar.gz -C reflexology-agent/

# Restart app
sudo systemctl start reflexology-agent

# Verify
curl http://your-domain.com:5001/health
```

---

## Configuration Tuning

### If Legitimate Users Get Blocked:

```bash
# Edit config
nano config/config.json

# Increase limits:
"anti_spam": {
  "rate_limit": {
    "max_messages_per_minute": 15,  // Increase from 10
    "max_messages_per_hour": 150     // Increase from 100
  },
  "blocking": {
    "auto_block_after_violations": 7  // Increase from 5
  }
}

# Restart
sudo systemctl restart reflexology-agent
```

### If Spammers Bypass Protection:

```bash
# Edit config
nano config/config.json

# Decrease limits:
"anti_spam": {
  "rate_limit": {
    "max_messages_per_minute": 5,   // Decrease from 10
    "max_messages_per_hour": 50      // Decrease from 100
  },
  "blocking": {
    "auto_block_after_violations": 3  // Decrease from 5
  }
}

# Restart
sudo systemctl restart reflexology-agent
```

---

## Verification Checklist

After deployment, verify:

- [ ] App starts without errors
- [ ] Health endpoint responds: `http://your-domain.com:5001/health`
- [ ] Logs show: "✓ Anti-Spam Manager initialized"
- [ ] Logs show: "✓ Webhook Validator initialized" (if secret configured)
- [ ] WhatsApp messages still work normally
- [ ] Web chat still works normally
- [ ] Rate limiting triggers after 10+ rapid messages
- [ ] Spam warning sent to users who trigger limits
- [ ] Manager number whitelisted (if configured)
- [ ] No errors in error log: `logs/ChatAgent_errors_*.log`

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'core.anti_spam'"

**Solution:**
```bash
# Verify file was uploaded
ls -la core/anti_spam.py

# Check file permissions
chmod 644 core/anti_spam.py

# Verify import works
python3 -c "from core.anti_spam import AntiSpamManager; print('OK')"
```

### Issue: "Anti-Spam Manager not initialized"

**Solution:**
```bash
# Check config.json
cat config/config.json | grep -A 20 "anti_spam"

# Verify it's not commented out or malformed
# Should start with: "anti_spam": {

# Check logs for initialization errors
grep "Anti-Spam\|anti_spam" logs/ChatAgent_*.log
```

### Issue: "Webhook signature verification failed"

**Solution:**
```bash
# Check webhook secret in .env
cat .env | grep WHAPI_WEBHOOK_SECRET

# Verify it matches Whapi dashboard
# If wrong, edit .env and restart

# OR disable verification temporarily:
nano .env
# Comment out: #WHAPI_WEBHOOK_SECRET=...

# Restart
sudo systemctl restart reflexology-agent
```

### Issue: "All users getting blocked immediately"

**Solution:**
```bash
# Check config - may be too strict
cat config/config.json | grep -A 10 "anti_spam"

# Temporarily disable for testing:
nano config/config.json

# Set to:
"anti_spam": {
  "rate_limit": {
    "enabled": false  // Temporary
  }
}

# Restart and investigate
sudo systemctl restart reflexology-agent
```

---

## Support Commands

```bash
# View active connections
netstat -tulpn | grep 5001

# Check disk space
df -h

# Check memory
free -h

# View running processes
ps aux | grep python

# Restart nginx (if using)
sudo systemctl restart nginx

# View system logs
journalctl -u reflexology-agent -f
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| View logs | `tail -f logs/ChatAgent_*.log` |
| View errors | `tail -f logs/ChatAgent_errors_*.log` |
| Check spam events | `grep "BLOCKED" logs/ChatAgent_$(date +%Y%m%d).log` |
| Restart app | `sudo systemctl restart reflexology-agent` |
| Check status | `sudo systemctl status reflexology-agent` |
| Test health | `curl http://your-domain.com:5001/health` |
| Edit config | `nano config/config.json` |
| Edit env | `nano .env` |

---

## Success Criteria

Deployment is successful when:
1. ✅ App runs without crashes
2. ✅ No errors in error log
3. ✅ WhatsApp bot responds normally
4. ✅ Web chat works normally
5. ✅ Spam protection triggers after 10+ messages
6. ✅ Legitimate users can chat normally
7. ✅ Logs show anti-spam initialization
8. ✅ Health endpoint returns 200 OK

---

## Post-Deployment

After 24 hours of stable operation:
1. Review spam logs: `grep "BLOCKED\|Violation" logs/ChatAgent_*.log | wc -l`
2. Check if any legitimate users were blocked
3. Adjust thresholds if needed
4. Update whitelist with trusted numbers
5. Document any configuration changes

---

**Deployment prepared by:** Claude Code
**Date:** 2025-11-27
**Version:** Anti-Spam v1.0

Good luck with the deployment! 🚀
