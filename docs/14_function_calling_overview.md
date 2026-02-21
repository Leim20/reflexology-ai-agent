# OpenAI Function Calling Overview

## Overview

Function Calling is **OpenAI's mechanism for enabling AI to invoke predefined functions** during conversation. Instead of the AI just generating text, it can decide to call specific tools/functions when appropriate, execute them, and use the results to formulate its response.

**Location:** Tool definitions in `web/app.py` (lines 960-1700)
**Total Tools:** 10 function calling tools
**Dependencies:** OpenAI API (GPT-4o-mini), `core/ai_engine.py`

---

## What is the Purpose?

Function Calling exists to:

1. **Enable AI Actions** — Let the AI do things beyond just talking (book appointments, register members, send images).

2. **Structured Data Extraction** — Extract specific fields from natural language in a reliable, typed format.

3. **Prevent Hallucination** — AI calls functions with validated parameters instead of making up information.

4. **Integrate External Systems** — Connect AI responses to Google Sheets, WhatsApp, databases.

5. **Control Flow** — Guide the booking conversation through defined steps.

---

## How It Works

### Function Calling Flow

```
┌─────────────────────────────────────────────────────────────┐
│              Customer Message                                │
│         "I want to book tomorrow 3pm"                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  OpenAI GPT-4o-mini                          │
│                                                              │
│  Input:                                                      │
│  - System prompt (with context)                             │
│  - User message                                              │
│  - Available tools (function definitions)                   │
│                                                              │
│  Decision:                                                   │
│  "I should call update_booking_fields with                  │
│   date='2026-02-22' and time='15:00'"                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              AI Response (with tool_calls)                   │
│                                                              │
│  {                                                           │
│    "choices": [{                                            │
│      "message": {                                           │
│        "tool_calls": [{                                     │
│          "id": "call_abc123",                               │
│          "function": {                                      │
│            "name": "update_booking_fields",                 │
│            "arguments": "{\"date\":\"2026-02-22\",          │
│                          \"time\":\"15:00\"}"               │
│          }                                                  │
│        }]                                                   │
│      }                                                      │
│    }]                                                       │
│  }                                                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              app.py — Function Handler                       │
│                                                              │
│  1. Parse tool_calls from response                          │
│  2. Match function name: "update_booking_fields"            │
│  3. Parse arguments JSON                                    │
│  4. Call handler: handle_update_booking_fields(args)        │
│  5. Execute business logic (save to Redis)                  │
│  6. Return result to AI                                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Second AI Call (with tool result)              │
│                                                              │
│  Input:                                                      │
│  - Previous messages                                        │
│  - Tool result: {"success": true, "saved": ["date","time"]} │
│                                                              │
│  Output:                                                     │
│  "Great! I've noted your booking for tomorrow at 3pm.       │
│   Would you prefer a male or female therapist?"             │
└─────────────────────────────────────────────────────────────┘
```

---

## Your 10 Function Calling Tools

| # | Tool Name | Category | Purpose |
|---|-----------|----------|---------|
| 1 | `escalate_to_human` | Escalation | Hand off to human manager |
| 2 | `register_member` | Membership | Register new member |
| 3 | `record_booking` | Booking | Save confirmed booking |
| 4 | `update_booking_fields` | Booking | Progressive field saving |
| 5 | `validate_booking_datetime` | Booking | Check date/time validity |
| 6 | `send_menu_image` | Utility | Send menu image via WhatsApp |
| 7 | `track_conversation_info` | Analytics | Track pain points & recommendations |
| 8 | `lookup_my_bookings` | Query | Refresh booking history |
| 9 | `check_my_membership` | Query | Refresh membership status |
| 10 | `log_cancellation_reason` | Analytics | Log cancellation reasons |

---

## Function Definition Structure

### Anatomy of a Function Definition

```python
def get_example_function_definition():
    return {
        "type": "function",                    # Always "function"
        "function": {
            "name": "function_name",           # Unique identifier
            "description": "...",              # When/how AI should use it
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",      # string, number, boolean
                        "description": "...",  # What this param means
                        "enum": ["a", "b"]     # Optional: allowed values
                    },
                    "param2": {
                        "type": "string",
                        "description": "..."
                    }
                },
                "required": ["param1"]         # Which params are mandatory
            }
        }
    }
```

### Real Example: escalate_to_human

```python
def get_escalation_function_definition():
    return {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Escalate customer inquiry to human manager when you cannot help. Use when: customer needs special assistance, has complaints, asks to speak with manager, or inquiry requires human judgment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_message": {
                        "type": "string",
                        "description": "The customer's original message that needs escalation"
                    },
                    "escalation_reason": {
                        "type": "string",
                        "description": "Brief clear reason why escalation is needed"
                    },
                    "escalation_type": {
                        "type": "string",
                        "enum": ["special_request", "complaint", "membership", "system_issue", "general"],
                        "description": "Type of escalation to route to correct manager"
                    }
                },
                "required": ["customer_message", "escalation_reason", "escalation_type"]
            }
        }
    }
```

---

## Step-by-Step: How I Built This

### Step 1: Collect All Tool Definitions

