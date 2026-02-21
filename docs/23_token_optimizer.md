# Token Optimizer (Prompt Caching Strategy)

## Overview

The Token Optimizer is a **cost-saving utility** that restructures messages to maximize OpenAI prompt caching. It reduces API costs by ensuring static content is cached and dynamic content is minimized.

**Location:** `utils/token_optimizer.py`
**Lines of code:** ~275 lines
**Dependencies:** `utils/logger.py`

---

## What is the Purpose?

The Token Optimizer exists to:

1. **Reduce API Costs** — Get 50% discount on cached tokens from OpenAI.

2. **Optimize Message Structure** — Place static content first for caching.

3. **Filter Knowledge Base** — Only send relevant KB sections.

4. **Compress Memory** — Minimize customer context token usage.

5. **Track Token Usage** — Estimate and log token consumption.

---

## OpenAI Prompt Caching

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                 OpenAI Prompt Caching                        │
│                                                              │
│  Request 1:                                                  │
│  [System Prompt] [Knowledge Base] [Memory] [Conversation]   │
│  └──────── CACHED (50% off) ─────┘                          │
│                                                              │
│  Request 2:                                                  │
│  [System Prompt] [Knowledge Base] [Memory] [Conversation]   │
│  └──────── SAME PREFIX = CACHED ─┘                          │
│                                                              │
│  Key: Static content at START = Cached                      │
│       Dynamic content at END = Not cached (but small)       │
└─────────────────────────────────────────────────────────────┘
```

### Caching Rules

| Position | Content Type | Cached? | Cost |
|----------|--------------|---------|------|
| First | System Prompt | ✅ Yes | 50% off |
| Second | Knowledge Base | ✅ Yes | 50% off |
| Third | Memory Context | ❌ No | Full price |
| Fourth | Conversation | ❌ No | Full price |

### Cost Savings Example

```
Without Caching:
  System prompt:    2,000 tokens × $0.01 = $0.020
  Knowledge base:   3,000 tokens × $0.01 = $0.030
  Memory:             200 tokens × $0.01 = $0.002
  Conversation:     1,000 tokens × $0.01 = $0.010
  TOTAL: $0.062 per request

With Caching:
  System prompt:    2,000 tokens × $0.005 = $0.010 (50% off)
  Knowledge base:   3,000 tokens × $0.005 = $0.015 (50% off)
  Memory:             200 tokens × $0.01  = $0.002
  Conversation:     1,000 tokens × $0.01  = $0.010
  TOTAL: $0.037 per request

SAVINGS: 40% cost reduction!
```

---

## The TokenOptimizer Class

### Initialization

```python
class TokenOptimizer:
    """
    Optimizes token usage through:
    1. Message restructuring for prompt caching
    2. Knowledge base section extraction
    3. Memory context compression
    """

    # Keywords for selective KB section retrieval
    KB_SECTION_KEYWORDS = {
        'pricing': ['price', 'cost', 'rm', 'how much', '多少钱', '价格', 'fee'],
        'cupping': ['cupping', '拔罐', 'cup'],
        'guasha': ['guasha', 'gua sha', '刮痧', 'scraping'],
        'booking': ['book', 'appointment', '预约', '预订', 'reserve'],
        'membership': ['member', '会员', 'register', '注册', 'birthday', '生日'],
        'hours': ['hour', 'time', 'open', 'close', '几点', '营业', '时间'],
        'therapist': ['therapist', 'male', 'female', '技师', '男', '女'],
    }

    def __init__(self):
        self.cached_static_content = None
        self.kb_sections = {}
