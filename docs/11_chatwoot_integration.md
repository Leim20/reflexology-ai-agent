# Chatwoot CRM Integration

## Overview

Chatwoot is an **open-source customer engagement platform** that provides a unified inbox for managing customer conversations. This integration syncs WhatsApp conversations to Chatwoot, enabling human agents to take over from the AI when needed.

**Source file:** `handlers/chatwoot_handler.py`
**Lines of code:** ~353 lines
**Dependencies:** `requests`, `utils.logger`

---

## What is the Purpose?

The Chatwoot Integration exists to:

1. **Provide human oversight** — Staff can see all AI conversations in a dashboard.

2. **Enable human takeover** — When AI can't help, human agents can step in.

3. **Sync customer contacts** — Customer info is automatically created in Chatwoot CRM.

4. **Track conversation history** — Full chat history is visible to support staff.

5. **Support attachments** — Images, documents, and voice messages are forwarded.

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WhatsApp (Customer)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     WHAPI Webhook                            │
│                   (receives message)                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
         ┌────────────────┴────────────────┐
         │                                 │
         ▼                                 ▼
┌─────────────────┐              ┌─────────────────┐
│   AI Engine     │              │   Chatwoot      │
│   (Jessica)     │              │   Handler       │
│                 │              │                 │
│ Process message │              │ 1. Find/create  │
│ Generate reply  │              │    contact      │
│                 │              │ 2. Find/create  │
│                 │              │    conversation │
│                 │              │ 3. Add message  │
└────────┬────────┘              │    (incoming)   │
         │                       └────────┬────────┘
         │                                │
         ▼                                ▼
┌─────────────────────────────────────────────────────────────┐
│                        Chatwoot                              │
│              ┌─────────────────────────────┐                │
│              │      Inbox Dashboard        │                │
│              │                             │                │
│              │  Customer: +60123456789     │                │
│              │  [AI] Hi! How can I help?   │                │
│              │  [Customer] I want to book  │                │
│              │  [AI] Sure! When would...   │                │
│              │                             │                │
│              │  [Type reply here...]       │                │
│              └─────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Human agent replies
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Chatwoot Webhook                           │
│               (outgoing message event)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   ChatwootHandler                            │
│               parse_chatwoot_webhook()                       │
│               → Forward to WhatsApp                          │
└─────────────────────────────────────────────────────────────┘
```

### Message Flow

1. **Customer sends message on WhatsApp**
2. **WHAPI webhook** receives it
3. **AI processes** and generates reply
4. **Chatwoot Handler** syncs message to Chatwoot inbox
5. **Staff sees conversation** in Chatwoot dashboard
6. **If staff replies** in Chatwoot, message is sent back to WhatsApp

---

## Key Methods

### 1. `create_or_get_contact()` — Find or Create Customer

**Purpose:** Ensure customer exists in Chatwoot CRM.

```python
contact = chatwoot_handler.create_or_get_contact(
    phone_number="60123456789",
    name="Alex"
)
# Returns: {'id': 12345, 'name': 'Alex', 'phone_number': '+60123456789', ...}
```

**Behavior:**
- Searches for existing contact by phone number
- Creates new contact if not found
- Returns contact object with ID

### 2. `create_or_get_conversation()` — Find or Create Chat Thread

**Purpose:** Get or create a conversation thread for the contact.

```python
conversation = chatwoot_handler.create_or_get_conversation(
    contact_id=12345,
    source_id="whatsapp_60123456789"
)
# Returns: {'id': 67890, 'status': 'open', ...}
```

### 3. `add_message_to_conversation()` — Add Message to Thread

**Purpose:** Add customer or AI message to Chatwoot conversation.

```python
# Add customer message (incoming)
chatwoot_handler.add_message_to_conversation(
    conversation_id=67890,
    message="I want to book tomorrow",
    message_type="incoming",
    private=False
)

# Add AI response (outgoing)
chatwoot_handler.add_message_to_conversation(
    conversation_id=67890,
    message="Sure! What time works for you?",
    message_type="outgoing",
    private=False
)
```

### 4. `add_message_with_attachments()` — Send Files

**Purpose:** Add message with images, documents, or voice files.

```python
attachments = [{
    "bytes": file_bytes,
    "filename": "voice_message.ogg",
    "mime_type": "audio/ogg"
}]

