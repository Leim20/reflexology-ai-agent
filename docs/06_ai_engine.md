# AI Engine

## Overview

The AI Engine is the **core brain** of the chat agent. It serves as the unified interface for all OpenAI API interactions, handling chat completions (GPT-4o-mini), voice transcription (Whisper), and function calling (tool use).

**Source file:** `core/ai_engine.py`
**Lines of code:** ~279 lines
**Dependencies:** `openai` Python SDK, `utils.logger`

---

## What is the Purpose?

The AI Engine exists to:

1. **Centralize AI API calls** — All OpenAI interactions go through one module, making it easy to monitor, debug, and optimize.

2. **Handle multiple AI capabilities** — Text generation, multimodal (images), voice transcription, and function calling are all managed here.

3. **Provide comprehensive logging** — Every API call is logged with timing, token usage, and response details for debugging and cost tracking.

4. **Abstract complexity** — The rest of the application doesn't need to know OpenAI API details; they just call `generate_response()` or `transcribe_audio()`.

5. **Enable cost optimization** — By centralizing API calls, we can track token usage and implement cost-saving measures.

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│   (WhatsApp Handler, Web Handler, Booking System, etc.)     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      AI Engine                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ generate_       │  │ transcribe_     │  │ Function    │ │
│  │ response()      │  │ audio()         │  │ Calling     │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘ │
│           │                    │                   │        │
│           └────────────────────┼───────────────────┘        │
│                                │                             │
│                    ┌───────────▼───────────┐                │
│                    │    OpenAI Client      │                │
│                    │  (self.client)        │                │
│                    └───────────┬───────────┘                │
└────────────────────────────────┼────────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     OpenAI API          │
                    │  - GPT-4o-mini          │
                    │  - Whisper              │
                    └─────────────────────────┘
```

### Initialization

When `AIEngine` is instantiated, it:

1. Receives API key, model name, temperature, and max_tokens as parameters
2. Creates an OpenAI client using the `openai` Python SDK
3. Stores default settings for all subsequent API calls
4. Logs the initialization for debugging

```python
ai_engine = AIEngine(
    api_key="sk-proj-...",
    model="gpt-4o-mini",      # Default model
    temperature=0.7,          # Creativity level (0.0 = deterministic, 1.0 = creative)
    max_tokens=1500           # Max response length
)
```

---

## Key Methods

### 1. `generate_response()` — Chat Completion

**Purpose:** Generate AI responses for customer messages.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `messages` | List[Dict] | Yes | Conversation history in OpenAI format |
| `temperature` | float | No | Override default temperature |
| `max_tokens` | int | No | Override default max_tokens |
| `tools` | List[Dict] | No | Function calling tool definitions |
| `tool_choice` | str | No | "auto", "none", or specific function |
| `model` | str | No | Override default model |

**Returns:**

```python
{
    'content': str,           # AI's response text
    'success': bool,          # True if API call succeeded
    'error': str or None,     # Error message if failed
    'usage': {
        'prompt_tokens': int,
        'completion_tokens': int,
        'total_tokens': int
    },
    'completion_id': str,     # OpenAI response ID
    'model': str,             # Model used
    'elapsed_time': float,    # Seconds taken
    'tool_calls': List or None # Function calls requested by AI
}
```

**Example Usage:**

```python
messages = [
    {"role": "system", "content": "You are Jessica, a reflexology consultant..."},
    {"role": "user", "content": "What massage do you recommend for back pain?"}
]

result = ai_engine.generate_response(messages)

if result['success']:
    print(result['content'])  # AI's recommendation
    print(f"Tokens used: {result['usage']['total_tokens']}")
else:
    print(f"Error: {result['error']}")
