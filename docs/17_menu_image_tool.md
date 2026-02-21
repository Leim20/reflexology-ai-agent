# Menu Image Tool

## Overview

The Menu Image Tool is an **OpenAI function calling tool** that sends the latest menu/price list image to customers via WhatsApp. It supports multiple languages (Chinese, English, Malay) and includes cooldown protection to prevent spam.

**Location:** `web/app.py` (lines 1336-1485)
**Tool:** `send_menu_image`
**Dependencies:** WhatsApp Handler, Chatwoot Handler (optional), static image files

---

## What is the Purpose?

The Menu Image Tool exists to:

1. **Instant Menu Access** — Send menu image when customer asks for prices/services.

2. **Multilingual Support** — Provide Chinese or English menu based on customer's language.

3. **Visual Pricing** — Images are clearer than text for complex pricing tables.

4. **Cooldown Protection** — Prevent repeated sends within short time period.

5. **Dual Delivery** — Send via Chatwoot (if available) or direct WhatsApp.

---

## How It Works

### Menu Request Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Customer: "有没有菜单?" / "Can I see the menu?"           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  AI detects menu request                                     │
│  Decides to call send_menu_image                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  AI calls: send_menu_image(language="chinese")              │
│                                                              │
│  (AI determines language from customer's message)           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Handler:                                                    │
│  1. Check cooldown (skip if sent < 10 seconds ago)          │
│  2. Get menu file path from config                          │
│  3. Read image bytes from file                              │
│  4. Send via Chatwoot OR WhatsApp                           │
│  5. Update cooldown timestamp                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Customer receives:                                          │
│  [Menu Image]                                               │
│  Caption: "这是我们最新的价目表! 有什么需要可以问我 😊"    │
└─────────────────────────────────────────────────────────────┘
```

---

## Function Definition

```python
def get_send_menu_image_function_definition():
    return {
        "type": "function",
        "function": {
            "name": "send_menu_image",
            "description": "Send the latest menu image (Chinese or English) to the customer via WhatsApp. Use when customer asks for menu/price list/menu photo/价目表/菜单/最新价格/etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "enum": ["chinese", "english", "malay"],
                        "description": "Choose which menu image to send: chinese, english, or malay. Default is based on customer's language."
                    }
                },
                "required": []  # Optional - AI detects language
            }
        }
    }
```

---

## Handler Implementation

```python
# Cooldown tracking
menu_image_cooldown = {}
MENU_IMAGE_COOLDOWN_SECONDS = 10