```python
def get_all_tools():
    """Collect all function definitions into a list"""
    return [
        get_escalation_function_definition(),
        get_register_member_function_definition(),
        get_record_booking_function_definition(),
        get_update_booking_fields_function_definition(),
        get_validate_booking_datetime_function_definition(),
        get_send_menu_image_function_definition(),
        get_track_conversation_info_function_definition(),
        get_lookup_my_bookings_function_definition(),
        get_check_my_membership_function_definition(),
        get_log_cancellation_reason_function_definition()
    ]
```

### Step 2: Pass Tools to OpenAI API

```python
def generate_response_with_tools(messages, system_prompt):
    response = ai_engine.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            *messages
        ],
        tools=get_all_tools(),        # Pass all tool definitions
        tool_choice="auto"            # Let AI decide when to use tools
    )
    return response
```

### Step 3: Detect Tool Calls in Response

```python
def process_response(response):
    message = response.choices[0].message

    # Check if AI wants to call a function
    if message.tool_calls:
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            # Route to appropriate handler
            result = handle_function_call(function_name, arguments)

            # Continue conversation with tool result
            return continue_with_tool_result(tool_call.id, result)
    else:
        # No tool call, just return AI's text response
        return message.content
```

### Step 4: Route to Function Handlers

```python
def handle_function_call(function_name: str, arguments: dict) -> dict:
    """Route function call to appropriate handler"""

    if function_name == "escalate_to_human":
        return handle_escalation_function_call(arguments)

    elif function_name == "register_member":
        return handle_register_member_function_call(arguments)

    elif function_name == "record_booking":
        return handle_record_booking_function_call(arguments)

    elif function_name == "update_booking_fields":
        return handle_update_booking_fields_function_call(arguments)

    elif function_name == "validate_booking_datetime":
        return validate_booking_datetime(
            arguments['booking_date'],
            arguments['booking_time']
        )

    elif function_name == "send_menu_image":
        return handle_send_menu_image_function_call(arguments)

    elif function_name == "track_conversation_info":
        return handle_track_conversation_info_function_call(arguments)

    elif function_name == "lookup_my_bookings":
        return handle_lookup_my_bookings(arguments)

    elif function_name == "check_my_membership":
        return handle_check_my_membership(arguments)

    elif function_name == "log_cancellation_reason":
        return handle_log_cancellation_reason_function_call(arguments)

    else:
        return {"error": f"Unknown function: {function_name}"}
```

### Step 5: Continue Conversation with Tool Result

```python
def continue_with_tool_result(tool_call_id: str, result: dict) -> str:
    """Send tool result back to AI for final response"""

    # Add tool result to conversation
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": json.dumps(result)
    })

    # Get AI's final response
    response = ai_engine.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=get_all_tools(),
        tool_choice="auto"
    )

    return response.choices[0].message.content
```

---

## Tool Choice Modes

### `tool_choice="auto"` (Default)

AI decides whether to call a tool or respond with text.

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    tools=tools,
    tool_choice="auto"  # AI decides
)
```

### `tool_choice="required"`

Force AI to call at least one tool.

### `tool_choice={"type": "function", "function": {"name": "..."}}`

Force AI to call a specific tool.

```python
# Force update_booking_fields during booking flow
tool_choice = {
    "type": "function",
    "function": {"name": "update_booking_fields"}
}
```

---

## Forcing Tool Calls in Booking Flow

In your booking flow, you force `update_booking_fields` to ensure fields are captured:

```python
# From app.py line 3879-3885
booking_flow_steps = ["pain_point", "service", "datetime", "therapist_gender", "personal_info"]

if should_guide_flow and current_step in booking_flow_steps:
    # Force AI to call update_booking_fields first
    tool_choice = {"type": "function", "function": {"name": "update_booking_fields"}}
    logger.info(f"FORCING update_booking_fields call (step: {current_step})")
else:
    tool_choice = "auto"
```

---

## Best Practices

### 1. Write Clear Descriptions

```python
# Good - specific about when to use
"description": "Escalate to human when: customer has complaints, asks for manager, needs special discount. Do NOT use for simple questions you can answer."

# Bad - vague
"description": "Send message to human"
```

### 2. Use Enums for Fixed Options

```python
"escalation_type": {
    "type": "string",
    "enum": ["complaint", "special_request", "membership", "general"],
    "description": "Type of escalation"
}
```

### 3. Mark Required vs Optional Parameters

```python
"parameters": {
    "properties": {
        "name": {"type": "string"},      # Required
        "notes": {"type": "string"}       # Optional
    },
    "required": ["name"]                  # Only name is required
}
```

### 4. Handle All Possible Errors

```python
def handle_function_call(name, args):
    try:
        result = execute_function(name, args)
        return {"success": True, "data": result}
    except ValidationError as e:
        return {"success": False, "error": f"Invalid input: {e}"}
    except Exception as e:
        return {"success": False, "error": "Internal error"}
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| AI not calling function | Description unclear | Improve description with examples |
| Wrong function called | Similar descriptions | Make descriptions more distinct |
| Missing required params | AI didn't extract | Add examples in description |
| Function call fails | Handler error | Check handler logs |

---

## Summary

Function Calling provides **structured AI actions**:

- **10 tools** for booking, membership, escalation, analytics
- **Auto mode** lets AI decide when to use tools
- **Forced mode** ensures booking fields are captured
- **Handler pattern** routes calls to business logic
- **Tool results** feed back into conversation

This system transforms the AI from a chatbot into an **intelligent agent** that can take real actions.