```

---

### 2. `transcribe_audio()` — Voice to Text

**Purpose:** Convert voice messages to text using Whisper API.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `audio_file_path` | str | Yes | Path to audio file (MP3, WAV, OGG, M4A, WEBM) |
| `language` | str | No | Language code (e.g., 'en', 'ms', 'zh') for better accuracy |
| `prompt` | str | No | Context prompt to guide transcription |

**Returns:**

```python
{
    'transcription': str,     # Transcribed text
    'success': bool,          # True if successful
    'error': str or None,     # Error message if failed
    'language': str,          # Language used
    'elapsed_time': float     # Seconds taken
}
```

**Example Usage:**

```python
result = ai_engine.transcribe_audio(
    audio_file_path="/tmp/voice_message.ogg",
    language="zh",  # Chinese
    prompt="Reflexology booking appointment massage"  # Expected vocabulary
)

if result['success']:
    print(f"Customer said: {result['transcription']}")
else:
    print(f"Transcription failed: {result['error']}")
```

---

### 3. Function Calling (Tool Use)

**Purpose:** Allow AI to call predefined functions (e.g., `record_booking`, `escalate_to_human`).

**How it works:**

1. You define tools (functions) with JSON schema
2. Pass tools to `generate_response()`
3. AI decides whether to call a function
4. If yes, `tool_calls` is returned with function name and arguments
5. Your code executes the function and returns result to AI

**Example:**

```python
# Define available tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "record_booking",
            "description": "Record a confirmed booking",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string"},
                    "service": {"type": "string"},
                    "date": {"type": "string"},
                    "time": {"type": "string"}
                },
                "required": ["customer_name", "service", "date", "time"]
            }
        }
    }
]

