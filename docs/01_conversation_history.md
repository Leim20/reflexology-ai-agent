# Conversation History

## Overview

The Conversation History feature manages every message exchanged between a customer and the AI agent (Jessica). It stores conversations in two layers: **in-memory** (for fast, real-time responses) and **persistently** in Google Sheets (for long-term records).

---

## How It Works

### Layer 1 — In-Memory Sessions (`core/conversation_manager.py`)

Each time a customer sends a message via WhatsApp or Web, the system:

1. **Creates or resumes a session** identified by the customer's phone number (WhatsApp) or browser session ID (Web).
2. **Prepends the system prompt** (Jessica's personality + knowledge base) as the first message.
3. **Appends each message** (user and assistant) with a timestamp to the session.
4. **Sends the full session history** to the AI model (GPT-4o-mini) so the AI understands context.
5. **Receives the AI response** and appends it to the session.

Sessions are stored in a Python dictionary keyed by `session_id`. They are held in RAM and lost on server restart.

```
ConversationManager.conversations = {
    "60123456789@s.whatsapp.net": [
        {"role": "system",    "content": "<knowledge base + prompt>"},
        {"role": "user",      "content": "Hi, what massage do you have?"},
        {"role": "assistant", "content": "Hi! We offer foot massage, body massage..."},
        ...
    ]
}
```

---

### Layer 2 — Persistent Storage in Google Sheets

After every conversation exchange, key data is written to two Google Sheets tabs:

#### Tab: `Conversation History`
| Column | Description |
|--------|-------------|
| A — Phone | Customer's WhatsApp number |
| B — Date | Date of conversation |
| C — Conversation Summary | AI-generated summary of the session |
| D — Interest Category | Detected interest (e.g., Booking, Inquiry, Complaint) |
| E — AI Confidence | Confidence score of the interest detection |

#### Tab: `Conversation Insights`
Stores deeper conversation data including:
- Detected pain points (e.g., "back pain", "stress")
- AI recommendations given
- Follow-up status
- Last updated timestamp

---

### Auto-Summarization (Token Optimization)

When a conversation grows long (exceeds ~3,000 tokens / ~12,000 characters), the system automatically:

1. Takes all messages **except the last 10**.
2. Sends them to GPT-4o-mini with prompt: *"Summarize this conversation in 2–3 sentences focusing on customer's interest, bookings, and preferences."*
3. Replaces the old messages with a single `[Previous conversation summary: ...]` system message.
4. Keeps the last 10 messages intact for full context.

**Result:** Token usage is reduced by ~60–70% while maintaining conversation continuity.

**Threshold settings** in `core/conversation_manager.py`:
```python
max_history_length = 20          # Max messages per session before trimming
summarization_threshold = 3000   # Token count to trigger summarization
```

---

### Context Window Management

If a session exceeds `max_history_length` (20 messages), the system:
- Keeps the system message (index 0)
- Removes the oldest messages
- Preserves the most recent messages

This is separate from summarization — it's a hard cut to prevent memory overflow.

---

## Data Flow Diagram

```
Customer sends message
        │
        ▼
WhatsApp Handler receives webhook
        │
        ▼
ConversationManager.add_message()  ← adds user message to session
        │
        ▼
AI Engine generates response (full session history sent)
        │
        ▼
ConversationManager.add_message()  ← adds AI response to session
        │
        ▼
LeadManager.save_conversation_history()  ← writes to Google Sheets
        │
        ▼
(Every 3+ messages) LeadManager.update_customer_record()
```

---

## Where to Find in Code

| Component | File | Key Method |
|-----------|------|------------|
| In-memory session management | `core/conversation_manager.py` | `add_message()`, `get_conversation_for_api()` |
| Summarization | `core/conversation_manager.py` | `summarize_if_needed()` |
| Google Sheets write | `handlers/tools/lead_manager.py` | `save_conversation_history()` |
| Conversation Insights write | `handlers/tools/lead_manager.py` | `track_conversation_info()` |
| Trigger point (WhatsApp) | `handlers/whatsapp_handler.py` | `handle_message()` |
| Export conversation | `web/app.py` | `/export-conversation` route |

---

## Configuration

In `config/config.json`:
```json
"conversation_history": {
    "save_conversation_summary": true,
    "extract_preferences": true,
    "tiered_detail": {
        "recent_detailed": 3,
        "medium_detail": 10,
        "brief_mention": 20
    }
}
```

**Tiered Detail** controls how much detail is loaded when retrieving customer memory:
- Last 3 conversations → full detail
- Conversations 4–10 → medium detail
- Conversations 11–20 → brief mention only

---

## Cache Behavior

The `CacheManager` (TTL: 300 seconds / 5 minutes) caches Google Sheets reads to reduce API quota usage. Reading conversation history from Sheets uses the cache — only refreshed if data is more than 5 minutes old.

Cache is in `utils/cache_manager.py` and is used by `LeadManager`.