chatwoot_handler.add_message_with_attachments(
    conversation_id=67890,
    content="[Voice message]",
    attachments=attachments,
    message_type="incoming"
)
```

### 5. `parse_chatwoot_webhook()` — Handle Agent Reply

**Purpose:** Parse Chatwoot webhook when human agent sends message.

```python
parsed = chatwoot_handler.parse_chatwoot_webhook(webhook_data)
# Returns:
# {
#     'conversation_id': 67890,
#     'message_id': 'abc123',
#     'phone_number': '60123456789',
#     'contact_name': 'Alex',
#     'message': 'Hello, this is the manager...',
#     'attachments': [],
#     'is_human_agent': True
# }
```

### 6. `update_contact()` — Update Customer Name

**Purpose:** Update contact name when AI learns it from conversation.

```python
chatwoot_handler.update_contact(
    contact_id=12345,
    name="Alex Tan"
)
```

---

## Step-by-Step: How I Built This

### Step 1: Initialize with Environment Variables

```python
class ChatwootHandler:
    def __init__(self):
        self.api_token = os.getenv("CHATWOOT_API_ACCESS_TOKEN")
        self.base_url = os.getenv("CHATWOOT_BASE_URL")
        self.account_id = os.getenv("CHATWOOT_ACCOUNT_ID")
        self.inbox_id = os.getenv("CHATWOOT_INBOX_ID")

        if not all([self.api_token, self.base_url, self.account_id, self.inbox_id]):
            raise ValueError("Chatwoot configuration incomplete")

        self.headers = {
            "api_access_token": self.api_token,
            "Content-Type": "application/json"
        }
```

### Step 2: Implement Contact Search/Create

```python
def create_or_get_contact(self, phone_number: str, name: str = None):
    search_url = f"{self.base_url}/api/v1/accounts/{self.account_id}/contacts/search"
    create_url = f"{self.base_url}/api/v1/accounts/{self.account_id}/contacts"

    phone_clean = phone_number.strip().lstrip("+")
    variants = [phone_clean, f"+{phone_clean}"]

    # Search with both formats
    for q in variants:
        response = requests.get(search_url, headers=self.headers, params={"q": q})
        if response.status_code == 200:
            contacts = response.json().get("payload", [])
            if contacts:
                return contacts[0]  # Found existing

    # Create new contact
    payload = {
        "inbox_id": int(self.inbox_id),
        "phone_number": f"+{phone_clean}",
    }
    if name:
        payload["name"] = name

    response = requests.post(create_url, headers=self.headers, json=payload)
    return response.json().get("payload", {}).get("contact", response.json())
```

### Step 3: Implement Conversation Management

```python
def create_or_get_conversation(self, contact_id: int, source_id: str = None):
    list_url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations"

    # Check for existing open conversation
    response = requests.get(list_url, headers=self.headers,
                           params={"inbox_id": self.inbox_id, "status": "open"})

    if response.status_code == 200:
        conversations = response.json().get("data", {}).get("payload", [])
        for conv in conversations:
            if conv.get("meta", {}).get("sender", {}).get("id") == contact_id:
                return conv  # Found existing

    # Create new conversation
    payload = {
        "source_id": source_id or f"whatsapp_{contact_id}",
        "inbox_id": int(self.inbox_id),
        "contact_id": contact_id
    }
    response = requests.post(list_url, headers=self.headers, json=payload)
    return response.json()
```

### Step 4: Implement Message Adding

```python
def add_message_to_conversation(self, conversation_id: int, message: str,
                                message_type: str = "incoming", private: bool = False):
    url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages"

    payload = {
        "content": message,
        "message_type": message_type,  # "incoming" or "outgoing"
        "private": private  # True for internal notes
    }

    response = requests.post(url, headers=self.headers, json=payload)
    return response.status_code in [200, 201]
```

### Step 5: Implement Webhook Parsing

```python
def parse_chatwoot_webhook(self, webhook_data: dict):
    event = webhook_data.get("event")
    if event != "message_created":
        return None

    message = webhook_data.get("message", {})
    conversation = webhook_data.get("conversation", {})

    # Check if it's an outgoing message from agent
    message_type = message.get("message_type")
    sender = message.get("sender", {})
    sender_type = sender.get("type", "unknown")

    is_outgoing = message_type in [1, "outgoing"]
    is_from_agent = sender_type in ["user", "User"]

    if not is_outgoing and not is_from_agent:
        return None  # Not from human agent

    # Skip private notes
    if message.get("private", False):
        return None

    # Extract contact info
    contact = conversation.get("meta", {}).get("sender", {})

    return {
        "conversation_id": conversation.get("id"),
        "message_id": message.get("id"),
        "phone_number": contact.get("phone_number", "").replace("+", ""),
        "contact_name": contact.get("name", "Customer"),
        "message": message.get("content", "").strip(),
        "attachments": message.get("attachments", []),
        "is_human_agent": True
    }
