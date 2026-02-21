# Anti-Spam & Rate Limiting System

## Overview

The Anti-Spam System protects the chat agent from **abuse, flooding, and malicious activity**. It implements multiple layers of protection including rate limiting, flood detection, cooldown periods, and automatic blocking.

**Source file:** `core/anti_spam.py`
**Lines of code:** ~498 lines
**Dependencies:** `utils.logger`

---

## What is the Purpose?

The Anti-Spam System exists to:

1. **Protect WhatsApp account** — Excessive messaging can get the business WhatsApp banned.

2. **Prevent API abuse** — Stop users from overwhelming the OpenAI API with requests.

3. **Ensure fair usage** — Prevent single users from monopolizing system resources.

4. **Block malicious actors** — Automatically block users who exhibit abusive patterns.

5. **Verify webhook authenticity** — Ensure incoming webhooks are from legitimate sources.

---

## How It Works

### Protection Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Incoming Message                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
         ┌────────────────┼────────────────────────────────────┐
         │                │                                    │
         ▼                ▼                                    │
┌─────────────┐  ┌─────────────┐                               │
│ Whitelist?  │  │ Blacklist?  │                               │
│ BYPASS ALL  │  │ PERMANENT   │                               │
│             │  │ BLOCK       │                               │
└──────┬──────┘  └──────┬──────┘                               │
       │                 │                                      │
       │ NO              │ YES → BLOCKED                       │
       │                 │                                      │
       ▼                 │                                      │
┌─────────────────────────────────────────────────────────────┐│
│ Layer 1: Temporary Block Check                              ││
│ Is user currently blocked from previous violations?         ││
└─────────────────────────┬───────────────────────────────────┘│
                          │                                     │
                          ▼                                     │
┌─────────────────────────────────────────────────────────────┐│
│ Layer 2: Cooldown Check                                     ││
│ Has enough time passed since last message?                  ││
│ (min 2 seconds between messages)                            ││
└─────────────────────────┬───────────────────────────────────┘│
                          │                                     │
                          ▼                                     │
┌─────────────────────────────────────────────────────────────┐│
│ Layer 3: Rate Limiting                                      ││
│ - Max 10 messages per minute                                ││
│ - Max 100 messages per hour                                 ││
│ - Burst detection (5 messages in 60 seconds)                ││
└─────────────────────────┬───────────────────────────────────┘│
                          │                                     │
                          ▼                                     │
┌─────────────────────────────────────────────────────────────┐│
│ Layer 4: Flood Detection                                    ││
│ - Same message 3+ times = flood                             ││
│ - 80%+ similar messages = spam pattern                      ││
└─────────────────────────┬───────────────────────────────────┘│
                          │                                     │
                          ▼                                     │
┌─────────────────────────────────────────────────────────────┐│
│ Layer 5: IP Rate Limiting (Web Chat only)                   ││
│ - Max 30 requests per minute per IP                         ││
└─────────────────────────┬───────────────────────────────────┘│
                          │                                     │
                          ▼                                     │
                 ┌─────────────────┐                            │
                 │ MESSAGE ALLOWED │                            │
                 └─────────────────┘                            │
```

---

## Key Components

### 1. AntiSpamManager — Main Protection Class

**Initialization:**

```python
from core.anti_spam import AntiSpamManager

spam_manager = AntiSpamManager(config={
    'rate_limit': {
        'enabled': True,
        'max_messages_per_minute': 10,
        'max_messages_per_hour': 100,
        'burst_threshold': 5
    },
    'flood_detection': {
        'enabled': True,
        'duplicate_threshold': 3,
        'similarity_threshold': 0.8
    },
    'cooldown': {
        'enabled': True,
        'min_seconds_between_messages': 2
    },
    'blocking': {
        'enabled': True,
        'auto_block_after_violations': 5,
        'block_duration_minutes': 30
    }
})
```

### 2. WebhookValidator — Verify Webhook Authenticity

```python
from core.anti_spam import WebhookValidator

validator = WebhookValidator(webhook_secret="your-secret")
is_valid = validator.verify_signature(payload_bytes, signature_header)
```

---

## Key Methods

### 1. `check_message()` — Main Entry Point

**Purpose:** Check if a message should be allowed through.

```python
allowed, reason = spam_manager.check_message(
    user_id="60123456789",
    message="Hello, I want to book",
    ip_address="192.168.1.1"  # Optional, for web chat
)

if allowed:
    # Process message
    process_customer_message(message)
else:
    # Message blocked
    send_reply(reason)  # e.g., "Please wait 30 seconds..."
