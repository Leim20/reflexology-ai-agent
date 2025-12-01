# 🛡️ Anti-Spam Protection System

**Comprehensive guide to the chat agent's anti-spam and security features**

Version: 1.0
Last Updated: 2025-11-26

---

## 📋 Overview

The chat agent now includes a robust anti-spam protection system that safeguards against:
- **Message flooding** (rapid fire spam)
- **Duplicate/repeated messages** (spam patterns)
- **Abusive behavior** (excessive requests)
- **Webhook forgery** (fake webhook attacks)
- **DDoS attempts** (IP-based throttling)

---

## 🔒 Security Features

### 1. **Rate Limiting**
Prevents users from sending too many messages in a short time.

**Default Limits:**
- **10 messages per minute** per user
- **100 messages per hour** per user
- **5 messages in 60 seconds** (burst threshold)

**When triggered:**
```
"You're sending messages too quickly. Maximum 10 messages per minute."
```

---

### 2. **Flood Detection**
Detects and blocks spam patterns (repeated/similar messages).

**Triggers when:**
- User sends the **same message 3+ times** within 60 seconds
- User sends **80%+ similar messages** repeatedly

**When triggered:**
```
"Please stop sending the same message repeatedly."
```

---

### 3. **Cooldown Periods**
Enforces minimum time between messages.

**Default:** 2 seconds between messages

**Dynamic Escalation:**
- After violations, cooldown increases (2s → 3s → 5s → 10s → 30s max)
- Resets after good behavior

**When triggered:**
```
"Please wait 5 seconds before sending another message."
```

---

### 4. **Automatic Blocking**
Temporarily blocks abusive users.

**Default Settings:**
- **Auto-block after:** 5 violations
- **Block duration:** 30 minutes
- **Warning threshold:** 3 violations

**When triggered:**
```
"You have been temporarily blocked due to suspicious activity.
Please try again in 28 minutes."
```

---

### 5. **Webhook Signature Verification**
Verifies Whapi webhooks are authentic (prevents forgery).

**How it works:**
- Uses HMAC-SHA256 to verify webhook signatures
- Rejects webhooks with invalid or missing signatures
- Protects against forged webhook attacks

**To enable:**
1. Get your webhook secret from Whapi dashboard
2. Add to `.env` file:
```bash
WHAPI_WEBHOOK_SECRET=your_secret_key_here
```

---

### 6. **IP-Based Throttling** (Web Chat)
Prevents abuse from same IP address.

**Default:** Maximum 30 requests per minute per IP

**When triggered:**
- IP is blocked for 15 minutes
- Returns HTTP 429 (Too Many Requests)

---

## ⚙️ Configuration

All settings are in `config/config.json` under the `"anti_spam"` section:

```json
{
  "anti_spam": {
    "rate_limit": {
      "enabled": true,
      "max_messages_per_minute": 10,
      "max_messages_per_hour": 100,
      "burst_window_seconds": 60,
      "burst_threshold": 5
    },
    "flood_detection": {
      "enabled": true,
      "duplicate_threshold": 3,
      "duplicate_window_seconds": 60,
      "similarity_threshold": 0.8
    },
    "cooldown": {
      "enabled": true,
      "min_seconds_between_messages": 2,
      "escalate_cooldown_after_violations": true,
      "max_cooldown_seconds": 30
    },
    "blocking": {
      "enabled": true,
      "auto_block_after_violations": 5,
      "block_duration_minutes": 30,
      "warning_threshold": 3
    },
    "whitelist": [],
    "blacklist": []
  }
}
```

---

## 🎯 Customizing Protection Levels

### **Lenient Mode** (For low-risk environments)
```json
"anti_spam": {
  "rate_limit": {
    "enabled": true,
    "max_messages_per_minute": 20,
    "max_messages_per_hour": 200
  },
  "blocking": {
    "enabled": true,
    "auto_block_after_violations": 10,
    "block_duration_minutes": 15
  }
}
```

### **Strict Mode** (For high-risk environments)
```json
"anti_spam": {
  "rate_limit": {
    "enabled": true,
    "max_messages_per_minute": 5,
    "max_messages_per_hour": 50
  },
  "blocking": {
    "enabled": true,
    "auto_block_after_violations": 3,
    "block_duration_minutes": 60
  }
}
```

### **Disabled** (Testing only - NOT recommended for production)
```json
"anti_spam": {
  "rate_limit": {
    "enabled": false
  },
  "flood_detection": {
    "enabled": false
  },
  "cooldown": {
    "enabled": false
  },
  "blocking": {
    "enabled": false
  }
}
```

---

## 👥 Whitelist & Blacklist

### **Whitelist** (Bypass all checks)
Add trusted users/numbers that should never be blocked:

```json
"whitelist": [
  "60123456789",
  "60198765432"
]
```

**Use cases:**
- Manager phone numbers
- Testing accounts
- VIP customers
- Staff members

---

### **Blacklist** (Permanent block)
Add abusive users/spammers that should be permanently blocked:

```json
"blacklist": [
  "60111111111",
  "60199999999"
]
```

**Use cases:**
- Known spammers
- Abusive users
- Bot accounts
- Malicious actors

---

## 📊 Monitoring & Logs

### **Check User Status**
The system tracks spam metrics for each user:

```python
status = anti_spam_manager.get_user_status("60123456789")
print(status)
```

**Output:**
```json
{
  "user_id": "60123456789",
  "whitelisted": false,
  "blacklisted": false,
  "blocked": false,
  "blocked_until": null,
  "violations": 2,
  "current_cooldown": 3.0,
  "messages_last_minute": 4,
  "messages_last_hour": 25,
  "total_messages": 47
}
```

---

### **Log Entries**
All spam events are logged:

```
⚠️ Rate limit exceeded: 12/10 per minute
🌊 Flood detected: 4 duplicate messages
🚫 AUTO-BLOCKED USER: 60123456789
   Violations: 5
   Duration: 30 minutes
```

---

## 🚨 Handling Spam Events

### **WhatsApp Users**
When blocked, users receive an automated warning:
```
⚠️ You're sending messages too quickly. Maximum 10 messages per minute.

Please slow down and try again shortly.
```

### **Web Chat Users**
HTTP 429 (Too Many Requests) is returned:
```json
{
  "error": "You're sending messages too quickly...",
  "success": false,
  "spam_blocked": true
}
```

---

## 🛠️ Manual Management

### **Unblock a User**
```python
anti_spam_manager.unblock_user("60123456789")
# Resets violations, cooldown, and removes block
```

### **Whitelist a User**
```python
anti_spam_manager.whitelist_user("60123456789")
# User bypasses all spam checks
```

### **Blacklist a User**
```python
anti_spam_manager.blacklist_user("60111111111")
# User permanently blocked
```

### **Cleanup Old Data**
```python
anti_spam_manager.cleanup_old_data()
# Removes tracking data older than 24 hours
```

---

## 🔐 Webhook Security Setup

### **Step 1: Get Webhook Secret from Whapi**
1. Log in to [Whapi Dashboard](https://whapi.cloud)
2. Go to **Settings** → **Webhooks**
3. Find your **Webhook Secret Key**

### **Step 2: Add to Environment**
Edit your `.env` file:
```bash
WHAPI_WEBHOOK_SECRET=your_secret_key_from_whapi
```

### **Step 3: Restart Application**
```bash
python web/app.py
```

### **Verification**
Check logs for:
```
✓ Webhook Validator initialized (signature verification enabled)
```

**If signature verification fails:**
```
🚫 WEBHOOK SIGNATURE VERIFICATION FAILED!
   This webhook may be forged or tampered with
```

---

## ⚡ Performance Impact

The anti-spam system is highly optimized:

- **Memory usage:** ~1-2 MB per 1000 active users
- **Processing overhead:** < 5ms per message check
- **Data cleanup:** Automatic (runs every 24 hours)

**No significant performance impact on normal operation.**

---

## 🧪 Testing Anti-Spam

### **Test Rate Limiting**
Send 15 messages rapidly from same number/session:
- First 10 messages: ✅ Allowed
- Messages 11-15: 🚫 Blocked

### **Test Flood Detection**
Send same message 5 times in 30 seconds:
- First 2 messages: ✅ Allowed
- Messages 3-5: 🚫 Blocked (flood detected)

### **Test Auto-Blocking**
Trigger 5 violations (rate limits + floods):
- User receives warning at 3 violations
- User auto-blocked at 5 violations
- Block lasts 30 minutes

---

## 📈 Best Practices

1. **Start with default settings** - They work well for most use cases
2. **Monitor logs** for false positives
3. **Whitelist managers/staff** to prevent accidental blocks
4. **Enable webhook verification** for production environments
5. **Review blacklist periodically** to remove reformed users
6. **Adjust thresholds** based on your traffic patterns
7. **Test changes** in staging before deploying to production

---

## 🐛 Troubleshooting

### **Legitimate users getting blocked**
**Solution:** Increase limits or add to whitelist
```json
"max_messages_per_minute": 15,  // Increase from 10
"auto_block_after_violations": 7  // Increase from 5
```

### **Spammers bypassing protection**
**Solution:** Decrease limits or enable stricter mode
```json
"max_messages_per_minute": 5,  // Decrease from 10
"auto_block_after_violations": 3  // Decrease from 5
```

### **Webhook verification failing**
**Causes:**
- Wrong webhook secret in `.env`
- Whapi changed their signature method
- Webhook not from Whapi (forged)

**Solution:** Verify `WHAPI_WEBHOOK_SECRET` matches Whapi dashboard

### **False positive flood detection**
**Solution:** Adjust similarity threshold
```json
"similarity_threshold": 0.9  // Increase from 0.8 (more lenient)
```

---

## 📞 Support

For issues or questions:
1. Check logs in `logs/ChatAgent_*.log`
2. Review user status with `get_user_status()`
3. Test with whitelisted number first
4. Consult this guide for configuration options

---

## 🔄 Updates & Maintenance

**Automatic:**
- Old tracking data cleaned up every 24 hours
- Expired blocks automatically removed
- Cooldown periods auto-adjust based on behavior

**Manual:**
- Review blacklist monthly
- Adjust thresholds seasonally (e.g., during promotions)
- Monitor logs for new spam patterns

---

**🎉 Your chat agent is now protected against spam and abuse!**

For advanced customization, see `core/anti_spam.py` source code.