result = ai_engine.generate_response(
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

if result['tool_calls']:
    for tool_call in result['tool_calls']:
        func_name = tool_call['function']['name']
        func_args = json.loads(tool_call['function']['arguments'])
        print(f"AI wants to call: {func_name}({func_args})")
```

---

## Step-by-Step: How I Built This

### Step 1: Create the OpenAI Client

```python
from openai import OpenAI

self.client = OpenAI(api_key=api_key)
```

The `openai` Python SDK handles authentication, retries, and connection management.

### Step 2: Build the API Call

```python
api_params = {
    'model': use_model,
    'messages': messages,
    'temperature': temperature or self.temperature,
    'max_tokens': max_tokens or self.max_tokens
}

# Add function calling if tools provided
if tools:
    api_params['tools'] = tools
    if tool_choice:
        api_params['tool_choice'] = tool_choice

response = self.client.chat.completions.create(**api_params)
```

### Step 3: Extract Response Data

```python
message = response.choices[0].message
content = message.content

# Check for function calls
if hasattr(message, 'tool_calls') and message.tool_calls:
    tool_calls = []
    for tool_call in message.tool_calls:
        tool_calls.append({
            'id': tool_call.id,
            'function': {
                'name': tool_call.function.name,
                'arguments': tool_call.function.arguments
            }
        })
```

### Step 4: Track Token Usage

```python
usage = {
    'prompt_tokens': response.usage.prompt_tokens,
    'completion_tokens': response.usage.completion_tokens,
    'total_tokens': response.usage.total_tokens
}
```

### Step 5: Comprehensive Logging

```python
logger.info(f"✓ Response received in {elapsed_time:.2f}s")
logger.info(f"  Tokens used: {usage['total_tokens']}")
logger.debug(f"  Response preview: {content[:200]}...")
```

### Step 6: Error Handling

```python
except Exception as e:
    logger.error(f"❌ AI RESPONSE GENERATION FAILED")
    logger.error(f"Error: {str(e)}")
    logger.exception("Full error traceback:")

    return {
        'content': None,
        'success': False,
        'error': str(e),
        ...
    }
```

---

## Configuration

### Model Selection

| Model | Cost | Speed | Use Case |
|-------|------|-------|----------|
| `gpt-4o-mini` | Low | Fast | Default for all conversations |
| `gpt-4o` | High | Medium | Complex reasoning, image analysis |
| `gpt-4-turbo` | High | Fast | Long context windows |

### Temperature Settings

| Value | Behavior | Use Case |
|-------|----------|----------|
| 0.0 | Deterministic | Data extraction, validation |
| 0.3 | Consistent | FAQ responses |
| 0.7 | Balanced (default) | Natural conversation |
| 1.0 | Creative | Marketing content |

### Token Limits

| Setting | Value | Notes |
|---------|-------|-------|
| `max_tokens` | 1500 | Default max response length |
| Input limit (gpt-4o-mini) | 128,000 | Context window |
| Output limit (gpt-4o-mini) | 16,384 | Max response tokens |

---

## Cost Tracking

### Token-to-Cost Calculation (GPT-4o-mini)

| Type | Price per 1M tokens |
|------|---------------------|
| Input | $0.15 |
| Output | $0.60 |

**Example:**
- 1000 prompt tokens = $0.00015
- 500 completion tokens = $0.0003
- Total per message = ~$0.00045

### Monitoring in Logs

```
2026-02-13 10:30:45 | INFO | Tokens used: 1847 (prompt: 1347, completion: 500)
```

---

## Integration Points

### Where AI Engine is Called

| Location | Method | Purpose |
|----------|--------|---------|
| `web/app.py` | `generate_response()` | Main conversation |
| `handlers/whatsapp_handler.py` | `transcribe_audio()` | Voice messages |
| `core/date_extractor.py` | `generate_response()` | LLM date parsing fallback |
| `core/booking_extractor.py` | `generate_response()` | Field extraction (deprecated) |

### Initialization in app.py

```python
from core import AIEngine

ai_engine = AIEngine(
    api_key=config.get_env('OPENAI_API_KEY'),
    model=config.get('ai.model', 'gpt-4o-mini'),
    temperature=config.get('ai.temperature', 0.7),
    max_tokens=config.get('ai.max_tokens', 1500)
)
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `AuthenticationError` | Invalid API key | Check `OPENAI_API_KEY` in `.env` |
| `RateLimitError` | Too many requests | Implement backoff or upgrade plan |
| `ContextLengthExceeded` | Conversation too long | Implement summarization |
| `TimeoutError` | Slow response | Increase timeout or retry |
| Empty response | API returned nothing | Check logs for error details |

### Debug Checklist

1. Check API key is set: `echo $OPENAI_API_KEY`
2. Verify model name is valid
3. Check token usage isn't exceeding limits
4. Review logs: `tail -f logs/ChatAgent_*.log | grep "AI"`
5. Test with simple message first

---

## Best Practices

### 1. Always Check Success

```python
result = ai_engine.generate_response(messages)
if not result['success']:
    logger.error(f"AI failed: {result['error']}")
    return "Sorry, I'm having trouble. Please try again."
```

### 2. Use Model Override for Cost Optimization

```python
# Use cheaper model for simple extraction
result = ai_engine.generate_response(
    messages=extraction_messages,
    model="gpt-4o-mini",  # Force cheaper model
    temperature=0         # Deterministic for extraction
)
```

### 3. Log Token Usage for Cost Monitoring

```python
if result['success']:
    tokens = result['usage']['total_tokens']
    logger.info(f"API call used {tokens} tokens")
```

### 4. Handle Function Calls Properly

```python
if result.get('tool_calls'):
    # AI wants to call a function - handle it
    for tc in result['tool_calls']:
        execute_function(tc['function']['name'], tc['function']['arguments'])
else:
    # Normal text response
    reply = result['content']
```

---

## Performance Metrics

### Typical Response Times

| Operation | Time | Notes |
|-----------|------|-------|
| Simple chat | 1-3s | Short messages |
| Complex reasoning | 3-6s | Long context or function calling |
| Voice transcription | 2-5s | Depends on audio length |
| Image analysis | 3-8s | GPT-4o vision |

### Token Usage Patterns

| Conversation Type | Avg Tokens/Message |
|-------------------|-------------------|
| FAQ question | 800-1200 |
| Booking flow | 1500-2500 |
| With knowledge base | 2000-4000 |
| Voice message | 500-1000 (transcription) |

---

## Summary

The AI Engine is the **central nervous system** of the chat agent:

- **Single entry point** for all OpenAI API calls
- **Supports text, voice, and function calling**
- **Comprehensive logging** for debugging and cost tracking
- **Error handling** with graceful degradation
- **Cost optimization** through model selection and token monitoring

Every AI-powered feature flows through this module, making it critical for the entire system's functionality.