```

**Returns:**
- `(True, None)` — Message allowed
- `(False, "reason")` — Message blocked with explanation

### 2. `whitelist_user()` — Bypass All Checks

```python
# Add manager to whitelist
spam_manager.whitelist_user("60123456789")
```

### 3. `blacklist_user()` — Permanent Block

```python
# Block abusive user permanently
spam_manager.blacklist_user("60987654321")
```

### 4. `unblock_user()` — Manual Unblock

```python
# Unblock a temporarily blocked user
spam_manager.unblock_user("60123456789")
```

### 5. `get_user_status()` — Debug Info

```python
status = spam_manager.get_user_status("60123456789")
# Returns:
# {
#     'user_id': '60123456789',
#     'whitelisted': False,
#     'blacklisted': False,
#     'blocked': False,
#     'blocked_until': None,
#     'violations': 2,
#     'current_cooldown': 2.0,
#     'messages_last_minute': 5,
#     'messages_last_hour': 23
# }
```

---

## Configuration Reference

### Rate Limiting

| Setting | Default | Description |
|---------|---------|-------------|
| `max_messages_per_minute` | 10 | Max messages in 60 seconds |
| `max_messages_per_hour` | 100 | Max messages in 3600 seconds |
| `burst_window_seconds` | 60 | Window for burst detection |
| `burst_threshold` | 5 | Messages in burst window = blocked |

### Flood Detection

| Setting | Default | Description |
|---------|---------|-------------|
| `duplicate_threshold` | 3 | Same message X times = flood |
| `duplicate_window_seconds` | 60 | Window for duplicate detection |
| `similarity_threshold` | 0.8 | 80%+ similar = spam |

### Cooldown

| Setting | Default | Description |
|---------|---------|-------------|
| `min_seconds_between_messages` | 2 | Minimum delay between messages |
| `escalate_cooldown_after_violations` | True | Increase cooldown after violations |
| `max_cooldown_seconds` | 30 | Maximum cooldown duration |

### Blocking

| Setting | Default | Description |
|---------|---------|-------------|
| `auto_block_after_violations` | 5 | Violations before auto-block |
| `block_duration_minutes` | 30 | How long to block |
| `warning_threshold` | 3 | Violations before warning |

---

## Step-by-Step: How I Built This

### Step 1: Set Up Data Structures

```python
class AntiSpamManager:
    def __init__(self, config: Dict = None):
        # User tracking
        self.user_messages: Dict[str, deque] = defaultdict(lambda: deque(maxlen=200))
        self.user_violations: Dict[str, int] = defaultdict(int)
        self.user_last_message: Dict[str, float] = {}
        self.user_cooldowns: Dict[str, float] = defaultdict(lambda: 2.0)
        self.blocked_users: Dict[str, float] = {}  # user_id -> unblock_time
        self.user_message_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))

        # IP tracking (web chat)
        self.ip_requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.blocked_ips: Dict[str, float] = {}
```

### Step 2: Implement Cooldown Check

```python
def _check_cooldown(self, user_id: str, current_time: float) -> Tuple[bool, Optional[str]]:
    if user_id not in self.user_last_message:
        return True, None

    last_message_time = self.user_last_message[user_id]
    required_cooldown = self.user_cooldowns[user_id]
    time_since_last = current_time - last_message_time

    if time_since_last < required_cooldown:
        remaining = int(required_cooldown - time_since_last)
        return False, f"Please wait {remaining} seconds before sending another message."

    return True, None
```

### Step 3: Implement Rate Limiting

```python
def _check_rate_limit(self, user_id: str, current_time: float) -> Tuple[bool, Optional[str]]:
    messages = self.user_messages[user_id]

    # Per minute check
    one_minute_ago = current_time - 60
    messages_last_minute = sum(1 for t in messages if t > one_minute_ago)

    if messages_last_minute >= self.config['rate_limit']['max_messages_per_minute']:
        return False, f"You're sending messages too quickly. Maximum 10 per minute."

    # Per hour check
    one_hour_ago = current_time - 3600
    messages_last_hour = sum(1 for t in messages if t > one_hour_ago)

    if messages_last_hour >= self.config['rate_limit']['max_messages_per_hour']:
        return False, f"You've reached the maximum of 100 messages per hour."

    # Burst detection
    burst_cutoff = current_time - self.config['rate_limit']['burst_window_seconds']
    messages_in_burst = sum(1 for t in messages if t > burst_cutoff)

    if messages_in_burst >= self.config['rate_limit']['burst_threshold']:
        return False, "Please slow down. You're sending messages too rapidly."

    return True, None
```

### Step 4: Implement Flood Detection

```python
def _check_flood(self, user_id: str, message: str, current_time: float) -> Tuple[bool, Optional[str]]:
    history = self.user_message_history[user_id]

    # Count exact duplicates in recent history
    duplicate_window = self.config['flood_detection']['duplicate_window_seconds']
    recent_cutoff = current_time - duplicate_window
    recent_messages = [h['message'] for h in history if h['time'] > recent_cutoff]

    duplicate_count = sum(
        1 for msg in recent_messages
        if msg.lower().strip() == message.lower().strip()[:100]
    )

    if duplicate_count >= self.config['flood_detection']['duplicate_threshold']:
        return False, "Please stop sending the same message repeatedly."

    # Check similarity
    similar_count = 0
    for msg in recent_messages[-5:]:
        similarity = self._calculate_similarity(message[:100].lower(), msg.lower())
        if similarity >= self.config['flood_detection']['similarity_threshold']:
            similar_count += 1

    if similar_count >= self.config['flood_detection']['duplicate_threshold']:
        return False, "Please stop sending similar messages repeatedly."

    return True, None