def handle_send_menu_image_function_call(
    function_args: dict,
    sender: str,
    language_hint: str = None,
    conversation_id: int = None
) -> Dict[str, str]:
    """Handle send_menu_image function call from AI"""

    logger.info("=" * 80)
    logger.info("SENDING MENU IMAGE (from AI tool call)")
    logger.info("=" * 80)

    # Get menu configuration
    menu_config = config.get('menu_image', {})
    if not (menu_config.get('enabled') and whatsapp_handler):
        logger.warning("Menu image disabled or WhatsApp handler missing")
        return {'success': False, 'message': 'Menu image not available'}

    # Determine language
    requested_language = function_args.get('language')

    if requested_language == 'chinese':
        menu_file_path = menu_config.get('chinese_file_path')
        caption = menu_config.get('caption_chinese', '')
        language = 'chinese'
    elif requested_language == 'english':
        menu_file_path = menu_config.get('english_file_path')
        caption = menu_config.get('caption_english', '')
        language = 'english'
    elif requested_language == 'malay':
        # Malay users default to English menu
        menu_file_path = menu_config.get('english_file_path')
        caption = menu_config.get('caption_english', '')
        language = 'english'
    elif language_hint == 'chinese':
        menu_file_path = menu_config.get('chinese_file_path')
        caption = menu_config.get('caption_chinese', '')
        language = 'chinese'
    else:
        # Default to English
        language = 'english'
        menu_file_path = menu_config.get('english_file_path')
        caption = menu_config.get('caption_english', '')

    if not menu_file_path:
        logger.warning(f"Menu file path not configured for language: {language}")
        return {'success': False, 'message': f'Menu not configured for {language}'}

    # Check cooldown
    last_sent = menu_image_cooldown.get(sender)
    now_ts = time.time()

    if last_sent and (now_ts - last_sent) < MENU_IMAGE_COOLDOWN_SECONDS:
        logger.info(f"Menu image skipped due to cooldown ({now_ts - last_sent:.1f}s ago)")
        return {
            'success': True,
            'message': 'Menu image recently sent (cooldown)',
            'language': language,
            'caption': caption
        }

    # Read image file
    try:
        with open(menu_file_path, 'rb') as f:
            image_bytes = f.read()
        logger.info(f"Read menu image from: {menu_file_path}")
    except Exception as e:
        logger.error(f"Failed to read menu image: {e}")
        return {'success': False, 'message': 'Failed to read menu image'}

    delivered_via = None
    filename = f"menu_{language}.png"
    mime_type = "image/png"

    # Try Chatwoot first (shows in conversation)
    if chatwoot_handler and conversation_id and image_bytes:
        sent = chatwoot_handler.add_message_with_attachments(
            conversation_id=conversation_id,
            content=caption,
            attachments=[{
                "bytes": image_bytes,
                "filename": filename,
                "mime_type": mime_type
            }],
            message_type="outgoing",
            private=False
        )
        if sent:
            delivered_via = "chatwoot_attachment"

    # Fallback to direct WhatsApp
    if not delivered_via:
        try:
            static_url = f"http://your-server:5002/static/menu/menu_{language}.png"
            result = whatsapp_handler.send_image(
                to=sender,
                image_url=static_url,
                caption=caption
            )

            if result.get('success'):
                delivered_via = "whapi_direct"
            else:
                logger.error(f"Failed to send menu image: {result.get('error')}")
        except Exception as e:
            logger.error(f"Exception sending menu image: {e}")

    # Update cooldown
    if delivered_via:
        menu_image_cooldown[sender] = now_ts
        logger.info(f"Menu image sent successfully via {delivered_via}")
        return {
            'success': True,
            'message': 'Menu image sent',
            'language': language,
            'caption': caption,
            'route': delivered_via
        }

    return {'success': False, 'message': 'Failed to send menu image'}
```

---

## Language Detection

### Automatic Detection (in app.py)

```python
def detect_language(message: str) -> str:
    """
    Detect if message is primarily Chinese, Malay, or English.
    Used to choose which menu image URL to send.
    """
    if not message:
        return "english"

    message_lower = message.lower()

    # Malay keyword detection
    malay_keywords = [
        'nak', 'sini', 'kah', 'boleh', 'saya', 'untuk', 'bila', 'berapa',
        'ada', 'tak', 'dah', 'apa', 'mana', 'siapa', 'kenapa', 'macam',
        'urut', 'servis', 'harga', 'tarikh', 'jantina', 'lelaki', 'perempuan'
    ]

    malay_count = sum(1 for word in malay_keywords if word in message_lower)

    if malay_count >= 2:
        return "malay"

    if malay_count == 1 and len(message) < 20:
        return "malay"

    # Chinese character detection
    chinese_chars = sum(1 for c in message if "一" <= c <= "鿿")
    total_chars = len([c for c in message if c.strip()])

    if total_chars == 0:
        return "english"

    ratio = chinese_chars / total_chars

    if ratio > 0.3:
        return "chinese"

    return "english"
```

### AI Language Selection

The AI can also determine language based on conversation context:

```python
# AI decides based on conversation
Customer: "你好，可以看菜单吗？"
AI calls: send_menu_image(language="chinese")

Customer: "Show me the price list"
AI calls: send_menu_image(language="english")

Customer: "Nak tengok menu"
AI calls: send_menu_image(language="malay")  # Falls back to English
```

---

## Configuration

### config.json

```json
{
    "menu_image": {
        "enabled": true,
        "chinese_file_path": "static/menu/menu_chinese.png",
        "english_file_path": "static/menu/menu_english.png",
        "caption_chinese": "这是我们最新的价目表! 有什么需要可以问我 😊",
        "caption_english": "Here's our latest menu! Let me know if you have any questions 😊"
    }
}
```

### Menu Keywords (for fallback detection)

```python
MENU_KEYWORDS = [
    "menu", "price", "pricing", "price list", "pricelist",
    "菜单", "价目表", "价格", "最新价格", "多少钱",
    "harga", "senarai harga"
]
```

---

## Cooldown Protection

### Why Cooldown?

Without cooldown, a customer spamming "menu" would receive multiple images:

```
Customer: menu
[Image sent]
Customer: menu
[Image sent]  ← Spam
Customer: menu
[Image sent]  ← Spam
```

### With Cooldown (10 seconds)

```
Customer: menu
[Image sent]
Customer: menu
[Skipped - cooldown]  ← Protected
Customer: menu
[Skipped - cooldown]  ← Protected
...wait 10 seconds...
Customer: menu
[Image sent]  ← Allowed again
```

### Implementation

```python
menu_image_cooldown = {}  # {sender: timestamp}
MENU_IMAGE_COOLDOWN_SECONDS = 10