```

---

## Key Methods

### 1. structure_messages_for_caching() — Message Restructuring

```python
def structure_messages_for_caching(
    self,
    system_prompt: str,
    knowledge_base: str,
    memory_context: Optional[str],
    conversation: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Structure messages to maximize OpenAI prompt caching.

    Order (for caching):
    1. System prompt (STATIC - cached)
    2. Knowledge base (STATIC - cached)
    3. Memory context (DYNAMIC - not cached, but small)
    4. Conversation history

    Args:
        system_prompt: The system prompt text
        knowledge_base: Full or filtered knowledge base
        memory_context: Optional customer memory/context
        conversation: List of conversation messages

    Returns:
        List of properly structured messages
    """
```

**Message Structure:**

```
┌─────────────────────────────────────────────────────────────┐
│                    STRUCTURED MESSAGES                       │
├─────────────────────────────────────────────────────────────┤
│  Message 1: System Prompt                                    │
│  {"role": "system", "content": "You are a helpful..."}     │
│  ─────────────────── CACHED ───────────────────────         │
├─────────────────────────────────────────────────────────────┤
│  Message 2: Knowledge Base                                   │
│  {"role": "system", "content": "REFERENCE INFO:\n..."}     │
│  ─────────────────── CACHED ───────────────────────         │
├─────────────────────────────────────────────────────────────┤
│  Message 3: Memory Context (optional)                        │
│  {"role": "system", "content": "CUSTOMER CONTEXT:\n..."}   │
│  ─────────────────── NOT CACHED ───────────────────         │
├─────────────────────────────────────────────────────────────┤
│  Message 4+: Conversation History                            │
│  {"role": "user", "content": "I want to book..."}          │
│  {"role": "assistant", "content": "Sure! What time?"}      │
│  ─────────────────── NOT CACHED ───────────────────         │
└─────────────────────────────────────────────────────────────┘
```

**Usage:**

```python
optimizer = TokenOptimizer()

messages = optimizer.structure_messages_for_caching(
    system_prompt="You are SERENITY booking assistant...",
    knowledge_base="SERVICES:\n- 60min foot massage RM68...",
    memory_context="CUSTOMER: John, returning customer",
    conversation=[
        {"role": "user", "content": "I want to book tomorrow"},
        {"role": "assistant", "content": "What time works for you?"}
    ]
)

# Result: Properly ordered messages for OpenAI
# [system_prompt, knowledge_base, memory, user_msg, assistant_msg]
```

---

### 2. get_relevant_kb_sections() — Knowledge Base Filtering

```python
def get_relevant_kb_sections(
    self,
    full_kb: str,
    user_message: str,
    always_include: List[str] = None
) -> str:
    """
    Extract only relevant KB sections based on user message.
    Reduces KB tokens by ~50-70% for most queries.

    Args:
        full_kb: The full knowledge base text
        user_message: The user's message to analyze
        always_include: Sections to always include (e.g., ['BUSINESS_INFO'])

    Returns:
        Filtered knowledge base with relevant sections only
    """
```

**Keyword Matching:**

```
┌─────────────────────────────────────────────────────────────┐
│                 KB Section Selection                         │
├─────────────────────────────────────────────────────────────┤
│  User: "How much is foot massage?"                          │
│                                                              │
│  Keywords detected: "how much" → PRICING section            │
│                                                              │
│  FULL KB (3000 tokens):                                     │
│  - BUSINESS_INFO                                            │
│  - SERVICES_PRICING  ← Selected                             │
│  - MEMBERSHIP                                               │
│  - BOOKING_RULES                                            │
│  - THERAPISTS                                               │
│  - CUPPING_INFO                                             │
│  - GUASHA_INFO                                              │
│                                                              │
│  FILTERED KB (900 tokens):                                  │
│  - BUSINESS_INFO (always included)                          │
│  - SERVICES_PRICING (keyword match)                         │
│                                                              │
│  SAVINGS: 70% token reduction!                              │
└─────────────────────────────────────────────────────────────┘
```

**Keyword Mappings:**

| Section | Keywords (EN) | Keywords (CN) |
|---------|---------------|---------------|
| PRICING | price, cost, rm, how much, fee | 多少钱, 价格 |
| CUPPING | cupping, cup | 拔罐 |
| GUASHA | guasha, gua sha, scraping | 刮痧 |
| BOOKING | book, appointment, reserve | 预约, 预订 |
| MEMBERSHIP | member, register, birthday | 会员, 注册, 生日 |
| HOURS | hour, time, open, close | 几点, 营业, 时间 |
| THERAPIST | therapist, male, female | 技师, 男, 女 |

**Usage:**

```python
optimizer = TokenOptimizer()

# Full KB is 3000+ tokens
full_kb = """
BUSINESS_INFO:
Serenity Reflexology Example City...

SERVICES_PRICING:
60min foot massage - RM68
90min body massage - RM128...

MEMBERSHIP:
Register for birthday discounts...

CUPPING_INFO:
Traditional cupping therapy...
"""

# User asks about pricing
filtered = optimizer.get_relevant_kb_sections(
    full_kb=full_kb,
    user_message="How much is foot massage?",
    always_include=['BUSINESS_INFO']
)

# Result: Only BUSINESS_INFO + SERVICES_PRICING
# 70% token reduction!
```

---

### 3. compress_memory_context() — Memory Compression

```python
def compress_memory_context(
    self,
    memory_data: Dict[str, Any],
    max_tokens: int = 200
) -> str:
    """
    Compress memory context to essential information only.

    Args:
        memory_data: Customer memory dictionary
        max_tokens: Maximum tokens for memory context

    Returns:
        Compressed memory string
    """
```

**Compression Strategy:**

```
┌─────────────────────────────────────────────────────────────┐
│                   FULL MEMORY (500 tokens)                   │
├─────────────────────────────────────────────────────────────┤
│  {                                                          │
│    "name": "John Tan",                                      │
│    "phone": "60123456789",                                  │
│    "preferences": "Likes strong pressure, female therapist,│
│                    usually books weekends, prefers foot    │
│                    massage, mentioned neck pain last time, │
│                    birthday in March...",                  │
│    "total_conversations": 12,                              │
│    "last_visit": "2026-02-15",                             │
│    "is_member": true,                                      │
│    "booking_history": [...50 items...],                    │
│    "notes": "VIP customer, always tips well..."            │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 COMPRESSED MEMORY (50 tokens)                │
├─────────────────────────────────────────────────────────────┤
│  CUSTOMER CONTEXT:                                          │
│  Name: John Tan                                             │
│  Preferences: Likes strong pressure, female therapist...   │
│  Returning customer (12 visits)                             │
│  Member: Yes                                                │
└─────────────────────────────────────────────────────────────┘

                    90% TOKEN REDUCTION!
```

**Essential Fields Only:**

| Field | Included? | Reason |
|-------|-----------|--------|
| `name` | ✅ Yes | Personalization |
| `preferences` | ✅ Yes (first 100 chars) | Service matching |
| `total_conversations` | ✅ Yes (if > 1) | Return customer indicator |
| `is_member` | ✅ Yes | Membership status |
| `phone` | ❌ No | Already known from sender |
| `booking_history` | ❌ No | Too large, pre-loaded separately |
| `last_visit` | ❌ No | Less important |
| `notes` | ❌ No | Internal notes |

**Usage:**

```python
optimizer = TokenOptimizer()

memory_data = {
    "name": "John Tan",
    "preferences": "Likes strong pressure, prefers female therapist, usually books weekend mornings",
    "total_conversations": 12,
    "is_member": True,
    "booking_history": [...]  # Large array
}

compressed = optimizer.compress_memory_context(
    memory_data=memory_data,
    max_tokens=200
)

# Result:
# "CUSTOMER CONTEXT:
# Name: John Tan
# Preferences: Likes strong pressure, prefers female therapist, usually books weekend mornings
# Returning customer (12 visits)
# Member: Yes"
```

---

## Helper Functions

### 1. estimate_tokens() — Quick Token Estimation

```python
def estimate_tokens(text: str) -> int:
    """Quick token estimation (1 token ≈ 4 characters)"""
    return len(text) // 4 if text else 0
```

**Usage:**

```python
text = "Hello, I want to book a foot massage for tomorrow at 3pm"
tokens = estimate_tokens(text)
# Result: 14 tokens (56 chars / 4)
```

**Accuracy:**

| Language | Actual Ratio | Estimation Accuracy |
|----------|--------------|---------------------|
| English | 1 token ≈ 4 chars | ~90% accurate |
| Chinese | 1 token ≈ 1.5 chars | ~70% accurate |
| Mixed | 1 token ≈ 3 chars | ~80% accurate |

---

### 2. log_token_usage() — Token Logging

```python
def log_token_usage(
    system_prompt: str,
    knowledge_base: str,
    memory: str,
    conversation: List[Dict],
    label: str = "Message"
) -> Dict[str, int]:
    """Log estimated token usage for debugging"""
```

**Output:**

```
📊 Token Estimate (Message):
   System prompt: 500
   Knowledge base: 750
   Memory: 50
   Conversation: 200
   TOTAL: 1500
```

**Usage:**

```python
from utils.token_optimizer import log_token_usage

tokens = log_token_usage(
    system_prompt=system_prompt,
    knowledge_base=filtered_kb,
    memory=compressed_memory,
    conversation=messages,
    label="Request to GPT-4"
)

print(f"Total tokens: {tokens['total']}")
```

---

## Global Instance

A global instance is created for convenience:

```python
# At module level
token_optimizer = TokenOptimizer()

# Use anywhere
from utils.token_optimizer import token_optimizer

messages = token_optimizer.structure_messages_for_caching(...)
```

---

## Integration Flow

### Complete Token Optimization Flow

```
┌─────────────────────────────────────────────────────────────┐
│              Customer Message Received                       │
│              "How much is 60min foot massage?"              │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Filter Knowledge Base                               │
│                                                              │
│  get_relevant_kb_sections(                                   │
│      full_kb=full_kb,                                       │
│      user_message="How much is 60min foot massage?"         │
│  )                                                          │
│                                                              │
│  Keywords: "how much" → PRICING section                     │
│  Result: BUSINESS_INFO + SERVICES_PRICING only              │
│  Reduction: 3000 → 900 tokens (70% saved)                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Compress Memory                                     │
│                                                              │
│  compress_memory_context(                                    │
│      memory_data=customer_memory,                           │
│      max_tokens=200                                         │
│  )                                                          │
│                                                              │
│  Result: Essential info only (name, prefs, member status)   │
│  Reduction: 500 → 50 tokens (90% saved)                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Structure Messages for Caching                      │
│                                                              │
│  structure_messages_for_caching(                            │
│      system_prompt=system_prompt,      # Position 1 - CACHED │
│      knowledge_base=filtered_kb,       # Position 2 - CACHED │
│      memory_context=compressed_memory, # Position 3         │
│      conversation=messages             # Position 4         │
│  )                                                          │
│                                                              │
│  Result: Properly ordered messages for OpenAI               │
│  Cached prefix: system_prompt + knowledge_base              │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Send to OpenAI                                      │
│                                                              │
│  Static content (cached): 1400 tokens × $0.005 = $0.007    │
│  Dynamic content:          250 tokens × $0.01  = $0.0025   │
│                                                              │
│  TOTAL COST: $0.0095                                        │
│  WITHOUT OPTIMIZATION: $0.035                               │
│  SAVINGS: 73%                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Integration in app.py

```python
from utils.token_optimizer import token_optimizer, log_token_usage

def generate_ai_response(phone: str, message: str, ...):
    # Step 1: Get relevant KB sections only
    filtered_kb = token_optimizer.get_relevant_kb_sections(
        full_kb=knowledge_base,
        user_message=message,
        always_include=['BUSINESS_INFO']
    )

    # Step 2: Compress memory context
    compressed_memory = token_optimizer.compress_memory_context(
        memory_data=customer_memory,
        max_tokens=200
    )

    # Step 3: Structure messages for caching
    messages = token_optimizer.structure_messages_for_caching(
        system_prompt=system_prompt,
        knowledge_base=filtered_kb,
        memory_context=compressed_memory,
        conversation=conversation_history
    )

    # Step 4: Log token usage (debug)
    log_token_usage(
        system_prompt=system_prompt,
        knowledge_base=filtered_kb,
        memory=compressed_memory,
        conversation=conversation_history,
        label=f"Request for {phone}"
    )

    # Step 5: Send to OpenAI
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        ...
    )
```

---

## Cost Analysis

### Before vs After Optimization

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| System Prompt | 2000 tokens | 2000 tokens (cached) | 50% |
| Knowledge Base | 3000 tokens | 900 tokens (cached) | 85% |
| Memory | 500 tokens | 50 tokens | 90% |
| Conversation | 500 tokens | 500 tokens | 0% |
| **TOTAL** | **6000 tokens** | **3450 tokens** | **42%** |
| **COST** | **$0.06** | **$0.025** | **58%** |

### Monthly Savings Estimate

```
Daily conversations: 200
Tokens per conversation: 6000 → 3450

Before: 200 × $0.06 = $12/day = $360/month
After:  200 × $0.025 = $5/day = $150/month

MONTHLY SAVINGS: $210 (58% reduction)
```

---

## Best Practices

### 1. Always Structure Messages Correctly

```python
# Good - Static content first
messages = token_optimizer.structure_messages_for_caching(
    system_prompt=prompt,      # First (cached)
    knowledge_base=kb,         # Second (cached)
    memory_context=memory,     # Third (small)
    conversation=history       # Last (varies)
)

# Bad - Mixed order (no caching benefit)
messages = [
    {"role": "user", "content": user_msg},       # Variable first
    {"role": "system", "content": system_prompt}, # Static after
    ...
]
```

### 2. Filter KB for Every Request

```python
# Good - Filter based on user message
filtered_kb = token_optimizer.get_relevant_kb_sections(
    full_kb=knowledge_base,
    user_message=user_message
)

# Bad - Send full KB every time
messages.append({
    "role": "system",
    "content": full_knowledge_base  # 3000+ tokens wasted
})
```

### 3. Keep Memory Minimal

```python
# Good - Compress memory
compressed = token_optimizer.compress_memory_context(
    memory_data=memory,
    max_tokens=200
)

# Bad - Include full history
messages.append({
    "role": "system",
    "content": json.dumps(full_customer_data)  # 500+ tokens
})
```

### 4. Monitor Token Usage

```python
# Log token usage periodically
if DEBUG_MODE:
    log_token_usage(
        system_prompt=system_prompt,
        knowledge_base=filtered_kb,
        memory=compressed_memory,
        conversation=messages,
        label=f"Phone: {phone}"
    )
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| No caching benefit | Messages out of order | Use structure_messages_for_caching() |
| KB not filtered | Keywords not matched | Add keywords to KB_SECTION_KEYWORDS |
| Memory too large | Not compressed | Use compress_memory_context() |
| Token estimate wrong | Chinese text | Adjust ratio for Chinese |

### Debug Checklist

1. Check message order (static first)
2. Verify KB filtering is working
3. Confirm memory is compressed
4. Monitor actual token usage in OpenAI dashboard

---

## Summary

The Token Optimizer provides **significant cost savings**:

- **Message Restructuring** — Static content first for 50% caching discount
- **KB Filtering** — Only relevant sections, 50-70% token reduction
- **Memory Compression** — Essential info only, 90% reduction
- **Token Logging** — Track and debug token usage

Combined, these optimizations can reduce API costs by **40-70%** while maintaining full functionality.