```

### Step 5: Implement Similarity Calculation

```python
def _calculate_similarity(self, text1: str, text2: str) -> float:
    """Simple word-based Jaccard similarity"""
    if not text1 or not text2:
        return 0.0

    set1 = set(text1.split())
    set2 = set(text2.split())

    if not set1 or not set2:
        return 0.0

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    return intersection / union if union > 0 else 0.0
```

### Step 6: Implement Violation Recording and Auto-Block

```python
def _record_violation(self, user_id: str, violation_type: str):
    self.user_violations[user_id] += 1
    violation_count = self.user_violations[user_id]

    logger.warning(f"Violation: {user_id} | {violation_type} | total: {violation_count}")

    # Escalate cooldown
    if self.config['cooldown']['escalate_cooldown_after_violations']:
        new_cooldown = min(
            self.user_cooldowns[user_id] * 1.5,
            self.config['cooldown']['max_cooldown_seconds']
        )
        self.user_cooldowns[user_id] = new_cooldown

    # Auto-block if threshold reached
    if violation_count >= self.config['blocking']['auto_block_after_violations']:
        block_duration = self.config['blocking']['block_duration_minutes'] * 60
        self.blocked_users[user_id] = time.time() + block_duration

        logger.warning(f"AUTO-BLOCKED: {user_id} for {block_duration // 60} minutes")
```

### Step 7: Implement Webhook Validation

```python
class WebhookValidator:
    def __init__(self, webhook_secret: Optional[str] = None):
        self.webhook_secret = webhook_secret
        self.enabled = bool(webhook_secret)

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        if not self.enabled:
            return True

        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)
```

---

## Integration in app.py

```python
from core.anti_spam import AntiSpamManager

# Initialize at startup
spam_manager = AntiSpamManager(config.get('anti_spam', {}))

# In webhook handler
@app.route('/webhook/whapi', methods=['POST'])
def whapi_webhook():
    phone = extract_phone(request.json)
    message = extract_message(request.json)

    # Check spam
    allowed, reason = spam_manager.check_message(
        user_id=phone,
        message=message
    )

    if not allowed:
        logger.warning(f"Message blocked: {phone} - {reason}")
        # Optionally send the reason back to customer
        return jsonify({"status": "blocked", "reason": reason}), 200

    # Process normally
    process_message(phone, message)
    return jsonify({"status": "ok"}), 200
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Legitimate user blocked | Too many messages | Add to whitelist or increase limits |
| Spam getting through | Limits too high | Lower thresholds |
| All messages blocked | Config error | Check config values |

### Debug Commands

```python
# Check user status
status = spam_manager.get_user_status("60123456789")
print(status)

# Manually unblock
spam_manager.unblock_user("60123456789")

# Add to whitelist (staff, VIPs)
spam_manager.whitelist_user("60123456789")
```

### Logging

```
⚠️ Rate limit exceeded: 12/10 per minute
🌊 Flood detected: 4 duplicate messages
🚫 AUTO-BLOCKED USER: 60123456789 (5 violations, 30 minutes)
✅ User unblocked: 60123456789
```

---

## Best Practices

### 1. Whitelist Staff and VIPs

```python
# Add staff numbers to whitelist
staff_numbers = ["60123456789", "60120000000"]
for number in staff_numbers:
    spam_manager.whitelist_user(number)
```

### 2. Monitor Violation Patterns

```python
# Periodically check for patterns
for user_id, violations in spam_manager.user_violations.items():
    if violations >= 3:
        logger.info(f"High violation user: {user_id} ({violations})")
```

### 3. Clean Up Old Data

```python
# Call periodically (e.g., every hour)
spam_manager.cleanup_old_data()
```

### 4. Adjust Limits Based on Usage

```python
# For busy hours, you might increase limits
spam_manager.config['rate_limit']['max_messages_per_minute'] = 15
```

---

## Summary

The Anti-Spam System provides **multi-layer protection**:

- **5 protection layers**: Whitelist/Blacklist → Blocking → Cooldown → Rate Limit → Flood Detection
- **Automatic escalation**: Violations increase cooldown and trigger auto-block
- **Configurable thresholds**: Adjust to business needs
- **IP-based limiting**: Protects web chat from abuse
- **Webhook validation**: Ensures authentic requests

This system protects both the business WhatsApp account and the AI API from abuse while ensuring legitimate customers can communicate freely.