# In handler:
last_sent = menu_image_cooldown.get(sender)
now_ts = time.time()

if last_sent and (now_ts - last_sent) < MENU_IMAGE_COOLDOWN_SECONDS:
    return {'success': True, 'message': 'Menu recently sent (cooldown)'}

# After successful send:
menu_image_cooldown[sender] = now_ts
```

---

## Delivery Methods

### Method 1: Chatwoot Attachment (Preferred)

```python
chatwoot_handler.add_message_with_attachments(
    conversation_id=conversation_id,
    content=caption,
    attachments=[{
        "bytes": image_bytes,
        "filename": "menu_chinese.png",
        "mime_type": "image/png"
    }],
    message_type="outgoing"
)
```

**Advantages:**
- Shows in Chatwoot conversation history
- Staff can see what was sent
- Better tracking

### Method 2: Direct WhatsApp (Fallback)

```python
whatsapp_handler.send_image(
    to=sender,
    image_url="http://server/static/menu/menu.png",
    caption=caption
)
```

**Used when:**
- Chatwoot not configured
- Chatwoot send fails
- No conversation_id available

---

## File Structure

```
static/
└── menu/
    ├── menu_chinese.png    # Chinese price list
    └── menu_english.png    # English price list
```

### Image Requirements

| Property | Recommendation |
|----------|----------------|
| Format | PNG or JPG |
| Size | < 5MB |
| Resolution | 1200x1600 pixels |
| Quality | Clear, readable text |

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Menu not sent | Not enabled in config | Set `enabled: true` |
| File not found | Wrong path | Check file_path in config |
| Wrong language | Detection failed | AI explicitly passes language |
| Image too slow | Large file | Compress image |

### Debug Logging

```
================================================================================
SENDING MENU IMAGE (from AI tool call)
================================================================================
Requested language: chinese
Menu file path: static/menu/menu_chinese.png
Read menu image successfully
Checking cooldown for 60123456789: OK (no recent send)
Attempting Chatwoot attachment...
Chatwoot send successful
Menu image sent successfully via chatwoot_attachment
================================================================================
```

---

## Alternative: AI Text Call Pattern

Sometimes AI outputs a text-based call pattern that gets parsed:

```python
def parse_menu_call_language(ai_response: str) -> Optional[str]:
    """
    Parse AI response for [CALL send_menu_image(language="xxx")] pattern
    """
    patterns = [
        r'\[CALL\s+send_menu_image\s*\(\s*language\s*=\s*["\'](\w+)["\']\s*\)\s*\]',
    ]

    for pattern in patterns:
        match = re.search(pattern, ai_response, re.IGNORECASE)
        if match:
            language = match.group(1).lower()
            if language in ["chinese", "english", "malay"]:
                return language

    return None


def clean_menu_call_from_response(ai_response: str) -> str:
    """
    Remove [CALL send_menu_image(...)] text from AI response
    """
    patterns_to_remove = [
        r'\[CALL\s+send_menu_image\s*\([^\)]*\)\s*\]',
    ]

    cleaned = ai_response
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    return cleaned.strip()
```

---

## Summary

The Menu Image Tool provides **instant visual pricing**:

- **Multilingual** — Chinese, English (Malay falls back to English)
- **AI-triggered** — Called via OpenAI function calling
- **Cooldown protected** — Prevents spam (10 second cooldown)
- **Dual delivery** — Chatwoot preferred, WhatsApp fallback
- **Auto language detection** — Based on customer's message

This makes it easy for customers to see pricing without the AI having to type out all service prices.