```

---

## Configuration

### Environment Variables (.env)

```bash
CHATWOOT_API_ACCESS_TOKEN=your_api_token_here
CHATWOOT_BASE_URL=https://app.chatwoot.com
CHATWOOT_ACCOUNT_ID=12345
CHATWOOT_INBOX_ID=67890
```

### Chatwoot Setup Steps

1. **Create Chatwoot Account** at chatwoot.com (or self-host)
2. **Create an Inbox** (API Inbox type)
3. **Get Inbox ID** from URL: `/app/accounts/X/settings/inboxes/Y/...`
4. **Create API Access Token** in Profile → Access Token
5. **Set up Webhook** pointing to your server

---

## Integration in app.py

### Initialize Handler

```python
from handlers import ChatwootHandler

try:
    chatwoot_handler = ChatwootHandler()
except ValueError:
    chatwoot_handler = None
    logger.warning("Chatwoot disabled - config incomplete")
```

### Sync Messages to Chatwoot

```python
def sync_to_chatwoot(phone: str, name: str, customer_message: str, ai_response: str):
    if not chatwoot_handler:
        return

    # Get or create contact
    contact = chatwoot_handler.create_or_get_contact(phone, name)
    if not contact:
        return

    contact_id = contact.get('id')

    # Get or create conversation
    conversation = chatwoot_handler.create_or_get_conversation(contact_id)
    if not conversation:
        return

    conv_id = conversation.get('id')

    # Add customer message
    chatwoot_handler.add_message_to_conversation(
        conv_id, customer_message, message_type="incoming"
    )

    # Add AI response
    chatwoot_handler.add_message_to_conversation(
        conv_id, ai_response, message_type="outgoing"
    )
```

### Handle Agent Reply Webhook

```python
@app.route('/webhook/chatwoot', methods=['POST'])
def chatwoot_webhook():
    data = request.json

    # Check if it's from Chatwoot
    if not chatwoot_handler.is_chatwoot_webhook(data):
        return jsonify({"error": "Not a Chatwoot webhook"}), 400

    parsed = chatwoot_handler.parse_chatwoot_webhook(data)
    if not parsed:
        return jsonify({"status": "ignored"}), 200

    # Forward to WhatsApp
    phone = parsed['phone_number']
    message = parsed['message']

    whatsapp_handler.send_message(phone, message)

    return jsonify({"status": "forwarded"}), 200
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Contact not created | Invalid phone format | Ensure `+` prefix |
| Message not appearing | Wrong message_type | Check "incoming" vs "outgoing" |
| Webhook not received | URL not set in Chatwoot | Configure webhook URL |
| 401 Unauthorized | Invalid API token | Check CHATWOOT_API_ACCESS_TOKEN |

### Debug Checklist

1. Check all 4 env vars are set
2. Verify inbox ID is correct (API Inbox type)
3. Test API token with curl
4. Check webhook URL is publicly accessible
5. Review Chatwoot logs

### Test API Connection

```bash
curl -X GET "https://app.chatwoot.com/api/v1/accounts/{ACCOUNT_ID}/contacts" \
  -H "api_access_token: {YOUR_TOKEN}"
```

---

## Best Practices

### 1. Handle Missing Chatwoot Gracefully

```python
if chatwoot_handler:
    sync_to_chatwoot(phone, name, message, response)
# Don't crash if Chatwoot is unavailable
```

### 2. Update Contact Name When Learned

```python
if customer_name and contact_id:
    chatwoot_handler.update_contact(contact_id, customer_name)
```

### 3. Use Private Notes for Internal Info

```python
# Add internal note (not visible to customer)
chatwoot_handler.add_message_to_conversation(
    conv_id,
    "Customer has 5 previous bookings. VIP status.",
    message_type="outgoing",
    private=True  # Internal note
)
```

### 4. Avoid Duplicate Messages

```python
# Use message_id for deduplication
processed_messages = set()

if parsed['message_id'] in processed_messages:
    return  # Skip duplicate
processed_messages.add(parsed['message_id'])
```

---

## Summary

The Chatwoot Integration provides **human oversight and takeover capability**:

- **Contact management**: Auto-create and sync customer contacts
- **Conversation threading**: Keep all messages organized
- **Two-way sync**: Messages flow both directions
- **Attachment support**: Forward images, documents, voice
- **Human takeover**: Staff can reply directly from Chatwoot

This integration transforms the AI from a standalone bot into a **supervised agent** that can hand off to humans when needed.
